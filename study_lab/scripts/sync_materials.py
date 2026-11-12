"""Índice de temario desde objetos Git: sin checkout ni ejecución de apuntes.

--refresh usa un mirror privado separado; nunca hace pull/reset sobre Big_Data.
Solo publica metadatos y encabezados, no cuerpos, outputs, datos ni credenciales.
"""
from __future__ import annotations
import argparse,contextlib,hashlib,json,os,pathlib,re,subprocess,sys,tempfile
from collections import Counter

APP=pathlib.Path(__file__).resolve().parents[1]
EXPECTED='Niistal/Big_Data'
ORIGIN='https://github.com/Niistal/Big_Data.git'
REGISTRY={
 '05_AA_Programazioa':('program','AA Programazioa'),
 '04_Ikaskuntza_Automatikorako_Sistemak':('ml','Ikaskuntza Automatikorako Sistemak'),
 '03_AA_Ereduak':('models','AA Ereduak'),
 '06_BD_Sistemak':('systems','BD Sistemak'),
 '07_BD_Aplikatua':('applied','BD Aplikatua'),
 '01_Orokorra':('general','General del curso'),
}
SECONDARY={'02_Erronka_1_CNC_Guard','08_Erronka_2_RetailEUS'}
EXTENSIONS={'.md':'Apunte','.ipynb':'Cuaderno','.pdf':'PDF','.py':'Código Python','.sql':'SQL','.json':'JSON / configuración','.conf':'Configuración','.yaml':'Configuración','.yml':'Configuración','.csv':'Datos CSV','.tab':'Datos Orange','.ows':'Flujo Orange','.docx':'Documento Word','.odt':'Documento de texto','.pptx':'Presentación','.odp':'Presentación','.txt':'Texto','.properties':'Configuración Kafka/Java','.toml':'Configuración','.sh':'Script de terminal','.html':'Documento / código web','.parquet':'Datos Parquet','.xlsx':'Datos Excel','.xml':'XML / configuración','.avsc':'Esquema Avro','.avro':'Datos Avro','.png':'Imagen / figura','.svg':'Imagen vectorial (referencia)','.m4a':'Audio','.mp4':'Vídeo','.zip':'Archivo de práctica (referencia)','.url':'Archivo de enlace (referencia)','.log':'Log de ejemplo (referencia)'}

SENSITIVE=re.compile(r'(?:^|[/_. -])(?:credentials?|secrets?|tokens?|passwords?|contraseñas?|credentials|id_rsa|id_ed25519|cookies|progreso|progress|sessions?)(?:$|[/_. -])',re.I)
SECRET_VALUE=re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',re.I)

def git(repo:pathlib.Path,*args:str,timeout:int=60)->bytes:
    result=subprocess.run(['git','-C',str(repo),*args],capture_output=True,timeout=timeout,env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GIT_NO_REPLACE_OBJECTS':'1'})
    if result.returncode:raise RuntimeError('Git no pudo completar '+args[0]+' (salida '+str(result.returncode)+')')
    return result.stdout

def validate_repo(repo:pathlib.Path)->None:
    remote=git(repo,'remote','get-url','origin').decode().strip()
    if remote not in {ORIGIN,'https://github.com/Niistal/Big_Data','git@github.com:Niistal/Big_Data.git','ssh://git@github.com/Niistal/Big_Data.git'}:
        raise ValueError('La fuente no está conectada al origen exacto Niistal/Big_Data.')
    if git(repo,'branch','--show-current').decode().strip()!='main':raise ValueError('La fuente debe estar en main; no se cambiará su rama.')

def safe_text(value:str,limit:int=160)->str:
    value=re.sub(r'[\u202a-\u202e\u2066-\u2069\u200b-\u200f\ufeff]','',value)
    value=re.sub(r'<[^>]*>','',value)
    value=re.sub(r'\[([^]]+)\]\([^)]*\)',r'\1',value)
    value=re.sub(r'[`*_#]','',value)
    value=' '.join(value.split())
    if SECRET_VALUE.search(value) or re.search(r'(?:password|contraseña|api[_ -]?key|authorization|bearer)\s*[:=]\s*\S+',value,re.I):return 'Título omitido por contener un identificador sensible'
    return value[:limit]

def module_for(path:str,roots:set[str])->tuple[str,str,str]|None:
    if re.search(r'[\x00-\x1f\x7f\u202a-\u202e\u2066-\u2069]',path):return None
    parts=pathlib.PurePosixPath(path).parts
    if parts and parts[-1] in {'AGENTS.md','CLAUDE.md','PROJECT_GOAL.md'}:return None
    if not parts or any(x in {'.','..'} or x.startswith('.') for x in parts) or '\\' in path:return None
    if any(part.lower() in {'node_modules','__pycache__','venv','data_raw','raw_private'} for part in parts):return None
    if SENSITIVE.search(path) or SECRET_VALUE.search(path):return None
    if len(parts)==1:
        return ('general','General del curso','01_Orokorra') if parts[0] in {'README.md','ARIKETAK_AURKIBIDEA.md'} else None
    folder=parts[1] if parts[0]=='NotebookLM_Material_Estudio' and len(parts)>2 else parts[0]
    if folder in SECONDARY:return None
    if folder in REGISTRY:
        cid,label=REGISTRY[folder];return cid,label,folder
    # Un módulo nuevo se reconoce por la raíz única, no por los temas que menciona.
    if not re.fullmatch(r'\d{2}_[\w-]+',folder,re.UNICODE):return None
    number=folder[:2]
    if number in {x[:2] for x in SECONDARY}:return None
    duplicate=sum(bool(re.fullmatch(r'\d{2}_[\w-]+',root)) and root[:2]==number for root in roots)>1
    if folder not in roots or number in {x[:2] for x in REGISTRY} or duplicate:
        return 'unassigned-'+folder,'Sin asignar: '+folder.replace('_',' '),folder
    return 'module-'+folder,folder.replace('_',' '),folder

def tree(repo:pathlib.Path,ref:str,remote_sizes:dict[str,int]|None=None)->list[dict]:
    # --long fuerza a Git a buscar tamaños de blobs en clones parciales: evitarlo.
    raw=git(repo,'ls-tree','-r','-z',ref)
    items=[]
    for record in raw.split(b'\0'):
        if not record:continue
        metadata,path=record.split(b'\t',1);mode,kind,oid=metadata.decode().split()
        if mode not in {'100644','100755'} or kind!='blob':continue
        try:name=path.decode('utf-8')
        except UnicodeDecodeError:continue
        items.append({'path':name,'blob':oid})
    if remote_sizes is None:
        promisor=subprocess.run(['git','-C',str(repo),'config','--get','remote.origin.promisor'],capture_output=True,text=True,timeout=10)
        if promisor.stdout.strip()=='true':raise ValueError('Usar --refresh para consultar tamaños remotos sin descargar todos los blobs.')
        result=subprocess.run(['git','-C',str(repo),'cat-file','--batch-check=%(objectname) %(objectsize)'],input=('\n'.join(sorted({i['blob'] for i in items}))+'\n').encode(),capture_output=True,timeout=30)
        if result.returncode:raise RuntimeError('No se pudieron consultar los tamaños locales')
        remote_sizes={line.split()[0]:int(line.split()[1]) for line in result.stdout.decode().splitlines()}
    for item in items:
        if item['blob'] not in remote_sizes:raise ValueError('Metadatos de tamaño incompletos para el árbol Git')
        item['size']=remote_sizes[item['blob']]
    return items

def github_sizes(repo:pathlib.Path,ref:str)->dict[str,int]:
    tree_id=git(repo,'rev-parse',ref+'^{tree}').decode().strip()
    result=subprocess.run(['gh','api',f'repos/{EXPECTED}/git/trees/{tree_id}?recursive=1'],capture_output=True,timeout=60,env={**os.environ,'GH_PROMPT_DISABLED':'1'})
    if result.returncode:raise RuntimeError('No se pudieron consultar los metadatos GitHub con la conexión existente')
    data=json.loads(result.stdout)
    if data.get('sha')!=tree_id or data.get('truncated'):raise ValueError('Árbol remoto incompleto o distinto del commit fijado')
    sizes={}
    for item in data.get('tree',[]):
        if item.get('type')!='blob':continue
        oid=item.get('sha');size=item.get('size')
        if not isinstance(oid,str) or not re.fullmatch('[0-9a-f]{40}',oid) or not isinstance(size,int) or size<0:raise ValueError('Metadatos GitHub inválidos')
        sizes[oid]=size
    return sizes

def headings(repo:pathlib.Path,item:dict)->list[str]:
    suffix=pathlib.PurePosixPath(item['path']).suffix.lower()
    maxsize=400_000 if suffix=='.md' else 2_000_000
    if suffix not in {'.md','.ipynb'} or item['size']>maxsize:return []
    text=git(repo,'cat-file','blob',item['blob']).decode('utf-8',errors='replace')
    if suffix=='.ipynb':
        try:
            notebook=json.loads(text)
            text='\n'.join(''.join(c.get('source',[])) for c in notebook.get('cells',[]) if isinstance(c,dict) and c.get('cell_type')=='markdown')
        except (ValueError,TypeError,RecursionError):return []
    result=[]
    for line in text.splitlines():
        if not re.match(r'^#{1,4}\s+\S',line):continue
        title=safe_text(line)
        if not title or re.match(r'(autor|egilea|profesor|alumno|email|usuario)\b',title,re.I):continue
        if title not in result:result.append(title)
        if len(result)==8:break
    return result

def kind_for(path:str,ext:str)->tuple[str,str]:
    if path.startswith('NotebookLM_Material_Estudio/'):return 'derived','Apoyo derivado de NotebookLM'
    if re.search(r'ebazpen|soluzi|solved|solucion|solución',path,re.I):return 'worked','Ejemplo resuelto del repositorio; posible asistencia IA'
    if ext in {'.py','.ipynb','.sql'}:return 'example','Código/cuaderno del repositorio; no se atribuye autoría humana'
    return 'original','Material versionado del curso'

def make_catalog(repo:pathlib.Path,ref:str,previous:dict|None=None,remote_sizes:dict[str,int]|None=None)->dict:
    validate_repo(repo)
    if not re.fullmatch(r'(?:main|refs/heads/main|[0-9a-f]{40})',ref):raise ValueError('Referencia Git no admitida')
    commit=git(repo,'rev-parse','--verify',ref+'^{commit}').decode().strip()
    entries=tree(repo,commit,remote_sizes);roots={x['path'].split('/')[0] for x in entries}
    resources=[];courses={};omitted=Counter();old_paths={r['path']:r for r in (previous or {}).get('resources',[])}
    for item in entries:
        path=item['path'];ext=pathlib.PurePosixPath(path).suffix.lower()
        if ext not in EXTENSIONS:continue
        module=module_for(path,roots)
        if not module:omitted['outside_or_sensitive']+=1;continue
        cid,label,folder=module
        stem=safe_text(pathlib.PurePosixPath(path).stem.replace('_',' '))
        if not stem:continue
        cached=old_paths.get(path);sections=[safe_text(h) for h in cached['sections']] if cached and cached['git_blob']==item['blob'] else headings(repo,item);title=sections[0] if sections else stem
        kind,provenance=kind_for(path,ext)
        resources.append({'id':'res-'+hashlib.sha256((EXPECTED+':'+path).encode()).hexdigest()[:20], 'course':cid,'module':folder,'path':path,'title':title,'sections':sections,'type':EXTENSIONS[ext],'extension':ext,'kind':kind,'assignment':'unassigned' if cid.startswith('unassigned-') else 'general' if cid=='general' else 'exact' if cid in {v[0] for v in REGISTRY.values()} else 'module','provenance':provenance,'git_blob':item['blob'],'size':item['size']})
        courses[cid]={'id':cid,'label':label,'folder':folder,'exam_course':cid in {v[0] for k,v in REGISTRY.items() if k!='01_Orokorra'}}
    resources.sort(key=lambda x:(x['course'],x['path']))
    if len(resources)>5000:raise ValueError('Más de 5000 recursos: revisar antes de generar un paquete excesivo')
    ids=[r['id'] for r in resources]
    if len(ids)!=len(set(ids)):raise ValueError('Colisión de IDs de recursos')
    fingerprint=hashlib.sha256(json.dumps(resources,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    old={r['id']:r for r in (previous or {}).get('resources',[])}
    changes={'initial':not bool(previous),'added':[r['id'] for r in resources if r['id'] not in old] if previous else [],'changed':[r['id'] for r in resources if r['id'] in old and r['git_blob']!=old[r['id']]['git_blob']],'removed':[k for k in old if k not in set(ids)]}
    return {'schema':1,'policy_version':4,'source':{'repo':EXPECTED,'branch':'main','commit':commit,'committed_at':git(repo,'show','-s','--format=%cI',commit).decode().strip()},'fingerprint':fingerprint,'root_modules':sorted(r for r in roots if re.fullmatch(r'\d{2}_[\w-]+',r)),'courses':sorted(courses.values(),key=lambda x:x['folder']),'resources':resources,'changes':changes,'exclusions':{'secondary_projects':sorted(SECONDARY),'omitted_count':sum(omitted.values()),'policy':'Sin cuerpos ni outputs de los archivos; rutas y encabezados con filtrado de identificadores sensibles detectables. Fuentes por ruta, no por parecido de título.'}}

def atomic_write(path:pathlib.Path,text:str)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as file:
        tmp=pathlib.Path(file.name);file.write(text)
    os.replace(tmp,path)

@contextlib.contextmanager
def lock(path:pathlib.Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    file=path.open('a+b')
    if file.seek(0,2)==0:file.write(b'0');file.flush()
    file.seek(0)
    try:
        if os.name=='nt':
            import msvcrt;msvcrt.locking(file.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl;fcntl.flock(file,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        file.close();raise BlockingIOError('Ya hay una sincronización en curso')
    try:yield
    finally:
        if os.name=='nt':
            import msvcrt;file.seek(0);msvcrt.locking(file.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl;fcntl.flock(file,fcntl.LOCK_UN)
        file.close()

def refresh_mirror(local:pathlib.Path,state:pathlib.Path)->pathlib.Path:
    validate_repo(local)
    mirror=state/'source-mirror.git'
    if not mirror.exists():
        subprocess.run(['git','clone','--bare','--filter=blob:none','--single-branch','--branch','main','--no-tags',ORIGIN,str(mirror)],check=True,capture_output=True,timeout=180,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'})
    validate_repo(mirror)
    git(mirror,'fetch','--no-tags','origin','+refs/heads/main:refs/heads/main',timeout=180)
    return mirror

def run(args)->dict:
    state=args.state_dir.resolve();state.mkdir(parents=True,exist_ok=True)
    if os.name!='nt':state.chmod(0o700)
    with lock(state/'catalog.lock'):
        repo=refresh_mirror(args.repo.resolve(),state) if args.refresh else args.repo.resolve()
        previous=json.loads(args.output.read_text()) if args.output.exists() else None
        catalog=make_catalog(repo,'main',previous,github_sizes(repo,'main') if args.refresh else None)
        changed=not previous or previous.get('fingerprint')!=catalog['fingerprint'] or previous.get('policy_version')!=catalog['policy_version']
        report={'status':'changed' if changed else 'unchanged','head':catalog['source']['commit'],'resource_count':len(catalog['resources']),'course_counts':dict(Counter(r['course'] for r in catalog['resources'])),'added':len(catalog['changes']['added']),'changed':len(catalog['changes']['changed']),'removed':len(catalog['changes']['removed']),'unassigned_count':sum(r['assignment']=='unassigned' for r in catalog['resources'])}
        if changed and not args.check:
            text=json.dumps(catalog,ensure_ascii=False,indent=2)+'\n'
            # Untrusted source headings must never terminate the standalone script element.
            js='const MATERIAL_CATALOG='+json.dumps(catalog,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')+';\n'
            atomic_write(args.output,text);atomic_write(args.output.with_suffix('.js'),js)
        atomic_write(state/'last-catalog-check.json',json.dumps(report,indent=2)+'\n')
        return report

def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,default=pathlib.Path('/home/admin/Big_Data'));p.add_argument('--refresh',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--state-dir',type=pathlib.Path,default=pathlib.Path.home()/'.local/state/niis-study-lab');p.add_argument('--output',type=pathlib.Path,default=APP/'materials.json');a=p.parse_args()
    try:print(json.dumps(run(a),ensure_ascii=False));return 0
    except BlockingIOError:print(json.dumps({'status':'busy'}));return 75
    except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as e:print(json.dumps({'status':'error','message':str(e)[:500]},ensure_ascii=False),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
