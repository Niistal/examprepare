"""Start isolated localhost/ChromeDriver processes and verify the material reader."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def port():
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
def ready(url,process):
    for _ in range(80):
        if process.poll() is not None:raise RuntimeError('QA server exited')
        try:
            with urllib.request.urlopen(url,timeout=.5) as response:
                if response.status==200:return
        except OSError:time.sleep(.1)
    raise RuntimeError('QA server timeout')
def main():
    web,driver=port(),port();processes=[]
    while driver==web:driver=port()
    try:
        processes.append(subprocess.Popen([sys.executable,str(ROOT/'local_server.py'),'--port',str(web)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
        processes.append(subprocess.Popen(['chromedriver','--port='+str(driver),'--allowed-ips=127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
        ready(f'http://127.0.0.1:{web}',processes[0]);ready(f'http://127.0.0.1:{driver}/status',processes[1])
        return subprocess.run([sys.executable,str(ROOT/'test_material_reader_browser.py')],env={**os.environ,'NIIS_TEST_URL':f'http://127.0.0.1:{web}','NIIS_DRIVER_URL':f'http://127.0.0.1:{driver}'},timeout=120).returncode
    finally:
        for process in reversed(processes):
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
if __name__=='__main__':raise SystemExit(main())
