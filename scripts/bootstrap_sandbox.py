"""Safe repository sync and isolated Python 3.12 / Playwright setup."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import venv

ROOT=Path(__file__).resolve().parents[1]
BRANCH='dev/poker-simulator-v03'
REMOTE='https://github.com/leblab000-max/pok.git'

def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True,encoding='utf-8').strip()

def sync_repository(root: Path, clone_base: Path | None=None) -> Path:
    """Never stash/reset/checkout over a user's changes or touch main.

    Unsafe-to-fast-forward checkouts get a separate clone, with the original tree
    and index untouched. Failure to fetch does not prevent using existing code.
    """
    branch=git(root,'branch','--show-current')
    dirty=bool(git(root,'status','--porcelain','--untracked-files=normal'))
    if branch!=BRANCH or dirty:
        base=clone_base or Path(os.environ.get('LOCALAPPDATA',str(root/'runs')))/'PokerAILab/checkouts'
        base.mkdir(parents=True,exist_ok=True);target=base/uuid.uuid4().hex[:12]
        print(f'Original checkout preserved ({branch}, dirty={dirty}). Cloning into {target}',flush=True)
        subprocess.check_call(['git','clone','--branch',BRANCH,'--single-branch',REMOTE,str(target)])
        return target
    try:
        # Fetch the known upstream rather than trusting a changed origin setting.
        subprocess.check_call(['git','-C',str(root),'fetch',REMOTE,BRANCH],timeout=90)
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
        print('WARNING: network sync unavailable; running the existing local revision.',flush=True)
        return root
    remote=git(root,'rev-parse','FETCH_HEAD')
    if subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor','HEAD',remote],capture_output=True).returncode:
        base=clone_base or Path(os.environ.get('LOCALAPPDATA',str(root/'runs')))/'PokerAILab/checkouts'
        base.mkdir(parents=True,exist_ok=True);target=base/uuid.uuid4().hex[:12]
        subprocess.check_call(['git','clone','--branch',BRANCH,'--single-branch',REMOTE,str(target)])
        print(f'Local commits preserved. Running a separate checkout: {target}',flush=True)
        return target
    subprocess.check_call(['git','-C',str(root),'merge','--ff-only',remote])
    return root

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-sync',action='store_true',help='Developer/offline use: preserve the current revision')
    parser.add_argument('--setup-only',action='store_true')
    parser.add_argument('--serve-only',action='store_true')
    args=parser.parse_args()
    if sys.version_info[:2]!=(3,12): raise RuntimeError('Python 3.12 is required')
    if not shutil.which('git'): raise RuntimeError('Git is required; install Git for Windows and reopen the launcher')
    print(sys.version);print(subprocess.check_output(['git','--version'],text=True).strip())
    root=ROOT if args.no_sync else sync_repository(ROOT)
    if root!=ROOT:
        command=[sys.executable,str(root/'scripts/bootstrap_sandbox.py'),'--no-sync']
        if args.setup_only:command.append('--setup-only')
        if args.serve_only:command.append('--serve-only')
        return subprocess.call(command,cwd=root)
    env_path=root/'.venv-sandbox';python=env_path/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    if not env_path.exists(): venv.EnvBuilder(with_pip=True).create(env_path)
    if not python.exists(): raise RuntimeError('Existing .venv-sandbox is incomplete; preserve/rename it before reinstalling')
    version=subprocess.check_output([str(python),'-c','import sys; print("%d.%d"%sys.version_info[:2])'],text=True).strip()
    if version!='3.12': raise RuntimeError('Existing .venv-sandbox uses another Python; preserve/rename it first')
    requirements=root/'requirements-sandbox.txt';fingerprint=hashlib.sha256(requirements.read_bytes()).hexdigest()
    marker=env_path/'sandbox-requirements.sha256'
    pins=dict(line.strip().split('==') for line in requirements.read_text().splitlines()
              if line.strip() and not line.lstrip().startswith('#'))
    dependencies_ok=subprocess.run([str(python),'-c',
        'from importlib.metadata import version; import json,sys; '
        'assert all(version(k)==v for k,v in json.loads(sys.argv[1]).items())',
        json.dumps(pins)],capture_output=True).returncode==0
    if not dependencies_ok or not marker.exists() or marker.read_text()!=fingerprint:
        subprocess.check_call([str(python),'-m','pip','install','-r',str(requirements)])
        marker.write_text(fingerprint)
    env=os.environ.copy();env['PLAYWRIGHT_BROWSERS_PATH']=str(root/'.sandbox-browsers')
    executable=subprocess.check_output([str(python),'-c',
        'from playwright.sync_api import sync_playwright\nwith sync_playwright() as p: print(p.chromium.executable_path)'],env=env,text=True).strip()
    if not Path(executable).exists(): subprocess.check_call([str(python),'-m','playwright','install','chromium'],env=env)
    print(f'Environment ready. Repository: {root}\nLaunch URL: http://127.0.0.1:8765',flush=True)
    if args.setup_only:return 0
    command=[str(python),str(root/'scripts/run_sandbox.py')]
    if args.serve_only:command.append('--serve-only')
    return subprocess.call(command,cwd=root,env=env)

if __name__=='__main__':
    try: sys.exit(main())
    except (Exception,KeyboardInterrupt) as exc:
        print(f'Setup failed: {exc}',file=sys.stderr);sys.exit(1)
