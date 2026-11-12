"""Allowlisted course files, shared by localhost and authenticated WSGI delivery."""
import hashlib,json,re
from pathlib import Path
from urllib.parse import quote

class MaterialAssets:
    def __init__(self,root):self.root=Path(root);self.verified={}
    def response(self,resource_id,range_header=None,download=False):
        if not re.fullmatch(r'res-[0-9a-f]{20}',resource_id):return 404,{},None,0,0
        try:
            manifest=json.loads((self.root/'material-library.json').read_text(encoding='utf-8'))
            item=manifest['resources'].get(resource_id)
            if not item or not item['available']:return 404,{},None,0,0
            filename=item['file']
            if not re.fullmatch(re.escape(resource_id)+r'\.[a-z0-9]+',filename):return 404,{},None,0,0
            if item['extension']!=Path(filename).suffix or any(c in item['mime'] for c in '\r\n'):return 503,{},None,0,0
            directory=self.root/'material-assets';path=directory/filename
            if directory.is_symlink() or path.is_symlink() or not path.is_file():return 404,{},None,0,0
            stat=path.stat();signature=(stat.st_ino,stat.st_mtime_ns,stat.st_size,item['sha256'])
            if stat.st_size!=item['size']:return 503,{},None,0,0
            if self.verified.get(resource_id)!=signature:
                digest=hashlib.sha256()
                with path.open('rb') as source:
                    for block in iter(lambda:source.read(1024*1024),b''):digest.update(block)
                if digest.hexdigest()!=item['sha256']:return 503,{},None,0,0
                self.verified[resource_id]=signature
            size=stat.st_size;start=0;end=size-1;status=200
            headers={'Content-Type':item['mime'],'Content-Length':str(size),'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Accept-Ranges':'bytes','ETag':'"'+item['sha256']+'"','Content-Security-Policy':"default-src 'none'; frame-ancestors 'self'; base-uri 'none'"}
            inline=item['extension'] in {'.pdf','.png','.mp4','.m4a'} and not download
            if not inline:headers['Content-Type']='application/octet-stream'
            headers['Content-Disposition']=('inline' if inline else 'attachment')+"; filename=material"+item['extension']+"; filename*=UTF-8''"+quote(item['filename'],safe='')
            if range_header:
                match=re.fullmatch(r'bytes=(\d*)-(\d*)',range_header)
                if not match or not any(match.groups()) or size==0:return 416,{'Content-Range':f'bytes */{size}','Content-Length':'0'},None,0,0
                a,b=match.groups()
                if not a:
                    count=int(b);start=max(0,size-count)
                    if count==0:return 416,{'Content-Range':f'bytes */{size}','Content-Length':'0'},None,0,0
                else:start=int(a);end=min(size-1,int(b)) if b else size-1
                if start>=size or start>end:return 416,{'Content-Range':f'bytes */{size}','Content-Length':'0'},None,0,0
                status=206;headers['Content-Range']=f'bytes {start}-{end}/{size}';headers['Content-Length']=str(end-start+1)
            return status,headers,path,start,max(0,end-start+1)
        except (OSError,ValueError,KeyError,TypeError):return 503,{},None,0,0
    @staticmethod
    def chunks(path,start,length):
        with path.open('rb') as source:
            source.seek(start)
            while length:
                data=source.read(min(65536,length))
                if not data:break
                length-=len(data);yield data
    def wsgi(self,environ,start_response,authorized):
        from http import HTTPStatus
        if not authorized:
            start_response('401 Unauthorized',[('Content-Length','0'),('Cache-Control','no-store')]);return []
        if environ['REQUEST_METHOD'] not in {'GET','HEAD'}:
            start_response('405 Method Not Allowed',[('Content-Length','0')]);return []
        ident=environ['PATH_INFO'].removeprefix('/api/materials/')
        status,headers,path,start,length=self.response(ident,environ.get('HTTP_RANGE'),'download=1' in environ.get('QUERY_STRING',''))
        headers.setdefault('Content-Length','0');headers.setdefault('Cache-Control','private, no-store');start_response(str(status)+' '+HTTPStatus(status).phrase,list(headers.items()))
        return self.chunks(path,start,length) if path and environ['REQUEST_METHOD']!='HEAD' else []
