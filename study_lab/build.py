"""Reconstruye el HTML standalone a partir de los ficheros editables (sin dependencias)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
shell = (ROOT / "shell.html").read_text(encoding="utf-8")
assert "/*__CSS__*/" in shell and "/*__JS__*/" in shell
html = shell.replace("/*__CSS__*/", (ROOT / "style.css").read_text(encoding="utf-8"))
html = html.replace("/*__JS__*/", (ROOT / "sources.js").read_text(encoding="utf-8") + "\n" + (ROOT / "app.js").read_text(encoding="utf-8"))
(ROOT / "index.html").write_text(html, encoding="utf-8")
print("index.html creado")
