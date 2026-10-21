import csv,hashlib,json,io
from email.message import EmailMessage
from email import policy
from pathlib import Path
import subprocess,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import analyze_fridge_complaints as app
from generate_sample_data import generate,TEXT

class EmailTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.emails=self.root/'emails';self.emails.mkdir();self.out=self.root/'report.csv'
 def message(self,body='The refrigerator denied my lunch request.',subject='Fictional complaint',name='a.eml',charset='utf-8',html=False,attachment=False):
  m=EmailMessage(policy=policy.SMTP);m['From']='Fictional Employee <employee@example.invalid>';m['Subject']=subject;m['To']='hr@example.invalid';m.set_content(body,charset=charset)
  if html:m.add_alternative('<p>Wrong performance rating: HTML must be ignored.</p>',subtype='html')
  if attachment:m.add_attachment(b'The fridge obtained confidential HR data.',maintype='application',subtype='octet-stream',filename='ignore.bin')
  p=self.emails/name;p.write_bytes(m.as_bytes());return p
 def cli(self):return subprocess.run([sys.executable,str(ROOT/'analyze_fridge_complaints.py'),str(self.emails),'--output',str(self.out)],capture_output=True,text=True)
 def test_plain_headers_and_body(self):
  p=self.message();sender,subject,body,notes=app.parse_email(p);self.assertIn('employee@example.invalid',sender);self.assertEqual(subject,'Fictional complaint');self.assertIn('denied my lunch',body);self.assertEqual(notes,[])
 def test_multipart_and_attachment_ignored(self):
  self.message(html=True,attachment=True);rows,stats=app.analyze(self.emails);self.assertEqual(rows[0]['categories'],'FOOD_ACCESS_DENIED');self.assertEqual(stats['category_matches'],1)
 def test_text_attachment_not_body(self):
  m=EmailMessage();m['Subject']='Shelves';m['From']='fictional@example.invalid';m.set_content('Please label the shelves.');m.add_attachment('The fridge denied lunch.',subtype='plain',filename='complaint.txt');p=self.emails/'a.eml';p.write_bytes(m.as_bytes());self.assertEqual(app.analyze(self.emails)[0][0]['categories'],'OTHER')
 def test_declared_latin1(self):
  p=self.message('Café employee: the fridge denied lunch.',charset='iso-8859-1');self.assertIn('Café',app.parse_email(p)[2])
 def test_base64_and_encoded_subject(self):
  m=EmailMessage();m['From']='Fictional Équipe <fictional@example.invalid>';m['Subject']='Café — complaint';m.set_content('The fridge denied lunch.',cte='base64');p=self.emails/'a.eml';p.write_bytes(m.as_bytes());sender,subject,body,_=app.parse_email(p);self.assertIn('Équipe',sender);self.assertEqual(subject,'Café — complaint');self.assertIn('denied lunch',body)
 def test_unknown_charset_error_row(self):
  (self.emails/'bad.eml').write_bytes(b'From: x@example.invalid\r\nSubject: Test\r\nContent-Type: text/plain; charset="unknown-mel-charset"\r\n\r\nbody');rows,s=app.analyze(self.emails);self.assertEqual(s['errors'],1);self.assertEqual(rows[0]['status'],'ERROR');self.assertEqual(s['other'],0)
 def test_invalid_charset_bytes(self):
  (self.emails/'bad.eml').write_bytes(b'From: x@example.invalid\nSubject: Test\nContent-Type: text/plain; charset=utf-8\n\n\xff');self.assertEqual(app.analyze(self.emails)[1]['errors'],1)
 def test_missing_body(self):
  (self.emails/'empty.eml').write_bytes(b'From: x@example.invalid\nSubject: Question\n\n');r,s=app.analyze(self.emails);self.assertEqual(s['parsed'],1);self.assertIn('EMPTY_BODY',r[0]['notes'])
 def test_html_only_does_not_match_body(self):
  m=EmailMessage();m['Subject']='Question';m['From']='x@example.invalid';m.set_content('The fridge denied lunch.',subtype='html');(self.emails/'html.eml').write_bytes(m.as_bytes());r,s=app.analyze(self.emails);self.assertEqual(r[0]['categories'],'OTHER');self.assertIn('NO_PLAIN_TEXT_BODY',r[0]['notes'])
 def test_missing_sender_is_warning(self):
  (self.emails/'a.eml').write_bytes(b'Subject: Request\n\nPlease label shelves.');r,s=app.analyze(self.emails);self.assertEqual(s['parsed'],1);self.assertIn('MISSING_FROM',r[0]['notes'])
 def test_malformed_bytes_error_not_crash(self):
  (self.emails/'bad.eml').write_bytes(b'not an email\xff\x00');self.assertEqual(app.analyze(self.emails)[1]['errors'],1)
 def test_broken_boundary_recoverable_warning(self):
  (self.emails/'bad.eml').write_bytes(b'From: x@example.invalid\nSubject: Request\nContent-Type: multipart/mixed; boundary="missing"\n\nno boundaries');r,s=app.analyze(self.emails);self.assertEqual(s['parsed'],1);self.assertEqual(r[0]['status'],'PARSED_WARNINGS')
 def test_every_documented_pattern_variation(self):
  for name,examples in TEXT.items():
   for text in examples:
    with self.subTest(name=name,text=text):self.assertEqual(app.classify(text),[name])
 def test_multi_category_and_counts(self):
  self.message('The fridge denied lunch. My rating is incorrect.');r,s=app.analyze(self.emails);self.assertEqual(s['parsed'],1);self.assertEqual(s['categorized'],1);self.assertEqual(s['category_matches'],2);self.assertIn('INCORRECT_PERFORMANCE_RATING',r[0]['categories'])
 def test_other_not_error(self):
  self.message('Please label the shelves.');r,s=app.analyze(self.emails);self.assertEqual(s['other'],1);self.assertEqual(s['categorized'],0);self.assertEqual(s['category_matches'],0)
 def test_isolated_keywords_not_classified(self):
  for text in ['Food and performance are topics.', 'The refrigerator is useful.', 'We ate lunch together.']:
   self.assertEqual(app.classify(text),['OTHER'])
 def test_simple_negation(self):self.assertEqual(app.classify('I was not denied lunch.'),['OTHER'])
 def test_case_whitespace_normalization(self):self.assertEqual(app.classify('REFUSED\n\tMY LUNCH'),['FOOD_ACCESS_DENIED'])
 def test_subject_classifies_without_body(self):self.assertEqual(app.classify('The refrigerator denied lunch.'),['FOOD_ACCESS_DENIED'])
 def test_csv_content_and_no_body(self):
  self.message('Secret body marker. The fridge denied lunch.',subject='Complaint, with comma');self.assertEqual(self.cli().returncode,0);rows=list(csv.DictReader(io.StringIO(self.out.read_text(encoding='utf-8'))));self.assertEqual(rows[0]['subject'],'Complaint, with comma');self.assertNotIn('Secret body marker',self.out.read_text());self.assertEqual(tuple(rows[0]),app.REPORT_FIELDS)
 def test_csv_formula_protection(self):self.assertEqual(app.safe_cell('=1+1'),"'=1+1");self.assertEqual(app.safe_cell('  @command'),"'  @command")
 def test_deterministic_order_and_input_hashes(self):
  self.message(name='z.EML');self.message(name='a.eml');before={p.name:p.read_bytes() for p in self.emails.iterdir()};rows,_=app.analyze(self.emails);self.assertEqual([r['source_file'] for r in rows],['a.eml','z.EML']);self.assertEqual(before,{p.name:p.read_bytes() for p in self.emails.iterdir()})
 def test_no_recursion(self):
  self.message();(self.emails/'nested').mkdir();(self.emails/'nested/b.eml').write_bytes(b'bad');self.assertEqual(app.analyze(self.emails)[1]['files'],1)
 def test_empty_directory(self):self.assertRaises(ValueError,app.analyze,self.emails)
 def test_missing_directory(self):self.assertRaises(ValueError,app.analyze,self.root/'missing')
 def test_existing_output_protected(self):
  self.message();self.out.write_text('keep');self.assertEqual(self.cli().returncode,2);self.assertEqual(self.out.read_text(),'keep')
 def test_output_inside_inputs_refused(self):
  self.message();r=subprocess.run([sys.executable,str(ROOT/'analyze_fridge_complaints.py'),str(self.emails),'--output',str(self.emails/'out.csv')],capture_output=True);self.assertEqual(r.returncode,2)
 def test_partial_failure_exit1_with_report(self):
  self.message();(self.emails/'bad.eml').write_bytes(b'broken');r=self.cli();self.assertEqual(r.returncode,1);self.assertTrue(self.out.exists());self.assertIn('Errors: 1',r.stdout)
 def test_read_error_is_counted(self):
  self.message()
  with patch.object(app,'parse_email',side_effect=PermissionError('secret/full/path')):rows,s=app.analyze(self.emails)
  self.assertEqual(s['errors'],1);self.assertEqual(rows[0]['notes'],'PermissionError')
 def test_oversize_is_counted(self):
  self.message()
  with patch.object(app,'MAX_BYTES',5):self.assertEqual(app.analyze(self.emails)[1]['errors'],1)
 def test_directory_named_eml_is_error(self):(self.emails/'folder.eml').mkdir();self.assertEqual(app.analyze(self.emails)[1]['errors'],1)
 def test_attachment_only_not_followed(self):
  m=EmailMessage();m['Subject']='Shelves';m['From']='x@example.invalid';m.add_attachment('The fridge denied lunch.',subtype='plain',filename='attached.txt');(self.emails/'a.eml').write_bytes(m.as_bytes());r,s=app.analyze(self.emails);self.assertEqual(r[0]['categories'],'OTHER')
 def test_reproducible_400_email_demo(self):
  a=self.root/'first';b=self.root/'second';manifest=generate(a);self.assertEqual(manifest,generate(b));self.assertEqual({p.name:p.read_bytes() for p in a.iterdir()},{p.name:p.read_bytes() for p in b.iterdir()})
  rows,s=app.analyze(a);self.assertEqual(s['parsed'],400);self.assertEqual(s['errors'],0);self.assertEqual(s['categorized']+s['other'],400)
  for row,expected in zip(rows,manifest):self.assertEqual(row['categories'].split(';'),expected['expected_categories'])
  self.assertGreater(s['category_matches'],s['categorized'])
 def test_report_deterministic(self):
  self.message();rows,_=app.analyze(self.emails);app.write_report(self.out,rows);p=self.root/'second.csv';app.write_report(p,rows);self.assertEqual(self.out.read_bytes(),p.read_bytes())

if __name__=='__main__':unittest.main()
