"""Install only this finite public-data study's user-level launchd job."""
import os,pathlib,plistlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent
LABEL='local.listed-surge.spot-alert-comparison-v1'
if __name__=='__main__':
 obj={'Label':LABEL,'ProgramArguments':[sys.executable,str(ROOT/'run_collector.py')],'WorkingDirectory':str(ROOT),'RunAtLoad':True,'StartInterval':60,'ProcessType':'Background','Nice':10,'EnvironmentVariables':{'PYTHONPYCACHEPREFIX':'/private/tmp/spot-alert-pycache'},'StandardOutPath':str(ROOT/'collector.stdout.log'),'StandardErrorPath':str(ROOT/'collector.stderr.log')}
 raw=plistlib.dumps(obj)
 expected=(ROOT/'collector.plist').read_bytes()
 if raw!=expected:raise ValueError('Installer/plist identity mismatch')
 import study
 study.load_freeze()
 dest=pathlib.Path.home()/'Library'/'LaunchAgents'/f'{LABEL}.plist'
 dest.parent.mkdir(exist_ok=True)
 if dest.exists():raise ValueError('Job file already exists; inspect instead of overwriting')
 with dest.open('xb') as h:h.write(raw)
 result=subprocess.run(['launchctl','bootstrap',f'gui/{os.getuid()}',str(dest)],capture_output=True,text=True)
 if result.returncode:
  dest.unlink();raise RuntimeError(result.stderr.strip())
 print(str(dest));print('Registered finite public-data collector; no order transport.')
