// QA server for the exact Worker artifact; loopback only, no production dependency.
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
const [workerFile,portText]=process.argv.slice(2);
const source=await readFile(resolve(workerFile),'utf8');
const {default:worker}=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const port=Number(portText);
if(!Number.isInteger(port)||port<1||port>65535)throw Error('Puerto inválido');
const server=createServer(async(req,res)=>{
  try{
    const response=await worker.fetch(new Request(`http://127.0.0.1:${port}${req.url}`,{method:req.method,headers:req.headers}));
    res.writeHead(response.status,Object.fromEntries(response.headers));
    res.end(Buffer.from(await response.arrayBuffer()));
  }catch{res.writeHead(500,{'content-type':'text/plain'});res.end('Error de QA');}
});
server.listen(port,'127.0.0.1');
