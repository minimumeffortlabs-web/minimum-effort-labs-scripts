"""Run the documented sample with the exact distributed CLI, offline."""
from pathlib import Path
import csv,hashlib,json,shutil,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class SampleTests(unittest.TestCase):
 def test_readme_sample(self):
  command=json.loads((ROOT/'sample/command.json').read_text(encoding='utf-8'))['argv']
  with tempfile.TemporaryDirectory() as name:
   work=Path(name);shutil.copytree(ROOT/'sample',work/'sample')
   script=command[1];shutil.copy2(ROOT/script,work/script)
   before={p.relative_to(work):digest(p) for p in (work/'sample').rglob('*') if p.is_file()}
   result=subprocess.run([sys.executable,*command[1:]],cwd=work,capture_output=True,text=True,encoding='utf-8')
   self.assertEqual(result.returncode,0,result.stderr+result.stdout)
   self.assertEqual(result.stderr,'')
   for path,sha in before.items():self.assertEqual(digest(work/path),sha)
   if script=='merge_pdfs.py':
    from pypdf import PdfReader
    expected=json.loads((work/'sample/expected.json').read_text())
    report=json.loads((work/'merge_report.json').read_text())
    self.assertEqual(report['documents'],expected['documents']);self.assertEqual(report['pages'],expected['pages'])
    self.assertEqual([x['file'] for x in report['processed']],expected['order'])
    merged=PdfReader(work/'merged.pdf');self.assertEqual(len(merged.pages),3)
    original=[page.extract_text() for p in sorted((work/'sample/input').glob('*.pdf')) for page in PdfReader(p).pages]
    self.assertTrue(all(original));self.assertEqual([p.extract_text() for p in merged.pages],original)
    self.assertEqual(result.stdout,'Merged 3 PDFs into merged.pdf\nVerified 3 pages. Original files unchanged.\n')
   elif script=='reconcile_timecards.py':
    self.assertEqual((work/'discrepancies.csv').read_bytes(),(work/'sample/expected_discrepancies.csv').read_bytes())
    self.assertEqual(result.stdout,'Checked 5 shifts. Matched 3.\nFlagged 2 for review -> discrepancies.csv\nInvalid rows: 1 timecards, 1 access events.\nMissing logs are not proof of absence. Inputs unchanged.\n')
   else:
    self.assertEqual((work/'weather_report.txt').read_bytes(),(work/'sample/expected_report.txt').read_bytes())
    self.assertIn('Replaying recorded-live-api captured 2026-10-20T05:31:11.932425+00:00',result.stdout)
    self.assertIn('Days analyzed: 5',result.stdout)
if __name__=='__main__':unittest.main()
