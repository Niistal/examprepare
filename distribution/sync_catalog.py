"""Push a tested catalog to the existing OCI host via a catalog-only SSH credential."""
import fcntl,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STATE=Path.home()/'.local/state/niis-study-lab'
RUNTIME=['distribution/server.py','distribution/login.html','distribution/sync.js']
SSH=['ssh','-i',str(STATE/'oci-catalog-key'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','study-publisher@51.170.37.119']

def command(args,timeout=120,input=None):
    result=subprocess.run(args,cwd=ROOT,input=input,capture_output=True,timeout=timeout,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'})
    if result.returncode:raise ValueError('Command failed: '+Path(args[0]).name)
    return result.stdout

def pending(record):
    fd,name=tempfile.mkstemp(dir=STATE,prefix='.oci-pending-')
    with os.fdopen(fd,'w') as f:json.dump(record,f);f.write('\n')
    os.replace(name,STATE/'oci-catalog-pending.json')

def clean():return not command(['git','status','--porcelain']).strip()
def run():
    STATE.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (STATE/'automation.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return {'status':'busy'}
        if not clean():return {'status':'foreground_work'}
        if command(['git','branch','--show-current']).strip()!=b'feat/niis-study-lab':return {'status':'blocked_branch'}
        commit=command(['git','rev-parse','HEAD']).decode().strip()
        remote=command(['git','ls-remote','origin','refs/heads/feat/niis-study-lab']).decode().split()
        if not remote or remote[0]!=commit:return {'status':'blocked_upstream'}
        payload=(ROOT/'study_lab/index.html').read_bytes();digest=hashlib.sha256(payload).hexdigest()
        runtime={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in RUNTIME}
        observed=json.loads(command(SSH,input=b'{"mode":"status"}\n'))
        if observed.get('runtime')!=runtime:return {'status':'blocked_runtime','message':'Server release needs explicit deployment'}
        if observed.get('sha256')==digest:
            pending({'status':'published','commit':commit,'sha256':digest})
            return {'status':'unchanged','commit':commit,'sha256':digest}
        pending({'status':'pending','commit':commit,'sha256':digest})
        for args in [[sys.executable,'study_lab/test_artifacts.py'],[sys.executable,'study_lab/test_materials.py'],['node','study_lab/test_learning.cjs'],['node','study_lab/test_generador.cjs'],[sys.executable,'study_lab/scripts/run_hosted_smoke.py']]:command(args,timeout=180)
        if not clean() or command(['git','rev-parse','HEAD']).decode().strip()!=commit or (ROOT/'study_lab/index.html').read_bytes()!=payload:return {'status':'foreground_work','message':'Source changed during verification; pending retained'}
        # Recheck remote source immediately before publication.
        if command(['git','ls-remote','origin','refs/heads/feat/niis-study-lab']).decode().split()[0]!=commit:return {'status':'blocked_upstream'}
        header={'mode':'publish','commit':commit,'size':len(payload),'sha256':digest,'runtime':runtime}
        result=json.loads(command(SSH,input=(json.dumps(header)+'\n').encode()+payload))
        if result.get('status') not in {'published','unchanged'} or result.get('sha256')!=digest:raise ValueError('Receiver did not confirm exact document')
        pending({**result,'status':'published'})
        return result

if __name__=='__main__':
    try:print(json.dumps(run()))
    except (OSError,ValueError,subprocess.SubprocessError):print(json.dumps({'status':'blocked','message':'Catalog update failed; pending retained for next timer run'}));raise SystemExit(1)
