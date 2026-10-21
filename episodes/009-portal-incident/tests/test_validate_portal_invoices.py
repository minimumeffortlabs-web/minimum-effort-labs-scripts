import csv
from decimal import Decimal, localcontext
import io
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import validate_portal_invoices as m
from generate_sample_data import generate


class InvoiceTests(unittest.TestCase):
 def row(self,**kw):return dict(dict(zip(m.FIELDS,['INV1','VEN1','2026-10-20','USD','0.10','Portal maintenance'])),**kw)
 def audit(self,*rows):return m.audit(list(rows),{'USD':2,'JPY':0,'KWD':3})
 def flags(self,**kw):return self.audit(self.row(**kw))[0][0]['anomaly_flags'].split(';')
 def test_valid_invoice(self):self.assertEqual(self.audit(self.row())[0][0]['validation_status'],'VALID')
 def test_decimal_exact_sum(self):self.assertEqual(self.audit(self.row(),self.row(invoice_id='INV2',vendor_id='VEN2',amount='0.20'))[1]['valid_totals'],{'USD':'0.30'})
 def test_decimal_no_context_rounding(self):
  with localcontext() as ctx:
   ctx.prec=2
   self.assertEqual(self.audit(self.row(amount='123456789.01'))[1]['valid_totals']['USD'],'123456789.01')
 def test_bad_amounts(self):
  for value in ['oops','NaN','sNaN','Infinity','-Infinity','0','-1','+1','1e2','1,000.00','$1','1.',' .5','1_000','1.000', '9'*65]:
   with self.subTest(value=value):self.assertIn('INVALID_AMOUNT',self.flags(amount=value))
 def test_currency_precision(self):
  for code,value,valid in [('JPY','1',True),('JPY','1.0',False),('KWD','1.123',True),('KWD','1.1234',False),('USD','1.20',True),('USD','1.200',False)]:
   with self.subTest(code=code,value=value):self.assertEqual('INVALID_AMOUNT' not in self.flags(currency=code,amount=value),valid)
 def test_unknown_currency_is_review_not_conversion(self):self.assertIn('UNKNOWN_CURRENCY',self.flags(currency='VOID'))
 def test_unknown_precision_fallback(self):self.assertNotIn('INVALID_AMOUNT',self.flags(currency='VOID',amount='1.123456'));self.assertIn('INVALID_AMOUNT',self.flags(currency='VOID',amount='1.1234567'))
 def test_normalized_currency(self):self.assertEqual(self.audit(self.row(currency=' usd '))[0][0]['currency'],'USD')
 def test_bad_dates(self):
  for value in ['2026-02-30','2026-2-03','20261020','2026-W01-1','']:
   with self.subTest(value=value):self.assertIn('INVALID_DATE',self.flags(invoice_date=value))
 def test_leap_day(self):self.assertNotIn('INVALID_DATE',self.flags(invoice_date='2024-02-29'))
 def test_all_required_fields(self):
  for field in m.FIELDS:
   with self.subTest(field=field):self.assertIn('MISSING_REQUIRED_FIELD',self.flags(**{field:' '}))
 def test_invalid_ids(self):self.assertIn('INVALID_ID',self.flags(invoice_id='../x'));self.assertIn('INVALID_ID',self.flags(vendor_id='x y'))
 def test_duplicate_ids_all_members(self):
  report,stats=self.audit(self.row(),self.row(vendor_id='VEN2'))
  self.assertTrue(all('DUPLICATE_INVOICE_ID' in r['anomaly_flags'] for r in report));self.assertEqual(stats['counts']['POSSIBLE_DUPLICATE_INVOICE'],0)
 def test_possible_claim_all_members_without_duplicate_id(self):
  report,stats=self.audit(self.row(),self.row(invoice_id='INV2',amount='0.1',description=' PORTAL   Maintenance '))
  self.assertEqual(stats['counts']['POSSIBLE_DUPLICATE_INVOICE'],2);self.assertEqual(stats['counts']['DUPLICATE_INVOICE_ID'],0)
 def test_different_description_not_claim(self):self.assertEqual(self.audit(self.row(),self.row(invoice_id='INV2',description='Different service'))[1]['flagged'],0)
 def test_different_currency_not_claim(self):self.assertEqual(self.audit(self.row(),self.row(invoice_id='INV2',currency='KWD'))[1]['flagged'],0)
 def test_invalid_core_not_used_for_claim(self):self.assertEqual(self.audit(self.row(amount='NaN'),self.row(invoice_id='INV2',amount='NaN'))[1]['counts']['POSSIBLE_DUPLICATE_INVOICE'],0)
 def test_multiple_flags_unique_rows(self):
  _,stats=self.audit(self.row(currency='VOID',amount='NaN',invoice_date='bad'),self.row(invoice_id='INV2'))
  self.assertEqual((stats['flagged'],stats['total_flags']),(1,3))
 def test_totals_are_per_currency_and_exclude_all_flagged_rows(self):
  _,stats=self.audit(self.row(),self.row(invoice_id='INV2',currency='KWD',amount='0.123'),self.row(invoice_id='INV3',currency='VOID'))
  self.assertEqual(stats['valid_totals'],{'KWD':'0.123','USD':'0.10'})
 def test_duplicate_claims_excluded_from_totals(self):self.assertEqual(self.audit(self.row(),self.row(invoice_id='INV2'))[1]['valid_totals'],{})
 def test_csv_formula_guard(self):self.assertEqual(m.safe_cell('=SUM(A1)'),'\'=SUM(A1)');self.assertEqual(m.safe_cell('a\nb'),'a b')
 def test_csv_quoted_description(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.csv';p.write_text('invoice_id,vendor_id,invoice_date,currency,amount,description\nI1,V1,2026-10-20,USD,1.00,"Portal, urgent"\n',encoding='utf-8-sig')
   self.assertEqual(m.read_csv(p,m.FIELDS)[0]['description'],'Portal, urgent')
 def test_bad_csv_headers_and_rows(self):
  for text in ['', 'invoice_id\nI1\n', ','.join(m.FIELDS)+',amount\n', ','.join(m.FIELDS)+'\nI1,V1\n',','.join(m.FIELDS)+'\n']:
   with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'x.csv';p.write_text(text)
    with self.assertRaises(ValueError):m.read_csv(p,m.FIELDS)
 def test_currency_config(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'c.csv';p.write_text('currency_code,description,decimal_places\nusd,Test,2\nJPY,Test,0\n');self.assertEqual(m.load_currencies(p),{'USD':2,'JPY':0})
 def test_bad_currency_config(self):
  for body in ['USD,Test,7','USD,Test,-1','USD,Test,2\nusd,Test,2','USD,,2','bad!,Test,2']:
   with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'c.csv';p.write_text('currency_code,description,decimal_places\n'+body+'\n')
    with self.assertRaises(ValueError):m.load_currencies(p)
 def test_cli_report_preserves_inputs_and_refuses_overwrite(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);generate(p/'sample',8);a=p/'sample/invoices.csv';c=p/'sample/approved_currencies.csv';out=p/'report.csv';before=(a.read_bytes(),c.read_bytes());args=[str(a),'--currencies',str(c),'--output',str(out)]
   with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
    self.assertEqual(m.main(args),0);output=out.read_bytes();self.assertEqual(m.main(args),2)
   self.assertEqual(out.read_bytes(),output);self.assertEqual((a.read_bytes(),c.read_bytes()),before)
   with out.open(encoding='utf-8',newline='') as f:report=list(csv.DictReader(f))
   self.assertEqual(len(report),8);self.assertEqual(tuple(report[0]),m.REPORT_FIELDS)
 def test_cli_missing_input(self):
  with redirect_stderr(io.StringIO()):self.assertEqual(m.main(['missing.csv','--currencies','missing-config.csv','--output','unused.csv']),2)
 def test_full_demo_independent_flags_and_determinism(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);manifest=generate(p/'a');generate(p/'b')
   for name in ['invoices.csv','approved_currencies.csv','expected-labels.json']:self.assertEqual((p/'a'/name).read_bytes(),(p/'b'/name).read_bytes())
   report,stats=m.audit(m.read_csv(p/'a/invoices.csv',m.FIELDS),m.load_currencies(p/'a/approved_currencies.csv'))
   for row,expected in zip(report,manifest['expected']):self.assertEqual(sorted(filter(None,row['anomaly_flags'].split(';'))),expected['flags'])
   self.assertEqual(len(report),500);self.assertEqual(stats['valid']+stats['flagged'],500)

if __name__=='__main__':unittest.main()
