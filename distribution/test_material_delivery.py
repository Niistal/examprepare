"""Shared course files require app cookies, not GitHub access; accounts retain isolation."""
import hashlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from wsgiref.util import setup_testing_defaults
from distribution.server import App
import distribution.server as server
class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.id='res-'+'b'*20
        folder=self.root/'study_lab/material-assets';folder.mkdir(parents=True);self.raw=b'%PDF-1.7\nshared course'
        (folder/(self.id+'.pdf')).write_bytes(self.raw)
        entry={'file':self.id+'.pdf','extension':'.pdf','filename':'tema.pdf','mime':'application/pdf','available':True,'size':len(self.raw),'sha256':hashlib.sha256(self.raw).hexdigest()}
        (self.root/'study_lab/material-library.json').write_text(json.dumps({'resources':{self.id:entry}}));self.app=App(self.root/'accounts.sqlite3','http://127.0.0.1:8090',development=True)
    def tearDown(self):self.tmp.cleanup()
    def request(self,path,cookie='',method='GET',body=None,range_value=None):
        env={};setup_testing_defaults(env);data=json.dumps(body).encode() if body else b''
        env.update(PATH_INFO=path,REQUEST_METHOD=method,HTTP_COOKIE=cookie,HTTP_ORIGIN='http://127.0.0.1:8090',CONTENT_TYPE='application/json',CONTENT_LENGTH=str(len(data)),**{'wsgi.input':io.BytesIO(data)})
        if range_value:env['HTTP_RANGE']=range_value
        result={}
        def start(status,headers):result.update(status=int(status.split()[0]),headers=dict(headers))
        with patch.object(server,'ROOT',self.root):result['body']=b''.join(self.app(env,start))
        return result
    def account(self,name):
        result=self.request('/api/register',method='POST',body={'username':name,'password':'only a QA password 123'});self.assertEqual(result['status'],200)
        return result['headers']['Set-Cookie'].split(';')[0]
    def test_two_students_share_course_file_and_anonymous_cannot(self):
        url='/api/materials/'+self.id;self.assertEqual(self.request(url)['status'],401)
        for name in ['studentone','studenttwo']:
            result=self.request(url,self.account(name),range_value='bytes=0-3');self.assertEqual(result['status'],206);self.assertEqual(result['body'],b'%PDF')
    def test_no_paths_writes_or_head_body(self):
        cookie=self.account('studentone')
        self.assertEqual(self.request('/api/materials/../../accounts.sqlite3',cookie)['status'],404)
        self.assertEqual(self.request('/api/materials/'+self.id,cookie,method='POST')['status'],405)
        self.assertEqual(self.request('/api/materials/'+self.id,cookie,method='HEAD')['body'],b'')
if __name__=='__main__':unittest.main()
