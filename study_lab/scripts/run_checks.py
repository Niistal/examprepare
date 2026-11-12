"""Suite reproducible. No instala paquetes, no publica y no modifica apuntes."""
import argparse,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path);p.add_argument('--browser',action='store_true');p.add_argument('--frameworks',action='store_true');p.add_argument('--external-docker',action='store_true');p.add_argument('--orange-python',type=pathlib.Path);args=p.parse_args()
commands=[['node','--check','app.js'],[sys.executable,'build.py'],['node','test_generador.cjs'],['node','test_learning.cjs'],['node','test_modalities.cjs'],[sys.executable,'test_local_tools.py'],[sys.executable,'test_materials.py'],[sys.executable,'test_material_reader.py'],[sys.executable,'test_sync_guards.py'],[sys.executable,'test_publication.py'],[sys.executable,'test_artifacts.py']+([str(args.repo.resolve())] if args.repo else []),[sys.executable,'test_solutions.py','--python',sys.executable]]
if args.frameworks:commands.append([sys.executable,'test_frameworks.py'])
if args.browser:commands.extend([[sys.executable,'test_browser.py'],[sys.executable,'test_learning_browser.py'],[sys.executable,'test_material_reader_browser.py']])
if args.orange_python:commands.extend([[str(args.orange_python.resolve()),'test_orange.py'],[sys.executable,'test_orange_bridge.py']])
if args.external_docker:commands.append([sys.executable,'test_external_docker.py'])
report=[]
for cmd in commands:
    result=subprocess.run(cmd,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600 if 'test_external_docker.py' in cmd else 180)
    label=' '.join(cmd[1:])
    report.append(('PASS' if result.returncode==0 else 'FAIL')+' '+label+'\n'+result.stdout+result.stderr)
    print(report[-1],flush=True)
    if result.returncode:
        (root/'qa-artifacts').mkdir(exist_ok=True);(root/'qa-artifacts/last-checks.txt').write_text('\n'.join(report), encoding='utf-8');sys.exit(result.returncode)
(root/'qa-artifacts').mkdir(exist_ok=True);(root/'qa-artifacts/last-checks.txt').write_text('\n'.join(report), encoding='utf-8')
print('PASS suite completa solicitada')
