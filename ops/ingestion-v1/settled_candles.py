"""Offline ingestion prototype. Does not collect, trade, or amend a frozen study."""
import hashlib,json,math
from decimal import Decimal
from types import MappingProxyType

class DataRevisionError(ValueError):pass

def validate(row):
 if not isinstance(row,(list,tuple)) or len(row)!=12:raise ValueError('Invalid candle schema')
 if type(row[0]) is not int or row[0]%60000 or row[6]!=row[0]+59999:raise ValueError('Invalid candle time')
 values=[Decimal(str(row[i])) for i in [1,2,3,4,5,7,9,10]]
 if any(not x.is_finite() for x in values) or min(values[:4])<=0 or min(values[4:])<0:raise ValueError('Invalid candle values')
 o,h,l,c=values[:4]
 if not l<=min(o,c)<=max(o,c)<=h or values[-1]>values[5]:raise ValueError('Invalid OHLC/turnover')

class AdmissionGate:
 """Require age and repeated stability; admitted history is permanently immutable.

 The 60s age and 15s separation are declared engineering choices, not estimates
 of universal venue finality or optimized trading parameters.
 """
 def __init__(self,minimum_age_ms=60000,minimum_separation_ms=15000):
  if minimum_age_ms<60000 or minimum_separation_ms<15000:raise ValueError('Prototype admission bounds')
  self.age=minimum_age_ms;self.separation=minimum_separation_ms
  self.pending={};self._admitted={};self._observations=[];self.last_seen={}

 @property
 def admitted(self):return MappingProxyType(self._admitted)

 @property
 def observations(self):return tuple(self._observations)

 def observe(self,symbol,row,received):
  if type(received) is not int:raise ValueError('Receipt time must be integer milliseconds')
  body=json.dumps(row,separators=(',',':'))
  # Retain original captured content and each subsequent observation.
  self._observations.append(MappingProxyType({'symbol':symbol,'received':received,'sha256':hashlib.sha256(body.encode()).hexdigest(),'raw':body}))
  validate(row)
  key=(symbol,row[0]);closed=row[6]+1
  if key in self.last_seen and received<self.last_seen[key]:raise ValueError('Out-of-order receipt')
  self.last_seen[key]=received;old=self.pending.get(key)
  if key in self.admitted:
   if self.admitted[key]['raw']!=body:raise DataRevisionError('Admitted candle changed; explicit review required')
   return self.admitted[key]
  if received<closed:return None
  if old is None or old['raw']!=body:
   self.pending[key]={'raw':body,'stable_since':received,'last_received':received};return None
  old['last_received']=received
  if received-closed<self.age or received-old['stable_since']<self.separation:return None
  result={'symbol':symbol,'open_time':row[0],'closed_at':closed,'available_at':received,'raw':body,'sha256':hashlib.sha256(body.encode()).hexdigest()}
  self._admitted[key]=MappingProxyType(result);return self._admitted[key]

def entry_time_eligible(admission,book_received,request_duration,study_end):
 """Truthful current-book timing; never backdate an admission or fill."""
 signal=admission['closed_at'];due=signal+60000;deadline=due+120000
 return admission['available_at']<=book_received<study_end and due<=book_received<=deadline and 0<=request_duration<=5
