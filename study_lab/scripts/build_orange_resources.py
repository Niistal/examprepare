"""Rebuild optional Orange resources using an existing Orange environment and read-only academic checkout."""
import argparse,json,shutil
from pathlib import Path
from xml.etree.ElementTree import Element,SubElement,ElementTree
import Orange
from sklearn.datasets import load_diabetes,load_breast_cancer,load_wine
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--academic',type=Path,required=True);args=p.parse_args()
r=ROOT/'resources';r.mkdir(exist_ok=True)
# Public built-in datasets already used by the existing cases; no fabricated measurements.
for key,loader in [('diabetes',load_diabetes),('breast-cancer',load_breast_cancer),('wine',load_wine)]:
 d=loader();attrs=[Orange.data.ContinuousVariable(n) for n in d.feature_names]
 target=Orange.data.ContinuousVariable('target') if key=='diabetes' else Orange.data.DiscreteVariable('target',values=['maligno','benigno'] if key=='breast-cancer' else list(d.target_names))
 table=Orange.data.Table.from_numpy(Orange.data.Domain(attrs,target),d.data,d.target)
 table.save(str(r/f'orange-{key}.csv'))
Orange.data.Table('iris').save(str(r/'orange-iris.csv'))
# Original academic CSV; retain full rows unchanged.
source='04_Ikaskuntza_Automatikorako_Sistemak/1_Datuak_eta_Aurreprozesamendua/cr7_analisia/cr7_career_goals.csv'
shutil.copyfile(args.academic/source,r/'orange-cr7.csv')
(r/'orange-audit.csv').write_text('edad,ciudad,clase\n20,Bilbo,0\n,Bilbo,1\n40,,0\n200,Gasteiz,1\n',encoding='utf-8')
learners={'knn':('kNN','Orange.widgets.model.owknn.OWKNNLearner'),'logistic':('Logistic Regression','Orange.widgets.model.owlogisticregression.OWLogisticRegression'),'tree':('Tree','Orange.widgets.model.owtree.OWTreeLearner'),'forest':('Random Forest','Orange.widgets.model.owrandomforest.OWRandomForest'),'svm':('SVM','Orange.widgets.model.owsvm.OWSVM'),'linear':('Linear Regression','Orange.widgets.model.owlinearregression.OWLinearRegression')}
configs={'M01':('cr7',[]),'M02':('diabetes',['linear']),'M03':('breast-cancer',['logistic']),'M04':('wine',['knn','knn','knn']),'M05':('iris',['tree','forest']),'M06':('iris',['svm','svm']),'M09':('iris',['knn','logistic','tree']),'M10':('audit',[])}
manifest={}
for key,(dataset,models) in configs.items():
 scheme=Element('scheme',version='2.0',title=f'NIIS {key} · {dataset}',description='Selecciona el CSV asociado en File. Revisa Target y Features. Configura los hiperparámetros indicados en la guía antes de evaluar.')
 nodes=SubElement(scheme,'nodes');links=SubElement(scheme,'links')
 def node(name,q):
  i=len(nodes);SubElement(nodes,'node',id=str(i),name=name,qualified_name=q,project_name='Orange3',version='',title=name,position=str((100+i%4*240,100+i//4*190)));return i
 def link(a,out,b,inp):SubElement(links,'link',id=str(len(links)),source_node_id=str(a),source_channel=out,sink_node_id=str(b),sink_channel=inp,enabled='true')
 file=node('File','Orange.widgets.data.owfile.OWFile');select=node('Select Columns','Orange.widgets.data.owselectcolumns.OWSelectAttributes');table=node('Data Table','Orange.widgets.data.owtable.OWDataTable');link(file,'Data',select,'Data');link(select,'Data',table,'Data')
 if models:
  score=node('Test and Score','Orange.widgets.evaluate.owtestandscore.OWTestAndScore');link(select,'Data',score,'Data')
  prep=node('Preprocess','Orange.widgets.data.owpreprocess.OWPreprocess');link(prep,'Preprocessor',score,'Preprocessor')
  for model in models:
   name,qualified=learners[model];n=node(name,qualified);link(n,'Learner',score,'Learner')
  if key!='M02':
   matrix=node('Confusion Matrix','Orange.widgets.evaluate.owconfusionmatrix.OWConfusionMatrix');link(score,'Evaluation Results',matrix,'Evaluation Results')
 SubElement(scheme,'annotations');SubElement(scheme,'node_properties')
 path=r/f'orange-{key}.ows';ElementTree(scheme).write(path,encoding='utf-8',xml_declaration=True)
 manifest[key]={'csv':f'orange-{dataset}.csv','workflow':path.name,'dataset':dataset,'provenance':source if key=='M01' else 'Caso original '+key+'; dataset incorporado de scikit-learn/Orange' if key!='M10' else 'Datos sintéticos del caso M10; cuatro registros'}
(r/'orange-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for csv_path in r.glob('*.csv'):
    csv_path.write_text(csv_path.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
print('Recursos para',len(manifest),'prácticas, sin modificar el repositorio académico')
