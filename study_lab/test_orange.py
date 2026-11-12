"""Optional integration test: run with an existing Orange Python, no installation."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import Orange
from AnyQt.QtWidgets import QApplication
from Orange.canvas import config
from orangecanvas.registry import WidgetRegistry
from orangecanvas.scheme import Scheme
root=Path(__file__).resolve().parent
app=QApplication([])
registry=WidgetRegistry();discovery=config.Config.widget_discovery(registry);discovery.run(config.Config.widgets_entry_points())
scheme=Scheme();scheme.load_from(str(root/'resources/orange-classification.ows'),registry=registry)
assert len(scheme.nodes)==9 and len(scheme.links)==8
import json
for key, resource in json.loads((root/'resources/orange-manifest.json').read_text()).items():
    case=Scheme();case.load_from(str(root/'resources'/resource['workflow']),registry=registry)
    assert len(case.nodes)>=3
    assert (root/'resources'/resource['csv']).is_file()
    print('PASS workflow específico',key,len(case.nodes),'widgets')
print('PASS Orange',Orange.__version__,'workflow: nueve widgets y ocho conexiones compatibles')
data=Orange.data.Table(str(root/'resources/orange-iris.csv'))
assert len(data)==150 and data.domain.class_var.is_discrete and len(data.domain.attributes)==4
learners=[Orange.classification.KNNLearner(n_neighbors=5),Orange.classification.LogisticRegressionLearner(max_iter=1000,preprocessors=[Orange.preprocess.Normalize()]),Orange.classification.TreeLearner()]
# Exercise real installed Orange learners and evaluation, not a mocked accuracy.
result=Orange.evaluation.CrossValidation(k=5,stratified=True,random_state=42)(data,learners)
for score in [Orange.evaluation.CA(result),Orange.evaluation.F1(result,average='macro')]:
 assert len(score)==3 and all(0<=s<=1 for s in score)
print('PASS CSV 150 filas, tres learners y CV real: CA',Orange.evaluation.CA(result))
print('LIMIT: GUI interactiva y apertura en escritorio Windows no verificadas por esta prueba offscreen')
