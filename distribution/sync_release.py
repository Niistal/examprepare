"""Host-local publisher: deploy only the current master commit after successful GitHub CI.
Install this file and deploy_release.py outside the development checkout before enabling its timer.
Uses existing gh authentication and the existing operator SSH key; never reads key contents.
"""
import fcntl, hashlib, json, os, subprocess, tempfile, uuid
from pathlib import Path
from urllib.request import urlopen
from deploy_release import unpack

REPO = 'Niistal/examprepare'
STATE = Path.home()/'.local/state/niis-study-lab'
SSH = ['ssh', '-i', str(Path.home()/'.ssh/product_radar_admin_20261106'),
       '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
       '-o', 'ConnectTimeout=10', 'ubuntu@51.170.37.119']


def command(args, **kwargs):
    return subprocess.check_output(args, timeout=180, **kwargs)


def api(path):
    return json.loads(command(['gh', 'api', 'repos/'+REPO+'/'+path]))


def master():
    return api('git/ref/heads/master')['object']['sha']


def verify_source(files, tree):
    if tree.get('truncated'):
        raise ValueError('Incomplete source tree')
    expected = {entry['path']: entry for entry in tree['tree']}
    for name, data in files.items():
        entry = expected.get(name, {})
        blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if entry.get('type') != 'blob' or entry.get('mode') != '100644' or entry.get('sha') != blob:
            raise ValueError('Artifact does not match the validated source: '+name)


def run():
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Share the legacy catalog lock to prevent two kinds of deployment at once.
    with (STATE/'automation.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'busy'}
        sha = master()
        marker = STATE/'release-published.json'
        if marker.exists() and json.loads(marker.read_text()).get('commit') == sha:
            return {'status': 'unchanged', 'commit': sha}
        runs = api('actions/workflows/release.yml/runs?branch=master&event=push&head_sha='+sha+'&per_page=20')['workflow_runs']
        runs = [r for r in runs if r['head_sha'] == sha and r['head_branch'] == 'master' and r['event'] == 'push']
        if not runs or runs[0]['status'] != 'completed' or runs[0]['conclusion'] != 'success':
            return {'status': 'waiting_for_successful_ci', 'commit': sha}
        selected = runs[0]
        with tempfile.TemporaryDirectory(prefix='study-release-') as tmp:
            command(['gh', 'run', 'download', str(selected['id']), '--repo', REPO,
                     '--name', 'study-release-'+sha, '--dir', tmp])
            archive = Path(tmp)/'release.tar.gz'
            data = archive.read_bytes()
            files = unpack(data)
            verify_source(files, api('git/trees/'+sha+'?recursive=1'))
            # Never publish an older passing commit while a newer master is pending.
            if master() != sha:
                return {'status': 'superseded', 'commit': sha}
            digest = hashlib.sha256(data).hexdigest()
            remote = '/tmp/study-release-'+uuid.uuid4().hex+'.tar.gz'
            try:
                command(SSH+['umask 077; cat > '+remote], input=data)
                if master() != sha:
                    return {'status': 'superseded', 'commit': sha}
                result = json.loads(command(SSH+['sudo -n python3 - '+remote+' '+digest+' '+sha],
                                            input=Path(__file__).with_name('deploy_release.py').read_bytes()))
            finally:
                command(SSH+['rm -f -- '+remote])
        if result.get('status') not in ('deployed', 'unchanged') or result.get('commit') != sha:
            raise RuntimeError('Host did not confirm deployment')
        # Observe HTTPS before recording success. Never request a user's account data.
        with urlopen('https://study.gripuno.com/health', timeout=15) as response:
            if response.status != 200 or json.load(response) != {'status': 'ok'}:
                raise RuntimeError('Production HTTPS health check failed')
        record = {**result, 'run_id': selected['id'], 'archive_sha256': digest}
        fd, pending = tempfile.mkstemp(dir=STATE, prefix='.release-')
        with os.fdopen(fd, 'w') as stream:
            json.dump(record, stream)
            stream.write('\n')
        os.replace(pending, marker)
        return record


if __name__ == '__main__':
    print(json.dumps(run()))
