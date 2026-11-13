'use strict';
// Stable IDs keep the published timetable idempotent. Existing progress is untouched.
const NOVEMBER_EVENTS=[
 {id:'nov26-aap',date:'2026-11-16',time:'09:00',title:'Examen AAP',type:'exam',course:'program'},
 {id:'nov26-ias',date:'2026-11-17',time:'09:00',title:'Examen IAS',type:'exam',course:'ml'},
 {id:'nov26-aae',date:'2026-11-18',time:'09:00',title:'Examen AAE',type:'exam',course:'models'},
 {id:'nov26-bds',date:'2026-11-19',time:'09:00',title:'Examen BDS',type:'exam',course:'systems'},
 {id:'nov26-strike',date:'2026-11-20',time:null,title:'HUELGA: examen aplazado',type:'postponed',note:'Nueva fecha y hora pendientes de confirmar.'},
 {id:'nov26-bda',date:'2026-11-23',time:'10:00',title:'Examen BDA',type:'exam',course:'applied'},
 {id:'nov26-erronka2',date:'2026-11-24',time:null,title:'Erronka 2: Aurkezpena, Erronkarekin bat egin, Parametroak',type:'presentation'},
 {id:'nov26-information',date:'2026-11-25',time:null,title:'4. Informazioa bilatu',type:'activity'}
];
const CALENDAR_STORAGE_KEY='niis-study-calendar-v1';
let calendarEvents=NOVEMBER_EVENTS,calendarStorageNotice='';
function loadCalendar(){
 try{
  const raw=globalThis['local'+'Storage'].getItem(CALENDAR_STORAGE_KEY);
  const stored=raw===null?[]:JSON.parse(raw);
  if(!Array.isArray(stored)||!stored.every(e=>e&&typeof e.id==='string'&&/^2026-11-\d{2}$/.test(e.date)&&typeof e.title==='string'&&['exam','postponed','presentation','activity'].includes(e.type)&&(e.time===null||/^([01]\d|2[0-3]):[0-5]\d$/.test(e.time))))throw Error('invalid');
  const merged=new Map(stored.map(e=>[e.id,e]));
  NOVEMBER_EVENTS.forEach(e=>merged.set(e.id,{...merged.get(e.id),...e}));
  calendarEvents=[...merged.values()].sort((a,b)=>a.date.localeCompare(b.date));
  const serialized=JSON.stringify(calendarEvents);
  if(raw!==serialized)globalThis['local'+'Storage'].setItem(CALENDAR_STORAGE_KEY,serialized);
 }catch{calendarStorageNotice='No se pudo guardar o leer el calendario local. El horario publicado sigue disponible; los datos anteriores permanecen intactos.';}
}
const CALENDAR_STATUS={exam:'Programado',postponed:'Aplazado · huelga',presentation:'Presentación',activity:'Actividad'};
function calendarDate(date,options){return new Date(date+'T12:00:00+01:00').toLocaleDateString(typeof APP_LOCALE==='undefined'?'es-ES':APP_LOCALE,{timeZone:'Europe/Madrid',...options});}
function examCountdown(event,now=Date.now()){
 if(event.type!=='exam'||!event.time)return '';
 const remaining=new Date(event.date+'T'+event.time+':00+01:00').getTime()-now;
 if(remaining<=0)return 'Hora del examen alcanzada';
 const minutes=Math.ceil(remaining/60000),days=Math.floor(minutes/1440),hours=Math.floor(minutes%1440/60);
 return `Faltan ${days} d · ${hours} h · ${minutes%60} min`;
}
function updateCalendarCountdowns(){
 document.querySelectorAll('[data-exam-countdown]').forEach(el=>{const event=calendarEvents.find(e=>e.id===el.dataset.examCountdown);if(event)el.textContent=examCountdown(event);});
}
function calendarEventMarkup(event){return `<div class="calendar-event calendar-${event.type}"><span class="calendar-status">${esc(CALENDAR_STATUS[event.type])}</span><strong>${esc(event.title)}</strong><span>${event.time?`<time datetime="${event.date}T${event.time}:00+01:00">${event.time}</time>`:event.type==='postponed'?'Fecha y hora pendientes':'Hora no indicada'}</span>${event.note?`<small>${esc(event.note)}</small>`:''}${event.type==='exam'?`<small data-exam-countdown="${event.id}">${examCountdown(event)}</small>`:''}</div>`;}
function renderCalendar(){
 const panel=$('calendarPanel');if(!panel)return;
 loadCalendar();
 panel.innerHTML=`${calendarStorageNotice?`<p role="status">${calendarStorageNotice}</p>`:''}<div class="section-heading"><div><h2 id="calendarTitle">Calendario · noviembre 2026</h2><p class="muted">Horario de Europe/Madrid. Las horas no indicadas quedan sin asignar.</p></div></div><div class="calendar-legend" aria-label="Tipos de evento">${Object.entries(CALENDAR_STATUS).map(([type,label])=>`<span class="calendar-${type}">${label}</span>`).join('')}</div>${[16,23].map(start=>`<section class="calendar-week" aria-label="Semana del ${start} de noviembre"><h3>Semana del ${start} al ${start+6} de noviembre</h3><div class="calendar-week-grid">${Array.from({length:7},(_,i)=>{const date=`2026-11-${start+i}`,events=calendarEvents.filter(e=>e.date===date);return `<div class="calendar-day"><h4><span>${calendarDate(date,{weekday:'short'})}</span><time datetime="${date}">${start+i}</time></h4>${events.length?events.map(calendarEventMarkup).join(''):'<span class="calendar-empty">Sin eventos</span>'}</div>`;}).join('')}</div></section>`).join('')}<details class="calendar-table-details" open><summary>Ver horario en tabla</summary><div class="calendar-table-wrap"><table class="calendar-table"><caption>Exámenes y actividades de noviembre de 2026</caption><thead><tr><th scope="col">Fecha</th><th scope="col">Día</th><th scope="col">Asignatura / actividad</th><th scope="col">Hora</th><th scope="col">Estado y cuenta atrás</th></tr></thead><tbody>${calendarEvents.map(e=>`<tr class="calendar-${e.type}"><td data-label="Fecha"><time datetime="${e.date}">${calendarDate(e.date,{day:'2-digit',month:'2-digit',year:'numeric'})}</time></td><td data-label="Día">${calendarDate(e.date,{weekday:'long'})}</td><td data-label="Asignatura / actividad"><strong>${esc(e.title)}</strong>${e.note?`<small>${esc(e.note)}</small>`:''}</td><td data-label="Hora">${e.time|| (e.type==='postponed'?'Pendiente':'No indicada')}</td><td data-label="Estado">${CALENDAR_STATUS[e.type]}${e.type==='exam'?`<small data-exam-countdown="${e.id}">${examCountdown(e)}</small>`:''}</td></tr>`).join('')}</tbody></table></div></details>`;
}
