"""Pruebas locales de las soluciones FastAPI y Streamlit, sin publicar servicios."""
import io,json,pathlib,subprocess,tempfile,textwrap,socket,sys,time,urllib.request
from unittest.mock import patch
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
root=pathlib.Path(__file__).resolve().parent
bank={q['id']:q for q in json.loads(subprocess.check_output(['node',str(root/'scripts/export_bank.cjs')]))}
namespace={}
exec(bank['P13']['solution'],namespace)
with TestClient(namespace['app']) as client:
    assert client.get('/salud').json()=={'ok':True}
    good=client.post('/productos',json={'nombre':'Cuaderno','precio':12.5})
    assert good.status_code==201 and good.json()['precio']==12.5
    assert client.post('/productos',json={'nombre':'X','precio':-1}).status_code==422
    assert client.get('/openapi.json').status_code==200
# Verificar además el comando real de arranque en loopback y un puerto efímero.
with tempfile.TemporaryDirectory(prefix='niis-api-') as folder:
    path=pathlib.Path(folder)/'app.py';path.write_text(bank['P13']['solution'], encoding='utf-8')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    process=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port',str(port)],cwd=folder,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        ready=False
        for _ in range(50):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/salud',timeout=.2) as response:
                    ready=json.load(response)=={'ok':True}
                if ready:break
            except (OSError,ValueError):time.sleep(.1)
        assert ready,'uvicorn no respondió en loopback'
    finally:
        process.terminate();process.wait(timeout=5)
print('PASS P13: salud, creación 201, validación 422 y OpenAPI')
# Fixture de entrada: sustituir solo el control de carga, no la lógica de solución.
fixture='categoria,importe\nA,10\nB,20\nA,15\n'
script='from unittest.mock import patch\nfrom io import BytesIO\nwith patch("streamlit.file_uploader",return_value=BytesIO('+repr(fixture.encode())+')):\n'+textwrap.indent(bank['P14']['solution'],'    ')
app=AppTest.from_string(script).run(timeout=15)
assert not app.exception,app.exception
assert app.metric[0].value=='3' and len(app.dataframe[0].value)==3
app.multiselect[0].set_value(['A']).run()
assert not app.exception and len(app.dataframe[0].value)==2
assert set(app.dataframe[0].value.categoria)=={'A'}
print('PASS P14: CSV de fixture, métrica y filtro de categorías en Streamlit AppTest')
