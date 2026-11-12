"""Package an exact, clean source commit, excluding all account data and credentials."""
import argparse,hashlib,json,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
paths=['study_lab/index.html','study_lab/python-worker.mjs','distribution/server.py','distribution/login.html','distribution/sync.js','distribution/requirements.txt','distribution/gunicorn.conf.py','distribution/study-lab.service','distribution/nginx.conf.template','distribution/Caddyfile.template','distribution/catalog_receiver.py']
if subprocess.check_output(['git','status','--porcelain','--',*paths],cwd=ROOT).strip():raise SystemExit('Commit the tested deployment files before packaging')
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
with tarfile.open(args.output,'x:gz') as archive:
    for name in paths:
        source=ROOT/name
        if source.is_symlink() or not source.is_file():raise SystemExit('Invalid source path')
        info=archive.gettarinfo(str(source),arcname=name);info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644
        with source.open('rb') as f:archive.addfile(info,f)
print(json.dumps({'status':'packaged_not_deployed','source_commit':sha,'archive':str(args.output.resolve()),'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'files':paths}))
