"""Opt-in same-origin local companion. No remote shell or installation endpoints."""
import argparse
import functools
import hmac
import importlib.util
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import socket
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from material_assets import MaterialAssets

ROOT = Path(__file__).resolve().parent
PRACTICES = json.loads((ROOT / 'resources/orange-manifest.json').read_text(encoding='utf-8'))
PUBLIC_RESOURCES = {'/resources/' + item[field] for item in PRACTICES.values() for field in ('csv', 'workflow')} | {'/resources/orange-classification.ows', '/resources/orange-iris.csv'}

def orange_command():
    # Launchers from existing installations, including Windows entry points and uv tools.
    for name in ('orange-canvas', 'orange-canvas.exe', 'Orange'):
        executable = shutil.which(name)
        if executable and Path(executable).is_file():
            return [executable]
    if importlib.util.find_spec('Orange'):
        return [sys.executable, '-m', 'Orange.canvas']
    return None

def port_open(port):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=.15):
            return True
    except OSError:
        return False

def tool_status():
    orange = orange_command()
    return {'os': platform.system(), 'orange': {'available': bool(orange), 'command': orange,
             'message': 'Lanzador localizado; el inicio de la GUI debe comprobarse en este equipo.' if orange else 'Orange no está instalado o no está en PATH. Descarga el workflow y ábrelo manualmente.'},
            'jupyter': {'available': bool(shutil.which('jupyter'))},
            'docker': {'available': bool(shutil.which('docker'))},
            # These ports come from the cited academic compose files, never proof of service identity.
            'services': {name: {'port': port, 'listening': port_open(port), 'identityVerified': False}
                         for name, port in [('elasticsearch', 9200), ('kibana', 5601), ('nifi', 8443), ('kafka', 9092)]}}

class LocalHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Never log the authorization token.
        pass

    def authorized(self, mutation=False):
        expected = f'127.0.0.1:{self.server.server_port}'
        origin = self.headers.get('Origin')
        return (self.headers.get('Host') == expected
                and (origin == 'http://' + expected if mutation else origin in (None, 'http://' + expected))
                and hmac.compare_digest(self.headers.get('X-Study-Token', '').encode('utf-8'), self.server.token.encode('ascii')))

    def reply(self, status, value, content_type='application/json'):
        body = (json.dumps(value, ensure_ascii=False) if content_type == 'application/json' else value).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type + '; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "frame-ancestors 'none'; base-uri 'none'; object-src 'none'")
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path.startswith('/api/materials/'):
            if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':return self.reply(403, {'error':'Host local requerido'})
            status,headers,file,start,length=self.server.material_assets.response(path.removeprefix('/api/materials/'),self.headers.get('Range'),'download=1' in urlsplit(self.path).query)
            self.send_response(status)
            for key,value in headers.items():self.send_header(key,value)
            self.end_headers()
            if file and self.command!='HEAD':
                for chunk in self.server.material_assets.chunks(file,start,length):self.wfile.write(chunk)
            return
        if path == '/api/tools/status':
            if not self.authorized():
                return self.reply(403, {'error': 'Autorización local requerida'})
            return self.reply(200, tool_status())
        if path in ('/', '/index.html'):
            if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
                return self.reply(403, {'error': 'Abre la dirección 127.0.0.1 indicada al arrancar'})
            html = (ROOT / 'index.html').read_text(encoding='utf-8')
            asset_bootstrap='const MATERIAL_ASSET_BASE="/api/materials/";' if (ROOT/'material-assets').is_dir() else ''
            html = html.replace('<script>', '<script>'+asset_bootstrap+'const LOCAL_TOOL_TOKEN=' + json.dumps(self.server.token) + ';</script><script>', 1)
            return self.reply(200, html, 'text/html')
        # Only serve explicit public resources; never expose source trees, dotfiles or secrets.
        if path == '/python-worker.mjs' or path in PUBLIC_RESOURCES:
            return super().do_GET()
        return self.reply(404, {'error': 'Recurso no disponible'})

    def do_HEAD(self):
        if urlsplit(self.path).path.startswith('/api/materials/'):return self.do_GET()
        self.send_error(405)

    def do_POST(self):
        if not self.authorized(mutation=True):
            return self.reply(403, {'error': 'Origen o autorización local no permitidos'})
        if urlsplit(self.path).path != '/api/tools/launch':
            return self.reply(404, {'error': 'Ruta no disponible'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 512 or self.headers.get('Content-Type') != 'application/json':
                raise ValueError()
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict) or not {'tool'} <= set(body) <= {'tool', 'practice'} or body['tool'] != 'orange' or not isinstance(body.get('practice', 'M09'), str) or body.get('practice', 'M09') not in PRACTICES:
                return self.reply(400, {'error': 'Solo se permite abrir Orange con el workflow del laboratorio'})
            command = orange_command()
            if not command:
                return self.reply(409, {'error': 'Orange no está instalado. Descarga el workflow y el CSV para abrirlos manualmente.'})
            previous = getattr(self.server, 'orange_process', None)
            if previous and previous.poll() is None:
                return self.reply(200, {'message': 'Orange ya se ha solicitado. Comprueba su ventana.'})
            workflow = PRACTICES[body.get('practice', 'M09')]['workflow']
            self.server.orange_process = subprocess.Popen(command + [str(ROOT / 'resources' / workflow)],
                cwd=ROOT / 'resources', stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, shell=False)
            try:
                code = self.server.orange_process.wait(timeout=.8)
                return self.reply(409, {'error': f'Orange terminó con código {code}. Comprueba una sesión gráfica y abre el workflow manualmente.'})
            except subprocess.TimeoutExpired:
                return self.reply(200, {'message': 'Proceso Orange iniciado; comprueba su ventana. No se ha certificado el resultado del workflow.'})
        except (ValueError, TypeError, UnicodeError):
            return self.reply(400, {'error': 'Petición no válida'})
        except OSError:
            return self.reply(503, {'error': 'No se pudo ejecutar Orange. Revisa la instalación y usa la descarga manual.'})

    def do_OPTIONS(self):
        self.send_error(405)  # No CORS: a hosted page cannot operate this companion.

    do_PUT = do_OPTIONS
    do_DELETE = do_OPTIONS


def create_server(port=8080):
    server = ThreadingHTTPServer(('127.0.0.1', port), functools.partial(LocalHandler, directory=str(ROOT)))
    server.material_assets = MaterialAssets(ROOT)
    server.token = secrets.token_urlsafe(32)
    return server

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    server = create_server(args.port)
    print(f'NIIS Study Lab: http://127.0.0.1:{server.server_port} — puente local voluntario', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
