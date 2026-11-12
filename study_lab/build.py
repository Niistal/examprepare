"""Reconstruye el HTML standalone a partir de los ficheros editables (sin dependencias)."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
shell = (ROOT / "shell.html").read_text(encoding="utf-8")
assert "/*__CSS__*/" in shell and "/*__JS__*/" in shell
html = shell.replace("/*__CSS__*/", (ROOT / "style.css").read_text(encoding="utf-8"))
html = html.replace("/*__JS__*/", "const PYTHON_WORKER_SOURCE="+json.dumps((ROOT/"python-worker.mjs").read_text(encoding="utf-8"),ensure_ascii=True).replace("<","\\u003c")+";\n"+ "\n".join((ROOT / name).read_text(encoding="utf-8") for name in ("sources.js", "materials.js", "app.js")))
(ROOT / "index.html").write_text(html, encoding="utf-8")
print("index.html creado")
