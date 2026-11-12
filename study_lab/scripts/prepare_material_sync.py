"""Preparación segura de un cambio de temario; nunca hace commit/push/deploy por sí sola."""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,subprocess,sys
from datetime import datetime,timezone
from types import SimpleNamespace
from sync_materials import atomic_write,lock,run as sync_run

ROOT=pathlib.Path(__file__).resolve().parents[2]
POLICY=ROOT/'deployment/sync-policy.json'
STATE=pathlib.Path.home()/'.local/state/niis-study-lab'

class GuardError(ValueError):pass

def command(*args)->str:
    result=subprocess.run(list(args),cwd=ROOT,capture_output=True,text=True,timeout=90,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'})
    if result.returncode:raise GuardError('No se pudo completar '+args[0]+' '+args[1]+' (salida '+str(result.returncode)+')')
    return result.stdout.strip()

def head()->str:return command('git','rev-parse','HEAD')
def changed_paths()->set[str]:
    tracked=command('git','diff','--name-only','-z','HEAD')
    other=command('git','ls-files','--others','--exclude-standard','-z')
    return {p for p in (tracked+'\0'+other).split('\0') if p}
def staged_paths()->set[str]:return {p for p in command('git','diff','--cached','--name-only','-z').split('\0') if p}
def digest(path:str)->str:return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def save_record(record:dict)->None:atomic_write(STATE/'prepared-sync.json',json.dumps(record,ensure_ascii=False,indent=2)+'\n')

def policy()->dict:
    p=json.loads(POLICY.read_text())
    if p['source_repository']!='Niistal/Big_Data' or p['source_branch']!='main' or p['access']!='owner_private':raise GuardError('Política de fuente/acceso no admitida')
    remote=command('git','remote','get-url','origin')
    if remote not in {'https://github.com/Niistal/examprepare','https://github.com/Niistal/examprepare.git','git@github.com:Niistal/examprepare.git'}:raise GuardError('Repositorio de aplicación inesperado')
    if command('git','branch','--show-current')!=p['app_branch']:raise GuardError('Rama de trabajo distinta: no se cambia automáticamente')
    expected={'study_lab/materials.json','study_lab/materials.js','study_lab/index.html'}
    if set(p['generated_paths'])!=expected:raise GuardError('La lista de archivos generados no está permitida')
    hosting=json.loads((ROOT/'deployment/hosting.json').read_text())
    if hosting['project_id']!=p['site_project_id']:raise GuardError('Identidad de alojamiento inconsistente')
    return p

def verify_files(record:dict,p:dict)->None:
    if set(record['hashes'])!=set(p['generated_paths']):raise GuardError('Candidato incompleto')
    if any(digest(name)!=sha for name,sha in record['hashes'].items()):raise GuardError('Un archivo cambió después de la verificación')
    if not changed_paths()<=set(p['generated_paths']):raise GuardError('Hay cambios ajenos a la sincronización')

def mark_committed(record:dict,p:dict)->dict:
    current=head();verify_files(record,p)
    if changed_paths() or staged_paths():raise GuardError('El commit no deja limpio el árbol de trabajo')
    if command('git','rev-parse','HEAD^')!=record['base_commit']:raise GuardError('El commit no parte de la base verificada')
    touched={x for x in command('git','diff-tree','--no-commit-id','--name-only','-r',current).splitlines() if x}
    if not touched or not touched<=set(p['generated_paths']):raise GuardError('El commit incluye cambios no permitidos')
    record.update(phase='committed',app_commit=current);save_record(record);return record

def resume(record:dict,p:dict)->dict|None:
    phase=record.get('phase')
    if phase=='prepared':
        if head()!=record['base_commit']:record=mark_committed(record,p)
        else:
            verify_files(record,p)
            if staged_paths():raise GuardError('Hay archivos en staging; no se altera staging ajeno')
            return {'status':'ready_for_commit','source_head':record['source_head'],'base_commit':record['base_commit'],'paths':p['generated_paths']}
    if record.get('phase')=='committed':
        if head()!=record['app_commit'] or changed_paths():raise GuardError('La base de publicación cambió; revisar antes de reintentar')
        verify_files(record,p)
        return {'status':'ready_for_publish','source_head':record['source_head'],'app_commit':record['app_commit'],'paths':p['generated_paths']}
    return None

def execute(args)->dict:
    STATE.mkdir(parents=True,exist_ok=True)
    if os.name!='nt':STATE.chmod(0o700)
    with lock(STATE/'automation.lock'):
        if args.automation:
            overnight=STATE/'overnight.json'
            if overnight.exists():
                raw_deadline=json.loads(overnight.read_text()).get('deadline_utc')
                if not isinstance(raw_deadline,str):raise GuardError('Plazo de trabajo inválido')
                deadline=datetime.fromisoformat(raw_deadline.replace('Z','+00:00'))
                if deadline.tzinfo is None:raise GuardError('El plazo debe tener zona horaria')
                if datetime.now(timezone.utc)<deadline:return {'status':'foreground_work','until':deadline.isoformat()}
        p=policy();record_path=STATE/'prepared-sync.json'
        record=json.loads(record_path.read_text()) if record_path.exists() else None
        if args.mark_committed:
            if not record or record.get('phase')!='prepared':raise GuardError('No hay candidato preparado para registrar')
            return {'status':'ready_for_publish',**mark_committed(record,p)}
        if args.mark_published:
            if not record or record.get('phase')!='committed':raise GuardError('No hay commit pendiente de publicación')
            if not args.deployment_id or not args.version_id or not args.hosted_commit:raise GuardError('Faltan identificadores devueltos por Sites')
            resume(record,p)
            record.update(phase='published',deployment_id=args.deployment_id,version_id=args.version_id,hosted_commit=args.hosted_commit,published_at=datetime.now(timezone.utc).isoformat())
            save_record(record);return {'status':'published','source_head':record['source_head'],'app_commit':record['app_commit']}
        if record:
            pending=resume(record,p)
            if pending:return pending
        if changed_paths() or staged_paths():return {'status':'blocked_worktree','message':'Hay trabajo local pendiente; no se sobrescribe ni se hace stash/reset.'}
        base=head();remote=command('git','ls-remote','origin','refs/heads/'+p['app_branch']).split()
        if not remote or remote[0]!=base:return {'status':'blocked_upstream','message':'La rama local y la remota no coinciden; no se hace pull/force por implicación.'}
        report=sync_run(SimpleNamespace(repo=pathlib.Path(p['local_source']),refresh=True,check=not args.apply,state_dir=STATE,output=ROOT/'study_lab/materials.json'))
        if report['status']=='unchanged' or not args.apply:return report
        # El código no se regenera a partir de las fuentes: solo datos de catálogo y standalone.
        for cmd in [[sys.executable,'study_lab/build.py'],['node','test_generador.cjs'],['node','test_learning.cjs'],[sys.executable,'test_materials.py'],[sys.executable,'test_artifacts.py']]:
            cwd=ROOT/'study_lab' if cmd[0]=='node' or cmd[-1] in {'test_materials.py','test_artifacts.py'} else ROOT
            result=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,timeout=90)
            if result.returncode:raise GuardError('Falló la verificación de catálogo: '+cmd[-1])
        if head()!=base:raise GuardError('La base Git cambió durante la preparación')
        if not changed_paths()<=set(p['generated_paths']):raise GuardError('Aparecieron cambios fuera del catálogo')
        record={'schema':1,'phase':'prepared','base_commit':base,'source_head':report['head'],'hashes':{path:digest(path) for path in p['generated_paths']},'report':report,'prepared_at':datetime.now(timezone.utc).isoformat()}
        save_record(record);return resume(record,p)

def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--automation',action='store_true');p.add_argument('--mark-committed',action='store_true');p.add_argument('--mark-published',action='store_true');p.add_argument('--deployment-id');p.add_argument('--version-id');p.add_argument('--hosted-commit');args=p.parse_args()
    try:print(json.dumps(execute(args),ensure_ascii=False));return 0
    except (ValueError,OSError,subprocess.SubprocessError) as error:print(json.dumps({'status':'blocked','message':str(error)[:500]},ensure_ascii=False));return 1
if __name__=='__main__':raise SystemExit(main())
