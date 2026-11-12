"""Actual streamed staging and replacement with malicious/missing archives rejected."""
import hashlib,io,json,tarfile,tempfile,unittest
from pathlib import Path
from distribution.install_materials import install
class MaterialInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.app=self.root/'study_lab';self.app.mkdir();self.ident='res-'+'a'*20;self.name=self.ident+'.pdf';self.data=b'%PDF course'
        entry={'file':self.name,'available':True,'size':len(self.data),'sha256':hashlib.sha256(self.data).hexdigest()}
        (self.app/'material-library.json').write_text(json.dumps({'source':{'commit':'b'*40},'resources':{self.ident:entry}}))
        self.original=self.app/'material-assets';self.original.mkdir();(self.original/'old-file').write_text('keep until success')
    def tearDown(self):self.tmp.cleanup()
    def archive(self,entries):
        output=self.root/'materials.tar.gz'
        with tarfile.open(output,'w:gz') as tar:
            for name,data,typ in entries:
                info=tarfile.TarInfo(name);info.size=len(data);info.type=typ;tar.addfile(info,io.BytesIO(data))
        return output,hashlib.sha256(output.read_bytes()).hexdigest()
    def test_verified_install_retains_previous_assets(self):
        archive,digest=self.archive([('study_lab/material-assets/'+self.name,self.data,tarfile.REGTYPE)])
        result=install(archive,digest,self.root);self.assertEqual((self.original/self.name).read_bytes(),self.data)
        self.assertEqual((Path(result['previous_assets'])/'old-file').read_text(),'keep until success')
    def test_bad_members_missing_or_changed_bytes_preserve_current(self):
        for entries in [[],[('../escape',b'x',tarfile.REGTYPE)],[('study_lab/material-assets/'+self.name,self.data,tarfile.SYMTYPE)],[('study_lab/material-assets/'+self.name,b'x'*len(self.data),tarfile.REGTYPE)]]:
            with self.subTest(entries=entries):
                archive,digest=self.archive(entries)
                with self.assertRaises(ValueError):install(archive,digest,self.root)
                self.assertEqual((self.original/'old-file').read_text(),'keep until success');self.assertFalse(list(self.app.glob('.materials-stage-*')))
    def test_wrong_outer_hash_and_target_symlink_rejected(self):
        archive,digest=self.archive([])
        with self.assertRaises(ValueError):install(archive,'0'*64,self.root)
        (self.original/'old-file').unlink();self.original.rmdir();self.original.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):install(archive,digest,self.root)
if __name__=='__main__':unittest.main()
