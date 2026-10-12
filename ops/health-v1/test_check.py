import copy,os,unittest
from unittest.mock import patch
from check import assess,REPOS,a_enabled,incident_categories
class HealthTests(unittest.TestCase):
 def setUp(self):
  self.now=2000000;self.st={'stage':'COLLECTING','last_tick':1900000,'frozen_identity_ok':True,'open_positions':0,'coverage':[{'symbol':str(i),'last':1860000} for i in range(44)]};self.cl={'repository':REPOS['B'],'host':'GITHUB_ACTIONS','stage':'COLLECTING','last_tick':1900000,'source_commit':'source'};self.run={'head_sha':'source','status':'in_progress','conclusion':None};self.f={'tail_end':3000000}
 def assess(self,label='B',enabled=True):return assess(label,self.st,self.cl,self.f,self.run,self.now,enabled)
 def test_fresh_receipts_are_healthy(self):self.assertEqual(self.assess()['state'],'HEALTHY')
 def test_running_job_with_stale_candles_fails(self):
  self.st['coverage'][0]['last']=1;self.assertIn('CANDLES_STALE',self.assess()['problems'])
 def test_stale_tick_fails(self):
  self.st['last_tick']=self.cl['last_tick']=1;self.assertIn('TICK_STALE',self.assess()['problems'])
 def test_frozen_identity_failure_is_detected(self):
  self.st['frozen_identity_ok']=False;self.assertIn('FROZEN_IDENTITY',self.assess()['problems'])
 def test_producer_source_mismatch_fails(self):
  self.run['head_sha']='other';self.assertIn('PRODUCER_SOURCE',self.assess()['problems'])
 def test_failed_producer_fails(self):
  self.run.update(status='completed',conclusion='failure');self.assertIn('PRODUCER_FAILED',self.assess()['problems'])
 def test_known_a_containment_is_explicit_and_quiet(self):
  self.cl['repository']=REPOS['A'];self.st['stage']=self.cl['stage']='INTEGRITY_HALT';self.st['last_tick']=self.cl['last_tick']=1
  self.assertEqual(self.assess('A',False)['state'],'KNOWN_CONTAINED_HALT_INCOMPLETE');self.assertEqual(self.assess('A',False)['problems'],[])
 def test_halted_a_with_open_positions_is_actionable(self):
  self.cl['repository']=REPOS['A'];self.st['stage']=self.cl['stage']='INTEGRITY_HALT';self.st['open_positions']=1
  self.assertIn('COLLECTOR_HALTED',self.assess('A',False)['problems'])
 def test_completed_tail_requires_terminal_status(self):
  self.now=3000000;self.assertIn('TERMINAL_STATUS_NOT_PUBLISHED',self.assess()['problems'])
 def test_tail_completion_is_expected(self):
  self.now=3000000;self.st['stage']=self.cl['stage']='COMPLETE_OR_UNRESOLVED_AT_TAIL';self.assertEqual(self.assess()['state'],'COMPLETE')
 def test_hosted_false_context_avoids_forbidden_variable_api(self):
  with patch.dict(os.environ,{'A_COLLECT_ENABLED':'false'}),patch('check.api') as api:
   self.assertFalse(a_enabled());api.assert_not_called()
 def test_hosted_true_context_avoids_forbidden_variable_api(self):
  with patch.dict(os.environ,{'A_COLLECT_ENABLED':'true'}),patch('check.api') as api:
   self.assertTrue(a_enabled());api.assert_not_called()
 def test_missing_workflow_variable_is_explicitly_unavailable(self):
  with patch.dict(os.environ,{'A_COLLECT_ENABLED':''}):
   with self.assertRaises(ValueError):a_enabled()
 def test_same_halt_does_not_change_category_when_staleness_grows(self):
  a,_=incident_categories({'B':{'state':'FAILURE','problems':['COLLECTOR_HALTED','PRODUCER_FAILED']}},{})
  b,_=incident_categories({'B':{'state':'FAILURE','problems':['COLLECTOR_HALTED','PRODUCER_FAILED','TICK_STALE','CANDLES_STALE']}},{})
  self.assertEqual(a,b)
 def test_one_transient_network_failure_does_not_alert(self):
  c,u=incident_categories({'B':{'state':'VERIFICATION_UNAVAILABLE','problems':['timeout']}},{})
  self.assertEqual(c,{});self.assertEqual(u,{'B':1})
 def test_repeated_unavailable_verification_is_actionable(self):
  c,_=incident_categories({'B':{'state':'VERIFICATION_UNAVAILABLE','problems':['timeout']}},{'consecutive_unavailable':{'B':1}})
  self.assertEqual(c,{'B':'VERIFICATION_UNAVAILABLE'})
 def test_recovery_clears_incident_category(self):
  c,u=incident_categories({'B':{'state':'HEALTHY','problems':[]}},{'consecutive_unavailable':{'B':2}})
  self.assertEqual(c,{});self.assertEqual(u,{})
if __name__=='__main__':unittest.main(verbosity=2)
