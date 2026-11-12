"""Release trust boundary tests: source identity, path allowlist and scoped proxy edits."""
import hashlib, io, sys, tarfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy_release import FILES, caddy_config, unpack
from sync_release import verify_source


def archive(entries):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w:gz') as tar:
        for name, data, kind in entries:
            member = tarfile.TarInfo(name)
            member.type = kind
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
    return out.getvalue()


class ReleaseTests(unittest.TestCase):
    def test_exact_package_only(self):
        entries = [(name, b'tested bytes', tarfile.REGTYPE) for name in FILES]
        self.assertEqual(set(unpack(archive(entries))), FILES)
        for extra in [('../escape', b'x', tarfile.REGTYPE),
                      ('/etc/cron.d/job', b'x', tarfile.REGTYPE),
                      (next(iter(FILES)), b'x', tarfile.SYMTYPE), entries[0]]:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                unpack(archive(entries+[extra]))
        with self.assertRaises(ValueError):
            unpack(archive(entries[:-1]))

    def test_artifact_bytes_must_match_source_blobs(self):
        data = b'exact source\n'
        blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        tree = {'tree': [{'path': 'file', 'type': 'blob', 'mode': '100644', 'sha': blob}]}
        verify_source({'file': data}, tree)
        for files, source in [({'file': b'tampered'}, tree), ({'missing': data}, tree),
                              ({'file': data}, {**tree, 'truncated': True})]:
            with self.assertRaises(ValueError):
                verify_source(files, source)

    def test_proxy_changes_only_study_lab_limits(self):
        other = 'radar.example {\n request_body { max_size 2MB }\n}\n'
        config = other+'# BEGIN NIIS STUDY LAB\nstudy.example {\n max_size 2MB\n request_buffers 2MB\n}\n# END NIIS STUDY LAB\n'
        updated = caddy_config(config)
        self.assertTrue(updated.startswith(other))
        self.assertIn('max_size 11MB', updated)
        self.assertIn('request_buffers 11MB', updated)
        self.assertEqual(caddy_config(updated), updated)
        with self.assertRaises(ValueError):
            caddy_config(other)

# Installation tests mock service control but exercise real file replacement and SQLite backup.
import json, sqlite3, subprocess, tempfile
from unittest.mock import patch
import deploy_release

class InstallTests(unittest.TestCase):
    def test_failed_start_restores_code_and_proxy_without_restoring_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); app = root/'app'; state = root/'state'; db = root/'accounts.sqlite3'; proxy = root/'Caddyfile'
            old = {name: b'previous' for name in FILES}
            new = {**old, 'study_lab/index.html': b'new verified HTML', 'distribution/server.py': b'new server'}
            for name, data in old.items():
                path = app/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
            original_proxy = '# BEGIN NIIS STUDY LAB\nmax_size 2MB\nrequest_buffers 2MB\n# END NIIS STUDY LAB\n'
            proxy.write_text(original_proxy)
            with sqlite3.connect(db) as conn:
                conn.execute('CREATE TABLE progress (answer TEXT)')
                conn.execute("INSERT INTO progress VALUES ('keep my answers')")
            package = root/'release.tar.gz'
            package.write_bytes(archive([(n, v, tarfile.REGTYPE) for n, v in new.items()]))
            failed = False
            def service(args, **kwargs):
                nonlocal failed
                if args == ['systemctl', 'start', 'study-lab'] and not failed:
                    failed = True
                    # Simulate an independent committed write after the backup.
                    with sqlite3.connect(db) as conn:
                        conn.execute("INSERT INTO progress VALUES ('new answer')")
                    raise subprocess.CalledProcessError(1, args)
                return subprocess.CompletedProcess(args, 0)
            with patch.multiple(deploy_release, APP=app, STATE=state, DATABASE=db, PROXY=proxy), \
                 patch.object(deploy_release.subprocess, 'run', side_effect=service), \
                 patch.object(deploy_release, 'healthy'):
                with self.assertRaises(subprocess.CalledProcessError):
                    deploy_release.install(package, hashlib.sha256(package.read_bytes()).hexdigest(), 'a'*40)
            self.assertEqual({n: (app/n).read_bytes() for n in FILES}, old)
            self.assertEqual(proxy.read_text(), original_proxy)
            self.assertFalse((state/'current.json').exists())
            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM progress').fetchone()[0], 2)
            backups = list(state.glob('*/study.sqlite3'))
            self.assertEqual(len(backups), 1)
            with sqlite3.connect(backups[0]) as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM progress').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
