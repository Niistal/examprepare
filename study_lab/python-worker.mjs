// Each run owns a fresh virtual filesystem; only bounded output files leave it.
const BASE='https://cdn.jsdelivr.net/pyodide/v314.0.7/full/';
const OUTPUT_DIR='/study-output', MAX_FILES=30, MAX_BYTES=10_000_000;
let outputSize=0;
function output(text){if(outputSize>=20000)return;const part=String(text).slice(0,20000-outputSize);outputSize+=part.length;self.postMessage({type:'output',text:part+'\n'});}
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
  const {code,wheels={}}=event.data;if(typeof code!=='string'||code.length>200000)throw Error('Código demasiado largo (máximo 200.000 caracteres).');
  const {loadPyodide}=await import(BASE+'pyodide.mjs');
  const py=await loadPyodide({indexURL:BASE,stdout:output,stderr:output});
  py.FS.mkdir(OUTPUT_DIR);py.FS.chdir(OUTPUT_DIR);
  await py.runPythonAsync("import os\nos.environ['MPLBACKEND'] = 'Agg'");
  self.postMessage({type:'loading',text:'Preparando las librerías que usa tu código…'});
  await py.loadPackagesFromImports(code);
  py.globals.set('_study_code',code);
  const needsSeaborn=py.runPython("import ast\nany((isinstance(n, ast.Import) and any(a.name.split('.')[0] == 'seaborn' for a in n.names)) or (isinstance(n, ast.ImportFrom) and (n.module or '').split('.')[0] == 'seaborn') for n in ast.walk(ast.parse(_study_code)))");
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
  try{const result=await py.runPythonAsync(code,{globals});result?.destroy?.();}
  finally{globals.destroy();exportFiles(py);}
  self.postMessage({type:'done'});
 }catch(error){self.postMessage({type:'error',text:String(error.message||error).slice(0,20000)});}
};
