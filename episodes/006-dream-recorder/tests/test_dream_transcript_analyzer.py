import hashlib
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import dream_transcript_analyzer as app
import generate_sample_data as fixture

class DreamTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.work=Path(self.tmp.name);self.inputs=self.work/'transcripts';self.inputs.mkdir()
    def text(self,name,value):
        p=self.inputs/name;p.write_text(value,encoding='utf-8');return p
    def analyze(self):return app.analyze_files(app.find_transcripts(self.inputs))
    def cli(self,*args):return subprocess.run([sys.executable,str(ROOT/'dream_transcript_analyzer.py'),*map(str,args)],capture_output=True,text=True)
    def test_find_sorted_top_level_text(self):
        self.text('b.TXT','Coffee');self.text('a.txt','Receipts');self.text('ignore.csv','No');(self.inputs/'sub').mkdir();self.text('sub/nested.txt','No')
        self.assertEqual([p.name for p in app.find_transcripts(self.inputs)],['a.txt','b.TXT'])
    def test_case_normalization(self):self.assertEqual(app.extract_words('Coffee COFFEE coffee'),['coffee']*3)
    def test_ascii_word_extraction(self):self.assertEqual(app.extract_words('Report_2047! two-word 42'),['report','two','word'])
    def test_punctuation_and_contractions(self):self.assertEqual(app.extract_words("we're, coffee... receipts!"),['we','re','coffee','receipts'])
    def test_word_frequency_and_stop_words(self):
        self.text('a.txt','The COFFEE and coffee with receipts.');r=self.analyze();self.assertEqual(r['words'],Counter(coffee=2,receipts=1));self.assertEqual((r['extracted'],r['analyzed']),(6,3))
    def test_adjacent_pairs(self):self.assertEqual(app.adjacent_phrases(['expense','reports','expense']),[('expense','reports'),('reports','expense')])
    def test_no_false_stop_word_adjacency(self):self.assertEqual(app.adjacent_phrases(app.extract_words('expense and the report')),[])
    def test_no_cross_file_phrases(self):
        self.text('a.txt','expense');self.text('b.txt','reports');self.assertEqual(self.analyze()['phrases'],Counter())
    def test_punctuation_is_ignored_documented(self):self.assertEqual(app.adjacent_phrases(app.extract_words('expense. reports')), [('expense','reports')])
    def test_empty_and_stop_only_files(self):
        self.text('a.txt','');self.text('b.txt','123...');self.text('c.txt','the and a');r=self.analyze();self.assertEqual((r['files'],r['empty'],r['extracted'],r['analyzed']),(3,2,3,0));self.assertEqual(r['words'],Counter());self.assertIn('(none)',app.format_report(r,10))
    def test_empty_directory(self):
        with self.assertRaisesRegex(ValueError,'No .txt'):app.find_transcripts(self.inputs)
    def test_missing_directory(self):
        with self.assertRaises(ValueError):app.find_transcripts(self.inputs/'missing')
    def test_invalid_utf8(self):
        (self.inputs/'bad.txt').write_bytes(b'\xff\xfe\x80')
        with self.assertRaisesRegex(ValueError,'bad.txt'):self.analyze()
    def test_unreadable_input_is_reported(self):
        p=self.text('locked.txt','expense reports')
        with patch.object(Path,'read_text',side_effect=PermissionError('denied')):
            with self.assertRaisesRegex(ValueError,'locked.txt'):app.analyze_files([p])
    def test_utf8_bom(self):
        p=self.inputs/'a.txt';p.write_text('Coffee receipts',encoding='utf-8-sig');self.assertEqual(self.analyze()['words'],Counter(coffee=1,receipts=1))
    def test_ties_alphabetical(self):self.assertEqual(app.rank_counts(Counter(zebra=2,apple=2,coffee=3),3),[('coffee',3),('apple',2),('zebra',2)])
    def test_occurrences_not_file_counts(self):
        self.text('a.txt','expense reports expense reports');r=self.analyze();self.assertEqual(r['files'],1);self.assertEqual(r['phrases'][('expense','reports')],2)
    def test_report_structure_and_top_limit(self):
        self.text('a.txt','Coffee receipts coffee');r=self.analyze();s=app.format_report(r,1);self.assertIn('Top 1 words:\n1. coffee: 2',s);self.assertIn('Top 1 adjacent two-word phrases:',s);self.assertIn('not psychological interpretation',s)
    def test_cli_report_determinism_and_input_preservation(self):
        p=self.text('a.txt','Coffee receipts coffee');before=p.read_bytes();a,b=self.work/'a.txt',self.work/'b.txt'
        for out in [a,b]:self.assertEqual(self.cli(self.inputs,'--output',out,'--top',2).returncode,0)
        self.assertEqual(a.read_bytes(),b.read_bytes());self.assertEqual(before,p.read_bytes())
    def test_cli_invalid_top_and_arguments(self):
        self.text('a.txt','Coffee')
        for value in ['0','-1','no','1.2']:
            run=self.cli(self.inputs,'--output',self.work/'out.txt','--top',value);self.assertEqual(run.returncode,2);self.assertFalse((self.work/'out.txt').exists())
        self.assertEqual(self.cli().returncode,2)
    def test_cli_empty_directory_and_invalid_text_no_output(self):
        out=self.work/'out.txt';self.assertEqual(self.cli(self.inputs,'--output',out).returncode,2);self.assertFalse(out.exists());(self.inputs/'bad.txt').write_bytes(b'\xff');self.assertEqual(self.cli(self.inputs,'--output',out).returncode,2);self.assertFalse(out.exists())
    def test_output_protection(self):
        p=self.text('a.txt','Coffee');out=self.work/'existing.txt';out.write_text('Keep')
        self.assertEqual(self.cli(self.inputs,'--output',out).returncode,2);self.assertEqual(out.read_text(),'Keep');self.assertEqual(self.cli(self.inputs,'--output',p).returncode,2);self.assertEqual(p.read_text(),'Coffee');self.assertEqual(self.cli(self.inputs,'--output',self.inputs/'new.txt').returncode,2)
    def test_small_documented_sample(self):
        sample=ROOT/'sample/transcripts';expected=ROOT/'sample/expected_report.txt'
        if not sample.exists():self.skipTest('Standalone sample not authored yet')
        out=self.work/'report.txt';run=self.cli(sample,'--output',out,'--top',10);self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(out.read_bytes(),expected.read_bytes())
    def test_full_generator_and_rankings(self):
        a,b=self.work/'a',self.work/'b';fixture.generate(a);fixture.generate(b)
        files=app.find_transcripts(a);self.assertEqual(len(files),300)
        self.assertEqual([p.read_bytes() for p in files],[p.read_bytes() for p in app.find_transcripts(b)])
        r=app.analyze_files(files);self.assertEqual(app.rank_counts(r['phrases'],1)[0][0],('expense','reports'));self.assertEqual({w for w,_ in app.rank_counts(r['words'],2)},{'expense','reports'})

if __name__=='__main__':unittest.main()
