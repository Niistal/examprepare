"""Package an exact, clean source commit, excluding all account data and credentials."""
import argparse,hashlib,json,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--require-materials',action='store_true');args=p.parse_args()
paths=['study_lab/index.html','study_lab/python-worker.mjs','study_lab/material_assets.py','study_lab/material-library.json','distribution/server.py','distribution/login.html','distribution/sync.js','distribution/requirements.txt','distribution/gunicorn.conf.py','distribution/study-lab.service','distribution/nginx.conf.template','distribution/Caddyfile.template','distribution/catalog_receiver.py']
if subprocess.check_output(['git','status','--porcelain','--',*paths],cwd=ROOT).strip():raise SystemExit('Commit the tested deployment files before packaging')
library=json.loads((ROOT/'study_lab/material-library.json').read_text())
asset_paths=[]
assets_present=(ROOT/'study_lab/material-assets').is_dir()
if args.require_materials and not assets_present:raise SystemExit('Build material-assets before a full library release')
for item in library['resources'].values() if assets_present else []:
    if not item['available']:continue
    relative='study_lab/material-assets/'+item['file'];asset=ROOT/relative
    if asset.is_symlink() or not asset.is_file():raise SystemExit('Regenera material-assets antes de empaquetar: '+item['file'])
    if hashlib.sha256(asset.read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Material asset hash mismatch: '+item['file'])
    asset_paths.append(relative)
paths+=asset_paths
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
with tarfile.open(args.output,'x:gz') as archive:
    for name in paths:
        source=ROOT/name
        if source.is_symlink() or not source.is_file():raise SystemExit('Invalid source path')
        info=archive.gettarinfo(str(source),arcname=name);info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644
        with source.open('rb') as f:archive.addfile(info,f)
print(json.dumps({'status':'packaged_not_deployed','source_commit':sha,'archive':str(args.output.resolve()),'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'files':paths,'material_files':len(asset_paths),'materials_status':'complete' if assets_present else 'reading_only','materials_commit':library['source']['commit']}))
