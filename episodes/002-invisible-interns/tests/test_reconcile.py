import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'reconcile_timecards.py'
spec = importlib.util.spec_from_file_location('reconciler', SCRIPT)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.cards = self.root/'timecards.csv'; self.doors = self.root/'door.csv'; self.out = self.root/'report.csv'
        self.cardrows=[dict(employee_id='A',clock_in='2026-10-15T08:00:00',clock_out='2026-10-15T16:00:00')]
        self.doorrows=[dict(employee_id='A',timestamp='2026-10-15T07:55:00',event='ENTRY',result='GRANTED')]
    def tearDown(self):self.temp.cleanup()
    def write(self,path,rows,headers):
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=headers); w.writeheader(); w.writerows(rows)
    def run_case(self):
        self.write(self.cards,self.cardrows,['employee_id','clock_in','clock_out'])
        self.write(self.doors,self.doorrows,['employee_id','timestamp','event','result'])
        before=[self.cards.read_bytes(),self.doors.read_bytes()]
        result=m.reconcile(self.cards,self.doors,self.out)
        self.assertEqual(before,[self.cards.read_bytes(),self.doors.read_bytes()])
        with self.out.open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),result['flagged']); return result,rows
    def test_match_and_readable_report(self):self.assertEqual(self.run_case()[0]['matched'],1)
    def test_missing_and_wrong_employee(self):
        self.doorrows[0]['employee_id']='B'; r,rows=self.run_case(); self.assertEqual(r['flagged'],1);self.assertEqual(rows[0]['reason'],'no_entry_in_window_review')
    def test_inclusive_boundaries_and_outside(self):
        for time,matched in [('07:30:00',1),('08:10:00',1),('07:29:59',0),('08:10:01',0)]:
            with self.subTest(time=time):
                self.out.unlink(missing_ok=True);self.doorrows[0]['timestamp']='2026-10-15T'+time
                self.assertEqual(self.run_case()[0]['matched'],matched)
    def test_duplicate_swipes_do_not_duplicate_results(self):
        self.doorrows*=3;self.assertEqual(self.run_case()[0]['matched'],1)
    def test_denied_and_exit_events_ignored(self):
        for key,value in [('event','EXIT'),('result','DENIED')]:
            with self.subTest(value=value):
                self.out.unlink(missing_ok=True);self.doorrows=[dict(employee_id='A',timestamp='2026-10-15T07:55:00',event='ENTRY',result='GRANTED')];self.doorrows[0][key]=value
                self.assertEqual(self.run_case()[0]['flagged'],1)
    def test_overnight(self):
        self.cardrows[0].update(clock_in='2026-10-15T22:00:00',clock_out='2026-10-16T06:00:00');self.doorrows[0]['timestamp']='2026-10-15T21:55:00'
        self.assertEqual(self.run_case()[0]['matched'],1)
    def test_invalid_timecards_are_reported(self):
        self.cardrows[0]['clock_in']='invalid';r,rows=self.run_case();self.assertEqual(r['invalid_timecards'],1);self.assertEqual(rows[0]['reason'],'invalid_timecard_review')
    def test_invalid_access_not_silently_counted(self):
        self.doorrows[0]['timestamp']='bad';r,_=self.run_case();self.assertEqual(r['invalid_access'],1);self.assertEqual(r['flagged'],1)
    def test_timezone_equivalent_instants(self):
        self.cardrows[0].update(clock_in='2026-10-15T08:00:00-06:00',clock_out='2026-10-15T16:00:00-06:00');self.doorrows[0]['timestamp']='2026-10-15T13:55:00+00:00'
        self.assertEqual(self.run_case()[0]['matched'],1)
    def test_mixed_timezone_conventions_rejected(self):
        self.doorrows[0]['timestamp']+='Z'
        with self.assertRaisesRegex(RuntimeError,'Do not mix'):self.run_case()
        self.assertFalse(self.out.exists())
    def test_missing_columns_and_files_fail_cleanly(self):
        self.cards.write_text('employee_id\nA\n');self.doors.write_text('employee_id,timestamp,event,result\n')
        with self.assertRaisesRegex(ValueError,'columns'):m.reconcile(self.cards,self.doors,self.out)
        self.cards.unlink()
        p=subprocess.run([sys.executable,str(SCRIPT),str(self.cards),str(self.doors),'--output',str(self.out)],capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertIn('ERROR:',p.stderr);self.assertFalse(self.out.exists())
    def test_no_overwrite_and_nonnegative_tolerance(self):
        self.out.write_text('keep')
        with self.assertRaises(ValueError):self.run_case()
        self.assertEqual(self.out.read_text(),'keep')
        with self.assertRaises(ValueError):m.reconcile(self.cards,self.doors,self.root/'new.csv',-1,10)
    def test_malformed_row_is_flagged(self):
        self.cardrows[0]['employee_id']='';self.assertEqual(self.run_case()[0]['invalid_timecards'],1)
    def test_reverse_shift_is_flagged(self):
        self.cardrows[0]['clock_out']='2026-10-14T16:00:00';self.assertEqual(self.run_case()[0]['flagged'],1)

if __name__=='__main__':unittest.main()
