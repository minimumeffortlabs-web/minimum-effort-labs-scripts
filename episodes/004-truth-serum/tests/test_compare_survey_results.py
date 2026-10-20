import csv
import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'compare_survey_results.py'
spec = importlib.util.spec_from_file_location('survey_lesson', SOURCE)
lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lesson)


class SurveyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, rows, header=None):
        path = self.root / name
        with path.open('w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header or ['customer_id', 'satisfaction_rating'])
            writer.writerows(rows)
        return path

    def run_cli(self, before, after, output='report.txt'):
        return subprocess.run([sys.executable, str(SOURCE), str(before), str(after), '--output', str(self.root/output)], capture_output=True, text=True, encoding='utf-8')

    def test_exact_pairs_and_means(self):
        pairs = lesson.paired_changes({'C001': 9, 'C002': 8, 'C003': 10, 'C004': 7}, {'C001': 3, 'C002': 2, 'C003': 4, 'C004': 1})
        self.assertTrue(all(row[3] == -6 for row in pairs))
        summary = lesson.summarize(pairs)
        self.assertEqual((summary['before'], summary['after'], summary['change'], summary['declines']), (8.5, 2.5, -6, 4))

    def test_invalid_missing_boundary_ratings(self):
        path = self.write('a.csv', [[f'C{i}', x] for i, x in enumerate(['', '-1', '0', '11', 'NaN', 'inf', '3.5', 'word', '1', '10'])])
        data = lesson.read_survey(path)
        self.assertEqual(data['ratings'], {'C8': 1, 'C9': 10})
        self.assertEqual(len(data['issues']), 8)

    def test_duplicate_ids_all_excluded_even_when_one_invalid(self):
        for rows in [[['A', 9], ['A', 3]], [['A', ''], ['A', 3]]]:
            data = lesson.read_survey(self.write('a.csv', rows))
            self.assertNotIn('A', data['ratings']); self.assertEqual(data['duplicates'], ['A'])

    def test_missing_ids_and_malformed_fields(self):
        data = lesson.read_survey(self.write('a.csv', [['', 5], ['A'], ['B', 4, 'extra'], ['C', 7]]))
        self.assertEqual(data['ratings'], {'C': 7})
        self.assertEqual(len(data['issues']), 3)

    def test_unmatched_and_invalid_pair_excluded_from_same_cohort(self):
        a = lesson.read_survey(self.write('a.csv', [['A', 8], ['B', 10], ['C', 7]]))
        b = lesson.read_survey(self.write('b.csv', [['A', 3], ['C', 'bad'], ['D', 9]]))
        pairs = lesson.paired_changes(a['ratings'], b['ratings'])
        self.assertEqual(pairs, [('A', 8, 3, -5)])
        text = lesson.format_report(a, b, pairs, lesson.summarize(pairs))
        self.assertIn('Before-only IDs: B', text); self.assertIn('After-only IDs: D', text)

    def test_improved_declined_unchanged(self):
        summary = lesson.summarize(lesson.paired_changes({'A': 2, 'B': 4, 'C': 8}, {'A': 3, 'B': 4, 'C': 2}))
        self.assertEqual([summary[k] for k in ['improvements', 'unchanged', 'declines']], [1, 1, 1])

    def test_empty_and_missing_headers(self):
        for content in ['', 'customer_id,satisfaction_rating\n', 'customer,rating\nA,8\n', 'customer_id,customer_id,satisfaction_rating\nA,A,8\n']:
            path = self.root/'empty.csv'; path.write_text(content, encoding='utf-8')
            with self.assertRaises(ValueError): lesson.read_survey(path)

    def test_unexpected_named_columns_allowed(self):
        data = lesson.read_survey(self.write('a.csv', [['A', 8, 'ignored']], ['customer_id', 'satisfaction_rating', 'comment']))
        self.assertEqual(data['ratings'], {'A': 8})

    def test_no_pairs_undefined(self):
        with self.assertRaises(ValueError): lesson.summarize([])

    def test_real_cli_report_and_input_preservation(self):
        a = self.write('before.csv', [['A', 9], ['B', 8]])
        b = self.write('after.csv', [['A', 3], ['B', 2]])
        before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in [a, b]]
        run = self.run_cli(a, b)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('Paired valid responses: 2', run.stdout)
        self.assertIn('Average change: -6.00 points', run.stdout)
        report = (self.root/'report.txt').read_text(encoding='utf-8')
        self.assertIn('A,9,3,-6', report); self.assertIn('causation', report)
        self.assertEqual(before, [hashlib.sha256(p.read_bytes()).hexdigest() for p in [a, b]])

    def test_overwrite_and_input_output_collision_refused(self):
        a = self.write('before.csv', [['A', 9]]); b = self.write('after.csv', [['A', 3]])
        (self.root/'report.txt').write_text('preserve')
        self.assertEqual(self.run_cli(a, b).returncode, 2)
        self.assertEqual((self.root/'report.txt').read_text(), 'preserve')
        self.assertEqual(self.run_cli(a, b, 'before.csv').returncode, 2)

    def test_missing_file_and_no_valid_pairs_fail_no_output(self):
        a = self.write('a.csv', [['A', 8]]); b = self.write('b.csv', [['B', 4]])
        self.assertEqual(self.run_cli(a, b).returncode, 2)
        self.assertEqual(self.run_cli(a, self.root/'missing.csv').returncode, 2)
        self.assertFalse((self.root/'report.txt').exists())

    def test_generator_reproducible_and_result_independently_checked(self):
        generator = SOURCE.with_name('generate_fictional_surveys.py')
        for name in ['one', 'two']:
            subprocess.run([sys.executable, str(generator), str(self.root/name)], check=True)
        self.assertEqual((self.root/'one/before.csv').read_bytes(), (self.root/'two/before.csv').read_bytes())
        self.assertEqual((self.root/'one/after.csv').read_bytes(), (self.root/'two/after.csv').read_bytes())
        a = lesson.read_survey(self.root/'one/before.csv'); b = lesson.read_survey(self.root/'one/after.csv')
        pairs = lesson.paired_changes(a['ratings'], b['ratings']); summary = lesson.summarize(pairs)
        self.assertEqual(summary['count'], 236)
        self.assertAlmostEqual(summary['change'], summary['after']-summary['before'])
        self.assertEqual(summary['count'], sum(summary[k] for k in ['improvements', 'declines', 'unchanged']))
        self.assertTrue(all(summary[k] > 0 for k in ['improvements', 'declines', 'unchanged']))


if __name__ == '__main__':
    unittest.main()
