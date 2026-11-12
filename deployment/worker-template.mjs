// Static study assets only; Python never executes on the server. Authentication and owner access are enforced by Sites dispatch.
const documentHTML = /*__DOCUMENT__*/;
const pythonWorker = /*__PYTHON_WORKER__*/;
const securityHeaders = /*__HEADERS__*/;
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const headers = new Headers(securityHeaders);
    if (!['GET', 'HEAD'].includes(request.method)) {
      headers.set('allow', 'GET, HEAD');
      return new Response('Método no permitido', {status:405,headers});
    }
    if (url.pathname==='/python-worker.mjs') {
      headers.set('content-type','text/javascript; charset=utf-8');
      headers.set('content-security-policy',"default-src 'none'; script-src https://cdn.jsdelivr.net/pyodide/v314.0.7/full/ 'unsafe-eval' 'wasm-unsafe-eval'; connect-src https://cdn.jsdelivr.net/pyodide/v314.0.7/full/; worker-src 'none'; object-src 'none'");
      return new Response(request.method==='HEAD'?null:pythonWorker,{status:200,headers});
    }
    if (!['/', '/index.html'].includes(url.pathname)) {
      return new Response(request.method==='HEAD'?null:'No encontrado', {status:404,headers});
    }
    headers.set('content-type','text/html; charset=utf-8');
    return new Response(request.method==='HEAD'?null:documentHTML, {status:200,headers});
  }
};
