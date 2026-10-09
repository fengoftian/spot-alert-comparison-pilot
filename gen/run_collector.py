"""Finite local collector wrapper; unload its own job after the fixed tail."""
import os,pathlib,subprocess,sys
import study
LABEL='local.listed-surge.spot-alert-comparison-v1'
if __name__=='__main__':
 sys.argv=[__file__,'tick'];study.main()
 f=study.load_freeze()
 if study.clock_ms()>=f['tail_end'] and (study.ROOT/'RESULTS.json').exists():
  source=pathlib.Path.home()/'Library'/'LaunchAgents'/f'{LABEL}.plist'
  # Remove only the exact job installed by this study. Keep the workspace artifact/logs.
  if source.exists() and source.read_bytes()==(study.ROOT/'collector.plist').read_bytes():source.unlink()
  subprocess.run(['launchctl','bootout',f'gui/{os.getuid()}/{LABEL}'],check=False)
