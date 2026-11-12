"""Import versioned course bodies and delivery assets. No notebook/code execution.
Requires markdown-it-py and pdftotext only when regenerating the library, not at runtime.
"""
from __future__ import annotations
import argparse,base64,gzip,hashlib,html,io,json,mimetypes,posixpath,re,subprocess,sys,tempfile,zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parent))
APP=Path(__file__).resolve().parents[1]
from sync_materials import make_catalog,git,script_data
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin
from latex2mathml.converter import convert as mathml

TEXT={'.md','.txt','.py','.sql','.json','.conf','.yaml','.yml','.sh','.ows','.properties','.toml','.html','.xml','.avsc','.csv','.tab','.log','.url','.svg'}
READING={'.md','.pdf','.ipynb','.docx','.pptx','.odt','.odp','.txt'}
KEY=re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{24,}|AKIA[A-Z0-9]{16}')
ASSIGN=re.compile(r'''(?im)(["']?(?:password|passwd|api[_-]?key|access[_-]?token|secret|contraseña)["']?\s*[:=]\s*)(["'])([^\n"']{4,})\2''')
def clean(text):
    text,n=KEY.subn('[credencial omitida]',text)
    def redact(m):return m[1]+m[2]+'[credencial omitida]'+m[2]
    text,k=ASSIGN.subn(redact,text)
    text,j=re.subn(r'(https?://[^\s:/]+:)[^@\s]+@',r'\1[credencial omitida]@',text)
    count=[0]
    def unquoted(m):
        if m[2].startswith('$') or m[2].lower() in {'false','true','none','null'}:return m[0]
        count[0]+=1;return m[1]+'[credencial omitida]'
    text=re.sub(r'(?im)(\b[\w.-]*(?:password|passwd|api[_-]?key|access[_-]?token|secret)[\w.-]*\s*[:=]\s*)([^\s\"\'#;<>\[\]{}]{4,})',unquoted,text)
    u=count[0]
    return text,n+k+j+u

def office_text(data,ext):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if ext=='.docx':names=['word/document.xml']
        elif ext=='.pptx':names=sorted((n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)),key=lambda n:int(re.search(r'(\d+)\.xml',n)[1]))
        else:names=['content.xml']
        sections=[]
        for i,name in enumerate(names):
            root=ET.fromstring(z.read(name));lines=[]
            for node in root.iter():
                if node.tag.rsplit('}',1)[-1] in {'p','h'}:
                    value=''.join(n.text or '' for n in node.iter() if n.tag.rsplit('}',1)[-1] in {'t','span','p','h'})
                    if value.strip():lines.append(value)
            sections.append(('## Diapositiva '+str(i+1)+'\n\n' if ext in {'.pptx','.odp'} else '')+'\n\n'.join(lines))
        return '\n\n'.join(sections)

def extract(data,ext):
    if ext in TEXT:return data.decode('utf-8-sig',errors='replace'),[]
    if ext=='.ipynb':
        notebook=json.loads(data);parts=[]
        for cell in notebook.get('cells',[]):
            source=''.join(cell.get('source',[]));typ=cell.get('cell_type')
            if typ=='markdown':parts.append(source)
            elif typ=='code':
                parts.append('```python\n'+source+'\n```')
                for output in cell.get('outputs',[]):
                    value=output.get('text',output.get('data',{}).get('text/plain',[]))
                    if value:parts.append('```text\n'+(''.join(value) if isinstance(value,list) else value)+'\n```')
        return '\n\n'.join(parts),['El cuaderno se muestra para leer: no se ejecuta su código ni sus salidas activas.']
    if ext in {'.docx','.pptx','.odt','.odp'}:return office_text(data,ext),['Vista de texto del documento; el original conserva imágenes, diseño y formato.']
    if ext=='.pdf':
        with tempfile.TemporaryDirectory(prefix='niis-pdf-read-') as d:
            p=Path(d)/'source.pdf';p.write_bytes(data)
            result=subprocess.run(['pdftotext','-layout','-enc','UTF-8',str(p),'-'],capture_output=True,timeout=60)
            if result.returncode:raise ValueError('No se pudo extraer el texto PDF')
            pages=result.stdout.decode('utf-8').split('\f');pages=pages[:-1] if not pages[-1].strip() else pages
            empty=[i+1 for i,p in enumerate(pages) if len(p.strip())<20]
            body='\n\n'.join('## Página '+str(i+1)+'\n\n```text\n'+p.strip()+'\n```' for i,p in enumerate(pages))
            return body,['Texto extraído del PDF; el visor original conserva diagramas y disposición.']+(['Páginas sin texto extraíble: '+', '.join(map(str,empty))+'. Consulta el PDF original.'] if empty else [])
    return '',[]

ALLOWED={'p','div','span','h1','h2','h3','h4','h5','h6','ul','ol','li','table','thead','tbody','tr','th','td','blockquote','pre','code','strong','em','del','hr','br','a','img','details','summary','sup','sub','kbd','math','mrow','mi','mn','mo','mfrac','msup','msub','mover','munder','msqrt','mtable','mtr','mtd','mtext','mstyle','mspace','msubsup','mfenced','menclose','semantics'}
VOID={'hr','br','img'}
class Sanitize(HTMLParser):
    def __init__(self,path,paths):super().__init__(convert_charrefs=True);self.path=path;self.paths=paths;self.out=[];self.skip=[]
    def resolve(self,url):
        value=urlsplit(unquote(url));path=value.path
        if value.scheme or value.netloc:
            if value.scheme=='https' and value.netloc=='github.com' and path.startswith('/Niistal/Big_Data/'):
                bits=path.split('/');path='/'.join(bits[5:]) if len(bits)>5 and bits[3] in {'blob','tree'} else ''
            else:return None
        elif path.startswith('/'):path=path.lstrip('/')
        else:path=posixpath.normpath(posixpath.join(posixpath.dirname(self.path),path))
        return self.paths.get(path)
    def handle_starttag(self,tag,attrs):
        if tag in {'script','style','iframe','object','form','button','input','textarea','select'}:self.skip.append(tag);return
        if self.skip or tag not in ALLOWED:return
        values=dict(attrs);safe=[]
        for key in ['title','alt']:
            if key in values:safe.append((key,values[key]))
        if tag=='math':safe.extend([('xmlns','http://www.w3.org/1998/Math/MathML'),('display','block' if values.get('display')=='block' else 'inline')])
        for key in ['mathvariant','stretchy','fence','columnalign','rowalign','columnspacing','rowspacing','width','height','depth','lspace','rspace']:
            if tag.startswith('m') and re.fullmatch(r'[a-zA-Z0-9 .%+-]{1,40}',values.get(key,'')):safe.append((key,values[key]))
        if tag=='a':
            url=values.get('href','');target=self.resolve(url)
            if url.startswith('#'):safe.append(('data-reader-anchor',unquote(url[1:])))
            elif target:safe.extend([('data-read-material',target['id']),('href','#material='+target['id'])])
            elif url.startswith('https://') and urlsplit(url).hostname!='github.com':safe.extend([('href',url),('target','_blank'),('rel','noopener noreferrer')])
        if tag=='img':
            target=self.resolve(values.get('src',''))
            if target:safe.append(('data-material-image',target['id']))
        if tag in {'th','td'}:
            for key in ['colspan','rowspan']:
                if values.get(key,'').isdigit() and int(values[key])<=20:safe.append((key,values[key]))
        if tag.startswith('h') and tag[1:].isdigit() and re.fullmatch(r'mr-section-\d+',values.get('id','')):safe.append(('id',values['id']))
        if tag=='code' and re.fullmatch(r'language-[\w+-]+',values.get('class','')):safe.append(('class',values['class']))
        self.out.append('<'+tag+''.join(' '+k+'="'+html.escape(v,quote=True)+'"' for k,v in safe)+'>')
    def handle_endtag(self,tag):
        if self.skip:
            if tag==self.skip[-1]:self.skip.pop()
            return
        if tag in ALLOWED and tag not in VOID:self.out.append('</'+tag+'>')
    def handle_data(self,data):
        if not self.skip:self.out.append(html.escape(data))

def render(text,r,paths):
    headings=[];md=MarkdownIt('commonmark',{'html':True}).enable('table').enable('strikethrough').use(dollarmath_plugin)
    def formula(tokens,idx,options,env):
        try:return mathml(tokens[idx].content,display='block' if tokens[idx].type=='math_block' else 'inline')
        except Exception:return '<code>'+html.escape(tokens[idx].content)+'</code>'
    md.add_render_rule('math_inline',lambda self,tokens,idx,options,env:formula(tokens,idx,options,env))
    md.add_render_rule('math_block',lambda self,tokens,idx,options,env:formula(tokens,idx,options,env))
    def heading(tokens,idx,options,env):
        title=tokens[idx+1].content;ident='mr-section-'+str(len(headings));tokens[idx].attrSet('id',ident);headings.append({'id':ident,'title':re.sub(r'[*`_]+','',title),'level':int(tokens[idx].tag[1:])})
        return md.renderer.renderToken(tokens,idx,options,env)
    md.add_render_rule('heading_open',lambda self,tokens,idx,options,env:heading(tokens,idx,options,env))
    if r['extension'] not in READING and r['extension']!='.html':text='```'+r['extension'][1:]+'\n'+text+'\n```'
    parsed=Sanitize(r['path'],paths);parsed.feed(md.render(text));return ''.join(parsed.out),headings

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--ref',required=True);p.add_argument('--output',type=Path,default=APP);args=p.parse_args()
    previous=json.loads((APP/'materials.json').read_text());catalog=make_catalog(args.repo,args.ref,previous);paths={r['path']:r for r in catalog['resources']}
    out=args.output;out.mkdir(parents=True,exist_ok=True);assetdir=out/'material-assets';assetdir.mkdir(exist_ok=True)
    docs={};manifest={};errors=[]
    for i,r in enumerate(catalog['resources']):
        raw=git(args.repo,'cat-file','blob',r['git_blob']);ext=r['extension'];text='';notices=[]
        try:text,notices=extract(raw,ext)
        except Exception as e:errors.append({'id':r['id'],'error':type(e).__name__});notices=['El original está disponible; no se pudo generar la vista de lectura.']
        text,redactions=clean(text)
        if redactions:notices.append('Se han omitido valores con formato de credenciales; la lectura conserva los conceptos.')
        # Text resources are delivered after the same credential filter, never executing HTML/SVG.
        delivered=text.encode('utf-8') if ext in TEXT and redactions else raw
        name=r['id']+ext
        # A binary containing credentials in its extracted text is not copied verbatim.
        available=not(redactions and ext not in TEXT)
        if available:(assetdir/name).write_bytes(delivered)
        else:(assetdir/name).unlink(missing_ok=True)
        preview=False
        if ext not in READING and ext!='.html' and len(text)>150_000:
            text=text[:50000];preview=True;notices.append('Vista previa de datos/código voluminoso. El archivo completo se descarga desde esta aplicación, sin GitHub.')
        if text:
            body,toc=render(text,r,paths)
            if ext=='.html':
                class VisibleText(HTMLParser):
                    def __init__(self):super().__init__();self.parts=[]
                    def handle_data(self,data):self.parts.append(data)
                visible=VisibleText();visible.feed(body);text=' '.join(visible.parts)
            docs[r['id']]={'html':body,'text':text,'toc':toc,'notices':notices,'format':ext,'originalAvailable':available,'preview':preview}
        else:docs[r['id']]={'html':'','text':'','toc':[],'notices':notices,'format':ext,'originalAvailable':available,'preview':preview}
        mime=mimetypes.guess_type(r['path'])[0] or 'application/octet-stream'
        manifest[r['id']]={'file':name,'filename':Path(r['path']).name,'extension':ext,'mime':mime,'available':available,'sha256':hashlib.sha256(delivered).hexdigest() if available else None,'size':len(delivered) if available else 0,'original_sha256':hashlib.sha256(raw).hexdigest(),'git_blob':r['git_blob'],'redactions':redactions,'readable':bool(text)}
    package={'schema':1,'source':catalog['source'],'catalogFingerprint':catalog['fingerprint'],'documents':docs}
    compressed=gzip.compress(json.dumps(package,ensure_ascii=False,separators=(',',':')).encode(),mtime=0)
    bundle={'schema':1,'encoding':'gzip-base64','source':catalog['source'],'catalogFingerprint':catalog['fingerprint'],'data':base64.b64encode(compressed).decode()}
    (out/'material-reader-data.js').write_text('const MATERIAL_READER_BUNDLE='+json.dumps(bundle,separators=(',',':'))+';\n')
    (out/'material-library.json').write_text(json.dumps({'schema':1,'source':catalog['source'],'catalogFingerprint':catalog['fingerprint'],'resources':manifest,'extractionErrors':errors},ensure_ascii=False,indent=2)+'\n')
    (out/'materials.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n');(out/'materials.js').write_text(script_data(catalog))
    print(json.dumps({'resources':len(docs),'readable':sum(bool(d['text']) for d in docs.values()),'readingDocuments':sum(r['extension'] in READING for r in catalog['resources']),'bundleBytes':len(compressed),'assetBytes':sum(r['size'] for r in manifest.values()),'redactedFiles':sum(r['redactions']>0 for r in manifest.values()),'extractionErrors':errors}))
if __name__=='__main__':main()
