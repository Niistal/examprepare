"""Revisor por resultados del worker Python, ejecutado con CPython sobre el banco real.
Run: study_lab/.venv/bin/python study_lab/test_reviewer.py
Comprueba: la solución de referencia se aprueba a sí misma, la plantilla sin resolver no se aprueba,
y soluciones alternativas (otro enfoque, otros nombres) se aceptan mientras los errores se detectan.
"""
import contextlib, io, json, os, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ.setdefault('MPLBACKEND', 'Agg')


def load_reviewer():
    src = (ROOT / 'python-worker.mjs').read_text(encoding='utf-8')
    body = src.split('# REVIEWER-BEGIN', 1)[1].split('# REVIEWER-END', 1)[0]
    ns = {}
    exec(body, ns)
    return ns['_study_review']


def load_exercises():
    script = ("const fs=require('fs'),vm=require('vm');const src=fs.readFileSync(process.argv[1],'utf8').split('\\n');"
              "const end=src.findIndex(l=>l.startsWith('const $=id=>'));const ctx={};vm.createContext(ctx);"
              "vm.runInContext(src.slice(0,end).join('\\n')+';this.OUT=BANK;',ctx);const seen=new Set();"
              "process.stdout.write(JSON.stringify(ctx.OUT.filter(q=>/PYTHON|PANDAS|NUMPY/i.test(q.kind)&&q.solution&&!['P13','P14'].includes(q.id)&&!seen.has(q.id)&&seen.add(q.id))))")
    out = subprocess.run(['node', '-e', script, str(ROOT / 'app.js')], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def run_student(code, workdir):
    ns, out = {'__name__': '__main__'}, io.StringIO()
    previous = os.getcwd(); os.chdir(workdir)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            exec(compile(code, '<exec>', 'exec'), ns)
        try:
            import matplotlib.pyplot as plt
            for n in plt.get_fignums():
                plt.figure(n).savefig(f'figure-{n}.png'); plt.close('all')
        except Exception:
            pass
    finally:
        os.chdir(previous)
    return ns, out.getvalue()


def review(reviewer, q, code):
    with tempfile.TemporaryDirectory() as stu, tempfile.TemporaryDirectory() as ref:
        try:
            ns, out = run_student(code, stu)
        except Exception as exc:
            return {'status': 'error', 'items': [], 'notes': [type(exc).__name__]}
        return json.loads(reviewer(ns, q['solution'], q.get('starter') or '', out, stu, ref))


ALTERNATIVES = [
    # Otro enfoque y otros nombres: debe aprobarse.
    ('P03', 'ok', 'etiquetas = [" bilbo ", "DONOSTIA", "bilbo", " gasteiz ", " "]\nvistos=[]\nfor e in etiquetas:\n    x=e.strip().capitalize()\n    if x and x not in vistos:\n        vistos.append(x)\nfinal=sorted(vistos,key=len)\nprint(final)'),
    ('P01', 'ok', 'import re\nLETRAS = "TRWAGMYFPDXBNJZSQVHLCKE"\ndef validar_nif(nif):\n    m = re.fullmatch(r"(\\d{8})([A-Za-z])", nif.strip())\n    return bool(m) and LETRAS[int(m[1]) % 23] == m[2].upper()\nprint(validar_nif("12345678Z"))'),
    ('P08', 'near', 'import pandas as pd\ndf = pd.DataFrame({"tienda":["A","A","B"],"total":[10,30,20]})\ntabla = df.groupby("tienda")["total"].agg(["sum","mean","count"])\ndf["media_tienda"] = df["tienda"].map(df.groupby("tienda")["total"].mean())\nprint(tabla)\nprint(df)'),
    ('P03', 'ok', 'etiquetas = [" bilbo ", "DONOSTIA", "bilbo", " gasteiz ", " "]\nprint(sorted(dict.fromkeys(e.strip().capitalize() for e in etiquetas if e.strip()), key=len))'),
    # Errores reales: no debe aprobarse.
    ('P01', 'bad', 'LETRAS = "TRWAGMYFPDXBNJZSQVHLCKE"\ndef validar_nif(nif):\n    raise NameError("x")'),
    ('P01', 'bad', 'LETRAS = "TRWAGMYFPDXBNJZSQVHLCKE"\ndef validar_nif(nif):\n    return len(nif) == 9 and LETRAS[int(nif[:8]) % 23] == nif[8]'),
    ('P03', 'bad', 'etiquetas = [" bilbo ", "DONOSTIA", "bilbo", " gasteiz ", " "]\nfinal=sorted([e.strip().capitalize() for e in etiquetas if e.strip()],key=len)\nprint(final)'),
    ('P12', 'bad', 'tp,fp,tn,fn = 30,10,50,5\nprecision=tp/(tp+fp)\nrecall=tp/(tp+fp)\nf1=2*precision*recall/(precision+recall)\naccuracy=(tp+tn)/(tp+fp+tn+fn)\nprint(precision,recall,f1,accuracy)'),
]


SYNTHETIC = [
    # (referencia, alumno, esperado) para casos límite señalados en la revisión cruzada.
    ('def agregar(l, x):\n    l.append(x)\nv = [1]\nagregar(v, 2)', 'def agregar(l, x):\n    pass\nv = [1, 2]', 'bad'),
    ('def agregar(l, x):\n    l.append(x)\nv = [1]\nagregar(v, 2)', 'def agregar(l, x):\n    l += [x]\nv = [1]\nagregar(v, 2)', 'ok'),
    ('import pandas as pd\ns = pd.Series({2020: 3, 2021: 5})\nr = s.sort_values(ascending=False)', 'import pandas as pd\nr = pd.Series([5, 3], index=[2020, 2021])', 'bad'),
    ('import pandas as pd\ndf = pd.DataFrame({"a": [1, -1, 2]})\npos = df[df.a > 0]', 'import pandas as pd\ndf = pd.DataFrame({"a": [1, -1, 2]})\npos = df.query("a > 0").reset_index(drop=True)', 'ok'),
    ('xs = [50, 100]\ntotal = sum(xs)', 'xs = [50, 100]\ntotal = sum(xs) * 10\nprint(total)', 'bad'),
    ('x = 3\nes_par = x % 2 == 0', 'x = 3\nes_par = True\nflag = False', 'bad'),
    ('tp, fp = 30, 10\nprecision = tp / (tp + fp)', 'tp, fp = 30, 10\nprec = tp / (tp + fp)', 'ok'),
    ('r = {0.1 + 0.2, 1.0}', 'r = {0.3, 1.0}', 'ok'),
    ('import pandas as pd\nr = pd.Series([1.0, None])', 'import pandas as pd\nr = pd.Series([1.0, None], dtype=object)', 'ok'),
]


def main():
    reviewer, exercises = load_reviewer(), load_exercises()
    failures, unavailable = [], []
    for q in exercises:
        own = review(reviewer, q, q['solution'])
        if own['status'] in ('unavailable', 'error'):
            unavailable.append(q['id']); continue
        if own['status'] != 'ok':
            failures.append((q['id'], 'referencia no aprobada', own))
        starter = review(reviewer, q, q.get('starter') or 'pass')
        if starter['status'] == 'ok':
            failures.append((q['id'], 'plantilla aprobada', starter))
    by_id = {q['id']: q for q in exercises}
    for qid, expected, code in ALTERNATIVES:
        got = review(reviewer, by_id[qid], code)
        accepted = {'ok': ('ok',), 'near': ('ok', 'partial'), 'bad': ('partial', 'fail')}[expected]
        if got['status'] not in accepted:
            failures.append((qid, f'alternativa: esperado {expected}', got))
    for i, (ref, code, expected) in enumerate(SYNTHETIC):
        got = review(reviewer, {'solution': ref, 'starter': ''}, code)
        if (got['status'] == 'ok') != (expected == 'ok'):
            failures.append((f'S{i}', f'sintético: esperado {expected}', got))
    print(f'{len(exercises)} ejercicios, {len(unavailable)} sin revisión automática: {", ".join(unavailable)}')
    for qid, why, rep in failures:
        print('FAIL', qid, why, json.dumps(rep, ensure_ascii=False)[:600])
    if failures:
        sys.exit(1)
    print('PASS revisor: referencias aprobadas, plantillas rechazadas y alternativas aceptadas')


if __name__ == '__main__':
    main()
