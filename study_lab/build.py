"""Reconstruye el HTML standalone a partir de las fuentes editables, sin dependencias."""
from pathlib import Path
import base64,hashlib,json

ROOT = Path(__file__).resolve().parent


def js_string(text):
    return json.dumps(text, ensure_ascii=True).replace('<', '\\u003c')


def render():
    wheel=(ROOT/'vendor/seaborn-0.13.2-py3-none-any.whl').read_bytes()
    assert hashlib.sha256(wheel).hexdigest()=='636f8336facf092165e27924f223d3c62ca560b1f2bb5dff7ab7fad265361987','Unexpected Seaborn wheel'
    package_js='const PYTHON_EXTRA_WHEELS='+json.dumps({'seaborn':base64.b64encode(wheel).decode()})+';\n'
    shell = (ROOT / 'shell.html').read_text(encoding='utf-8')
    assert '/*__CSS__*/' in shell and '/*__JS__*/' in shell
    content = json.loads((ROOT / 'learning-content.json').read_text(encoding='utf-8'))
    learning_js = 'const LEARNING_CONTENT=' + json.dumps(content, ensure_ascii=False).replace('<', '\\u003c') + ';\n'
    prelude = '\n'.join('const ' + key + '=' + js_string((ROOT / name).read_text(encoding='utf-8')) + ';' for key, name in [
        ('ORANGE_CSV', 'resources/orange-iris.csv'),
        ('ORANGE_WORKFLOW', 'resources/orange-classification.ows'),
        ('PYTHON_WORKER_SOURCE', 'python-worker.mjs')])
    manifest = json.loads((ROOT / 'resources/orange-manifest.json').read_text(encoding='utf-8'))
    resources = {key: {**value, 'csvText': (ROOT / 'resources' / value['csv']).read_text(encoding='utf-8'), 'workflowText': (ROOT / 'resources' / value['workflow']).read_text(encoding='utf-8')} for key, value in manifest.items()}
    prelude += '\nconst ORANGE_CASE_RESOURCES=' + json.dumps(resources, ensure_ascii=True).replace('<', '\\u003c') + ';'
    sources = [learning_js if name == 'learning-content.js' else (ROOT / name).read_text(encoding='utf-8').removesuffix('init();\n') if name == 'app.js' else (ROOT / name).read_text(encoding='utf-8') for name in (
        'sources.js', 'materials.js', 'learning-content.js', 'learning-engine.js', 'app.js', 'learning-ui.js')]
    html = shell.replace('/*__CSS__*/', (ROOT / 'style.css').read_text(encoding='utf-8'))
    return html.replace('/*__JS__*/', package_js + prelude + '\n' + '\n'.join(sources) + '\ninit();\nbootModalStudy();\n'), learning_js


if __name__ == '__main__':
    html, learning_js = render()
    (ROOT / 'learning-content.js').write_text(learning_js, encoding='utf-8')
    (ROOT / 'index.html').write_text(html, encoding='utf-8', newline='\n')
    print('index.html creado')
