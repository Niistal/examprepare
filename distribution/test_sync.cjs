const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const original={ratings:{},answers:{},history:[]};
function setup(fetch){
 const handlers={},label={textContent:''};
 const context=vm.createContext({CLOUD_BOOTSTRAP:{state:original,revision:0,csrf:'test',username:'student'},fetch,document:{getElementById:()=>label},window:{addEventListener:(name,fn)=>handlers[name]=fn},setTimeout:()=>1,clearTimeout(){}});
 vm.runInContext(fs.readFileSync(__dirname+'/sync.js','utf8'),context);
 return {store:vm.runInContext('cloudStorage',context),handlers,label};
}
const state=JSON.stringify({...original,answers:{P35:'my unsaved answer'}});
const response=(status,body)=>({status,ok:status>=200&&status<300,json:async()=>body});
(async()=>{
 let calls=0;
 const success=setup(async()=>{calls++;return response(200,{revision:calls});});
 success.store.setItem('key',state);assert(await success.store.flush());assert.equal(calls,1);
 assert.equal(success.label.textContent,'Progreso guardado en tu cuenta');
 assert(await success.store.flush());assert.equal(calls,1);console.log('PASS no duplicate writes after success');
 let phase=0;
 const lost=setup(async()=>{phase++;if(phase===1)throw Error('offline');if(phase===2)return response(409,{});return response(200,{revision:1,state:JSON.parse(state)});});
 lost.store.setItem('key',state);assert.equal(await lost.store.flush(),false);assert.equal(lost.store.getItem('key'),state);
 let warned=false;lost.handlers.beforeunload({preventDefault(){warned=true;}});assert(warned);
 assert(await lost.store.flush());assert.equal(phase,3);console.log('PASS retained pending state and reconciled a lost response without duplicate commit');
 let count=0;
 const conflict=setup(async()=>{count++;return count===1?response(409,{}):response(200,{revision:1,state:original});});
 conflict.store.setItem('key',state);assert.equal(await conflict.store.flush(),false);assert.equal(conflict.store.getItem('key'),state);
 assert(conflict.label.textContent.includes('Conflicto'));assert.equal(await conflict.store.flush(),false);assert.equal(count,2);console.log('PASS conflict preserves pending answers and blocks overwrites');
})().catch(e=>{console.error(e);process.exitCode=1;});
