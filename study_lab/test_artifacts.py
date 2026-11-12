"""Comprueba sincronización standalone y trazabilidad; solo biblioteca estándar."""
from pathlib import Path
import hashlib,json,subprocess,sys
root=Path(__file__).resolve().parent
shell=(root/'shell.html').read_text()
expected=shell.replace('/*__CSS__*/',(root/'style.css').read_text()).replace('/*__JS__*/',(root/'sources.js').read_text()+'\n'+(root/'app.js').read_text())
assert (root/'index.html').read_text()==expected,'Ejecuta python build.py'
bank=json.loads(subprocess.check_output(['node',str(root/'scripts/export_bank.cjs')]))
audit=json.loads((root/'sources.json').read_text())
assert len({q['id'] for q in bank})==len(bank)
for q in bank:
    x=audit['questions'][q['id']]
    assert x['source_path'] and x['source_section'] and isinstance(x['verified'],bool)
    assert not x['verified'] or x['source_section']!='Pendiente de contraste'
    assert not x['source_path'].startswith(('02_','08_'))
    if len(sys.argv)>1:
        p=Path(sys.argv[1])/x['source_path']
        assert p.is_file(),p
        assert hashlib.sha256(p.read_bytes()).hexdigest()==x['source_sha256'],p
print('PASS HTML autónomo sincronizado y',len(bank),'fuentes con metadatos'+(' y hashes contrastados' if len(sys.argv)>1 else ''))
