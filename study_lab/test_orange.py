"""Optional integration test: run with an existing Orange Python, no installation."""
import os,tempfile,atexit,time
profile=tempfile.TemporaryDirectory(prefix='niis-orange-widgets-')
atexit.register(profile.cleanup)
os.environ['QT_QPA_PLATFORM']='offscreen'
for key,folder in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data')]:os.environ[key]=profile.name+'/'+folder
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
from orangewidget.workflow.widgetsscheme import WidgetsScheme
widget_scheme=WidgetsScheme();widget_scheme.load_from(str(root/'resources/orange-M09.ows'),registry=registry)
widgets=[widget_scheme.widget_for_node(node) for node in widget_scheme.nodes]
file_widget=widgets[0];file_widget.add_path(str(root/'resources/orange-iris.csv'));file_widget.load_data()
assert len(file_widget.data)==150
score=widgets[3];deadline=time.monotonic()+40
while time.monotonic()<deadline:
 app.processEvents()
 if len(score.learners)==3 and all(slot.results is not None and slot.results.success for slot in score.learners.values()):break
 time.sleep(.05)
assert len(score.learners)==3 and all(slot.results is not None and slot.results.success for slot in score.learners.values())
print('PASS real GUI widget chain: File → Select Columns → Test & Score, three learner results')
widget_scheme.clear();app.processEvents()
print('LIMIT: rendering uses Qt offscreen; native Windows desktop is not tested')
