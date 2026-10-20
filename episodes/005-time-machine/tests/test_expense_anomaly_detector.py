import csv
import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import expense_anomaly_detector as app
import generate_expenses

def row(**kw):
    return dict(dict(zip(app.FIELDS,['E1','P1','2026-10-19','Cafe','10.20','Fictional meal'])),**kw)

class ExpenseTests(unittest.TestCase):
    def audit(self,rows):return app.audit_expenses(rows,date(2026,10,20))
    def flags(self,r):return set(self.audit([r])[0][0]['anomaly_flags'].split('|'))
    def test_future(self):self.assertEqual(self.flags(row(expense_date='2026-10-21')),{'FUTURE_DATE'})
    def test_on_cutoff_and_past(self):self.assertEqual(self.audit([row(expense_date='2026-10-20')])[0],[])
    def test_invalid_calendar_and_iso(self):
        for value in ['2026-02-30','20261019','2026-W43-1','2026-1-2','yesterday']:
            self.assertIn('INVALID_DATE',self.flags(row(expense_date=value)))
    def test_missing_date(self):self.assertIn('INVALID_DATE',self.flags(row(expense_date='')))
    def test_leap_day(self):self.assertEqual(app.parse_date('2024-02-29'),date(2024,2,29))
    def test_repeated_ids_all_rows(self):
        report,c=self.audit([row(),row(employee_id='P2')]);self.assertEqual(c['DUPLICATE_EXPENSE_ID'],2);self.assertEqual(c['POSSIBLE_DUPLICATE_CLAIM'],0)
    def test_suspected_claims_different_ids(self):
        report,c=self.audit([row(),row(expense_id='E2',merchant=' cafe ',amount='10.2')]);self.assertEqual(c['POSSIBLE_DUPLICATE_CLAIM'],2);self.assertEqual(c['DUPLICATE_EXPENSE_ID'],0)
    def test_multiple_flags_unique_rows(self):
        report,c=self.audit([row(expense_date='2026-11-01'),row(expense_date='2026-11-01')]);self.assertEqual(len(report),2);self.assertEqual(sum(c.values()),6)
    def test_decimal_exactness(self):self.assertEqual(app.parse_amount('0.10')+app.parse_amount('0.20'),Decimal('0.30'))
    def test_invalid_amounts(self):
        for amount in ['','NaN','Infinity','-Infinity','0','0.00','-1','1.234','1e2','+1','$2','1,000','abc']:
            self.assertIn('INVALID_AMOUNT',self.flags(row(amount=amount)))
    def test_invalid_claim_keys_not_grouped(self):
        report,c=self.audit([row(expense_date=''),row(expense_id='E2',expense_date='')]);self.assertEqual(c['POSSIBLE_DUPLICATE_CLAIM'],0)
    def test_blank_identifiers_flagged(self):self.assertTrue({'MISSING_EXPENSE_ID','MISSING_EMPLOYEE_ID','MISSING_MERCHANT'}<=self.flags(row(expense_id='',employee_id='',merchant='')))
    def test_input_values_preserved(self):
        original=row(expense_date=' bad ',merchant=' Cafe ');report,_=self.audit([original]);self.assertTrue(all(report[0][k]==original[k] for k in app.FIELDS))
    def test_empty_missing_duplicate_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'in.csv'
            for content in ['',','.join(app.FIELDS)+'\n','expense_id,amount\nE1,1\n',','.join(app.FIELDS+['amount'])+'\n']:
                p.write_text(content)
                with self.assertRaises(ValueError):app.read_expenses(p)
    def test_malformed_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'in.csv'
            for content in ['E1,P1','E1,P1,2026-10-19,Cafe,1,meal,extra','E1,P1,"unterminated']:
                p.write_text(','.join(app.FIELDS)+'\n'+content)
                with self.assertRaises((ValueError,csv.Error)):app.read_expenses(p)
    def test_generator_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/'a.csv',Path(tmp)/'b.csv';generate_expenses.generate(a);generate_expenses.generate(b)
            self.assertEqual(a.read_bytes(),b.read_bytes());self.assertEqual(len(app.read_expenses(a)),500)
    def test_documented_sample_and_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=ROOT/'sample/expenses.csv'
            if not source.exists():generate_expenses.generate(Path(tmp)/'expenses.csv');source=Path(tmp)/'expenses.csv'
            before=hashlib.sha256(source.read_bytes()).hexdigest();out=Path(tmp)/'audit_report.csv'
            run=subprocess.run([sys.executable,str(ROOT/'expense_anomaly_detector.py'),str(source),'--as-of','2026-10-20','--output',str(out)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(before,hashlib.sha256(source.read_bytes()).hexdigest())
            with out.open(newline='',encoding='utf-8') as f:reader=csv.DictReader(f);self.assertEqual(reader.fieldnames,app.REPORT_FIELDS);rows=list(reader)
            self.assertEqual(len(rows),len(app.audit_expenses(app.read_expenses(source),date(2026,10,20))[0]))
            expected=ROOT/'sample/expected_audit_report.csv'
            if expected.exists():self.assertEqual(out.read_bytes(),expected.read_bytes())
            second=subprocess.run([sys.executable,str(ROOT/'expense_anomaly_detector.py'),str(source),'--as-of','2026-10-20','--output',str(out)],capture_output=True,text=True)
            self.assertEqual(second.returncode,2)
    def test_cli_invalid_arguments(self):
        for args in [[],['missing.csv','--output','report.csv'],['missing.csv','--as-of','2026-02-30','--output','report.csv'],['missing.csv','--as-of','2026-10-20','--output','report.csv']]:
            p=subprocess.run([sys.executable,str(ROOT/'expense_anomaly_detector.py'),*args],capture_output=True,text=True);self.assertEqual(p.returncode,2)
    def test_output_collision_and_unicode_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'input.csv';p.write_text(','.join(app.FIELDS)+'\nE1,P1,2026-11-01,Café,2.50,Meal\n',encoding='utf-8-sig');before=p.read_bytes()
            self.assertEqual(app.main([str(p),'--as-of','2026-10-20','--output',str(p)]),2);self.assertEqual(before,p.read_bytes());self.assertEqual(len(app.read_expenses(p)),1)
    def test_unflagged_report_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'out.csv';app.write_report(p,[])
            with p.open(newline='') as f:self.assertEqual(next(csv.reader(f)),app.REPORT_FIELDS)

if __name__=='__main__':unittest.main()
