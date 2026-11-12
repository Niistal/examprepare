"""Checks the real production WSGI entrypoint and concurrent optimistic writes on loopback."""
import concurrent.futures,json,os,re,socket,subprocess,tempfile,time,urllib.error,urllib.request
from pathlib import Path

def main():
    executable=os.environ.get('STUDY_GUNICORN','gunicorn')
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    with tempfile.TemporaryDirectory() as tmp:
        process=subprocess.Popen([executable,'--config','distribution/gunicorn.conf.py','--bind',f'127.0.0.1:{port}','distribution.server:create_app()'],env={**os.environ,'STUDY_DB':str(Path(tmp)/'qa.sqlite3'),'STUDY_ORIGIN':'https://study.test'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        def request(path,method='GET',body=None,cookie='',csrf=''):
            req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,method=method,data=json.dumps(body).encode() if body is not None else None,headers={'Origin':'https://study.test','Content-Type':'application/json','Cookie':cookie,'X-CSRF-Token':csrf})
            try:r=urllib.request.urlopen(req,timeout=15)
            except urllib.error.HTTPError as e:r=e
            with r:return r.status,r.headers,r.read().decode()
        try:
            for _ in range(100):
                if process.poll() is not None:raise AssertionError('Gunicorn failed to start')
                try:
                    if request('/health')[0]==200:break
                except OSError:time.sleep(.1)
            else:raise AssertionError('Gunicorn startup timed out')
            status,headers,_=request('/api/register','POST',{'username':'production-test','password':'test password for gunicorn'})
            assert status==200
            assert '; Secure' in headers['Set-Cookie'];cookie=headers['Set-Cookie'].split(';')[0]
            _,_,html=request('/',cookie=cookie);bootstrap=json.loads(html.split('const CLOUD_BOOTSTRAP=',1)[1].split(';\n',1)[0]);csrf=bootstrap['csrf']
            body={'revision':0,'state':{'ratings':{},'answers':{'P35':'production test'},'history':[]}}
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(lambda _:request('/api/progress','PUT',body,cookie,csrf)[0],range(2)))
            assert sorted(results)==[200,409],results
            assert json.loads(request('/api/progress',cookie=cookie)[2])['revision']==1
            print('PASS Gunicorn: factory, secure session and two concurrent workers (200/409, no lost update)')
        finally:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()

if __name__=='__main__':main()
