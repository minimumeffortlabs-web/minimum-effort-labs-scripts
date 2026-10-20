"""Exercise the actual downloadable lesson function and guarded command line."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject

SCRIPT = Path(__file__).resolve().parents[1] / 'merge_pdfs.py'


class LessonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / 'input'
        self.folder.mkdir()
        self.out = self.root / 'merged.pdf'

    def tearDown(self):
        self.temp.cleanup()

    def pdf(self, name, number=1, encrypted=False):
        with PdfWriter() as writer:
            page = writer.add_blank_page(200, 200)
            page[NameObject('/TestOrder')] = NumberObject(number)
            if encrypted:
                writer.encrypt('secret')
            writer.write(self.folder / name)

    def run_cli(self):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.folder), str(self.out)], capture_output=True, text=True)

    def test_displayed_function_really_merges_in_filename_order(self):
        self.pdf('002.pdf', 2)
        self.pdf('001.pdf', 1)
        (self.folder / 'notes.txt').write_text('ignore')
        before = {path.name: path.read_bytes() for path in self.folder.iterdir()}
        spec = importlib.util.spec_from_file_location('lesson', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.merge_pdfs(self.folder, self.out), 2)
        with PdfReader(self.out) as reader:
            self.assertEqual([page['/TestOrder'] for page in reader.pages], [1, 2])
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.folder.iterdir()})

    def test_cli_success_matches_real_output(self):
        self.pdf('001.pdf')
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('Merged 1 PDFs into merged.pdf', result.stdout)
        self.assertEqual(len(PdfReader(self.out).pages), 1)

    def test_existing_output_not_overwritten(self):
        self.pdf('001.pdf')
        self.out.write_bytes(b'keep')
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertEqual(self.out.read_bytes(), b'keep')

    def test_corrupt_input_creates_no_output(self):
        self.pdf('001.pdf')
        (self.folder / '002.pdf').write_bytes(b'broken')
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertFalse(self.out.exists())

    def test_encrypted_input_creates_no_output(self):
        self.pdf('001.pdf', encrypted=True)
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertFalse(self.out.exists())

    def test_missing_folder_reports_failure(self):
        self.folder.rmdir()
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn('Input folder does not exist', result.stdout)
        self.assertFalse(self.out.exists())

    def test_empty_folder_fails_clearly(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn('No lowercase .pdf files', result.stdout)


if __name__ == '__main__':
    unittest.main()
