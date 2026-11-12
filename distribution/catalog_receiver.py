"""Forced SSH command: accept only one bounded, hash-verified application document.

No shell, arbitrary paths, service management, account DB, or cloud operations.
"""
import fcntl,hashlib,json,os,re,sys,tempfile
from pathlib import Path
APP=Path('/opt/niis-study-lab')
STATE=Path('/var/lib/study-lab-publisher')
RUNTIME=['distribution/server.py','distribution/login.html','distribution/sync.js','study_lab/material_assets.py','study_lab/material-library.json']
MAX_SIZE=8*1024*1024

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data,mode):
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.study-publish-')
    try:
        os.fchmod(fd,mode)
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def receive(stream,app=APP,state=STATE):
    header=stream.readline(4097)
    if len(header)>4096 or not header.endswith(b'\n'):raise ValueError('header')
    request=json.loads(header)
    if not isinstance(request,dict):raise ValueError('header')
    runtime={name:sha(app/name) for name in RUNTIME}
    current=sha(app/'study_lab/index.html')
    if request.get('mode')=='status':return {'status':'observed','sha256':current,'runtime':runtime}
    if request.get('mode')!='publish':raise ValueError('mode')
    size=request.get('size');commit=request.get('commit');expected=request.get('sha256')
    if type(size) is not int or not 0<size<=MAX_SIZE or not isinstance(commit,str) or not re.fullmatch('[0-9a-f]{40}',commit) or not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):raise ValueError('metadata')
    if request.get('runtime')!=runtime:raise ValueError('runtime_requires_manual_release')
    payload=stream.read(size+1)
    if len(payload)!=size or hashlib.sha256(payload).hexdigest()!=expected:raise ValueError('payload_hash')
    html=payload.decode('utf-8')
    if not html.startswith('<!DOCTYPE html>') and not html.lower().startswith('<!doctype html>'):raise ValueError('document')
    if "const STATE_KEY='niis-study-lab-v1';" not in html or '</html>' not in html:raise ValueError('document')
    state.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (state/'publish.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        # Recheck under the lock; a repeated delivery converges without a second write.
        changed=sha(app/'study_lab/index.html')!=expected
        if changed:atomic(app/'study_lab/index.html',payload,0o644)
        record={'status':'published' if changed else 'unchanged','commit':commit,'sha256':expected,'runtime':runtime}
        atomic(state/'deployed.json',(json.dumps(record)+'\n').encode(),0o600)
        return record

if __name__=='__main__':
    try:print(json.dumps(receive(sys.stdin.buffer)))
    except (ValueError,TypeError,UnicodeError,OSError):
        print(json.dumps({'status':'blocked','message':'Publication rejected; previous document preserved or rechecked on retry'}));raise SystemExit(1)
