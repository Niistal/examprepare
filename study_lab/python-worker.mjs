// Each run owns a fresh virtual filesystem; only bounded output files leave it.
const BASE='https://cdn.jsdelivr.net/pyodide/v314.0.7/full/';
const OUTPUT_DIR='/study-output', REF_DIR='/study-reference', MAX_FILES=30, MAX_BYTES=10_000_000;
let outputSize=0;
function output(text){if(outputSize>=20000)return;const part=String(text).slice(0,20000-outputSize);outputSize+=part.length;self.postMessage({type:'output',text:part+'\n'});}
// Revisor por resultados: compara lo que produce tu código con lo que produce la solución de
// referencia (variables por valor, llamadas a funciones, archivos, gráficas y números impresos).
// No compara el texto del código: cualquier enfoque que llegue al mismo resultado es válido.
// Delimitado por REVIEWER-BEGIN/END para que test_reviewer.py lo ejecute con CPython.
const REVIEWER=String.raw`
# REVIEWER-BEGIN
import ast, contextlib, copy, io, json, math, os, re

def _study_review(student_ns, reference, starter, student_stdout, student_dir, ref_dir):
    items, notes = [], []
    def add(ok, label, hard=True):
        items.append({'ok': bool(ok), 'label': label, 'hard': hard})
    try:
        import numpy as np
    except Exception:
        np = None
    try:
        import pandas as pd
    except Exception:
        pd = None

    def scalar(x):
        if np is not None and isinstance(x, np.generic):
            return x.item()
        return x

    def is_num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    def same_num(a, b):
        a, b = float(a), float(b)
        if math.isnan(a) or math.isnan(b):
            return math.isnan(a) and math.isnan(b)
        return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)

    def same_series(a, b):
        if len(a) != len(b):
            return False
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b) and not pd.api.types.is_bool_dtype(a) and not pd.api.types.is_bool_dtype(b):
            return bool(np.allclose(a.to_numpy(dtype=float), b.to_numpy(dtype=float), rtol=1e-6, atol=1e-9, equal_nan=True))
        return all(same(x, y, 4) for x, y in zip(a.tolist(), b.tolist()))

    def meaningful_index(obj):
        # Un índice entero creciente (filas filtradas) no importa; uno reordenado o de etiquetas sí.
        idx = obj.index
        return not (isinstance(idx, pd.RangeIndex) or (pd.api.types.is_integer_dtype(idx) and idx.is_monotonic_increasing and idx.is_unique))

    def same_frame(a, b, loose=False):
        if a.shape != b.shape:
            return False
        ca, cb = [str(c) for c in a.columns], [str(c) for c in b.columns]
        if ca != cb and loose:
            b = b.copy(); b.columns = a.columns
        elif ca != cb:
            if len(set(ca)) != len(ca) or sorted(ca) != sorted(cb):
                return False
            b = b.iloc[:, [cb.index(c) for c in ca]]
        if (meaningful_index(a) or meaningful_index(b)) and [str(i) for i in a.index] != [str(i) for i in b.index]:
            return False
        a2, b2 = a.reset_index(drop=True), b.reset_index(drop=True)
        return all(same_series(a2.iloc[:, i], b2.iloc[:, i]) for i in range(a2.shape[1]))

    def same(a, b, depth=0):
        if depth > 6:
            return False
        a, b = scalar(a), scalar(b)
        def missing(x):
            return x is None or (isinstance(x, float) and math.isnan(x)) or (pd is not None and x is pd.NA)
        if missing(a) or missing(b):
            return missing(a) and missing(b)
        if pd is not None:
            if isinstance(a, pd.DataFrame) or isinstance(b, pd.DataFrame):
                if isinstance(a, pd.DataFrame) and isinstance(b, pd.DataFrame):
                    return same_frame(a, b) or same_frame(a.reset_index(), b) or same_frame(a, b.reset_index())
                return False
            if isinstance(a, pd.Series) or isinstance(b, pd.Series):
                if isinstance(a, pd.Series) and isinstance(b, pd.Series):
                    if (meaningful_index(a) or meaningful_index(b)) and [str(i) for i in a.index] != [str(i) for i in b.index]:
                        return False
                    return same_series(a.reset_index(drop=True), b.reset_index(drop=True))
                return False
            if isinstance(a, pd.Index) and isinstance(b, pd.Index):
                return same(a.tolist(), b.tolist(), depth + 1)
        if np is not None and (isinstance(a, np.ndarray) or isinstance(b, np.ndarray)):
            try:
                a2, b2 = np.asarray(a), np.asarray(b)
                if a2.shape != b2.shape:
                    return False
                if a2.dtype.kind in 'iuf' and b2.dtype.kind in 'iuf':
                    return bool(np.allclose(a2.astype(float), b2.astype(float), rtol=1e-6, atol=1e-9, equal_nan=True))
                return bool(np.array_equal(a2, b2))
            except Exception:
                return False
        if isinstance(a, bool) or isinstance(b, bool):
            return isinstance(a, bool) and isinstance(b, bool) and a == b
        if is_num(a) and is_num(b):
            return same_num(a, b)
        if isinstance(a, str) and isinstance(b, str):
            return a.strip() == b.strip()
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            return len(a) == len(b) and all(same(x, y, depth + 1) for x, y in zip(a, b))
        if isinstance(a, (set, frozenset)) and isinstance(b, (set, frozenset)):
            if len(a) != len(b):
                return False
            try:
                return a == b or same(sorted(map(scalar, a)), sorted(map(scalar, b)), depth + 1)
            except TypeError:
                return a == b
        if isinstance(a, dict) and isinstance(b, dict):
            ka = {str(k): k for k in a}
            kb = {str(k): k for k in b}
            return set(ka) == set(kb) and all(same(a[ka[k]], b[kb[k]], depth + 1) for k in ka)
        try:
            return bool(a == b) and type(a) is type(b)
        except Exception:
            return False

    def describe(v):
        v = scalar(v)
        if pd is not None and isinstance(v, pd.DataFrame):
            return 'tabla %d×%d' % v.shape
        if pd is not None and isinstance(v, pd.Series):
            return 'serie de %d valores' % len(v)
        if np is not None and isinstance(v, np.ndarray):
            return 'array ' + '×'.join(map(str, v.shape))
        if isinstance(v, bool):
            return 'booleano'
        if is_num(v):
            return 'número'
        if isinstance(v, str):
            return 'texto'
        if isinstance(v, (list, tuple)):
            return 'lista de %d elementos' % len(v)
        if isinstance(v, dict):
            return 'diccionario de %d claves' % len(v)
        if isinstance(v, (set, frozenset)):
            return 'conjunto de %d elementos' % len(v)
        return type(v).__name__

    def why_differs(a, b):
        a, b = scalar(a), scalar(b)
        if pd is not None and isinstance(a, pd.DataFrame) and isinstance(b, pd.DataFrame):
            if a.shape != b.shape:
                return 'tu tabla mide %d×%d y debería medir %d×%d' % (a.shape + b.shape)
            if sorted(map(str, a.columns)) != sorted(map(str, b.columns)):
                extra = sorted(set(map(str, a.columns)) - set(map(str, b.columns)))
                miss = sorted(set(map(str, b.columns)) - set(map(str, a.columns)))
                return 'columnas distintas' + (': sobran ' + ', '.join(extra) if extra else '') + ('; faltan ' + ', '.join(miss) if miss else '')
            return 'mismas dimensiones y columnas, pero algunos valores u orden de filas no coinciden'
        if type(a) is not type(b) and not (is_num(a) and is_num(b)):
            return 'es %s y se esperaba %s' % (describe(a), describe(b))
        if isinstance(a, (list, tuple, dict, set)) and len(a) != len(b):
            return 'tiene %d elementos y se esperaban %d' % (len(a), len(b))
        if np is not None and isinstance(a, np.ndarray) and a.shape != np.asarray(b).shape:
            return 'forma %s, se esperaba %s' % (a.shape, np.asarray(b).shape)
        return 'el valor no coincide'

    def is_data(v, depth=0):
        v = scalar(v)
        if v is None or isinstance(v, (bool, int, float, str)):
            return True
        if depth > 3:
            return False
        if isinstance(v, (list, tuple, set, frozenset)):
            return all(is_data(x, depth + 1) for x in list(v)[:50])
        if isinstance(v, dict):
            return all(is_data(k, depth + 1) and is_data(x, depth + 1) for k, x in list(v.items())[:50])
        if np is not None and isinstance(v, np.ndarray):
            return v.dtype.kind != 'O' or all(is_data(x, depth + 1) for x in v.ravel()[:50])
        return pd is not None and isinstance(v, (pd.DataFrame, pd.Series, pd.Index))

    # Nombres de nivel de módulo que la referencia crea o modifica más allá de la plantilla.
    class Assigned(ast.NodeVisitor):
        def __init__(self):
            self.counts, self.loops, self.fed, self.wrote, self.step = {}, set(), {}, {}, 0
        @property
        def feeds(self):
            # Intermedio: su último uso para calcular otra cosa es posterior a su última modificación.
            return {k for k, i in self.fed.items() if i >= self.wrote.get(k, -1)}
        def note_feeds(self, stmt, written):
            # Un nombre que alimenta el cálculo de OTRO resultado es intermedio, no un entregable.
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id in ('print', 'display'):
                return
            for n in ast.walk(stmt):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in written:
                    self.fed[n.id] = self.step
        def visit_Module(self, node):
            for stmt in node.body:
                if isinstance(stmt, ast.Assert):
                    continue
                before = dict(self.counts)
                self.visit(stmt)
                written = {k for k in self.counts if self.counts[k] != before.get(k, 0)}
                self.step += 1
                for k in written:
                    self.wrote[k] = self.step
                if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
                    self.note_feeds(stmt, written)
        def bump(self, node):
            while isinstance(node, (ast.Subscript, ast.Attribute)):
                node = node.value
            if isinstance(node, ast.Name):
                self.counts[node.id] = self.counts.get(node.id, 0) + 1
            elif isinstance(node, (ast.Tuple, ast.List)):
                for elt in node.elts:
                    self.bump(elt)
        def visit_FunctionDef(self, node): pass
        visit_AsyncFunctionDef = visit_ClassDef = visit_Lambda = visit_FunctionDef
        def visit_ListComp(self, node): pass
        visit_SetComp = visit_DictComp = visit_GeneratorExp = visit_ListComp
        def visit_Assign(self, node):
            for t in node.targets:
                self.bump(t)
            self.generic_visit(node)
        def visit_AugAssign(self, node):
            self.bump(node.target); self.generic_visit(node)
        def visit_AnnAssign(self, node):
            if node.value is not None:
                self.bump(node.target)
            self.generic_visit(node)
        def visit_For(self, node):
            names = Assigned(); names.bump(node.target); self.loops |= set(names.counts)
            self.generic_visit(node)
        def visit_With(self, node):
            for it in node.items:
                if it.optional_vars is not None:
                    names = Assigned(); names.bump(it.optional_vars); self.loops |= set(names.counts)
            self.generic_visit(node)
        MUTATORS = {'append', 'extend', 'insert', 'pop', 'remove', 'sort', 'reverse', 'update', 'clear', 'add', 'discard', 'setdefault', 'popitem', 'fill', 'resize', 'shuffle', 'fit', 'partial_fit', 'rename_axis', 'set_axis'}
        def visit_Expr(self, node):
            call = node.value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
                inplace = any(k.arg == 'inplace' and isinstance(k.value, ast.Constant) and k.value.value is True for k in call.keywords)
                if inplace or call.func.attr in self.MUTATORS:
                    self.bump(call.func.value)
            self.generic_visit(node)

    def assigned(code):
        v = Assigned()
        try:
            v.visit(ast.parse(code or ''))
        except SyntaxError:
            pass
        return v

    ref_tree = ast.parse(reference)
    ref_assigned, starter_assigned = assigned(reference), assigned(starter)
    func_names = [n.name for n in ref_tree.body if isinstance(n, ast.FunctionDef)]
    for node in ref_tree.body:
        if isinstance(node, ast.FunctionDef):
            node.decorator_list.insert(0, ast.Name(id='_study_record', ctx=ast.Load()))
    ast.fix_missing_locations(ref_tree)
    calls = {name: [] for name in func_names}
    def _study_record(fn):
        log = calls.setdefault(fn.__name__, [])
        def wrapper(*args, **kwargs):
            entry = None
            if len(log) < 15:
                try:
                    entry = {'args': copy.deepcopy(args), 'kwargs': copy.deepcopy(kwargs)}
                except Exception:
                    entry = None
            try:
                result = fn(*args, **kwargs)
                if entry is not None:
                    try:
                        entry['after'] = copy.deepcopy(args)
                    except Exception:
                        pass
            except BaseException as exc:
                if entry is not None:
                    entry['raised'] = type(exc).__name__; log.append(entry)
                raise
            if entry is not None:
                try:
                    entry['result'] = copy.deepcopy(result)
                except Exception:
                    entry['result'] = result
                log.append(entry)
            return result
        wrapper.__name__ = fn.__name__
        return wrapper

    ref_ns = {'__name__': '__main__', '_study_record': _study_record}
    ref_out = io.StringIO()
    previous = os.getcwd()
    os.makedirs(ref_dir, exist_ok=True)
    os.chdir(ref_dir)
    try:
        with contextlib.redirect_stdout(ref_out), contextlib.redirect_stderr(io.StringIO()):
            exec(compile(ref_tree, '<referencia>', 'exec'), ref_ns)
        try:
            import matplotlib.pyplot as plt
            if plt.get_fignums():
                plt.show()
        except Exception:
            pass
    except BaseException as exc:
        return json.dumps({'status': 'unavailable', 'items': [], 'notes': ['La solución de referencia no se puede ejecutar en el navegador (%s). Revisa tu código con los criterios del ejercicio.' % type(exc).__name__]})
    finally:
        os.chdir(previous)

    # 1) Funciones: se llaman las tuyas con los mismos argumentos que usó la referencia.
    for name in func_names:
        log = [c for c in calls.get(name, []) if 'args' in c]
        fn = student_ns.get(name)
        if not log:
            continue
        if not callable(fn):
            add(False, 'Falta la función %s() que pide el enunciado.' % name)
            continue
        good, first_bad = 0, None
        for call in log:
            try:
                args = copy.deepcopy(call['args'])
                with contextlib.redirect_stdout(io.StringIO()):
                    got = fn(*args, **copy.deepcopy(call['kwargs']))
                ok = 'raised' not in call and same(got, call['result'])
                detail = 'devuelve %r' % (got,) if not ok else ''
                # Funciones que modifican sus argumentos (append, df[...] = ...): el efecto también cuenta.
                if ok and 'after' in call and not same(list(args), list(call['after'])):
                    ok, detail = False, 'no deja los argumentos modificados como se esperaba'
            except Exception as exc:
                # Si la referencia lanza un error, el tuyo debe ser del mismo tipo (o una subclase).
                expected_exc = call.get('raised')
                ok = bool(expected_exc) and any(k.__name__ == expected_exc for k in type(exc).__mro__)
                detail = 'lanza %s' % type(exc).__name__
            good += ok
            if not ok and first_bad is None:
                shown = ', '.join([repr(a)[:60] for a in call['args']] + ['%s=%r' % (k, v) for k, v in call['kwargs'].items()])
                expected = 'debería lanzar %s' % call['raised'] if 'raised' in call else 'debería devolver %r' % (call['result'],)
                first_bad = '%s(%s) %s; %s' % (name, shown, detail[:120], expected[:120])
        if good == len(log):
            add(True, '%s() da el resultado correcto en %d caso(s) de prueba.' % (name, len(log)))
        else:
            add(False, '%s() falla %d de %d casos. Ejemplo: %s' % (name, len(log) - good, len(log), first_bad))

    # 2) Variables: se buscan por valor, aunque las llames de otra forma.
    flat_stdout = re.sub(r'\s+', '', student_stdout or '')
    def printed(v):
        # Resultado final mostrado con print() aunque no se guarde en una variable.
        texts = []
        try:
            texts.append(v.to_string() if pd is not None and isinstance(v, (pd.DataFrame, pd.Series)) else str(v))
            texts.append(repr(v))
        except Exception:
            return False
        # Límites de token: 150 no debe encontrarse dentro de 1500 ni 0.5 dentro de 10.55.
        return any(len(t) >= 3 and re.search(r'(?<![\w.])' + re.escape(re.sub(r'\s+', '', t)) + r'(?![\w.])', flat_stdout) for t in texts)
    def distinctive(v):
        # Un alias por valor solo es fiable si el valor no es trivial (0, 1, True… coinciden por azar).
        v = scalar(v)
        if isinstance(v, bool) or v is None:
            return False
        if isinstance(v, int):
            return abs(v) >= 1000
        if isinstance(v, float):
            return not v.is_integer()
        if isinstance(v, str):
            return len(v.strip()) >= 4
        try:
            return len(v) >= 2
        except Exception:
            return True
    pool = [(k, v) for k, v in student_ns.items() if not k.startswith('_') and is_data(v)][:300]
    for name, value in ref_ns.items():
        if name.startswith('_') or name in ref_assigned.loops or not is_data(value):
            continue
        if ref_assigned.counts.get(name, 0) <= starter_assigned.counts.get(name, 0):
            continue
        soft = isinstance(scalar(value), str) or name in ref_assigned.feeds
        if name in student_ns and same(student_ns[name], value):
            add(True, 'Resultado %s correcto (%s).' % (name, describe(value)), not soft)
            continue
        def loose(v):
            return pd is not None and isinstance(v, pd.DataFrame) and isinstance(value, pd.DataFrame) and (same_frame(v, value, True) or same_frame(v.reset_index(), value.reset_index(), True))
        if name in student_ns:
            # Misma variable con otro valor: es un fallo, no se busca un alias casual.
            mine = student_ns[name]
            if loose(mine):
                add(False, 'Casi: los valores de %s están bien, pero las columnas se llaman distinto (%s; se esperaba %s).' % (name, ', '.join(map(str, mine.columns))[:200], ', '.join(map(str, value.columns))[:200]), not soft)
            else:
                add(False, 'Tu %s no coincide: %s.' % (name, why_differs(mine, value)), not soft)
            continue
        alias = next((k for k, v in pool if same(v, value)), None) if distinctive(value) else None
        renamed = None if alias else next((k for k, v in pool if loose(v)), None)
        if renamed:
            add(False, 'Casi: los valores de %s están bien en %s, pero las columnas se llaman distinto (%s; se esperaba %s).' % (name, renamed, ', '.join(map(str, student_ns[renamed].columns))[:200], ', '.join(map(str, value.columns))[:200]), not soft)
        elif alias:
            add(True, 'Resultado equivalente a %s encontrado en tu variable %s (%s).' % (name, alias, describe(value)), not soft)
        elif not soft and printed(value):
            add(True, 'Resultado equivalente a %s mostrado en tu salida (%s).' % (name, describe(value)))
        elif not soft:
            add(False, 'No encuentro un resultado equivalente a %s (%s).' % (name, describe(value)))

    # 3) Archivos y gráficas generados.
    def listing(root):
        found = {}
        for base, _, files in os.walk(root):
            for f in files:
                found[os.path.relpath(os.path.join(base, f), root)] = os.path.join(base, f)
        return found
    ref_files, stu_files = listing(ref_dir), listing(student_dir)
    def same_file(p, q):
        try:
            if p.lower().endswith('.csv') and pd is not None:
                return same(pd.read_csv(p), pd.read_csv(q))
            if p.lower().endswith('.json'):
                with open(p, encoding='utf-8') as fa, open(q, encoding='utf-8') as fb:
                    return same(json.load(fa), json.load(fb))
            with open(p, 'rb') as fa, open(q, 'rb') as fb:
                return fa.read().strip() == fb.read().strip()
        except Exception:
            return False
    images = ('.png', '.svg', '.jpg', '.jpeg', '.pdf', '.gif')
    ref_figs = [f for f in ref_files if f.lower().endswith(images)]
    stu_figs = [f for f in stu_files if f.lower().endswith(images)]
    if ref_figs:
        add(bool(stu_figs), 'Has generado %d imagen(es) de gráfico; su contenido no se compara automáticamente, revísalo a la vista.' % len(stu_figs) if stu_figs else 'Falta generar o guardar el gráfico (savefig o plt.show()).')
    for rel, path in ref_files.items():
        if rel.lower().endswith(images):
            continue
        if rel in stu_files:
            add(same_file(path, stu_files[rel]), 'Archivo %s %s.' % (rel, 'correcto' if same_file(path, stu_files[rel]) else 'creado, pero su contenido no coincide'))
        else:
            alias = next((r for r, q in stu_files.items() if os.path.splitext(r)[1].lower() == os.path.splitext(rel)[1].lower() and same_file(path, q)), None)
            add(bool(alias), 'Archivo equivalente a %s guardado como %s.' % (rel, alias) if alias else 'Falta crear el archivo %s.' % rel)

    # 4) Salida por pantalla: números que imprime la referencia frente a los tuyos (con redondeo).
    number = re.compile(r'-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')
    ref_nums = number.findall(ref_out.getvalue())
    stu_nums = number.findall(student_stdout or '')
    def close(r, s):
        decimals = len(s.split('.')[1].split('e')[0].split('E')[0]) if '.' in s else 0
        try:
            return abs(float(r) - float(s)) <= max(1e-6 * abs(float(r)), 0.5 * 10 ** -decimals + 1e-12)
        except (ValueError, OverflowError):
            return False
    hard = [i for i in items if i['hard']]
    if ref_nums:
        remaining = list(stu_nums)
        hits = 0
        for r in ref_nums[:400]:
            idx = next((i for i, s in enumerate(remaining) if close(r, s)), None)
            if idx is not None:
                hits += 1; remaining.pop(idx)
        ratio = hits / min(len(ref_nums), 400)
        if hard:
            if ratio < 0.6:
                notes.append('Tus cálculos están bien, pero imprime los resultados que pide el enunciado: en la salida solo aparecen %d de %d valores esperados.' % (hits, min(len(ref_nums), 400)))
        else:
            add(ratio >= 0.9, 'La salida contiene %d de %d valores esperados.' % (hits, min(len(ref_nums), 400)))
    elif not hard and ref_out.getvalue().strip():
        expected_lines = [l.strip().lower() for l in ref_out.getvalue().splitlines() if l.strip()]
        got = (student_stdout or '').lower()
        hits = sum(1 for l in expected_lines if l in got)
        add(hits >= 0.9 * len(expected_lines), 'La salida contiene %d de %d líneas esperadas.' % (hits, len(expected_lines)))

    if re.search(r'\brandom\b|np\.random|sample\(|shuffle', reference) and not re.search(r'seed|random_state', reference):
        notes.append('El ejercicio usa aleatoriedad sin semilla: los valores pueden variar entre ejecuciones.')
    hard = [i for i in items if i['hard']]
    if not hard:
        status = 'unavailable'
        notes.append('Este ejercicio no tiene un resultado comprobable automáticamente: revisa los criterios y compara con la solución.')
    else:
        good = sum(i['ok'] for i in hard)
        status = 'ok' if good == len(hard) else 'partial' if good * 2 >= len(hard) else 'fail'
    return json.dumps({'status': status, 'items': items, 'notes': notes}, ensure_ascii=False, default=str)
# REVIEWER-END
`;
function exportFiles(py){
 let count=0,bytes=0,visited=0,truncated=false;
 function walk(dir,depth=0){
  if(depth>10){truncated=true;return;}
  for(const name of py.FS.readdir(dir)){
   if(name==='.'||name==='..')continue;
   if(++visited>300||count>=MAX_FILES){truncated=true;return;}
   const path=dir+'/'+name,stat=py.FS.lstat(path);
   if(py.FS.isDir(stat.mode)){walk(path,depth+1);continue;}
   if(!py.FS.isFile(stat.mode))continue;
   if(bytes+stat.size>MAX_BYTES){truncated=true;continue;}
   const data=py.FS.readFile(path);bytes+=data.byteLength;count++;
   self.postMessage({type:'file',name:path.slice(OUTPUT_DIR.length+1),data},[data.buffer]);
  }
 }
 walk(OUTPUT_DIR);
 if(truncated)output('Algunos archivos no se muestran: máximo 30 archivos y 10 MB por ejecución.');
}
self.onmessage=async event=>{
 try{
  const {code,wheels={},reference=null,starter=''}=event.data;if(typeof code!=='string'||code.length>200000)throw Error('Código demasiado largo (máximo 200.000 caracteres).');
  const review=typeof reference==='string'&&reference.trim()&&reference.length<=200000;
  let studentStdout='';
  const capture=text=>{if(studentStdout.length<200000)studentStdout+=String(text)+'\n';output(text);};
  const {loadPyodide}=await import(BASE+'pyodide.mjs');
  const py=await loadPyodide({indexURL:BASE,stdout:capture,stderr:output});
  py.FS.mkdir(OUTPUT_DIR);py.FS.chdir(OUTPUT_DIR);
  await py.runPythonAsync("import os\nos.environ['MPLBACKEND'] = 'Agg'");
  self.postMessage({type:'loading',text:'Preparando las librerías que usa tu código…'});
  const allCode=review?code+'\n'+reference:code;
  await py.loadPackagesFromImports(code);
  if(review){try{await py.loadPackagesFromImports(reference);}catch{}}
  py.globals.set('_study_code',allCode);
  const needsSeaborn=py.runPython("import ast\ndef _study_seaborn(src):\n    try:\n        tree = ast.parse(src)\n    except SyntaxError:\n        return False\n    return any((isinstance(n, ast.Import) and any(a.name.split('.')[0] == 'seaborn' for a in n.names)) or (isinstance(n, ast.ImportFrom) and (n.module or '').split('.')[0] == 'seaborn') for n in ast.walk(tree))\n_study_seaborn(_study_code)");
  if(needsSeaborn){
   if(!wheels.seaborn)throw Error('Falta el paquete Seaborn. Reconstruye la aplicación con build.py.');
   await py.loadPackage(['numpy','pandas','matplotlib']);
   py.FS.writeFile('/tmp/seaborn.whl',Uint8Array.from(atob(wheels.seaborn),c=>c.charCodeAt(0)));
   await py.runPythonAsync("import zipfile, sys\nwith zipfile.ZipFile('/tmp/seaborn.whl') as wheel:\n    wheel.extractall('/study-packages')\nsys.path.insert(0, '/study-packages')");
  }
  // show() produces a downloadable image, including when savefig() is not used.
  await py.runPythonAsync(`
import importlib.util
if importlib.util.find_spec('matplotlib'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    def _study_show(*args, **kwargs):
        from pathlib import Path
        for number in plt.get_fignums():
            index = 1
            while Path(f'figure-{index}.png').exists():
                index += 1
            plt.figure(number).savefig(f'figure-{index}.png', dpi=150, bbox_inches='tight')
        plt.close('all')
    plt.show = _study_show
`);
  self.postMessage({type:'running'});
  const globals=py.toPy({__name__:'__main__'});
  try{
   try{const result=await py.runPythonAsync(code,{globals});result?.destroy?.();}
   finally{
    // Figures left open without show()/savefig() still count as the student's output.
    try{py.runPython("import sys\nif 'matplotlib.pyplot' in sys.modules:\n    import matplotlib.pyplot as _p\n    if _p.get_fignums(): _p.show()");}catch{}
    exportFiles(py);
   }
   if(review){
    self.postMessage({type:'reviewing'});
    try{
     py.runPython(REVIEWER);
     const reviewFn=py.globals.get('_study_review');
     const report=reviewFn(globals,reference,String(starter||''),studentStdout,OUTPUT_DIR,REF_DIR);reviewFn.destroy();
     self.postMessage({type:'review',report:JSON.parse(report)});
    }catch(error){self.postMessage({type:'review',report:{status:'unavailable',items:[],notes:['El revisor no pudo completar la comparación: '+String(error.message||error).split('\n').filter(Boolean).pop().slice(0,300)]}});}
   }
  }finally{globals.destroy();}
  self.postMessage({type:'done'});
 }catch(error){self.postMessage({type:'error',text:String(error.message||error).slice(0,20000)});}
};
