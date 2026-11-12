"""Inicia y cierra servidores de QA propios en puertos efímeros; sin perfil del usuario."""
from __future__ import annotations
import argparse,os,pathlib,socket,subprocess,sys,time,urllib.request
APP=pathlib.Path(__file__).resolve().parents[1];ROOT=APP.parent

def port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def ready(url,process):
    for _ in range(60):
        if process.poll() is not None:raise RuntimeError('El servicio de QA no pudo arrancar')
        try:
            with urllib.request.urlopen(url,timeout=.3) as r:
                if r.status==200:return
        except OSError:time.sleep(.1)
    raise RuntimeError('Timeout al preparar servicio de QA')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runner',action='store_true');args=parser.parse_args()
    subprocess.run([sys.executable,str(APP/'scripts/build_hosted.py')],check=True,cwd=ROOT)
    subprocess.run(['node',str(APP/'test_worker.mjs')],check=True,cwd=ROOT)
    web_port,driver_port=port(),port();processes=[]
    while driver_port==web_port:driver_port=port()
    try:
        web=subprocess.Popen(['node',str(APP/'scripts/serve_hosted.mjs'),str(ROOT/'hosted_study_lab/dist/server/index.js'),str(web_port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);processes.append(web)
        driver=subprocess.Popen(['chromedriver',f'--port={driver_port}','--allowed-ips=127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);processes.append(driver)
        ready(f'http://127.0.0.1:{web_port}',web);ready(f'http://127.0.0.1:{driver_port}/status',driver)
        result=subprocess.run([sys.executable,str(APP/'test_browser.py')],cwd=ROOT,env={**os.environ,'NIIS_TEST_URL':f'http://127.0.0.1:{web_port}','NIIS_DRIVER_URL':f'http://127.0.0.1:{driver_port}','NIIS_TEST_HOSTED':'1','NIIS_TEST_RUNNER':'1' if args.runner else ''},capture_output=True,text=True,timeout=360)
        print(result.stdout,end='')
        if result.returncode:print(result.stderr,file=sys.stderr,end='')
        return result.returncode
    finally:
        for process in reversed(processes):
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
if __name__=='__main__':raise SystemExit(main())
