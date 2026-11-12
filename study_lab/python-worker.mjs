// Python stays inside this worker's in-memory WebAssembly filesystem.
const BASE='https://cdn.jsdelivr.net/pyodide/v314.0.7/full/';
let outputSize=0;
function output(text){if(outputSize>=20000)return;const part=String(text).slice(0,20000-outputSize);outputSize+=part.length;self.postMessage({type:'output',text:part+'\n'});}
self.onmessage=async event=>{
 try{
  const {code}=event.data;if(typeof code!=='string'||code.length>200000)throw Error('Código demasiado largo (máximo 200.000 caracteres).');
  const {loadPyodide}=await import(BASE+'pyodide.mjs');
  const py=await loadPyodide({indexURL:BASE,stdout:output,stderr:output});
  self.postMessage({type:'loading',text:'Preparando las librerías que usa tu código…'});
  await py.loadPackagesFromImports(code);
  self.postMessage({type:'running'});
  const globals=py.toPy({__name__:'__main__'});
  try{const result=await py.runPythonAsync(code,{globals});result?.destroy?.();}finally{globals.destroy();}
  self.postMessage({type:'done'});
 }catch(error){self.postMessage({type:'error',text:String(error.message||error).slice(0,20000)});}
};
