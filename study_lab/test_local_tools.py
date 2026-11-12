"""Local companion transport, refusal paths and OS discovery; no services installed/launched."""
import importlib.util
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch, MagicMock
import urllib.request
import urllib.error

spec=importlib.util.spec_from_file_location('local_server',Path(__file__).with_name('local_server.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LocalTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=m.create_server(0);cls.port=cls.server.server_port;cls.base=f'http://127.0.0.1:{cls.port}'
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def request(self,path,body=None,token=True,origin=None):
        headers={'Content-Type':'application/json'}
        if token:headers['X-Study-Token']=self.server.token
        if origin:headers['Origin']=origin
        request=urllib.request.Request(self.base+path,headers=headers,data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(request) as r:return r.status,r.read().decode()
        except urllib.error.HTTPError as e:
            with e:return e.code,e.read().decode()
    def test_local_binding(self):self.assertEqual(self.server.server_address[0],'127.0.0.1')
    def test_status_auth(self):self.assertEqual(self.request('/api/tools/status',token=False)[0],403)
    def test_hosted_origin_refused(self):self.assertEqual(self.request('/api/tools/launch',{'tool':'orange'},origin='https://study.example')[0],403)
    def test_no_origin_refused(self):self.assertEqual(self.request('/api/tools/launch',{'tool':'orange'})[0],403)
    def test_no_commands(self):self.assertEqual(self.request('/api/tools/launch',{'tool':'bash'},origin=self.base)[0],400)
    def test_invalid_practice(self):
        for practice in ['../../etc/passwd', [], 42]:self.assertEqual(self.request('/api/tools/launch',{'tool':'orange','practice':practice},origin=self.base)[0],400)
    def test_no_arguments(self):self.assertEqual(self.request('/api/tools/launch',{'tool':'orange','args':['--eval','evil']},origin=self.base)[0],400)
    def test_missing_tool(self):
        with patch.object(m,'orange_command',return_value=None):
            status,body=self.request('/api/tools/launch',{'tool':'orange'},origin=self.base)
            self.assertEqual(status,409);self.assertIn('no está instalado',body)
    def test_spawn_error(self):
        with patch.object(m,'orange_command',return_value=['orange-canvas']),patch.object(m.subprocess,'Popen',side_effect=OSError()):
            self.assertEqual(self.request('/api/tools/launch',{'tool':'orange'},origin=self.base)[0],503)
    def test_launch_allowlist(self):
        process=MagicMock();process.wait.side_effect=m.subprocess.TimeoutExpired('Orange',.8)
        with patch.object(m,'orange_command',return_value=['orange-canvas']),patch.object(m.subprocess,'Popen',return_value=process) as popen:
            self.assertEqual(self.request('/api/tools/launch',{'tool':'orange'},origin=self.base)[0],200)
            args,kwargs=popen.call_args;self.assertEqual(args[0],['orange-canvas',str(m.ROOT/'resources/orange-M09.ows')]);self.assertIs(kwargs['shell'],False)
        self.server.orange_process=None
    def test_windows_discovery(self):
        with patch.object(m.shutil,'which',side_effect=lambda n:'C:/Orange/orange-canvas.exe' if n=='orange-canvas.exe' else None),patch.object(m.Path,'is_file',return_value=True):self.assertEqual(m.orange_command(),['C:/Orange/orange-canvas.exe'])
    def test_linux_module_fallback(self):
        with patch.object(m.shutil,'which',return_value=None),patch.object(m.importlib.util,'find_spec',return_value=object()):self.assertEqual(m.orange_command(),[m.sys.executable,'-m','Orange.canvas'])
    def test_static_is_restricted(self):
        for path in ['/local_server.py','/.env','/../distribution/server.py']:self.assertEqual(self.request(path)[0],404)
        self.assertEqual(self.request('/resources/orange-classification.ows')[0],200)
    def test_status_truthful(self):
        status,body=self.request('/api/tools/status');self.assertEqual(status,200);self.assertFalse(json.loads(body)['services']['kafka']['identityVerified'])
    def test_index_bootstrap(self):
        status,body=self.request('/');self.assertEqual(status,200);self.assertIn('const LOCAL_TOOL_TOKEN=',body)
if __name__=='__main__':unittest.main()
