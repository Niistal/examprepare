// Static document only. Authentication and owner access are enforced by Sites dispatch.
const documentHTML = /*__DOCUMENT__*/;
const securityHeaders = /*__HEADERS__*/;
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const headers = new Headers(securityHeaders);
    if (!['GET', 'HEAD'].includes(request.method)) {
      headers.set('allow', 'GET, HEAD');
      return new Response('Método no permitido', {status:405,headers});
    }
    if (!['/', '/index.html'].includes(url.pathname)) {
      return new Response(request.method==='HEAD'?null:'No encontrado', {status:404,headers});
    }
    headers.set('content-type','text/html; charset=utf-8');
    return new Response(request.method==='HEAD'?null:documentHTML, {status:200,headers});
  }
};
