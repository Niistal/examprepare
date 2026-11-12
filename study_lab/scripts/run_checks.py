"""Suite reproducible. No instala paquetes, no publica y no modifica apuntes."""
import argparse,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path);p.add_argument('--browser',action='store_true');p.add_argument('--frameworks',action='store_true');args=p.parse_args()
commands=[['node','--check','app.js'],[sys.executable,'build.py'],['node','test_generador.cjs'],['node','test_learning.cjs'],[sys.executable,'test_artifacts.py']+([str(args.repo.resolve())] if args.repo else []),[sys.executable,'test_solutions.py','--python',sys.executable]]
if args.frameworks:commands.append([sys.executable,'test_frameworks.py'])
if args.browser:commands.append([sys.executable,'test_browser.py'])
report=[]
for cmd in commands:
    result=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=180)
    label=' '.join(cmd[1:])
    report.append(('PASS' if result.returncode==0 else 'FAIL')+' '+label+'\n'+result.stdout+result.stderr)
    print(report[-1],flush=True)
    if result.returncode:
        (root/'qa-artifacts').mkdir(exist_ok=True);(root/'qa-artifacts/last-checks.txt').write_text('\n'.join(report));sys.exit(result.returncode)
(root/'qa-artifacts').mkdir(exist_ok=True);(root/'qa-artifacts/last-checks.txt').write_text('\n'.join(report))
print('PASS suite completa solicitada')
