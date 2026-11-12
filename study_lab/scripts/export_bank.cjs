const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const src=fs.readFileSync(path.join(root,'app.js'),'utf8').replace(/\ninit\(\);\s*$/,'');
vm.runInNewContext(src+'\nconsole.log(JSON.stringify(BANK));',{console,localStorage:{getItem:()=>null},document:{getElementById:()=>({})}});
