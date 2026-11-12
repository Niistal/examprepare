"""Verifica bytes/cabeceras del Site con acceso de servicio existente.

Credencial solo por stdin con eco desactivado. Nunca se guarda ni imprime.
No crea tokens ni demuestra el login/MFA del propietario.
"""
from __future__ import annotations
import hashlib,json,pathlib,re,sys,urllib.error,urllib.parse,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[2]
STAGE='configuration'
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def receive():
    state=None
    if sys.stdin.isatty() and sys.platform!='win32':
        import termios
        state=termios.tcgetattr(sys.stdin.fileno());hidden=state.copy();hidden[3]&=~termios.ECHO;termios.tcsetattr(sys.stdin.fileno(),termios.TCSADRAIN,hidden)
    print('Ready for private verification JSON on stdin (input hidden).',flush=True)
    try:data=json.loads(sys.stdin.readline())
    finally:
        if state is not None:
            import termios;termios.tcsetattr(sys.stdin.fileno(),termios.TCSADRAIN,state)
    token=data.get('token')
    if not isinstance(token,str) or len(token)<20:raise ValueError('Falta acceso de servicio válido')
    return token

def request(url,headers=None):
    opener=urllib.request.build_opener(NoRedirect)
    try:return opener.open(urllib.request.Request(url,headers=headers or {}),timeout=20)
    except urllib.error.HTTPError as response:return response

def compare_document(body:bytes,expected:bytes)->dict:
    if body==expected:return {'app_document_matches':True,'edge_injection_detected':False}
    boundary=b'</body>\n</html>\n'
    if not expected.endswith(boundary):raise ValueError('Cierre de documento inesperado')
    prefix=expected[:-len(boundary)]
    if not body.startswith(prefix) or not body.endswith(boundary):raise ValueError('Contenido de aplicación diferente')
    extra=body[len(prefix):-len(boundary)]
    # Cloudflare añade JavaScript de detección al final del HTML servido. No se elimina
    # contenido de aplicación ni se relaja CSP para ejecutarlo; se informa por separado.
    if len(extra)>20_000 or not re.fullmatch(rb'<script>[^<]*</script>',extra) or b'__CF$cv$params' not in extra or b'/cdn-cgi/challenge-platform/' not in extra:
        raise ValueError('Transformación de plataforma desconocida')
    return {'app_document_matches':True,'edge_injection_detected':True,'edge_injection':'Cloudflare JavaScript detection; no se valida su código ni se amplía CSP'}

def verify_headers(observed,expected:dict)->None:
    for name,value in expected.items():
        actual=observed.get(name,'')
        if name=='cache-control':
            if {v.strip().lower() for v in actual.split(',')}!={v.strip().lower() for v in value.split(',')}:raise ValueError('Política de caché distinta')
        elif ' '.join(actual.split())!=' '.join(value.split()):raise ValueError('Cabecera de seguridad diferente: '+name)

def main():
    global STAGE
    policy=json.loads((ROOT/'deployment/sync-policy.json').read_text(encoding='utf-8'));origin=policy['site_origin'];parsed=urllib.parse.urlsplit(origin)
    if parsed.scheme!='https' or not parsed.hostname or not parsed.hostname.endswith('.chatgpt.site') or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'','/'}:raise ValueError('Origen del Site no admitido')
    STAGE='receive';token=receive();expected=(ROOT/'hosted_study_lab/qa/document.html').read_bytes()
    STAGE='anonymous_access';anon=request(origin+'/');status=anon.code;anon.close()
    if status not in {301,302,303,307,308,401,403}:raise ValueError('Revisar acceso anónimo')
    STAGE='service_access'
    with request(origin+'/',{'OAI-Sites-Authorization':'Bearer '+token}) as response:
        if response.code!=200:raise ValueError('Acceso de servicio no aceptado')
        STAGE='document_bytes';body=response.read(len(expected)+100_001)
        comparison=compare_document(body,expected)
        STAGE='security_headers';verify_headers(response.headers,json.loads((ROOT/'hosted_study_lab/qa/headers.json').read_text(encoding='utf-8')))
        print(json.dumps({'status':'verified','anonymous_status':status,'app_body_sha256':hashlib.sha256(expected).hexdigest(),**comparison,'http_security_headers':True,'scope':'Acceso de servicio; no prueba MFA, Proton ni login interactivo del propietario'}),flush=True)
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError):
        print(json.dumps({'status':'not_verified','stage':STAGE,'message':'No se ha completado la comprobación privada; conservar el detalle de acceso fuera de logs públicos'}),flush=True);raise SystemExit(1)
