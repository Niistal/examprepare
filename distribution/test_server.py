"""Security and persistence checks; test accounts and DB exist only in a temporary directory."""
import io,json,tempfile,unittest
from pathlib import Path
from wsgiref.util import setup_testing_defaults
from distribution.server import App,EMPTY

class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.db=Path(self.tmp.name)/'test.sqlite3'
        self.app=App(self.db,'http://127.0.0.1:8090',development=True)
    def tearDown(self):self.tmp.cleanup()
    def request(self,path,method='GET',body=None,cookie='',csrf='',origin='http://127.0.0.1:8090'):
        env={};setup_testing_defaults(env);payload=json.dumps(body).encode() if body is not None else b''
        env.update(PATH_INFO=path,REQUEST_METHOD=method,CONTENT_TYPE='application/json',CONTENT_LENGTH=str(len(payload)),HTTP_COOKIE=cookie,HTTP_X_CSRF_TOKEN=csrf,HTTP_ORIGIN=origin,REMOTE_ADDR='127.0.0.1',**{'wsgi.input':io.BytesIO(payload)})
        result={}
        def start(status,headers):result.update(status=int(status.split()[0]),headers=dict(headers))
        result['body']=b''.join(self.app(env,start)).decode();return result
    def register(self,name='student1'):
        result=self.request('/api/register','POST',{'username':name,'password':'a test password 123'})
        self.assertEqual(result['status'],200,result);cookie=result['headers']['Set-Cookie'].split(';')[0]
        page=self.request('/',cookie=cookie);self.assertEqual(page['status'],200)
        bootstrap=json.loads(page['body'].split('const CLOUD_BOOTSTRAP=',1)[1].split(';\n',1)[0])
        return cookie,bootstrap['csrf']
    def test_isolation_and_cross_device_persistence(self):
        a,csrf=self.register();b,other=self.register('student2')
        state={'ratings':{'P35':2},'answers':{'single::P35':'private answer'},'history':[]}
        saved=self.request('/api/progress','PUT',{'revision':0,'state':state,'user_id':'ignored'},a,csrf)
        self.assertEqual(saved['status'],200)
        self.assertEqual(json.loads(self.request('/api/progress',cookie=b)['body'])['state'],EMPTY)
        self.app=App(self.db,'http://127.0.0.1:8090',development=True)
        login=self.request('/api/login','POST',{'username':'student1','password':'a test password 123'})
        fresh=login['headers']['Set-Cookie'].split(';')[0]
        self.assertEqual(json.loads(self.request('/api/progress',cookie=fresh)['body'])['state'],state)
        # Cookie changed to account B but old tab's CSRF cannot write to B.
        self.assertEqual(self.request('/api/progress','PUT',{'revision':0,'state':state},b,csrf)['status'],403)
    def test_conflict_never_overwrites(self):
        cookie,csrf=self.register();state={**EMPTY,'answers':{'P35':'first'}}
        self.assertEqual(self.request('/api/progress','PUT',{'revision':0,'state':state},cookie,csrf)['status'],200)
        self.assertEqual(self.request('/api/progress','PUT',{'revision':0,'state':EMPTY},cookie,csrf)['status'],409)
        self.assertEqual(json.loads(self.request('/api/progress',cookie=cookie)['body'])['state'],state)
    def test_auth_origin_csrf_and_logout(self):
        self.assertEqual(self.request('/')['status'],401)
        self.assertEqual(self.request('/api/progress')['status'],401)
        self.assertEqual(self.request('/api/register','POST',{'username':'abc','password':'long password 123'},origin='https://evil.example')['status'],403)
        cookie,csrf=self.register()
        self.assertIn('HttpOnly',self.request('/api/login','POST',{'username':'student1','password':'a test password 123'})['headers']['Set-Cookie'])
        self.assertEqual(self.request('/api/progress','PUT',{'revision':0,'state':EMPTY},cookie)['status'],403)
        self.assertEqual(self.request('/api/logout','POST',{},cookie,csrf)['status'],200)
        self.assertEqual(self.request('/api/progress',cookie=cookie)['status'],401)
    def test_validation_and_private_assets(self):
        cookie,csrf=self.register()
        for path in ['/../distribution/server.py','/distribution/server.py','/study.sqlite3','/.git/config']:
            self.assertEqual(self.request(path,cookie=cookie)['status'],404)
        self.assertEqual(self.request('/python-worker.mjs')['status'],401)
        for value in [None,{}, {'ratings':{'P35':True},'answers':{},'history':[]}]:
            self.assertEqual(self.request('/api/progress','PUT',{'revision':0,'state':value},cookie,csrf)['status'],400)
        page=self.request('/',cookie=cookie)
        self.assertIn("'sha256-",page['headers']['Content-Security-Policy'])
        self.assertNotIn("script-src 'unsafe-inline'",page['headers']['Content-Security-Policy'])
        self.assertNotIn('localStorage',page['body'])
    def test_passwords_sessions_and_expiry(self):
        a,_=self.register();self.register('student2')
        with self.app.db() as db:
            rows=db.execute('SELECT * FROM users').fetchall()
            self.assertNotEqual(rows[0]['password'],rows[1]['password'])
            self.assertTrue(all('a test password 123' not in str(dict(row)) for row in rows))
            self.assertNotEqual(db.execute('SELECT token FROM sessions').fetchone()[0],a.split('=',1)[1])
            db.execute('UPDATE sessions SET expires=0')
        self.assertEqual(self.request('/',cookie=a)['status'],401)
        self.assertEqual(self.request('/api/login','POST',{'username':'student1','password':'wrong password 123'})['status'],401)
    def test_rate_limit_and_secure_cookie(self):
        for _ in range(30):self.request('/api/login','POST',{'username':'missing','password':'invalid password 123'})
        self.assertEqual(self.request('/api/register','POST',{'username':'new','password':'long password 123'})['status'],429)
        with self.assertRaises(ValueError):App(self.db,'http://public.example')
        self.app=App(self.db,'https://study.example')
        with self.app.db() as db:db.execute('DELETE FROM attempts')
        result=self.request('/api/register','POST',{'username':'new','password':'long password 123'},origin='https://study.example')
        self.assertIn('__Host-study=',result['headers']['Set-Cookie']);self.assertIn('; Secure',result['headers']['Set-Cookie'])

if __name__=='__main__':unittest.main()
