"""Install a full course asset archive against the already installed, Git-verified manifest.
Stream files into a staging directory; never execute/extract arbitrary archive members or touch accounts.
"""
import argparse,hashlib,json,os,re,shutil,tarfile,tempfile,time
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda:source.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def install(archive,expected_sha,root):
    archive,root=Path(archive),Path(root)
    if not re.fullmatch('[a-f0-9]{64}',expected_sha) or archive.stat().st_size>700_000_000 or digest(archive)!=expected_sha:raise ValueError('Invalid archive identity or size')
    app=root/'study_lab';target=app/'material-assets'
    if app.is_symlink() or not app.is_dir() or target.is_symlink() or target.exists() and not target.is_dir():raise ValueError('Unsafe material directory')
    manifest_bytes=(app/'material-library.json').read_bytes();manifest=json.loads(manifest_bytes);expected={}
    for ident,item in manifest['resources'].items():
        if not item['available']:continue
        if not re.fullmatch(r'res-[a-f0-9]{20}',ident) or not re.fullmatch(re.escape(ident)+r'\.[a-z0-9]+',item['file']):raise ValueError('Invalid manifest path')
        if type(item['size']) is not int or not 0<=item['size']<=200_000_000 or not re.fullmatch('[a-f0-9]{64}',item['sha256']):raise ValueError('Invalid manifest size/hash')
        expected['study_lab/material-assets/'+item['file']]=item
    if sum(i['size'] for i in expected.values())>1_000_000_000:raise ValueError('Library exceeds allowed size')
    stage=Path(tempfile.mkdtemp(prefix='.materials-stage-',dir=app));backup=None
    try:
        seen=set()
        with tarfile.open(archive,mode='r|gz') as tar:
            for member in tar:
                item=expected.get(member.name)
                if not item or member.name in seen or not member.isfile() or member.size!=item['size']:raise ValueError('Unexpected material archive member')
                seen.add(member.name);h=hashlib.sha256()
                with tar.extractfile(member) as source,(stage/item['file']).open('xb') as dest:
                    remaining=member.size
                    while remaining:
                        block=source.read(min(1024*1024,remaining))
                        if not block:raise ValueError('Truncated material')
                        dest.write(block);h.update(block);remaining-=len(block)
                os.chmod(stage/item['file'],0o644)
                if h.hexdigest()!=item['sha256']:raise ValueError('Material hash mismatch')
        if seen!=set(expected):raise ValueError('Incomplete material archive')
        if (app/'material-library.json').read_bytes()!=manifest_bytes:raise ValueError('Runtime manifest changed during installation; retry after runtime settles')
        if target.exists():
            backup=app/('material-assets.previous-'+time.strftime('%Y%m%dT%H%M%S')+'-'+stage.name.rsplit('-',1)[-1]);os.replace(target,backup)
        # The installer may run as root while Gunicorn runs as study-lab.
        # Publish only after verification, then allow the service to traverse the directory.
        os.chmod(stage,0o755)
        try:os.replace(stage,target)
        except Exception:
            if backup:os.replace(backup,target)
            raise
        return {'status':'installed','files':len(seen),'academic_commit':manifest['source']['commit'],'previous_assets':str(backup) if backup else None}
    finally:
        if stage.exists():shutil.rmtree(stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('sha256');p.add_argument('--root',type=Path,default=Path('/opt/niis-study-lab'));a=p.parse_args()
    print(json.dumps(install(a.archive,a.sha256,a.root)))
