"""Empaqueta solo el HTML de estudio para Sites, sin apuntes, venv ni progreso."""
from pathlib import Path
import base64,hashlib,json,re,subprocess
repo=Path(__file__).resolve().parents[2]
app=repo/'study_lab'
subprocess.run(['python',str(app/'build.py')],check=True)
html=(app/'index.html').read_text()
html=html.replace('<b>100 % local</b>','<b>Acceso privado</b>')
html=html.replace('<span id="todayLabel"', '<a class="session-signout" href="/signout-with-chatgpt?return_to=%2F" target="_top">Cerrar sesión</a><span id="todayLabel"')
html=html.replace('<div class="metric-grid">','<div class="hosting-notice" role="note"><b>Tu espacio privado de estudio.</b> El progreso se guarda en este navegador. Para llevarlo a otro dispositivo, exporta e importa el JSON desde Mi progreso.</div><div class="metric-grid">')
html=html.replace('<meta name="color-scheme"', '<meta name="referrer" content="no-referrer"><meta name="robots" content="noindex,nofollow"><meta name="color-scheme"')
# Bloquea scripts externos/inyección de scripts; el código standalone se autoriza por hash.
scripts=re.findall(r'<script>([\s\S]*?)</script>',html)
hashes=' '.join("'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in scripts)
csp=f"default-src 'none'; script-src {hashes}; style-src 'unsafe-inline'; img-src data:; font-src 'none'; connect-src 'none'; base-uri 'none'; form-action 'none'; object-src 'none'"
html=html.replace('<meta charset="utf-8">','<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="'+csp+'">')
output=repo/'hosted_study_lab';(output/'dist').mkdir(parents=True,exist_ok=True);(output/'.openai').mkdir(exist_ok=True)
(output/'dist/index.html').write_text(html)
config=json.loads((repo/'deployment/hosting.json').read_text())
(output/'.openai/hosting.json').write_text(json.dumps(config,indent=2)+'\n')
print('Hosted: solo dist/index.html y manifest; sin secretos ni progreso')
