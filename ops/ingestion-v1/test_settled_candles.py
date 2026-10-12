import copy,json,pathlib,unittest
from settled_candles import AdmissionGate,DataRevisionError,entry_time_eligible
def bar(t=0):return [t,'100','101','99','100','1',t+59999,'100',1,'0.5','50','0']
class AdmissionTests(unittest.TestCase):
 def test_forming_candle_is_not_admitted(self):
  g=AdmissionGate();self.assertIsNone(g.observe('TEST',bar(),59000));self.assertEqual(g.admitted,{})
 def test_stability_before_minimum_age_is_insufficient(self):
  g=AdmissionGate();g.observe('TEST',bar(),61000);self.assertIsNone(g.observe('TEST',bar(),80000))
 def test_two_stable_observations_and_age_admit(self):
  g=AdmissionGate();g.observe('TEST',bar(),61000);a=g.observe('TEST',bar(),120000);self.assertEqual(a['available_at'],120000)
 def test_pending_revision_restarts_stability(self):
  g=AdmissionGate();first=bar();g.observe('TEST',first,60757);second=copy.deepcopy(first);second[4]='99.98';second[5]='1.1';second[7]='110';second[8]=2
  self.assertIsNone(g.observe('TEST',second,120697));self.assertIsNone(g.observe('TEST',second,130000));a=g.observe('TEST',second,180000)
  self.assertEqual(a['raw'],g.observations[-1]['raw']);self.assertEqual(g.observations[0]['raw'],__import__('json').dumps(first,separators=(',',':')))
 def test_admitted_revision_halts_and_preserves_history(self):
  g=AdmissionGate();g.observe('TEST',bar(),61000);a=g.observe('TEST',bar(),120000);changed=bar();changed[4]='99.9'
  with self.assertRaises(DataRevisionError):g.observe('TEST',changed,180000)
  self.assertEqual(g.admitted[('TEST',0)],a)
 def test_duplicate_admitted_observation_is_idempotent(self):
  g=AdmissionGate();g.observe('TEST',bar(),61000);a=g.observe('TEST',bar(),120000);self.assertEqual(g.observe('TEST',bar(),180000),a)
 def test_caller_cannot_rewrite_admitted_or_observed_history(self):
  g=AdmissionGate();g.observe('TEST',bar(),61000);a=g.observe('TEST',bar(),120000)
  with self.assertRaises(TypeError):a['raw']='rewritten'
  with self.assertRaises(TypeError):g.observations[0]['raw']='rewritten'
  with self.assertRaises(TypeError):g.admitted[('TEST',0)]={}
 def test_invalid_schema_and_values_are_rejected(self):
  for row in [bar()[:5],bar()+[1]]:
   with self.assertRaises(ValueError):AdmissionGate().observe('TEST',row,120000)
  row=bar();row[4]='NaN'
  with self.assertRaises(ValueError):AdmissionGate().observe('TEST',row,120000)
 def test_crossed_ohlc_and_excess_taker_turnover_are_rejected(self):
  for index,value in [(3,'102'),(10,'101')]:
   row=bar();row[index]=value
   with self.assertRaises(ValueError):AdmissionGate().observe('TEST',row,120000)
 def test_out_of_order_receipt_is_rejected(self):
  g=AdmissionGate();g.observe('TEST',bar(),90000)
  with self.assertRaises(ValueError):g.observe('TEST',bar(),80000)
 def test_out_of_order_after_admission_is_rejected(self):
  g=AdmissionGate();g.observe('TEST',bar(),61000);g.observe('TEST',bar(),120000);g.observe('TEST',bar(),180000)
  with self.assertRaises(ValueError):g.observe('TEST',bar(),170000)
 def test_invalid_observation_is_retained_for_diagnostics(self):
  g=AdmissionGate();row=bar()[:3]
  with self.assertRaises(ValueError):g.observe('TEST',row,120000)
  self.assertEqual(len(g.observations),1);self.assertEqual(g.admitted,{})
 def test_minimum_admission_bounds_cannot_be_reduced(self):
  with self.assertRaises(ValueError):AdmissionGate(minimum_age_ms=1)
 def test_admission_cannot_enable_a_past_book(self):
  a={'closed_at':60000,'available_at':180000}
  self.assertFalse(entry_time_eligible(a,130000,1,1000000));self.assertTrue(entry_time_eligible(a,180000,1,1000000))
 def test_expired_or_slow_book_or_cutoff_cannot_fill(self):
  a={'closed_at':60000,'available_at':180000}
  self.assertFalse(entry_time_eligible(a,240001,1,1000000));self.assertFalse(entry_time_eligible(a,180000,5.1,1000000));self.assertFalse(entry_time_eligible(a,180000,1,180000))
 def test_actual_archived_aave_revision_remains_pending_until_stable(self):
  fixture=json.loads((pathlib.Path(__file__).parent/'aave_revision_fixture.json').read_text());g=AdmissionGate()
  self.assertIsNone(g.observe(fixture['symbol'],fixture['original'],fixture['original_received']))
  self.assertIsNone(g.observe(fixture['symbol'],fixture['later'],fixture['later_received']))
  # A hypothetical third stable receipt tests the gate, not market finality or a fill.
  a=g.observe(fixture['symbol'],fixture['later'],fixture['later_received']+60000)
  self.assertEqual(json.loads(a['raw']),fixture['later']);self.assertEqual(json.loads(g.observations[0]['raw']),fixture['original'])
if __name__=='__main__':unittest.main(verbosity=2)
