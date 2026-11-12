"""Audita rutas sin modificar Big_Data; genera metadatos reproducibles del banco."""
import argparse, ast, hashlib, json, pathlib, re, subprocess
root = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('repo', type=pathlib.Path)
args = parser.parse_args()
repo = args.repo.resolve()
remote=subprocess.check_output(['git','-C',str(repo),'remote','get-url','origin'],text=True).strip()
branch=subprocess.check_output(['git','-C',str(repo),'branch','--show-current'],text=True).strip()
if not re.search(r'github\.com[:/]Niistal/Big_Data(?:\.git)?/?$',remote,re.I) or branch!='main':
    raise SystemExit('La fuente debe ser Niistal/Big_Data en main; no se han cambiado metadatos.')
bank = json.loads(subprocess.check_output(['node', str(root/'scripts/export_bank.cjs')]))
# Carpetas que solo contienen PDF: guía derivada como apoyo, no verificación de PDF.
fallback = {'E06': ('03_AA_Ereduak','4. Fuzzy Logic'), 'A01': ('07_BD_Aplikatua','GetFile'), 'A03': ('07_BD_Aplikatua','UpdateAttribute')}
metadata = {}
for q in bank:
    p = repo / q['source']
    if q['id'] in fallback:
        folder, term = fallback[q['id']]
        p = repo/f'NotebookLM_Material_Estudio/{folder}/Guias_de_Estudio/Guia_Estudio_{folder}.md'
    elif p.is_dir():
        candidates = [f for f in p.rglob('*') if f.suffix in {'.md','.py','.ipynb'} and not any(x.startswith('.') for x in f.relative_to(p).parts)]
        candidates.sort(key=lambda f:(f.name!='README.md',str(f)))
        p = candidates[0] if candidates else p
    if q['id'] in {'S02','S09'}:
        p=repo/'06_BD_Sistemak/ariketak/3_ETL_eta_Formatuak/README.md'
    if q['id']=='M09':
        p=repo/'04_Ikaskuntza_Automatikorako_Sistemak/README.md'
    if q['id']=='E08':
        p=repo/'03_AA_Ereduak/3_Etika_eta_Legea/1.1_prompt_injection_diseinua_soluzioa.ipynb'
    raw=p.read_bytes() if p.is_file() else b''
    text=raw.decode('utf-8',errors='replace')
    if p.suffix=='.ipynb':
        cells=json.loads(text)['cells']; section=next((''.join(c['source']).splitlines()[0] for c in cells if c['cell_type']=='markdown'),'Cuaderno')
    elif p.suffix=='.py':
        doc=ast.get_docstring(ast.parse(text))
        section=next((line.strip() for line in (doc or '').splitlines() if line.strip()),'Código del módulo')
    else:
        section=next((x.lstrip('# ').strip() for x in text.splitlines() if x.startswith('#') and not x.startswith('#!') and re.search(r'[A-Za-zÁÉÍÓÚáéíóú]',x)),'Archivo completo: configuración / datos')
    explicit=q.get('source_section')
    normalized=lambda value: re.sub(r'\s+',' ',value.replace('#','').replace('*','')).lower()
    if explicit and explicit!='Pendiente de contraste' and normalized(explicit) in normalized(text):
        section=explicit
    tracked=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+str(p.relative_to(repo))])
    if tracked!=raw:raise SystemExit('La fuente contiene cambios fuera de HEAD: '+str(p))
    if q['id'] in fallback:
        term=fallback[q['id']][1]
        section=next((x.lstrip('# ').strip() for x in text.splitlines() if term.lower() in x.lower()),section)
    metadata[q['id']]={'source_path':str(p.relative_to(repo)), 'source_section':section[:200], 'verified':bool(raw), 'verification_scope':'Ruta y tema contrastados; microcaso propio, no enunciado del profesor', 'source_sha256':hashlib.sha256(raw).hexdigest()}
sha=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
output={'repo':'Niistal/Big_Data','branch':'main','commit':sha,'questions':metadata}
(root/'sources.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
(root/'sources.js').write_text('const SOURCE_AUDIT='+json.dumps(output,ensure_ascii=False,indent=2)+';\n')
print(f'{len(metadata)} fuentes auditadas; commit {sha}; sin modificar el repositorio académico')
