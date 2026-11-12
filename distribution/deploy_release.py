"""Install a verified application package on the existing host; never restore account data.
Run as root through the existing operator SSH connection. No cloud resource mutations.
"""
import argparse, fcntl, hashlib, io, json, os, re, sqlite3, subprocess, tarfile, tempfile, time
from pathlib import Path
from urllib.request import urlopen

FILES = frozenset([
    'study_lab/index.html', 'study_lab/python-worker.mjs', 'study_lab/material_assets.py',
    'study_lab/material-library.json', 'distribution/install_materials.py', 'distribution/server.py',
    'distribution/login.html', 'distribution/sync.js', 'distribution/requirements.txt',
    'distribution/gunicorn.conf.py', 'distribution/study-lab.service',
    'distribution/nginx.conf.template', 'distribution/Caddyfile.template',
    'distribution/catalog_receiver.py',
])
APP = Path('/opt/niis-study-lab')
STATE = Path('/var/lib/study-lab-releases')
DATABASE = Path('/var/lib/study-lab/study.sqlite3')
PROXY = Path('/etc/caddy/Caddyfile')


def unpack(data):
    """Read an exact file allowlist without extracting paths or following links."""
    if len(data) > 20_000_000:
        raise ValueError('Release archive too large')
    result = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for member in archive:
            if member.name not in FILES or member.name in result or not member.isfile():
                raise ValueError('Unexpected release member')
            if not 0 <= member.size <= 15_000_000:
                raise ValueError('Release member too large')
            result[member.name] = archive.extractfile(member).read()
            if sum(map(len, result.values())) > 30_000_000:
                raise ValueError('Expanded release too large')
    if result.keys() != FILES:
        raise ValueError('Incomplete release')
    return result


def atomic(path, data, mode=0o644):
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.release-')
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def healthy():
    for _ in range(30):
        try:
            with urlopen('http://127.0.0.1:8090/health', timeout=2) as response:
                if response.status == 200 and json.load(response) == {'status': 'ok'}:
                    return
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    raise RuntimeError('Application health check failed')


def caddy_config(original):
    begin, end = '# BEGIN NIIS STUDY LAB', '# END NIIS STUDY LAB'
    if original.count(begin) != 1 or original.count(end) != 1:
        raise ValueError('Cannot identify the existing Study Lab proxy block')
    before, block = original.split(begin, 1)
    block, after = block.split(end, 1)
    # Only the two known limits in the existing application block may change.
    for name in ('max_size', 'request_buffers'):
        block, count = re.subn(r'(?m)^(\s*' + name + r' )\d+MB(\s*)$', r'\g<1>11MB\2', block)
        if count != 1:
            raise ValueError('Unexpected proxy limit configuration')
    return before + begin + block + end + after


def install(archive, digest, commit):
    if not re.fullmatch('[0-9a-f]{40}', commit) or not re.fullmatch('[0-9a-f]{64}', digest):
        raise ValueError('Invalid release identity')
    data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('Archive hash mismatch')
    files = unpack(data)
    # Dependency upgrades require their own reviewed installation procedure.
    for name in ('distribution/requirements.txt', 'distribution/study-lab.service'):
        if files[name] != (APP/name).read_bytes():
            raise ValueError('Dependency or service-unit change requires explicit operator installation')
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (STATE/'release.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        hashes = {name: hashlib.sha256(value).hexdigest() for name, value in files.items()}
        current = STATE/'current.json'
        if current.exists() and json.loads(current.read_text()).get('commit') == commit:
            if all((APP/name).read_bytes() == value for name, value in files.items()):
                healthy()
                return {'status': 'unchanged', 'commit': commit}
        backup = STATE/(time.strftime('%Y%m%dT%H%M%S') + '-' + commit[:12])
        backup.mkdir(mode=0o700)
        previous = {name: (APP/name).read_bytes() if (APP/name).exists() else None for name in FILES}
        for name, value in previous.items():
            if value is None:
                continue
            target = backup/name
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            target.write_bytes(value)
        # A consistent, host-local backup; rollback restores code only.
        with sqlite3.connect(DATABASE) as source:
            with sqlite3.connect(backup/'study.sqlite3') as target:
                source.backup(target)
        os.chmod(backup/'study.sqlite3', 0o600)
        proxy = PROXY
        old_proxy = proxy.read_bytes()
        new_proxy = caddy_config(old_proxy.decode()).encode()
        (backup/'Caddyfile').write_bytes(old_proxy)
        changed_proxy = new_proxy != old_proxy
        stopped = False
        try:
            if changed_proxy:
                atomic(proxy, new_proxy)
                subprocess.run(['caddy', 'validate', '--config', str(proxy), '--adapter', 'caddyfile'], check=True, capture_output=True)
            subprocess.run(['systemctl', 'stop', 'study-lab'], check=True)
            stopped = True
            for name, value in files.items():
                atomic(APP/name, value)
            # Avoid stale bytecode when files have the same size and timestamp granularity.
            for path in [* (APP/'distribution/__pycache__').glob('*.pyc'),* (APP/'study_lab/__pycache__').glob('*.pyc')]:
                path.unlink()
            subprocess.run(['systemctl', 'start', 'study-lab'], check=True)
            healthy()
            if changed_proxy:
                subprocess.run(['systemctl', 'restart', 'caddy'], check=True)
            subprocess.run(['systemctl', 'is-active', '--quiet', 'study-lab', 'caddy'], check=True)
            record = {'commit': commit, 'archive_sha256': digest, 'files': hashes, 'backup': str(backup)}
            atomic(current, (json.dumps(record)+'\n').encode(), 0o600)
            return {'status': 'deployed', 'commit': commit, 'archive_sha256': digest}
        except Exception:
            if changed_proxy:
                atomic(proxy, old_proxy)
                subprocess.run(['systemctl', 'restart', 'caddy'], check=True)
            if stopped:
                subprocess.run(['systemctl', 'stop', 'study-lab'], check=False)
                for name, value in previous.items():
                    if value is None:
                        (APP/name).unlink(missing_ok=True)
                    else:
                        atomic(APP/name, value)
                for path in [* (APP/'distribution/__pycache__').glob('*.pyc'),* (APP/'study_lab/__pycache__').glob('*.pyc')]:
                    path.unlink()
                subprocess.run(['systemctl', 'start', 'study-lab'], check=True)
                healthy()
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    parser.add_argument('sha256')
    parser.add_argument('commit')
    args = parser.parse_args()
    print(json.dumps(install(args.archive, args.sha256, args.commit)))
