"""Ejecuta soluciones propias en carpetas temporales, nunca en Big_Data."""
import argparse,json,os,pathlib,subprocess,tempfile
root=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--python',default=os.sys.executable);args=parser.parse_args()
bank=json.loads(subprocess.check_output(['node',str(root/'scripts/export_bank.cjs')]))
checks={
'P01':'assert not validar_nif("²2345678Z")\nassert not validar_nif("１２３４５６７８Z")',
'P02':'assert len(cargar("productos.json"))==2',
'P03':'assert ordenadas==["Bilbo","Gasteiz","Donostia"]',
'P05':'assert filtrados.tolist()==[3,4,5,6,7,8]\nassert a.tolist()==[[1,2,3],[4,5,6],[0,0,0]]',
'P06':'assert np.allclose(z.mean(axis=0),0)\nassert np.allclose(z.std(axis=0),1)',
'P07':'assert df.total.tolist()==[20.,0.]',
'P08':'assert resumen.loc["A","suma"]==40',
'P09':'assert huerfanos.id_cliente.tolist()==[99]',
'P10':'assert len(axs)==2',
'P11':'assert len(pipe.predict(X_test))==len(y_test)',
'P12':'assert abs(precision-.75)<1e-9\nassert abs(recall-30/35)<1e-9',
'P17':'assert len(resultado)==6\nassert set(resultado.origen)=={"Q1","Q2","Q3"}',
'P18':'''import pandas as pd
X=pd.DataFrame({"edad":[20,30,40,50,25,45],"sueldo":[10,20,30,40,15,35],"ciudad":["A","B","A","B","A","B"]})
pipe.fit(X,[0,0,1,1,0,1])
assert len(pipe.predict(pd.DataFrame({"edad":[None],"sueldo":[22],"ciudad":["Nueva"]})))==1''',
'P19':'assert Path("ejemplo.json").exists()',
'P20':'assert np.allclose(A@B,[[2,4],[6,8]])',
'P21':'assert len(df)==3',
'P22':'assert Path("grafico.svg").exists()\nassert Path("grafico.png").exists()',
'P23':'assert len(pred)==len(yte)',
'P24':'assert len(grid.cv_results_["params"])==2\nassert grid.score(Xte,yte)>.8',
'P25':'assert decidir({"label":"POSITIVE","score":.8})=="POSITIVE"',
'P27':'assert abs(con_iva(100)-121)<1e-9',
'M10':'assert X.edad.isna().sum()==2\nassert len(X)==4 and len(y)==4',
'A12':'assert pd.isna(df.media2.iloc[0])\nassert df.media2.iloc[-1]==25',
'M02':'assert len(pred)==len(yte) and mean_absolute_error(yte,pred)>0',
'M03':'assert len(mod.predict(Xte))==len(yte)\nassert recall_score(yte,mod.predict(Xte))>.8',
'M04':'assert len(cross_val_score(model,X,y,cv=cv))==5',
'M05':'assert accuracy_score(yte,mod.predict(Xte))>.8',
'M06':'assert cross_val_score(model,X,y,cv=5).mean()>.8',
'M08':'assert abs(accuracy-2/3)<1e-9 and abs(recall-2/3)<1e-9',
'S08':'assert len(pd.read_csv("usuarios_fake.csv"))==10'
}
for q in bank:
    if q['id'] not in checks:continue
    with tempfile.TemporaryDirectory(prefix='niis-qa-') as folder:
        tmp=pathlib.Path(folder)
        if q['id']=='P17':
            (tmp/'datos').mkdir()
            for n in [1,2,3]:(tmp/f'datos/Q{n}.csv').write_text('producto,importe\nA,10\nB,20\n')
        code='from pathlib import Path\n'+q['solution']+'\n'+checks[q['id']]+'\n'
        (tmp/'exercise.py').write_text(code)
        result=subprocess.run([args.python,str(tmp/'exercise.py')],cwd=tmp,env={**os.environ,'MPLBACKEND':'Agg'},capture_output=True,text=True,timeout=40)
        if result.returncode:raise AssertionError(q['id']+'\n'+result.stderr)
        print('PASS',q['id'])
print(f'{len(checks)} soluciones ejecutadas con comprobaciones de resultado')
