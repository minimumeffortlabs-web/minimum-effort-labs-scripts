import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

BASE=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,BASE/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=module('reconstruct_event_timeline');g=module('generate_sample_data')

def event(id='E1',time='2026-10-19T12:00:00Z',**extra):
    return dict(event_id=id,timestamp=time,source='IT',event_type='CHECK',description='Routine check',**extra)

class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.logs=self.root/'logs';self.logs.mkdir()
    def put(self,name,records):
        p=self.logs/name;p.write_text(json.dumps(records),encoding='utf-8');return p
    def load(self):return m.load_events(self.logs)
    def cli(self,**kw):
        out=io.StringIO();err=io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            code=m.main([str(self.logs),'--output',str(kw.get('output',self.root/'timeline.txt'))])
        return code,out.getvalue(),err.getvalue()
    def test_valid(self):
        self.put('a.json',[event()]);a,b,s=self.load();self.assertEqual(s['valid'],1);self.assertFalse(b)
    def test_multiple_files(self):
        self.put('b.json',[event('B')]);self.put('a.json',[event('A')]);self.assertEqual([x['event_id'] for x in self.load()[0]],['A','B'])
    def test_out_of_order(self):
        self.put('a.json',[event('late','2026-10-19T12:00:00Z'),event('early','2026-10-19T11:00:00Z')]);self.assertEqual(self.load()[0][0]['event_id'],'early')
    def test_offset_not_lexicographic(self):
        self.put('a.json',[event('later','2026-10-19T06:00:00-07:00'),event('earlier','2026-10-19T12:30:00Z')]);self.assertEqual(self.load()[0][0]['event_id'],'earlier')
    def test_z(self):self.assertEqual(m.utc_text(m.parse_timestamp('2026-10-19T12:00:00Z')),'2026-10-19T12:00:00Z')
    def test_offset(self):self.assertEqual(m.parse_timestamp('2026-10-19T17:30:00+05:30'),m.parse_timestamp('2026-10-19T12:00:00Z'))
    def test_tie_file_then_row(self):
        self.put('b.json',[event('Z')]);self.put('a.json',[event('Y'),event('X')]);self.assertEqual([x['event_id'] for x in self.load()[0]],['Y','X','Z'])
    def test_naive(self):
        with self.assertRaises(ValueError):m.parse_timestamp('2026-10-19T12:00:00')
    def test_invalid_iso(self):
        for text in ['2026-02-30T00:00:00Z','yesterday','2026-10-19 12:00:00Z','2026-10-19T12:00:00+00:99','2026-10-19T12:00:00-00:00']:
            with self.subTest(text=text),self.assertRaises(ValueError):m.parse_timestamp(text)
    def test_overflow(self):
        self.put('a.json',[event(time='0001-01-01T00:00:00+01:00')]);self.assertEqual(self.load()[2]['rejected_records'],1)
    def test_missing_each_field(self):
        rows=[]
        for k in m.FIELDS:
            a=event();a.pop(k);rows.append(a)
        self.put('a.json',rows);self.assertEqual(self.load()[2]['rejected_records'],5)
    def test_nonstring(self):
        a=event();a['description']=2;self.put('a.json',[a]);self.assertEqual(self.load()[2]['rejected_records'],1)
    def test_nonobject(self):
        self.put('a.json',[2,None,'bad']);self.assertEqual(self.load()[2]['rejected_records'],3)
    def test_invalid_json_and_valid_file(self):
        (self.logs/'a.json').write_text('{broken');self.put('b.json',[event()]);s=self.load()[2];self.assertEqual((s['valid'],s['file_errors']),(1,1))
    def test_top_level(self):
        self.put('a.json',{});self.assertEqual(self.load()[2]['file_errors'],1)
    def test_duplicate_property(self):
        (self.logs/'a.json').write_text('[{"event_id":"A","event_id":"B"}]');self.assertEqual(self.load()[2]['file_errors'],1)
    def test_nonstandard_json(self):
        (self.logs/'a.json').write_text('[NaN]');self.assertEqual(self.load()[2]['file_errors'],1)
    def test_duplicate_ids_all_excluded(self):
        self.put('a.json',[event(),event()]);a,b,s=self.load();self.assertFalse(a);self.assertEqual(s['duplicate_records'],2)
    def test_duplicate_with_invalid_member(self):
        a=event();a['timestamp']='bad';self.put('a.json',[a,event()]);a,b,s=self.load();self.assertFalse(a);self.assertEqual(s['rejected_records'],2)
    def test_repeated_description(self):
        self.put('a.json',[event('A'),event('B')]);self.assertEqual(self.load()[2]['valid'],2)
    def test_empty_array(self):
        self.put('a.json',[]);self.assertEqual(self.load()[2]['valid'],0);self.assertEqual(self.cli()[0],0)
    def test_empty_directory(self):self.assertEqual(self.cli()[0],2)
    def test_missing_directory(self):
        with self.assertRaises(ValueError):m.load_events(self.root/'missing')
    def test_report_contents(self):
        self.put('a.json',[event()]);self.assertEqual(self.cli()[0],0);s=(self.root/'timeline.txt').read_text();self.assertIn('2026-10-19T12:00:00Z | IT | CHECK | Routine check | a.json:1 | E1',s)
    def test_errors_report_and_exit1(self):
        self.put('a.json',[event(time='bad')]);self.assertEqual(self.cli()[0],1);self.assertIn('INVALID_RECORD',(self.root/'timeline.txt').read_text())
    def test_no_overwrite(self):
        self.put('a.json',[event()]);p=self.root/'timeline.txt';p.write_text('KEEP');self.assertEqual(self.cli()[0],2);self.assertEqual(p.read_text(),'KEEP')
    def test_no_output_among_inputs(self):
        self.put('a.json',[event()]);self.assertEqual(self.cli(output=self.logs/'output.txt')[0],2)
    def test_input_hashes_unchanged(self):
        p=self.put('a.json',[event()]);before=p.read_bytes();self.cli();self.assertEqual(p.read_bytes(),before)
    def test_control_escaping(self):
        a=event();a['description']='Fake\nline | bad';self.put('a.json',[a]);self.cli();s=(self.root/'timeline.txt').read_text();self.assertIn(r'Fake\nline \x7c bad',s)
    def test_deterministic_generator(self):
        a=self.root/'one';b=self.root/'two';self.assertEqual(g.generate(a),g.generate(b));self.assertEqual({p.name:p.read_bytes() for p in a.iterdir()},{p.name:p.read_bytes() for p in b.iterdir()})
    def test_generated_1000_independent_utc_order(self):
        p=self.root/'full';truth=g.generate(p);events,errors,s=m.load_events(p);self.assertEqual(s['valid'],1000);self.assertFalse(errors)
        expected=sorted(events,key=lambda e:(truth['utc_by_id'][e['event_id']],e['source_file'],e['row']))
        self.assertEqual([e['event_id'] for e in events],[e['event_id'] for e in expected])
        for e in events:self.assertEqual(e['parsed_timestamp'].isoformat(),truth['utc_by_id'][e['event_id']])
    def test_second_wipe(self):
        p=self.root/'full';g.generate(p);events=m.load_events(p)[0];r=next(e for e in events if e['event_id']=='EVT-SECOND-WIPE');self.assertEqual(m.utc_text(r['parsed_timestamp']),'2026-10-19T02:47:00Z');self.assertEqual(r['description'],g.RECOVERED['description'])
    def test_generator_preserves_existing(self):
        with self.assertRaises(ValueError):g.generate(self.logs)
    def test_bom_and_uppercase_extension(self):
        (self.logs/'a.JSON').write_text(json.dumps([event()]),encoding='utf-8-sig');self.assertEqual(self.load()[2]['valid'],1)

if __name__=='__main__':unittest.main()
