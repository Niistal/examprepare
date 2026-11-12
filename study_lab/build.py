"""Reconstruye el HTML standalone a partir de los ficheros editables (sin dependencias)."""
from pathlib import Path
import base64,hashlib,json

ROOT = Path(__file__).resolve().parent
wheel=(ROOT/'vendor/seaborn-0.13.2-py3-none-any.whl').read_bytes()
assert hashlib.sha256(wheel).hexdigest()=='636f8336facf092165e27924f223d3c62ca560b1f2bb5dff7ab7fad265361987','Unexpected Seaborn wheel'
package_js='const PYTHON_EXTRA_WHEELS='+json.dumps({'seaborn':base64.b64encode(wheel).decode()})+';\n'
shell = (ROOT / "shell.html").read_text(encoding="utf-8")
assert "/*__CSS__*/" in shell and "/*__JS__*/" in shell
html = shell.replace("/*__CSS__*/", (ROOT / "style.css").read_text(encoding="utf-8"))
html = html.replace("/*__JS__*/", package_js+"const PYTHON_WORKER_SOURCE="+json.dumps((ROOT/"python-worker.mjs").read_text(encoding="utf-8"),ensure_ascii=True).replace("<","\\u003c")+";\n"+ "\n".join((ROOT / name).read_text(encoding="utf-8") for name in ("sources.js", "materials.js", "app.js")))
(ROOT / "index.html").write_text(html, encoding="utf-8", newline="\n")
print("index.html creado")
