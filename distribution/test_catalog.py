import hashlib,io,json,tempfile,unittest
from pathlib import Path
from distribution.catalog_receiver import receive,RUNTIME

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.app=self.root/'app';self.state=self.root/'state'
        for name in RUNTIME+['study_lab/index.html']:
            p=self.app/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('original')
        self.runtime={n:hashlib.sha256(b'original').hexdigest() for n in RUNTIME}
        self.html=b"<!DOCTYPE html><script>const STATE_KEY='niis-study-lab-v1';</script></html>"
    def tearDown(self):self.tmp.cleanup()
    def publish(self,**changes):
        h={'mode':'publish','commit':'a'*40,'size':len(self.html),'sha256':hashlib.sha256(self.html).hexdigest(),'runtime':self.runtime};h.update(changes)
        return receive(io.BytesIO((json.dumps(h)+'\n').encode()+self.html),self.app,self.state)
    def test_exact_and_idempotent_delivery(self):
        self.assertEqual(self.publish()['status'],'published')
        inode=(self.app/'study_lab/index.html').stat().st_ino
        self.assertEqual(self.publish()['status'],'unchanged')
        self.assertEqual((self.app/'study_lab/index.html').stat().st_ino,inode)
        self.assertEqual((self.app/'distribution/server.py').read_text(),'original')
    def test_bad_hash_runtime_size_or_commit_never_replaces_document(self):
        for changes in [{'sha256':'b'*64},{'runtime':{}},{'size':9_000_000},{'commit':'../oops'}]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.publish(**changes)
            self.assertEqual((self.app/'study_lab/index.html').read_text(),'original')
    def test_status_contains_only_deployment_metadata(self):
        result=receive(io.BytesIO(b'{"mode":"status"}\n'),self.app,self.state)
        self.assertEqual(set(result),{'status','sha256','runtime'})
        self.assertFalse(self.state.exists())
if __name__=='__main__':unittest.main()
