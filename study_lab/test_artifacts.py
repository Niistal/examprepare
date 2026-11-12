"""Comprueba sincronización standalone y trazabilidad; solo biblioteca estándar."""
from pathlib import Path
import hashlib,json,subprocess,sys
root=Path(__file__).resolve().parent
from build import render
expected, learning_js = render()
assert (root/'learning-content.js').read_text(encoding='utf-8') == learning_js
assert (root/'index.html').read_text(encoding='utf-8')==expected,'Ejecuta python build.py'
bank=json.loads(subprocess.check_output(['node',str(root/'scripts/export_bank.cjs')]))
audit=json.loads((root/'sources.json').read_text(encoding='utf-8'))
encoded_audit='const SOURCE_AUDIT='+json.dumps(audit,ensure_ascii=False,indent=2).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')+';\n'
assert (root/'sources.js').read_text(encoding='utf-8')==encoded_audit,'Metadatos de contraste JS/JSON desincronizados o sin escape seguro'
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

materials=json.loads((root/'materials.json').read_text(encoding='utf-8'))
encoded='const MATERIAL_CATALOG='+json.dumps(materials,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')+';\n'
assert (root/'materials.js').read_text(encoding='utf-8')==encoded,'Catálogo JS/JSON desincronizado'
assert len({r['id'] for r in materials['resources']})==len(materials['resources'])
for r in materials['resources']:
    assert r['module'] not in {'02_Erronka_1_CNC_Guard','08_Erronka_2_RetailEUS'}
    assert not r['path'].endswith(('AGENTS.md','CLAUDE.md','PROJECT_GOAL.md'))
print('PASS catálogo y JS seguro sincronizados:',len(materials['resources']),'recursos')

registry={'05_AA_Programazioa':'program','04_Ikaskuntza_Automatikorako_Sistemak':'ml','03_AA_Ereduak':'models','06_BD_Sistemak':'systems','07_BD_Aplikatua':'applied','01_Orokorra':'general'}
for r in materials['resources']:
    parts=Path(r['path']).parts
    folder=parts[1] if parts[0]=='NotebookLM_Material_Estudio' else parts[0]
    if len(parts)==1:assert r['course']=='general' and r['path'] in {'README.md','ARIKETAK_AURKIBIDEA.md'}
    elif folder in registry:assert r['course']==registry[folder] and r['module']==folder,r['path']
    else:
        assert r['course'] in {'module-'+folder,'unassigned-'+folder}
        if r['assignment']=='unassigned':assert r['course']=='unassigned-'+folder
        else:assert r['course']=='module-'+folder and folder in materials['root_modules'] and folder[:2] not in {v[:2] for v in registry}
    assert r['id']=='res-'+hashlib.sha256(('Niistal/Big_Data:'+r['path']).encode()).hexdigest()[:20]
assert materials['fingerprint']==hashlib.sha256(json.dumps(materials['resources'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
print('PASS asignación exacta por ruta y huella de todos los recursos')
