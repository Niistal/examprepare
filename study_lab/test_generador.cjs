// Test offline, sin npm: node test_generador.cjs
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
let src=fs.readFileSync(path.join(__dirname,'app.js'),'utf8');
src=src.replace(/\ninit\(\);\s*$/,'\n');
src+=`
for (const subject of COURSES) {
  const samples = new Set();
  for (let i=1;i<=1000;i++) {
    const ids = questionsFor(subject.id,i);
    if(ids.join('/')!==questionsFor(subject.id,i).join('/'))throw Error('No determinista');
    if(ids.length!==5 || new Set(ids).size!==5) throw Error('Repetición dentro del examen: '+subject.id+'/'+i);
    samples.add(ids.join('/'));
  }
  if(samples.size!==1000) throw Error('Colisión entre exámenes: '+subject.id+' ('+samples.size+')');
  console.log('OK',subject.name,byCourse(subject.id).length,'ejercicios, 1000 secuencias diferentes');
}
for(const c of COURSES){const route=STUDY_ROUTES[c.id].flatMap(x=>x[1]);if(new Set(route).size!==route.length||route.length!==byCourse(c.id).length||route.some(id=>!byCourse(c.id).some(q=>q.id===id)))throw Error('Recorrido incompleto: '+c.id);}
console.log('BANCO',BANK.length,'ejercicios y recorridos completos');
`;
vm.runInNewContext(src,{console,localStorage:{getItem:()=>null},document:{getElementById:()=>({})}});
