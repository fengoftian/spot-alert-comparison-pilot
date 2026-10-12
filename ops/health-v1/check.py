"""Read-only study health checks. State writes target only the observer branch."""
import base64,datetime as dt,gzip,hashlib,json,os,pathlib,re,subprocess,sys,urllib.parse
OWN='fengoftian/spot-alert-comparison-pilot'
REPOS={'A':OWN,'B':'fengoftian/spot-alert-extensions-pilot'}
FREEZES={'A':'46031d8cc91e78679fab8a3b93a77e474e2423c3000944b26b3306a368b9a01e','B':'cb008dca30c97fe1d3eb28afd8367b7838fadf667ea44bdb80023b853e9a0cd9'}
SEEDS={'A':'5d7b88ea9b1c1cf43fa036ecb513461656ace1d69238fd879140d4f4a22d38dc','B':'1e3d70452562dc74ab85c3b744162aa82511545804eb13e402c019839e7b4ced'}
MAX_AGE_SECONDS=900

def api(path,method='GET',data=None):
 cmd=['gh','api',path,'--method',method]
 if data is not None:cmd+=['--input','-']
 p=subprocess.run(cmd,input=json.dumps(data) if data is not None else None,capture_output=True,text=True,timeout=20)
 if p.returncode:raise RuntimeError('GitHub API request failed: '+path+' '+p.stderr[:250])
 return json.loads(p.stdout) if p.stdout.strip() else None

def file(repo,path,ref):
 if not re.fullmatch('[a-f0-9]{40}',ref):raise ValueError('Invalid commit identity')
 r=api(f'repos/{repo}/contents/{path}?ref={ref}');b=base64.b64decode(r['content'])
 if hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()!=r['sha']:raise ValueError('Git blob mismatch')
 return b

def a_enabled():
 # Built-in workflow tokens cannot call the repository Variables API. Use the
 # authoritative workflow context in hosted runs; the owner CLI can read it locally.
 value=os.environ.get('A_COLLECT_ENABLED')
 if value is None:value=api(f'repos/{OWN}/actions/variables/COLLECT_ENABLED')['value']
 if value not in {'true','false'}:raise ValueError('A collection enable status unavailable')
 return value=='true'

def assess(label,status,cloud,freeze,producer,now,enabled=True):
 problems=[]
 if cloud.get('repository')!=REPOS[label] or cloud.get('host')!='GITHUB_ACTIONS':problems.append('PRODUCER_IDENTITY')
 if producer.get('head_sha')!=cloud.get('source_commit'):problems.append('PRODUCER_SOURCE')
 if status.get('last_tick')!=cloud.get('last_tick') or status.get('stage')!=cloud.get('stage'):problems.append('STATUS_MISMATCH')
 if not status.get('frozen_identity_ok'):problems.append('FROZEN_IDENTITY')
 if label=='A' and not enabled and status.get('stage')=='INTEGRITY_HALT' and status.get('open_positions')==0:
  return {'state':'KNOWN_CONTAINED_HALT_INCOMPLETE','problems':problems,'collection_active':False}
 if now>=freeze['tail_end']:
  if status.get('stage')!='COMPLETE_OR_UNRESOLVED_AT_TAIL':problems.append('TERMINAL_STATUS_NOT_PUBLISHED')
  return {'state':'COMPLETE' if not problems else 'FAILURE','problems':problems,'collection_active':False}
 if status.get('stage') not in {'COLLECTING','WARMUP_BEFORE_FUTURE_START','SETTLEMENT_TAIL'}:problems.append('COLLECTOR_HALTED')
 if producer.get('status')=='completed' and producer.get('conclusion')!='success':problems.append('PRODUCER_FAILED')
 age=(now-(status.get('last_tick') or 0))/1000
 if age>MAX_AGE_SECONDS:problems.append('TICK_STALE')
 if age < -60:problems.append('TICK_FROM_FUTURE')
 coverage=status.get('coverage',[])
 if len(coverage)!=44:problems.append('COHORT_COVERAGE')
 oldest=max([(now-x['last']-60000)/1000 for x in coverage],default=float('inf'))
 if oldest>MAX_AGE_SECONDS:problems.append('CANDLES_STALE')
 return {'state':'HEALTHY' if not problems else 'FAILURE','problems':sorted(set(problems)),'collection_active':True,'tick_age_seconds':round(age,2),'oldest_close_age_seconds':round(oldest,2)}

def inspect(label,now):
 repo=REPOS[label];head=api(f'repos/{repo}/branches/observations')['commit']['sha']
 st=json.loads(file(repo,'STATUS.json',head));cl=json.loads(file(repo,'CLOUD_STATUS.json',head));seed=json.loads(file(repo,'SEED.json',head))
 frozen_bytes=file(repo,'gen/FREEZE.json',cl['source_commit']);fr=json.loads(frozen_bytes)
 if hashlib.sha256(frozen_bytes).hexdigest()!=FREEZES[label] or seed['seed_sha256']!=SEEDS[label]:raise ValueError('Original freeze or seed changed')
 producer=api(f'repos/{repo}/actions/runs/{cl["run_id"]}')
 enabled=True
 if label=='A':enabled=a_enabled()
 result=assess(label,st,cl,fr,producer,now,enabled)
 result.update(commit=head,producer_id=cl['run_id'],source_commit=cl['source_commit'],tail_end=fr['tail_end'],seed_identity_verified=True,freeze_identity_verified=True)
 if result['state'] not in {'HEALTHY'}:return result
 delta=file(repo,f'journal/{cl["checkpoint_sequence"]:08d}.json.gz',head)
 if hashlib.sha256(delta).hexdigest()!=cl['checkpoint_sha256']:raise ValueError('Checkpoint identity mismatch')
 changes=json.loads(gzip.decompress(delta));raw=None
 for x in changes['changes']:
  if x['table']=='kv' and x['key']==['last_raw'] and x['row'] is not None:raw=json.loads(x['row'][1])
 if raw is None:raise ValueError('Latest checkpoint lacks candle receipt pointer')
 if not re.fullmatch(r'raw/\d+-candles-[a-f0-9]{8}\.json\.gz',raw):raise ValueError('Invalid receipt path')
 receipts=json.loads(gzip.decompress(file(repo,raw,head)));seen=set()
 for rec in receipts:
  if rec.get('status')!=200 or hashlib.sha256(rec['raw'].encode()).hexdigest()!=rec['sha256']:raise ValueError('Unsuccessful/mismatched candle response')
  url=urllib.parse.urlparse(rec['url'])
  if url.netloc!='data-api.binance.vision' or url.path!='/api/v3/klines':raise ValueError('Unexpected public endpoint')
  seen.add(urllib.parse.parse_qs(url.query)['symbol'][0])
 if seen!={x['symbol'] for x in st['coverage']}:raise ValueError('Receipt cohort mismatch')
 result.update(successful_responses=len(receipts),receipt_symbols=len(seen),prospective_receipts=st['prospective_bar_receipts'],warmup_receipts=st['warmup_bar_receipts'])
 if st['open_positions']:
  tree=api(f'repos/{repo}/git/trees/{head}?recursive=1')
  if tree.get('truncated'):raise ValueError('Receipt tree truncated')
  books=[x['path'] for x in tree['tree'] if re.fullmatch(r'raw/\d+-books-[a-f0-9]{8}\.json\.gz',x['path'])]
  if not books:raise ValueError('Missing public book receipt')
  name=max(books,key=lambda n:int(pathlib.PurePosixPath(n).name.split('-')[0]));batch=json.loads(gzip.decompress(file(repo,name,head)))
  for rec in batch:
   if rec.get('status')!=200 or rec['duration']>5 or now-rec['received']>MAX_AGE_SECONDS*1000 or hashlib.sha256(rec['raw'].encode()).hexdigest()!=rec['sha256']:raise ValueError('Book capture failure/staleness')
   url=urllib.parse.urlparse(rec['url'])
   if url.netloc!='data-api.binance.vision' or url.path!='/api/v3/depth':raise ValueError('Unexpected book endpoint')
   book=json.loads(rec['raw'])
   if not book.get('bids') or not book.get('asks'):raise ValueError('Missing book sides')
   if float(book['bids'][0][0])>=float(book['asks'][0][0]):raise ValueError('Crossed/locked book')
  if not batch:raise ValueError('Empty book batch')
  result.update(latest_book_batch_responses=len(batch),book_capture_check='PASS_LATEST_CAPTURE_BATCH')
 return result

def main():
 now=int(dt.datetime.now(dt.timezone.utc).timestamp()*1000);results={}
 for label in REPOS:
  try:results[label]=inspect(label,now)
  except Exception as ex:results[label]={'state':'VERIFICATION_UNAVAILABLE','problems':[type(ex).__name__+': '+str(ex)[:250]]}
 out={'checked_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'studies':results,'scope':'Collection integrity/freshness only; no account economics'}
 print(json.dumps(out,indent=2));pathlib.Path('health-output.json').write_text(json.dumps(out,indent=2)+'\n')
 if os.environ.get('GITHUB_ACTIONS')=='true':
  with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as h:h.write('### Collection observer\n\n```json\n'+json.dumps(out,indent=2)+'\n```\n')
 # Unavailable verification is explicit, never reported as a collection failure or health.
 failed={k:(['VERIFICATION_UNAVAILABLE'] if v['state']=='VERIFICATION_UNAVAILABLE' else v['problems']) for k,v in results.items() if v['problems']}
 fingerprint=hashlib.sha256(json.dumps(failed,sort_keys=True).encode()).hexdigest() if failed else None
 previous={};content_sha=None
 try:
  prev=api(f'repos/{OWN}/contents/health-state.json?ref=health-state');content_sha=prev['sha'];previous=json.loads(base64.b64decode(prev['content']))
 except RuntimeError:pass
 state={'fingerprint':fingerprint,'checked_utc':out['checked_utc'],'studies':results}
 if os.environ.get('GITHUB_ACTIONS')=='true':
  body={'message':'Record collection observer state','content':base64.b64encode((json.dumps(state,indent=2)+'\n').encode()).decode(),'branch':'health-state'}
  if content_sha:body['sha']=content_sha
  api(f'repos/{OWN}/contents/health-state.json',method='PUT',data=body)
  if all('tail_end' in v for v in results.values()) and now>=max(v['tail_end'] for v in results.values()):
   api(f'repos/{OWN}/actions/workflows/health.yml/disable',method='PUT')
 if failed and fingerprint!=previous.get('fingerprint'):return 1
 return 0

if __name__=='__main__':raise SystemExit(main())
