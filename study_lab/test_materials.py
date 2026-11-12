"""Git fixtures: nuevas notas, asignación exacta y contenido hostil. Sin red ni apuntes reales."""
import importlib.util,json,pathlib,subprocess,sys,tempfile,unittest
from unittest.mock import patch
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('sync_materials',pathlib.Path(__file__).parent/'scripts/sync_materials.py')
sync=importlib.util.module_from_spec(spec);spec.loader.exec_module(sync)

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='niis-source-');self.addCleanup(self.temp.cleanup)
        self.repo=pathlib.Path(self.temp.name)/'repo';self.repo.mkdir()
        self.git('init','-b','main');self.git('config','user.name','Fixture QA');self.git('config','user.email','qa@example.invalid');self.git('remote','add','origin',sync.ORIGIN)
    def git(self,*args):return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.DEVNULL)
    def write(self,path,text):
        f=self.repo/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text, encoding='utf-8')
    def commit(self):self.git('add','.');self.git('commit','-m','fixture')
    def test_exact_assignment_and_derivatives(self):
        for folder,(cid,_) in sync.REGISTRY.items():self.write(folder+'/README.md','# '+folder+'\n## Tema\n')
        self.write('05_AA_Programazioa/04_Ikaskuntza_Automatikorako_Sistemak.md','# KNN\n')
        self.write('NotebookLM_Material_Estudio/04_Ikaskuntza_Automatikorako_Sistemak/Guias_de_Estudio/Guia.md','# Pandas\n')
        self.write('02_Erronka_1_CNC_Guard/README.md','# Proyecto avanzado\n')
        self.write('08_Erronka_2_RetailEUS/README.md','# Proyecto avanzado\n')
        self.write('05_AA_Programazioa/AGENTS.md','# Instrucciones\n')
        self.commit();catalog=sync.make_catalog(self.repo,'main');by={r['path']:r for r in catalog['resources']}
        self.assertEqual(by['05_AA_Programazioa/04_Ikaskuntza_Automatikorako_Sistemak.md']['course'],'program')
        derived=by['NotebookLM_Material_Estudio/04_Ikaskuntza_Automatikorako_Sistemak/Guias_de_Estudio/Guia.md']
        self.assertEqual((derived['course'],derived['kind']),('ml','derived'))
        self.assertFalse(any(p.startswith(('02_','08_')) or p.endswith('AGENTS.md') for p in by))
        self.assertEqual({r['course'] for r in by.values()},{v[0] for v in sync.REGISTRY.values()})
    def test_new_module_never_reuses_known_number(self):
        self.write('09_Nueva_Asignatura/apunte.md','# Nuevo\n');self.write('05_Carpeta_Equivocada/apunte.md','# Confuso\n');self.commit()
        resources=sync.make_catalog(self.repo,'main')['resources']
        self.assertEqual(len(resources),2);by={r['module']:r for r in resources};self.assertEqual(by['09_Nueva_Asignatura']['course'],'module-09_Nueva_Asignatura');self.assertEqual(by['05_Carpeta_Equivocada']['course'],'unassigned-05_Carpeta_Equivocada')
    def test_updates_and_stable_ids(self):
        self.write('05_AA_Programazioa/a.md','# NumPy\n');self.commit();before=sync.make_catalog(self.repo,'main')
        self.write('05_AA_Programazioa/a.md','# NumPy actualizado\n');self.write('06_BD_Sistemak/b.md','# Elastic\n');self.commit()
        after=sync.make_catalog(self.repo,'main',before)
        self.assertEqual(before['resources'][0]['id'],next(r['id'] for r in after['resources'] if r['path'].endswith('a.md')))
        self.assertEqual((len(after['changes']['added']),len(after['changes']['changed'])),(1,1))
    def test_dirty_working_tree_not_read(self):
        self.write('05_AA_Programazioa/a.md','# Versionado\n');self.commit();self.write('05_AA_Programazioa/a.md','# NO VERSIONADO\n')
        self.assertEqual(sync.make_catalog(self.repo,'main')['resources'][0]['title'],'Versionado')
    def test_private_outputs_and_secret_headers_not_extracted(self):
        notebook={'cells':[{'cell_type':'markdown','source':['# Seguro\n','## password=valor-ficticio\n']},{'cell_type':'code','source':['x=1'],'outputs':[{'text':['DATO PRIVADO NO COPIAR']}]}]}
        self.write('05_AA_Programazioa/a.ipynb',json.dumps(notebook));self.write('05_AA_Programazioa/credentials.json','{}');self.commit()
        catalog=sync.make_catalog(self.repo,'main');serialized=json.dumps(catalog)
        self.assertNotIn('DATO PRIVADO',serialized);self.assertNotIn('valor-ficticio',serialized);self.assertEqual(len(catalog['resources']),1)
    def test_markdown_code_fences_are_not_sections(self):
        self.write('05_AA_Programazioa/a.md','# Real\n```python\n# No es apartado\n```\n~~~text\n## Tampoco\n~~~\n## Segundo\n');self.commit()
        resource=sync.make_catalog(self.repo,'main')['resources'][0]
        self.assertEqual(resource['sections'],['Real','Segundo'])
    def test_malformed_notebook_has_no_extracted_sections(self):
        self.write('05_AA_Programazioa/a.ipynb','[]');self.commit()
        resource=sync.make_catalog(self.repo,'main')['resources'][0]
        self.assertEqual(resource['sections'],[]);self.assertEqual(resource['title'],'a')
    def test_wrong_remote_or_branch_fails_closed(self):
        self.write('05_AA_Programazioa/a.md','# A\n');self.commit();self.git('remote','set-url','origin','https://github.com/Niistal/T2-erronka1.git')
        with self.assertRaises(ValueError):sync.make_catalog(self.repo,'main')
    def test_source_audit_rejects_lookalike_remote_before_writing(self):
        self.write('05_AA_Programazioa/a.md','# A\n');self.commit()
        app=pathlib.Path(__file__).parent;before={name:(app/name).read_bytes() for name in ['sources.json','sources.js']}
        self.git('remote','set-url','origin','https://not-github.com/Niistal/Big_Data.git')
        result=subprocess.run([sys.executable,str(app/'scripts/verify_sources.py'),str(self.repo)],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertIn('Niistal/Big_Data en main',result.stderr)
        self.assertTrue(all((app/name).read_bytes()==raw for name,raw in before.items()))
    def test_non_main_branch_rejected_without_checkout(self):
        self.write('05_AA_Programazioa/a.md','# A\n');self.commit();self.git('branch','-m','other')
        with self.assertRaises(ValueError):sync.make_catalog(self.repo,'main')
        self.assertEqual(self.git('branch','--show-current').decode().strip(),'other')
    def test_duplicate_new_module_codes_are_not_guessed(self):
        self.write('09_Asignatura_A/a.md','# A\n');self.write('09_Asignatura_B/b.md','# B\n');self.commit()
        resources=sync.make_catalog(self.repo,'main')['resources'];self.assertEqual(len(resources),2);self.assertTrue(all(r['assignment']=='unassigned' and r['course'].startswith('unassigned-') for r in resources))
    def test_script_breakout_is_encoded_in_js(self):
        self.write('05_AA_Programazioa/escape.md','# Archivo\n');self.commit()
        catalog=sync.make_catalog(self.repo,'main')
        catalog['resources'][0]['path']='05_AA_Programazioa/x</script>.md'
        output=pathlib.Path(self.temp.name)/'output/materials.json'
        args=SimpleNamespace(repo=self.repo,refresh=False,check=False,state_dir=pathlib.Path(self.temp.name)/'state',output=output)
        with patch.object(sync,'make_catalog',return_value=catalog):
            self.assertEqual(sync.run(args)['status'],'changed')
        js=output.with_suffix('.js').read_text(encoding='utf-8');self.assertNotIn('</script>',js);self.assertIn('\\u003c',js)
    def test_failed_generation_preserves_previous_files(self):
        self.write('05_AA_Programazioa/a.md','# A\n');self.commit()
        output=pathlib.Path(self.temp.name)/'output/materials.json';output.parent.mkdir();output.write_text('{"schema":1,"resources":[]}', encoding='utf-8')
        args=SimpleNamespace(repo=self.repo,refresh=False,check=False,state_dir=pathlib.Path(self.temp.name)/'state',output=output)
        before=output.read_bytes()
        with patch.object(sync,'make_catalog',side_effect=ValueError('invalid')):
            with self.assertRaises(ValueError):sync.run(args)
        self.assertEqual(output.read_bytes(),before)
    def test_partial_pair_write_repairs_on_retry(self):
        self.write('05_AA_Programazioa/a.md','# A\n');self.commit()
        output=pathlib.Path(self.temp.name)/'output/materials.json'
        args=SimpleNamespace(repo=self.repo,refresh=False,check=False,state_dir=pathlib.Path(self.temp.name)/'state',output=output)
        original=sync.atomic_write
        def fail_js(path,text):
            if path.suffix=='.js':raise OSError('fixture write failure')
            original(path,text)
        with patch.object(sync,'atomic_write',side_effect=fail_js):
            with self.assertRaises(OSError):sync.run(args)
        self.assertTrue(output.exists());self.assertFalse(output.with_suffix('.js').exists())
        result=sync.run(args);self.assertEqual(result['status'],'changed');self.assertTrue(result['artifact_repaired'])
        self.assertEqual(output.with_suffix('.js').read_text(encoding='utf-8'),sync.script_data(json.loads(output.read_text(encoding='utf-8'))))
        self.assertEqual(sync.run(args)['status'],'unchanged')
    def test_replace_failure_removes_only_owned_temporary_file(self):
        output=pathlib.Path(self.temp.name)/'output.json';output.write_text('previous', encoding='utf-8')
        before=set(output.parent.iterdir())
        with patch.object(sync.os,'replace',side_effect=OSError('fixture disk failure')):
            with self.assertRaises(OSError):sync.atomic_write(output,'new')
        self.assertEqual(output.read_text(encoding='utf-8'),'previous');self.assertEqual(set(output.parent.iterdir()),before)
    def test_oversized_catalog_is_rejected(self):
        self.write('05_AA_Programazioa/a.md','# A\n');self.commit()
        entries=[{'path':f'05_AA_Programazioa/datos/{i}.csv','blob':f'{i:040x}','size':10} for i in range(5001)]
        with patch.object(sync,'tree',return_value=entries):
            with self.assertRaisesRegex(ValueError,'5000'):sync.make_catalog(self.repo,'main')
    def test_new_derived_subject_without_primary_root_is_quarantined(self):
        self.write('NotebookLM_Material_Estudio/09_Nueva/guia.md','# Nuevo tema\n');self.commit()
        resource=sync.make_catalog(self.repo,'main')['resources'][0]
        self.assertEqual(resource['course'],'unassigned-09_Nueva');self.assertEqual(resource['assignment'],'unassigned')
    def test_git_errors_do_not_echo_credentials(self):
        result=subprocess.CompletedProcess(['git'],1,stdout=b'',stderr=b'Authorization: Bearer not-a-real-credential')
        with patch.object(sync.subprocess,'run',return_value=result):
            with self.assertRaises(RuntimeError) as caught:sync.git(self.repo,'fetch')
        self.assertNotIn('not-a-real-credential',str(caught.exception))
    def test_no_symlink_traversal(self):
        self.write('05_AA_Programazioa/a.md','# A\n');self.commit()
        target=self.repo/'link-target';target.write_text('/etc/passwd',encoding='utf-8')
        blob=self.git('hash-object','-w',str(target)).decode().strip()
        self.git('update-index','--add','--cacheinfo',f'120000,{blob},05_AA_Programazioa/secret.md')
        self.git('commit','-m','symlink fixture')
        self.assertEqual(len(sync.make_catalog(self.repo,'main')['resources']),1)

if __name__=='__main__':unittest.main()
