"""Package an exact clean runtime and, optionally, a separately verified course archive."""
import argparse,hashlib,json,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--require-materials',action='store_true');p.add_argument('--materials-output',type=Path);args=p.parse_args()
paths=['study_lab/index.html','study_lab/python-worker.mjs','study_lab/material_assets.py','study_lab/material-library.json','distribution/install_materials.py','distribution/server.py','distribution/login.html','distribution/sync.js','distribution/requirements.txt','distribution/gunicorn.conf.py','distribution/study-lab.service','distribution/nginx.conf.template','distribution/Caddyfile.template','distribution/catalog_receiver.py']
if subprocess.check_output(['git','status','--porcelain','--',*paths],cwd=ROOT).strip():raise SystemExit('Commit the tested deployment files before packaging')
if args.require_materials and not args.materials_output:raise SystemExit('--require-materials also requires --materials-output')
library=json.loads((ROOT/'study_lab/material-library.json').read_text(encoding='utf-8'))
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()

def checksum(path):
    digest=hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda:source.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()
def write_archive(path,names):
    with tarfile.open(path,'x:gz') as archive:
        for name in names:
            source=ROOT/name
            if source.is_symlink() or not source.is_file():raise SystemExit('Invalid source path')
            info=archive.gettarinfo(str(source),arcname=name);info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644
            with source.open('rb') as source_file:archive.addfile(info,source_file)
    return {'archive':str(path.resolve()),'sha256':checksum(path)}
assets=[]
if args.materials_output:
    for ident,item in library['resources'].items():
        if not item['available']:continue
        if item['file']!=ident+item['extension'] or '/' in item['file'] or '\\' in item['file']:raise SystemExit('Invalid material path')
        relative='study_lab/material-assets/'+item['file'];asset=ROOT/relative
        if asset.is_symlink() or not asset.is_file() or checksum(asset)!=item['sha256']:raise SystemExit('Missing or changed material: '+item['file'])
        assets.append(relative)
record={'status':'packaged_not_deployed','source_commit':sha,**write_archive(args.output,paths),'files':paths,'materials_status':'separate_archive' if assets else 'reading_only','materials_commit':library['source']['commit']}
if args.materials_output:record['materials']={**write_archive(args.materials_output,assets),'file_count':len(assets)}
print(json.dumps(record))
