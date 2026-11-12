"""Private study distribution server. Run behind HTTPS; never executes student code."""
from __future__ import annotations
import base64,hashlib,hmac,io,ipaddress,json,os,re,secrets,sqlite3,time
from contextlib import contextmanager
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
EMPTY={'ratings':{},'answers':{},'history':[]}
MAX_BODY=2_000_000

def encode(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'))

def safe_json(value):
    return encode(value).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')

def password_hash(password,salt):
    return hashlib.scrypt(password.encode(),salt=salt,n=131072,r=8,p=1,maxmem=256*1024*1024).hex()

def valid_progress(value):
    if not isinstance(value,dict):return False
    ratings,answers,history=(value.get(k) for k in ('ratings','answers','history'))
    return (isinstance(ratings,dict) and isinstance(answers,dict) and isinstance(history,list)
        and all(type(v) is int and 0<=v<=2 for v in ratings.values())
        and all(isinstance(v,str) for v in answers.values())
        and all(isinstance(v,dict) and isinstance(v.get('id'),str) and type(v.get('rating')) is int
            and 0<=v['rating']<=2 and isinstance(v.get('date'),str) for v in history))

class App:
    def __init__(self,db_path,origin,development=False,trusted_proxy=False):
        self.db_path=str(db_path);self.origin=origin.rstrip('/');self.development=development;self.trusted_proxy=trusted_proxy
        parsed=urlsplit(self.origin)
        if (parsed.scheme!='https' and not (development and parsed.scheme=='http' and parsed.hostname in {'127.0.0.1','localhost'})) or parsed.path not in {'','/'} or parsed.query or parsed.fragment or parsed.username:
            raise ValueError('Set an exact HTTPS origin (HTTP allowed only for loopback development)')
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,username TEXT UNIQUE NOT NULL,salt BLOB NOT NULL,password TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT NOT NULL,csrf TEXT NOT NULL,expires INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS progress(user_id TEXT PRIMARY KEY,revision INTEGER NOT NULL,payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS attempts(key TEXT NOT NULL,created INTEGER NOT NULL);
            CREATE INDEX IF NOT EXISTS attempts_key ON attempts(key,created);
            ''')
        os.chmod(self.db_path,0o600)
    @contextmanager
    def db(self):
        db=sqlite3.connect(self.db_path,timeout=10);db.row_factory=sqlite3.Row
        try:
            with db:yield db
        finally:db.close()
    def __call__(self,environ,start_response):
        handler=Handler();handler.server=self;handler.command=environ['REQUEST_METHOD'];handler.path=environ.get('PATH_INFO','/')
        remote=environ.get('REMOTE_ADDR','unknown')
        if self.trusted_proxy and remote in {'127.0.0.1','::1'}:
            try:remote=str(ipaddress.ip_address(environ.get('HTTP_X_REAL_IP','')))
            except ValueError:pass
        handler.client_address=(remote,0)
        handler.headers={key[5:].replace('_','-').lower():value for key,value in environ.items() if key.startswith('HTTP_')}
        handler.headers.update({'content-type':environ.get('CONTENT_TYPE',''),'content-length':environ.get('CONTENT_LENGTH','0')})
        handler.rfile=environ['wsgi.input'];handler.wfile=io.BytesIO();handler.response_headers=[]
        try:
            if handler.command in {'GET','HEAD'}:handler.do_GET()
            elif handler.command in {'PUT','POST'}:handler.mutate()
            else:handler.reply(405,{'error':'Método no permitido'})
        except (OSError,sqlite3.Error,RecursionError):
            handler.wfile=io.BytesIO();handler.response_headers=[];handler.reply(503,{'error':'Servicio no disponible; conserva tu copia y reintenta'})
        start_response(str(handler.response_status)+' '+HTTPStatus(handler.response_status).phrase,handler.response_headers)
        return [] if handler.command=='HEAD' else [handler.wfile.getvalue()]

class Handler:
    server:App
    def send_response(self,status):self.response_status=status
    def send_header(self,key,value):self.response_headers.append((key,value))
    def end_headers(self):pass
    def header(self,key,default=''):return self.headers.get(key.lower(),default)
    def reply(self,status,value,content_type='application/json',cookie=None):
        body=(encode(value) if content_type=='application/json' else value).encode()
        self.send_response(status)
        self.send_header('Content-Type',content_type+'; charset=utf-8')
        self.send_header('Cache-Control','private, no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        hashes=' '.join("'sha256-"+base64.b64encode(hashlib.sha256(code.encode()).digest()).decode()+"'" for code in re.findall(r'<script>([\s\S]*?)</script>',value)) if content_type=='text/html' else "'none'"
        self.send_header('Content-Security-Policy',f"default-src 'none'; script-src {hashes}; style-src 'unsafe-inline'; connect-src 'self'; worker-src 'self'; img-src data:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; object-src 'none'")
        if cookie:self.send_header('Set-Cookie',cookie)
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def cookie(self,token,max_age=604800):
        name='study_dev' if self.server.development else '__Host-study'
        return f'{name}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={max_age}'+('' if self.server.development else '; Secure')
    def identity(self):
        from http.cookies import SimpleCookie,CookieError
        try:
            cookies=SimpleCookie(self.header('Cookie',''));name='study_dev' if self.server.development else '__Host-study'
            token=cookies[name].value if name in cookies else ''
        except CookieError:return None
        if not re.fullmatch(r'[a-zA-Z0-9_-]{43}',token):return None
        with self.server.db() as db:
            return db.execute('SELECT sessions.*,users.username FROM sessions JOIN users ON users.id=sessions.user_id WHERE token=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
    def read_json(self):
        length=int(self.header('Content-Length','0'))
        if not 0<length<=MAX_BODY:raise ValueError('Tamaño no permitido')
        if self.header('Content-Type','').split(';')[0]!='application/json':raise ValueError('Se requiere JSON')
        value=json.loads(self.rfile.read(length))
        if not isinstance(value,dict):raise ValueError('Objeto JSON requerido')
        return value
    def do_GET(self):
        path=urlsplit(self.path).path;user=self.identity()
        if path=='/health':return self.reply(200,{'status':'ok'})
        if path=='/login':return self.reply(200,(ROOT/'distribution/login.html').read_text(),'text/html')
        if not user:return self.reply(401,'<html lang="es"><meta charset="utf-8"><title>Inicia sesión</title><a href="/login">Inicia sesión o crea una cuenta</a></html>','text/html')
        if path=='/api/progress':
            with self.server.db() as db:row=db.execute('SELECT revision,payload FROM progress WHERE user_id=?',(user['user_id'],)).fetchone()
            return self.reply(200,{'revision':row['revision'] if row else 0,'state':json.loads(row['payload']) if row else EMPTY})
        if path=='/python-worker.mjs':
            code=(ROOT/'study_lab/python-worker.mjs').read_text()
            # The runner needs its pinned Pyodide runtime; the application cannot fetch arbitrary origins.
            self.send_response(200);self.send_header('Content-Type','text/javascript; charset=utf-8')
            self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self' 'unsafe-eval' 'wasm-unsafe-eval' https://cdn.jsdelivr.net/pyodide/v314.0.7/full/; connect-src https://cdn.jsdelivr.net/pyodide/v314.0.7/full/; worker-src 'none'; object-src 'none'")
            self.send_header('Cache-Control','private, no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(code.encode());return
        if path in {'/','/index.html'}:
            with self.server.db() as db:row=db.execute('SELECT revision,payload FROM progress WHERE user_id=?',(user['user_id'],)).fetchone()
            bootstrap={'revision':row['revision'] if row else 0,'state':json.loads(row['payload']) if row else EMPTY,'csrf':user['csrf'],'username':user['username']}
            html=(ROOT/'study_lab/index.html').read_text()
            if "const STATE_KEY='niis-study-lab-v1';" not in html:return self.reply(503,{'error':'Paquete no compatible'})
            # Memory adapter: never reads or overwrites the owner's browser-local progress.
            html=html.replace('localStorage','cloudStorage')
            client=(ROOT/'distribution/sync.js').read_text()
            html=html.replace('<script>', '<script>const CLOUD_BOOTSTRAP='+safe_json(bootstrap)+';\n'+client+'\n</script><script>',1)
            html=html.replace('<b>100 % local</b>','<b>Cuenta privada</b>')
            html=html.replace('Datos guardados en este navegador','Progreso sincronizado por cuenta').replace('progreso local ·','progreso por cuenta ·')
            html=html.replace('Guardado local','Borrador en memoria').replace("'Autoguardado'","'Borrador en memoria · consulta el estado de cuenta'")
            return self.reply(200,html,'text/html')
        return self.reply(404,{'error':'Ruta no disponible'})
    def do_POST(self):self.mutate()
    def do_PUT(self):self.mutate()
    def mutate(self):
        # No forwarded-IP trust: limits fail closed when all traffic comes from one proxy.
        if self.header('Origin')!=self.server.origin:return self.reply(403,{'error':'Origen no permitido'})
        try:
            body=self.read_json();path=urlsplit(self.path).path
            if path in {'/api/register','/api/login'} and self.command=='POST':return self.authenticate(path,body)
            user=self.identity()
            if not user:return self.reply(401,{'error':'Sesión caducada; exporta tus respuestas antes de volver a entrar'})
            if not hmac.compare_digest(self.header('X-CSRF-Token',''),user['csrf']):return self.reply(403,{'error':'CSRF inválido'})
            if path=='/api/logout' and self.command=='POST':
                with self.server.db() as db:db.execute('DELETE FROM sessions WHERE token=?',(user['token'],))
                return self.reply(200,{'ok':True},cookie=self.cookie('',0))
            if path=='/api/progress' and self.command=='PUT':
                if type(body.get('revision')) is not int or not valid_progress(body.get('state')):raise ValueError('Progreso inválido')
                payload=encode(body['state'])
                with self.server.db() as db:
                    db.execute('BEGIN IMMEDIATE')
                    row=db.execute('SELECT revision FROM progress WHERE user_id=?',(user['user_id'],)).fetchone();revision=row['revision'] if row else 0
                    if revision!=body['revision']:return self.reply(409,{'error':'Otro dispositivo ha guardado cambios. Exporta tu copia antes de recargar.'})
                    db.execute('INSERT INTO progress VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET revision=excluded.revision,payload=excluded.payload',(user['user_id'],revision+1,payload))
                return self.reply(200,{'revision':revision+1})
            return self.reply(404,{'error':'Ruta no disponible'})
        except (ValueError,UnicodeError,TypeError):return self.reply(400,{'error':'Petición inválida'})
    def authenticate(self,path,body):
        username=body.get('username','');password=body.get('password','')
        if not isinstance(username,str) or not isinstance(password,str):raise ValueError()
        username=username.strip().lower()
        if not re.fullmatch(r'[a-z0-9_.-]{3,40}',username) or not 12<=len(password)<=256:return self.reply(400,{'error':'Usuario: 3–40 letras/números, punto, guion o _. Contraseña: 12–256 caracteres.'})
        now=int(time.time());key=hashlib.sha256(self.client_address[0].encode()).hexdigest()
        with self.server.db() as db:
            db.execute('BEGIN IMMEDIATE');db.execute('DELETE FROM attempts WHERE created<?',(now-900,));db.execute('DELETE FROM sessions WHERE expires<?',(now,))
            count=db.execute('SELECT COUNT(*) FROM attempts WHERE key=?',(key,)).fetchone()[0]
            if count>=30:return self.reply(429,{'error':'Demasiados intentos; espera 15 minutos'})
            db.execute('INSERT INTO attempts VALUES(?,?)',(key,now))
        with self.server.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
            if path=='/api/register':
                if db.execute('SELECT COUNT(*) FROM users').fetchone()[0]>=100:return self.reply(503,{'error':'Se ha alcanzado el límite de 100 cuentas; contacta con el propietario'})
                if row:return self.reply(409,{'error':'Nombre no disponible'})
                salt=secrets.token_bytes(16);digest=password_hash(password,salt);uid=secrets.token_hex(16)
                try:db.execute('INSERT INTO users VALUES(?,?,?,?)',(uid,username,salt,digest))
                except sqlite3.IntegrityError:return self.reply(409,{'error':'Nombre no disponible'})
            else:
                salt=row['salt'] if row else b'0'*16;actual=password_hash(password,salt)
                if not row or not hmac.compare_digest(actual,row['password']):return self.reply(401,{'error':'Usuario o contraseña incorrectos'})
                uid=row['id']
            token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32)
            db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),uid,csrf,now+604800))
        return self.reply(200,{'ok':True},cookie=self.cookie(token))

def create_app():
    db=Path(os.environ.get('STUDY_DB','/var/lib/study-lab/study.sqlite3'))
    db.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    return App(db,os.environ['STUDY_ORIGIN'],trusted_proxy=True)

if __name__=='__main__':
    # Local development only. Production uses Gunicorn behind the TLS proxy.
    from wsgiref.simple_server import make_server
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--development',action='store_true',required=True);p.add_argument('--port',type=int,default=8090);args=p.parse_args()
    db=Path(os.environ['STUDY_DB'])
    app=App(db,f'http://127.0.0.1:{args.port}',development=True)
    make_server('127.0.0.1',args.port,app).serve_forever()
