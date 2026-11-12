"""Empaqueta solo el HTML de estudio para Sites, sin apuntes, venv ni progreso."""
from pathlib import Path
import base64,hashlib,json,re,subprocess,sys
repo=Path(__file__).resolve().parents[2]
app=repo/'study_lab'
subprocess.run([sys.executable,str(app/'build.py')],check=True)
html=(app/'index.html').read_text(encoding='utf-8')
html=html.replace('<b>100 % local</b>','<b>Acceso privado</b>')
html=html.replace('<span id="todayLabel"', '<a class="session-signout" href="/signout-with-chatgpt?return_to=%2F" target="_top">Cerrar sesión</a><span id="todayLabel"')
html=html.replace('<div class="metric-grid">','<div class="hosting-notice" role="note"><b>Tu espacio privado de estudio.</b> El progreso se guarda en este navegador. Para llevarlo a otro dispositivo, exporta e importa el JSON desde Mi progreso.</div><div class="metric-grid">')
html=html.replace('<meta name="color-scheme"', '<meta name="referrer" content="no-referrer"><meta name="robots" content="noindex,nofollow"><meta name="color-scheme"')
# Bloquea scripts externos/inyección de scripts; el código standalone se autoriza por hash.
scripts=re.findall(r'<script>([\s\S]*?)</script>',html)
hashes=' '.join("'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in scripts)
csp=f"default-src 'none'; script-src {hashes}; style-src 'unsafe-inline'; img-src data:; font-src 'none'; connect-src 'none'; base-uri 'none'; form-action 'none'; object-src 'none'; worker-src 'self'"
html=html.replace('<meta charset="utf-8">','<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="'+csp+'">')
output=repo/'hosted_study_lab';(output/'dist/server').mkdir(parents=True,exist_ok=True);(output/'.openai').mkdir(exist_ok=True);(output/'qa').mkdir(exist_ok=True)
config=json.loads((repo/'deployment/hosting.json').read_text(encoding='utf-8'))
if 'static' in config:raise ValueError('El paquete con cabeceras usa el Worker mínimo, no static.directory')
headers={'cache-control':'private, no-store','content-security-policy':csp+"; frame-ancestors 'self' https://chatgpt.com",'referrer-policy':'no-referrer','x-content-type-options':'nosniff','permissions-policy':'camera=(), microphone=(), geolocation=(), payment=()'}
js_string=lambda value:json.dumps(value,ensure_ascii=False).replace('\u2028','\\u2028').replace('\u2029','\\u2029')
worker=(repo/'deployment/worker-template.mjs').read_text(encoding='utf-8').replace('/*__DOCUMENT__*/',js_string(html)).replace('/*__PYTHON_WORKER__*/',js_string((app/'python-worker.mjs').read_text(encoding='utf-8'))).replace('/*__HEADERS__*/',json.dumps(headers,separators=(',',':')))
(output/'dist/server/index.js').write_text(worker, encoding='utf-8')
(output/'qa/document.html').write_text(html, encoding='utf-8')
(output/'qa/headers.json').write_text(json.dumps(headers,indent=2)+'\n',encoding='utf-8')
(output/'dist/index.html').unlink(missing_ok=True)
(output/'.openai/hosting.json').write_text(json.dumps(config,indent=2)+'\n', encoding='utf-8')
(output/'dist/.openai').mkdir(exist_ok=True)
(output/'dist/.openai/hosting.json').write_text(json.dumps(config,indent=2)+'\n', encoding='utf-8')
ignore=output/'.gitignore'
text=ignore.read_text(encoding='utf-8') if ignore.exists() else ''
if 'qa/' not in text.splitlines():ignore.write_text(text+'\nqa/\n', encoding='utf-8')
(output/'README.md').write_text('Generated private NIIS Study Lab publication. Canonical sources: Niistal/examprepare, study_lab/. Regenerate with study_lab/scripts/build_hosted.py. No credentials or learner progress belong in this repository.\n', encoding='utf-8')
print('Hosted: Worker estático con cabeceras HTTP; sin APIs de ejecución ni secretos')
