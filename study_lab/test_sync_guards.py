"""Guardas del publicador: solo tres artefactos, sin tocar staging ni trabajo ajeno."""
import importlib.util,json,pathlib,subprocess,sys,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
SCRIPT=pathlib.Path(__file__).parent/'scripts';sys.path.insert(0,str(SCRIPT))
spec=importlib.util.spec_from_file_location('prepare_material_sync',SCRIPT/'prepare_material_sync.py');sync=importlib.util.module_from_spec(spec);spec.loader.exec_module(sync)

class SyncGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='niis-guard-');self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name)/'app';self.root.mkdir();self.state=pathlib.Path(self.temp.name)/'state';self.state.mkdir()
        self.git('init','-b','feat/niis-study-lab');self.git('config','user.name','Fixture QA');self.git('config','user.email','qa@example.invalid');self.git('remote','add','origin','https://github.com/Niistal/examprepare')
        self.p={'schema':1,'source_repository':'Niistal/Big_Data','source_branch':'main','app_branch':'feat/niis-study-lab','site_project_id':'fixture-private','access':'owner_private','generated_paths':['study_lab/materials.json','study_lab/materials.js','study_lab/index.html']}
        self.write('deployment/sync-policy.json',json.dumps(self.p));self.write('deployment/hosting.json',json.dumps({'project_id':'fixture-private'}))
        for f in self.p['generated_paths']:self.write(f,'baseline')
        self.commit();self.base=self.git('rev-parse','HEAD').strip()
        patches=[patch.object(sync,'ROOT',self.root),patch.object(sync,'POLICY',self.root/'deployment/sync-policy.json'),patch.object(sync,'STATE',self.state)]
        for p in patches:p.start();self.addCleanup(p.stop)
    def git(self,*args):return subprocess.check_output(['git','-C',str(self.root),*args],stderr=subprocess.DEVNULL,text=True)
    def write(self,name,text):p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    def commit(self):self.git('add','.');self.git('commit','-m','fixture')
    def record(self):
        for f in self.p['generated_paths']:self.write(f,'candidate '+f)
        return {'schema':1,'phase':'prepared','base_commit':self.base,'source_head':'a'*40,'hashes':{f:sync.digest(f) for f in self.p['generated_paths']}}
    def args(self,**kw):return SimpleNamespace(**({'automation':False,'apply':False,'mark_committed':False,'mark_published':False,'deployment_id':None,'version_id':None,'hosted_commit':None}|kw))
    def test_worktree_is_not_cleaned_or_overwritten(self):
        self.write('mi_trabajo.md','no borrar')
        self.assertEqual(sync.execute(self.args())['status'],'blocked_worktree')
        self.assertEqual((self.root/'mi_trabajo.md').read_text(),'no borrar')
    def test_prepared_commit_and_publish_resume(self):
        record=self.record();self.assertEqual(sync.resume(record,self.p)['status'],'ready_for_commit')
        self.commit();updated=sync.mark_committed(record,self.p)
        self.assertEqual(updated['phase'],'committed');self.assertEqual(sync.resume(updated,self.p)['status'],'ready_for_publish')
    def test_human_changes_are_blocked(self):
        record=self.record();self.write('app.js','cambio humano')
        with self.assertRaises(sync.GuardError):sync.resume(record,self.p)
    def test_candidate_tampering_is_blocked(self):
        record=self.record();self.write('study_lab/index.html','otra versión')
        with self.assertRaises(sync.GuardError):sync.resume(record,self.p)
    def test_unrelated_commit_is_not_adopted(self):
        record=self.record();self.write('otro.md','otro');self.commit()
        with self.assertRaises(sync.GuardError):sync.mark_committed(record,self.p)
    def test_public_or_wrong_site_is_blocked(self):
        self.p['access']='public';self.write('deployment/sync-policy.json',json.dumps(self.p))
        with self.assertRaises(sync.GuardError):sync.policy()
    def test_wrong_branch_is_not_checked_out(self):
        self.git('checkout','-b','otra')
        with self.assertRaises(sync.GuardError):sync.policy()
        self.assertEqual(self.git('branch','--show-current').strip(),'otra')
    def test_foreground_deadline_guard(self):
        self.write('placeholder','x');(self.state/'overnight.json').write_text(json.dumps({'deadline_utc':'2999-01-01T00:00:00Z'}))
        self.assertEqual(sync.execute(self.args(automation=True))['status'],'foreground_work')
    def test_staging_is_not_reused(self):
        record=self.record();self.git('add','study_lab/materials.json')
        with self.assertRaises(sync.GuardError):sync.resume(record,self.p)
        self.assertIn('study_lab/materials.json',self.git('diff','--cached','--name-only'))
if __name__=='__main__':unittest.main()
