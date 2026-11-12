"""Real external-tool integration on disposable Docker containers, using installed images only.
Never starts/stops existing containers, mounts user paths, pulls images or reads user credentials.
"""
import argparse
import concurrent.futures
import json
import secrets
import ssl
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

LABEL='niis.study.qa'
IMAGES={'elastic':'docker.elastic.co/elasticsearch/elasticsearch:9.5.4','kibana':'docker.elastic.co/kibana/kibana:9.5.4','kafka':'apache/kafka:latest','nifi':'apache/nifi:2.12.0'}

def docker(*args,input=None,timeout=45,check=True):
    result=subprocess.run(['docker',*args],input=input,text=True,capture_output=True,timeout=timeout)
    if check and result.returncode:raise RuntimeError('Docker command failed: '+str(args[:3])+': '+result.stderr[-1200:])
    return result

def http(url,method='GET',body=None,headers=None,raw=False):
    payload=body if isinstance(body,bytes) else json.dumps(body).encode() if body is not None else None
    request=urllib.request.Request(url,method=method,data=payload,headers={'Content-Type':'application/json',**(headers or {})})
    # Only this test's own loopback NiFi uses a temporary self-signed certificate.
    context=ssl._create_unverified_context() if url.startswith('https://127.0.0.1:') else None
    try:response=urllib.request.urlopen(request,timeout=15,context=context)
    except urllib.error.HTTPError as error:response=error
    with response:
        data=response.read();status=response.status
    if raw:return status,data.decode()
    try:return status,json.loads(data)
    except ValueError:return status,{'text':data.decode()[:200]}

def wait_for(label,fn,timeout=240):
    deadline=time.monotonic()+timeout;last=None
    while time.monotonic()<deadline:
        try:
            result=fn()
            if result:return result
        except (OSError,ValueError,RuntimeError,AssertionError) as error:last=type(error).__name__
        time.sleep(1)
    raise AssertionError(label+' timed out'+(' ('+str(last)+')' if last else ''))

class Lab:
    def __init__(self):
        self.prefix='niis-study-qa-'+secrets.token_hex(4);self.containers=[];self.network=False;self.urls={};self.password=secrets.token_urlsafe(24)
    def start(self,services):
        for image in [IMAGES[k] for k in services]:docker('image','inspect',image)
        docker('network','create','--opt','com.docker.network.bridge.host_binding_ipv4=127.0.0.1','--label',LABEL+'='+self.prefix,self.prefix);self.network=True
        common={'elastic':(9200,'1536m',{'discovery.type':'single-node','xpack.security.enabled':'false','ES_JAVA_OPTS':'-Xms512m -Xmx512m'}),'kibana':(5601,'1536m',{'ELASTICSEARCH_HOSTS':'http://'+self.prefix+'-elastic:9200','SERVER_HOST':'0.0.0.0','XPACK_SECURITY_ENABLED':'false','TELEMETRY_ENABLED':'false','NODE_OPTIONS':'--max-old-space-size=768'}),'kafka':(9092,'1024m',{'KAFKA_NODE_ID':'1','KAFKA_PROCESS_ROLES':'broker,controller','KAFKA_LISTENERS':'PLAINTEXT://:9092,CONTROLLER://:9093','KAFKA_ADVERTISED_LISTENERS':'PLAINTEXT://localhost:9092','KAFKA_CONTROLLER_LISTENER_NAMES':'CONTROLLER','KAFKA_LISTENER_SECURITY_PROTOCOL_MAP':'CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT','KAFKA_CONTROLLER_QUORUM_VOTERS':'1@localhost:9093','KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR':'1','KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR':'1','KAFKA_TRANSACTION_STATE_LOG_MIN_ISR':'1','KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS':'0','KAFKA_HEAP_OPTS':'-Xms256m -Xmx256m'}),'nifi':(8443,'2048m',{'SINGLE_USER_CREDENTIALS_USERNAME':'study-qa','SINGLE_USER_CREDENTIALS_PASSWORD':self.password,'NIFI_WEB_HTTPS_PORT':'8443','NIFI_WEB_PROXY_HOST':'localhost:8443,127.0.0.1:8443','NIFI_JVM_HEAP_INIT':'256m','NIFI_JVM_HEAP_MAX':'768m','NIFI_SENSITIVE_PROPS_KEY':secrets.token_urlsafe(24)})}
        for key,(port,memory,env) in common.items():
            if key not in services:continue
            name=self.prefix+'-'+key
            # Credentials go over stdin, never in the tool call, logs, files or command arguments.
            docker('run','-d','--pull=never','--name',name,'--label',LABEL+'='+self.prefix,'--network',self.prefix,'--memory',memory,'--cpus','2','-p',f'127.0.0.1::{port}','--env-file','/dev/stdin',IMAGES[key],input='\n'.join(k+'='+v for k,v in env.items())+'\n')
            self.containers.append(name)
            info=json.loads(docker('inspect',name).stdout)[0]
            bindings=info['NetworkSettings']['Ports'].get(str(port)+'/tcp')
            if not bindings:
                details=docker('logs','--tail','20',name,check=False).stderr if key!='nifi' else 'NiFi startup failed'
                raise RuntimeError(key+' has no published port; state='+str(info['State']['Status'])+'; '+details[-1800:])
            binding=bindings[0]
            self.urls[key]=('https' if key=='nifi' else 'http')+'://127.0.0.1:'+binding['HostPort']
        print('START isolated Docker lab; all published ports bound to 127.0.0.1',flush=True)
    def cleanup(self):
        for name in reversed(self.containers):
            info=json.loads(docker('inspect',name,check=False).stdout or '[]')
            if info and info[0]['Config']['Labels'].get(LABEL)==self.prefix:docker('rm','-f','-v',name,check=False)
        if self.network:docker('network','rm',self.prefix,check=False)
        print('CLEANUP disposable containers/network removed; existing containers unchanged',flush=True)
    def elastic(self):
        base=self.urls['elastic'];wait_for('Elasticsearch',lambda:http(base)[0]==200)
        index='/niis-study-products'
        status,_=http(base+index,'PUT',{'mappings':{'properties':{'nombre':{'type':'text','fields':{'raw':{'type':'keyword'}}},'categoria':{'type':'keyword'},'precio':{'type':'double'}}}});assert status==200
        for i,(category,price) in enumerate([('A',10),('A',20),('B',5)]):assert http(base+index+'/_doc/'+str(i),'PUT',{'nombre':'Producto '+str(i),'categoria':category,'precio':price})[0]==201
        assert http(base+index+'/_refresh','POST')[0]==200
        status,result=http(base+index+'/_search','POST',{'query':{'range':{'precio':{'gte':10}}}});assert status==200 and result['hits']['total']['value']==2
        status,result=http(base+index+'/_search','POST',{'size':0,'aggs':{'categorias':{'terms':{'field':'categoria'},'aggs':{'ventas':{'sum':{'field':'precio'}}}}}});assert status==200
        assert {b['key']:b['ventas']['value'] for b in result['aggregations']['categorias']['buckets']}=={'A':30,'B':5}
        assert http(base+index+'/_doc/bad','PUT',{'precio':'not-a-number'})[0]==400
        print('PASS Elasticsearch: mapping, indexing, Query DSL, aggregations and invalid numeric value',flush=True)
        return {'version':http(base)[1]['version']['number'],'checks':5}
    def kibana(self):
        base=self.urls['kibana'];wait_for('Kibana',lambda:http(base+'/api/status')[0]==200,timeout=300)
        status,result=http(base+'/api/status');assert result['status']['overall']['level']=='available'
        headers={'kbn-xsrf':'study-qa'}
        status,view=http(base+'/api/data_views/data_view','POST',{'data_view':{'title':'niis-study-products','name':'Study QA'}},headers);assert status==200,(status,view)
        ident=view['data_view']['id'];status,loaded=http(base+'/api/data_views/data_view/'+ident);assert status==200 and loaded['data_view']['title']=='niis-study-products'
        # Exercise Kibana's real KQL parser/compiler from the installed distribution.
        expression="const {fromKueryExpression,toElasticsearchQuery}=require('@kbn/es-query');const q=toElasticsearchQuery(fromKueryExpression('categoria: A and precio >= 10'));console.log(JSON.stringify(q));"
        converted=docker('exec',self.prefix+'-kibana','/usr/share/kibana/node/glibc-217/bin/node','-e',expression,timeout=30)
        query=json.loads(converted.stdout);wait_for('Kibana data',lambda:http(self.urls['elastic']+'/niis-study-products/_count','POST',{'query':query})[1].get('count')==2)
        assert http(base+'/api/data_views/data_view/'+ident,'DELETE',headers=headers)[0]==200
        print('PASS Kibana: real API status, data view round-trip, KQL compiled and executed in Elasticsearch',flush=True)
        return {'image':IMAGES['kibana'],'checks':4}
    def kafka(self):
        name=self.prefix+'-kafka';bin='/opt/kafka/bin/'
        def run(command,*args,**kw):return docker('exec',name,bin+command,*args,**kw)
        wait_for('Kafka',lambda:run('kafka-topics.sh','--bootstrap-server','localhost:9092','--list',timeout=15,check=False).returncode==0)
        run('kafka-topics.sh','--bootstrap-server','localhost:9092','--create','--topic','niis-study-qa','--partitions','2','--replication-factor','1')
        messages=[json.dumps({'sensor':i,'valor':10*i},separators=(',',':')) for i in range(3)]
        docker('exec','-i',name,bin+'kafka-console-producer.sh','--bootstrap-server','localhost:9092','--topic','niis-study-qa',input='\n'.join(messages)+'\n')
        result=run('kafka-console-consumer.sh','--bootstrap-server','localhost:9092','--topic','niis-study-qa','--from-beginning','--group','niis-study-qa-group','--max-messages','3','--timeout-ms','15000',timeout=25)
        assert sorted(result.stdout.splitlines())==sorted(messages)
        description=run('kafka-consumer-groups.sh','--bootstrap-server','localhost:9092','--describe','--group','niis-study-qa-group').stdout
        rows=[line.split() for line in description.splitlines() if line.startswith('niis-study-qa-group')]
        assert len(rows)==2 and sum(int(row[3]) for row in rows)==3 and all(row[3]==row[4] for row in rows),description
        empty=run('kafka-console-consumer.sh','--bootstrap-server','localhost:9092','--topic','niis-study-qa','--group','niis-study-qa-group','--max-messages','1','--timeout-ms','3000',check=False,timeout=15)
        assert not empty.stdout.strip(),'group reread already committed messages'
        print('PASS Kafka: topic, two partitions, producer/consumer JSON, committed offsets and resume without rereading',flush=True)
        run('kafka-topics.sh','--bootstrap-server','localhost:9092','--create','--topic','niis-connect-qa','--partitions','1','--replication-factor','1')
        docker('exec',name,'sh','-c','mkdir -p /tmp/niis-connect-plugins && cp /opt/kafka/libs/connect-file-*.jar /tmp/niis-connect-plugins/')
        files={
          'worker.properties':'bootstrap.servers=localhost:9092\nkey.converter=org.apache.kafka.connect.storage.StringConverter\nvalue.converter=org.apache.kafka.connect.storage.StringConverter\noffset.storage.file.filename=/tmp/niis-connect-offsets\noffset.flush.interval.ms=100\nplugin.path=/tmp/niis-connect-plugins\nlisteners=http://127.0.0.1:8083\n',
          'source.properties':'name=niis-source\nconnector.class=org.apache.kafka.connect.file.FileStreamSourceConnector\ntasks.max=1\nfile=/tmp/niis-connect-input.txt\ntopic=niis-connect-qa\n',
          'sink.properties':'name=niis-sink\nconnector.class=org.apache.kafka.connect.file.FileStreamSinkConnector\ntasks.max=1\nfile=/tmp/niis-connect-output.txt\ntopics=niis-connect-qa\n',
          'niis-connect-input.txt':'niis-one\nniis-two\n'}
        for filename,text in files.items():docker('exec','-i',name,'sh','-c','cat > /tmp/'+filename,input=text)
        docker('exec','-d',name,'sh','-c','exec /opt/kafka/bin/connect-standalone.sh /tmp/worker.properties /tmp/source.properties /tmp/sink.properties > /tmp/niis-connect-worker.log 2>&1')
        wait_for('Kafka Connect source/topic/sink',lambda:docker('exec',name,'cat','/tmp/niis-connect-output.txt',check=False).stdout=='niis-one\nniis-two\n',timeout=90)
        print('PASS Kafka Connect: real FileStream source → topic → FileStream sink, exact output',flush=True)
        return {'checks':6,'records':3,'connect':'FileStream source/sink; JDBC/MongoDB plugins are not substituted'}
    def nifi(self):
        base=self.urls['nifi']+'/nifi-api';headers={'Host':'localhost:8443'}
        def access():
            payload=urllib.parse.urlencode({'username':'study-qa','password':self.password}).encode()
            status,token=http(base+'/access/token','POST',payload,{**headers,'Content-Type':'application/x-www-form-urlencoded'},raw=True)
            return token if status in (200,201) else None
        token=wait_for('NiFi',access,timeout=300);headers['Authorization']='Bearer '+token
        def api(path,method='GET',body=None):
            status,value=http(base+path,method,body,headers);assert 200<=status<300,(path,status,str(value)[:600]);return value
        root=api('/flow/process-groups/root')['processGroupFlow']['id']
        group=api('/process-groups/'+root+'/process-groups','POST',{'revision':{'version':0},'component':{'name':'NIIS disposable GetFile PutFile'}})['id']
        docker('exec',self.prefix+'-nifi','mkdir','-p','/tmp/niis-study-in','/tmp/niis-study-out')
        def processor(typ,props,auto):
            return api('/process-groups/'+group+'/processors','POST',{'revision':{'version':0},'component':{'type':'org.apache.nifi.processors.standard.'+typ,'name':typ,'config':{'properties':props,'autoTerminatedRelationships':auto,'schedulingPeriod':'1 sec'}}})['id']
        get=processor('GetFile',{'Input Directory':'/tmp/niis-study-in','Keep Source File':'false'},[])
        put=processor('PutFile',{'Directory':'/tmp/niis-study-out','Conflict Resolution Strategy':'fail'},['success','failure'])
        api('/process-groups/'+group+'/connections','POST',{'revision':{'version':0},'component':{'name':'success','source':{'id':get,'groupId':group,'type':'PROCESSOR'},'destination':{'id':put,'groupId':group,'type':'PROCESSOR'},'selectedRelationships':['success'],'backPressureObjectThreshold':10,'backPressureDataSizeThreshold':'1 MB'}})
        for ident in [put,get]:
            wait_for('NiFi processor validation',lambda:api('/processors/'+ident)['component']['validationStatus']=='VALID')
            entity=api('/processors/'+ident);api('/processors/'+ident+'/run-status','PUT',{'revision':entity['revision'],'state':'RUNNING'})
        sample='producto,importe\nA,10\nB,20\n'
        docker('exec','-i',self.prefix+'-nifi','sh','-c','cat > /tmp/niis-study-in/ventas.csv',input=sample)
        def output():return docker('exec',self.prefix+'-nifi','cat','/tmp/niis-study-out/ventas.csv',check=False).stdout==sample
        wait_for('NiFi file output',output,timeout=90)
        # Search real provenance generated by the processors, not a synthesized trace.
        def provenance():
            value=api('/provenance','POST',{'provenance':{'request':{'maxResults':20,'searchTerms':{}}}})
            ident=value['provenance']['id'];result=wait_for('NiFi provenance query',lambda:(lambda v:v if v['provenance']['finished'] else None)(api('/provenance/'+ident)),timeout=30)
            events=result['provenance']['results']['provenanceEvents'];api('/provenance/'+ident,'DELETE')
            return events if any(e.get('componentId') in [get,put] for e in events) else None
        events=wait_for('NiFi provenance persisted',provenance,timeout=60)
        for ident in [get,put]:
            entity=api('/processors/'+ident);api('/processors/'+ident+'/run-status','PUT',{'revision':entity['revision'],'state':'STOPPED'})
        print('PASS NiFi: authenticated API, GetFile → PutFile, exact CSV output, relationships/backpressure and real provenance',flush=True)
        return {'checks':5,'provenanceEvents':len(events)}

def logstash(lab):
    image='docker.elastic.co/logstash/logstash:9.5.4';docker('image','inspect',image)
    name=lab.prefix+'-logstash';lab.containers.append(name)
    pipeline='input { stdin { codec => json_lines } } filter { grok { match => { "message" => "%{TIMESTAMP_ISO8601:fecha} %{LOGLEVEL:nivel} importe=%{NUMBER:importe}" } } date { match => ["fecha", "ISO8601"] } mutate { convert => { "importe" => "float" } } } output { stdout { codec => json_lines } }'
    result=docker('run','--rm','-i','--pull=never','--name',name,'--label',LABEL+'='+lab.prefix,'--network','none','--memory','1024m','--cpus','2','-e','LS_JAVA_OPTS=-Xms256m -Xmx256m','-e','XPACK_MONITORING_ENABLED=false',image,'--log.level','error','--pipeline.workers','1','--pipeline.batch.size','1','-e',pipeline,input=json.dumps({'message':'2026-11-12T10:00:00Z INFO importe=12.5'})+'\n',timeout=90)
    events=[]
    for line in result.stdout.splitlines():
        try:events.append(json.loads(line))
        except ValueError:pass
    assert any(e.get('importe')==12.5 and e.get('nivel')=='INFO' and e.get('@timestamp','').startswith('2026-11-12T10:00:00') for e in events), 'Logstash did not emit the transformed event'
    print('PASS Logstash: real JSON input, grok, date, mutate and JSON output',flush=True)
    return {'checks':4,'image':image}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--services',nargs='+',choices=['elasticsearch','kibana','kafka','nifi','logstash'],default=['elasticsearch','kibana','kafka','nifi','logstash'])
    args=parser.parse_args();lab=Lab();report={}
    selected=set(args.services)
    if 'kibana' in selected:selected.add('elasticsearch')
    containers=[k for k in IMAGES if k in selected or k=='elastic' and ('elasticsearch' in selected or 'kibana' in selected)]
    try:
        lab.start(containers)
        methods={'elasticsearch':lab.elastic,'kibana':lab.kibana,'kafka':lab.kafka,'nifi':lab.nifi,'logstash':lambda:logstash(lab)}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            jobs={pool.submit(methods[name]):name for name in methods if name in selected}
            for future in concurrent.futures.as_completed(jobs):
                name=jobs[future]
                try:report[name]={'status':'PASS',**future.result()}
                except Exception as error:
                    import traceback
                    where=[(Path(f.filename).name,f.lineno) for f in traceback.extract_tb(error.__traceback__)]
                    report[name]={'status':'FAIL','error':str(error)[:1500],'where':where};print('FAIL',name,str(error)[:1500],where,flush=True)
        target=Path(__file__).with_name('qa-artifacts')/'external-docker.json';target.parent.mkdir(exist_ok=True)
        previous=json.loads(target.read_text()) if target.exists() else {}
        target.write_text(json.dumps({**previous,**report},indent=2)+'\n')
        assert all(r['status']=='PASS' for r in report.values()),'External integration failures: '+', '.join(k for k,v in report.items() if v['status']!='PASS')
    finally:lab.cleanup()
if __name__=='__main__':main()
