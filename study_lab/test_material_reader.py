"""Committed reader coverage/sanitization and bounded binary delivery. Stdlib only."""
import base64,gzip,hashlib,io,json,re,tempfile,unittest
from html.parser import HTMLParser
from urllib.parse import urlsplit
from pathlib import Path
from material_assets import MaterialAssets
ROOT=Path(__file__).resolve().parent

def bundle():
    script=(ROOT/'material-reader-data.js').read_text();meta=json.loads(script.split('=',1)[1].rstrip(';\n'));return json.loads(gzip.decompress(base64.b64decode(meta['data'])))
class ReaderTests(unittest.TestCase):
    def test_complete_reading_coverage(self):
        data=bundle();catalog=json.loads((ROOT/'materials.json').read_text());self.assertEqual(data['catalogFingerprint'],catalog['fingerprint'])
        self.assertEqual(set(data['documents']),{r['id'] for r in catalog['resources']})
        docs=[r for r in catalog['resources'] if r['extension'] in {'.md','.pdf','.ipynb','.docx','.pptx','.txt','.odt','.odp'}]
        for r in docs:
            body=data['documents'][r['id']];self.assertTrue(body['text'].strip(),r['path']);self.assertFalse(body['preview'],r['path'])
        self.assertEqual(len(docs),218);self.assertEqual(sum(r['extension']=='.md' for r in catalog['resources']),127)
    def test_no_active_content_or_external_github_requirement(self):
        class Audit(HTMLParser):
            def handle_starttag(inner,tag,attrs):
                self.assertNotIn(tag,{'script','iframe','object','embed','form','input'})
                for key,value in attrs:
                    self.assertFalse(key.lower().startswith('on'))
                    if key in {'href','src'}:self.assertFalse(value.lower().startswith(('javascript:','data:text/html')));self.assertNotEqual(urlsplit(value).hostname,'github.com')
        data=bundle()
        for doc in data['documents'].values():Audit().feed(doc['html'])
        self.assertTrue(any('<math ' in d['html'] for d in data['documents'].values()))
        self.assertTrue(any('<table>' in d['html'] for d in data['documents'].values()))
    def test_assets_match_manifest_when_installed(self):
        if not (ROOT/'material-assets').is_dir():self.skipTest('Binary asset package not installed; inline reading is still checked')
        manifest=json.loads((ROOT/'material-library.json').read_text());self.assertEqual(manifest['extractionErrors'],[])
        for item in manifest['resources'].values():
            if item['available']:
                file=ROOT/'material-assets'/item['file'];self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),item['sha256'])
class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);(self.root/'material-assets').mkdir();self.id='res-'+'a'*20
        self.file=self.root/'material-assets'/(self.id+'.pdf');self.file.write_bytes(b'%PDF-1.7\nfixture')
        self.item={'file':self.file.name,'filename':'tema español.pdf','extension':'.pdf','mime':'application/pdf','available':True,'size':self.file.stat().st_size,'sha256':hashlib.sha256(self.file.read_bytes()).hexdigest()}
        self.save();self.store=MaterialAssets(self.root)
    def save(self):(self.root/'material-library.json').write_text(json.dumps({'resources':{self.id:self.item}}))
    def tearDown(self):self.temp.cleanup()
    def test_ranges_and_head(self):
        status,headers,path,start,length=self.store.response(self.id,'bytes=0-3');self.assertEqual(status,206);self.assertEqual(b''.join(self.store.chunks(path,start,length)),b'%PDF')
        self.assertEqual(self.store.response(self.id,'bytes=999-')[0],416);self.assertEqual(self.store.response(self.id,'bytes=1-2,4-5')[0],416)
        result={};body=self.store.wsgi({'PATH_INFO':'/api/materials/'+self.id,'REQUEST_METHOD':'HEAD'},lambda s,h:result.update(status=s,headers=dict(h)),True);self.assertEqual(list(body),[]);self.assertTrue(result['status'].startswith('200'))
    def test_authentication_and_method(self):
        for authorized,method,status in [(False,'GET','401'),(True,'POST','405')]:
            result={};body=self.store.wsgi({'PATH_INFO':'/api/materials/'+self.id,'REQUEST_METHOD':method},lambda s,h:result.update(status=s),authorized);self.assertTrue(result['status'].startswith(status));self.assertEqual(list(body),[])
    def test_traversal_symlink_tampering(self):
        self.assertEqual(self.store.response('../server.py')[0],404)
        self.file.write_bytes(b'tampered');self.assertEqual(self.store.response(self.id)[0],503)
        self.file.unlink();self.file.symlink_to(self.root/'material-library.json');self.assertEqual(self.store.response(self.id)[0],404)
    def test_html_is_attachment(self):
        self.item.update(extension='.html',file=self.id+'.html',mime='text/html');self.file.rename(self.root/'material-assets'/self.item['file']);self.save()
        _,headers,*_=self.store.response(self.id);self.assertEqual(headers['Content-Type'],'application/octet-stream');self.assertTrue(headers['Content-Disposition'].startswith('attachment'))
if __name__=='__main__':unittest.main()
