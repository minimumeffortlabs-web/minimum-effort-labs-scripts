import contextlib,copy,importlib.util,io,json,sys,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch,Mock
import requests
SCRIPT=Path(__file__).resolve().parents[1]/'weather_change_report.py'
spec=importlib.util.spec_from_file_location('weather_report',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
NOW=datetime(2026,10,20,5,30,tzinfo=timezone.utc)
def fixture():
 params=m.request_params(39.1,-94.58,'America/Chicago',5,NOW)
 data=dict(latitude=39.1,longitude=-94.58,timezone='America/Chicago',utc_offset_seconds=-18000,
 daily_units=dict(time='iso8601',temperature_2m_max='\u00b0C',temperature_2m_min='\u00b0C',precipitation_sum='mm',wind_speed_10m_max='km/h'),
 daily=dict(time=['2026-10-15','2026-10-16','2026-10-17','2026-10-18','2026-10-19'],temperature_2m_max=[20,22,21,24,23],temperature_2m_min=[10,11,8,12,9],precipitation_sum=[1,2,0,3,.5],wind_speed_10m_max=[12,20,14,30,21]))
 return dict(kind='synthetic-test-fixture',params=params,response=data,retrieved_at=NOW.isoformat(),api_url=m.API_URL)
class WeatherTests(unittest.TestCase):
 def setUp(self):self.capture=fixture();self.params=self.capture['params'];self.data=self.capture['response']
 def test_valid_five_days(self):self.assertIs(m.validate_data(self.data,self.params,NOW),self.data)
 def test_exact_completed_dates_and_local_midnight(self):
  p=m.request_params(39.1,-94.58,'America/Chicago',5,datetime(2026,10,20,4,30,tzinfo=timezone.utc));self.assertEqual((p['start_date'],p['end_date']),('2026-10-14','2026-10-18'));self.assertEqual(self.params['end_date'],'2026-10-19')
 def test_extremes_and_daily_changes(self):
  a=m.analyze(self.data);self.assertEqual([x['change'] for x in a['rows']],[None,2,-1,3,-1]);self.assertEqual(a['warmest'],(24,'2026-10-18'));self.assertEqual(a['coldest'],(8,'2026-10-17'))
 def test_precipitation_and_wind(self):
  a=m.analyze(self.data);self.assertAlmostEqual(a['total_precipitation'],6.5);self.assertEqual(a['highest_wind'],(30,'2026-10-18'))
 def test_missing_precipitation_is_not_zero(self):
  self.data['daily']['precipitation_sum'][1]=None;m.validate_data(self.data,self.params,NOW);a=m.analyze(self.data);self.assertIsNone(a['total_precipitation']);self.assertEqual(a['known_precipitation'],4.5);self.assertIn('Incomplete precipitation',m.format_report(self.capture))
 def test_all_precipitation_missing_remains_unknown(self):
  self.data['daily']['precipitation_sum']=[None]*5;a=m.analyze(self.data);self.assertIsNone(a['total_precipitation']);self.assertIsNone(a['known_precipitation'])
 def test_missing_temperature_no_bridge(self):
  self.data['daily']['temperature_2m_max'][1]=None;m.validate_data(self.data,self.params,NOW);a=m.analyze(self.data);self.assertEqual([x['change'] for x in a['rows']],[None,None,None,3,-1]);self.assertEqual(a['coverage']['temperature_2m_max'],4)
 def test_inconsistent_arrays(self):
  self.data['daily']['wind_speed_10m_max'].pop()
  with self.assertRaisesRegex(ValueError,'array'):m.validate_data(self.data,self.params,NOW)
 def test_missing_json_structure(self):
  for data in [[],{},dict(error=True),dict(daily={})]:
   with self.subTest(data=data),self.assertRaises(ValueError):m.validate_data(data,self.params,NOW)
 def test_partial_or_unordered_dates_rejected(self):
  for dates in [['2026-10-16','2026-10-17','2026-10-18','2026-10-19','2026-10-20'],list(reversed(self.data['daily']['time']))]:
   self.data['daily']['time']=dates
   with self.assertRaises(ValueError):m.validate_data(self.data,self.params,NOW)
 def test_invalid_coordinates_and_day_counts(self):
  for lat,lon,days in [(91,0,5),(0,-181,5),(float('nan'),0,5),(0,float('inf'),5),(0,0,0),(0,0,32),(0,0,True)]:
   with self.subTest(values=(lat,lon,days)),self.assertRaises(ValueError):m.request_params(lat,lon,'UTC',days,NOW)
 def test_date_bounds(self):
  for end in ['2026-10-20','2026-01-01']:
   with self.subTest(end=end),self.assertRaises(ValueError):m.request_params(39.1,-94.58,'America/Chicago',5,NOW,end)
 def test_timezone_and_offset_mismatch(self):
  self.data['utc_offset_seconds']=0
  with self.assertRaisesRegex(ValueError,'offset'):m.validate_data(self.data,self.params,NOW)
 def test_dst_period_fails_explicitly(self):
  with self.assertRaisesRegex(ValueError,'DST'):m.request_params(39.1,-94.58,'America/Chicago',5,datetime(2026,11,4,16,tzinfo=timezone.utc))
 def test_units_and_invalid_numeric_values(self):
  self.data['daily_units']['temperature_2m_max']='F'
  with self.assertRaisesRegex(ValueError,'units'):m.validate_data(self.data,self.params,NOW)
  self.data=fixture()['response'];self.data['daily']['precipitation_sum'][0]=-1
  with self.assertRaises(ValueError):m.validate_data(self.data,self.params,NOW)
  self.data['daily']['precipitation_sum'][0]=float('nan')
  with self.assertRaises(ValueError):m.validate_data(self.data,self.params,NOW)
 def test_https_timeout_and_json_handling(self):
  response=Mock();response.json.return_value=self.data
  with patch.object(m.requests,'get',return_value=response) as get:
   self.assertEqual(m.fetch_data(self.params),self.data);get.assert_called_once_with(m.API_URL,params=self.params,timeout=15);self.assertTrue(m.API_URL.startswith('https://'));response.raise_for_status.assert_called_once()
 def test_http_errors(self):
  response=Mock();response.raise_for_status.side_effect=requests.HTTPError('503')
  with patch.object(m.requests,'get',return_value=response),self.assertRaises(requests.HTTPError):m.fetch_data(self.params)
  response.json.assert_not_called()
 def test_network_timeout(self):
  with patch.object(m.requests,'get',side_effect=requests.Timeout('timeout')),self.assertRaises(requests.Timeout):m.fetch_data(self.params)
 def test_malformed_json(self):
  response=Mock();response.json.side_effect=ValueError('malformed json')
  with patch.object(m.requests,'get',return_value=response),self.assertRaises(ValueError):m.fetch_data(self.params)
 def test_output_and_no_overwrite(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'report.txt';text=m.format_report(self.capture);m.save_report(path,text);self.assertEqual(path.read_text(encoding='utf-8'),text);self.assertIn('Machine effectiveness: Not established.',text);self.assertGreater(len(text.splitlines()),15)
   with self.assertRaises(FileExistsError):m.save_report(path,'replace')
 def test_offline_cli_replay(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);src=root/'synthetic.json';src.write_text(json.dumps(self.capture));dest=root/'weather.txt'
   with patch.object(sys,'argv',['weather','--replay',str(src),'--output',str(dest)]),patch.object(m.requests,'get') as get,contextlib.redirect_stdout(io.StringIO()) as stdout:
    self.assertEqual(m.main(),0);get.assert_not_called();self.assertIn('synthetic-test-fixture',stdout.getvalue());self.assertTrue(dest.exists())
 def test_cli_errors_not_success(self):
  with tempfile.TemporaryDirectory() as folder:
   with patch.object(sys,'argv',['weather','--latitude','999','--output',str(Path(folder)/'x.txt')]),contextlib.redirect_stderr(io.StringIO()) as stderr:
    self.assertEqual(m.main(),2);self.assertIn('ERROR:',stderr.getvalue())
if __name__=='__main__':unittest.main()
