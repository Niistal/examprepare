'use strict';
// UI language is a browser preference, separate from local or account progress.
const APP_LOCALE=(()=>{try{const cookie=document.cookie.match(/(?:^|;\s*)study_language=(eu|es-ES)(?:;|$)/);if(cookie)return cookie[1];return globalThis['local'+'Storage'].getItem('niis-study-language')==='es-ES'?'es-ES':'eu';}catch{return 'eu';}})();
const EUSKARA_EDUCATIONAL={};
function collectEducationalTranslations(original,localized){
 if(typeof original==='string'&&typeof localized==='string'&&original!==localized)EUSKARA_EDUCATIONAL[original]=localized;
 else if(original&&localized&&typeof original==='object'&&typeof localized==='object')for(const key of Object.keys(original))collectEducationalTranslations(original[key],localized[key]);
}
if(typeof LEARNING_CONTENT!=='undefined')collectEducationalTranslations(LEARNING_CONTENT,EUSKARA_LEARNING);
const I18N_EXCLUDED='script,style,pre,code,textarea,input,[contenteditable="true"],[data-i18n-skip],#readerBody,#readerTOC,#readerPath,.account-name,.account-avatar,.account-menu-panel>strong,#recoveryCode';
const I18N_ATTRIBUTE_EXCLUDED='script,style,pre,code,[data-i18n-skip],#readerBody,#readerTOC,#readerPath,.account-name,.account-avatar,.account-menu-panel>strong,#recoveryCode';
const i18nPatterns=Object.entries(EUSKARA_UI).filter(([key])=>/\{\d+\}/.test(key)).map(([source,target])=>{
 const keys=[];
 const escaped=source.replace(/[.*+?^${}()|[\]\\]/g,'\\$&').replace(/\\\{(\d+)\\\}/g,(_,id)=>{keys.push(id);return '(.+)';});
 return {regex:new RegExp('^'+escaped+'$','s'),keys,target,source,specificity:source.replace(/\{\d+\}/g,'').length};
}).sort((a,b)=>b.specificity-a.specificity);
function translateText(value,depth=0){
 if(APP_LOCALE==='es-ES'||typeof value!=='string'||depth>6)return value;
 const key=value.trim();if(!key)return value;
 let translated=EUSKARA_UI[key]??EUSKARA_CASES[key]??EUSKARA_EDUCATIONAL[key];
 if(translated===undefined)for(const pattern of i18nPatterns){
  const match=key.match(pattern.regex);if(!match)continue;
  translated=pattern.target.replace(/\{(\d+)\}/g,(_,id)=>{
   const captured=match[pattern.keys.indexOf(id)+1]??'';
   // Account identity and recovery values are literal, never translated.
   return captured.length<key.length&&!/^(Cuenta de |Guárdalo en un lugar privado)/.test(pattern.source)?translateText(captured,depth+1):captured;
  });break;
 }
 if(translated===undefined){
  // Renderers combine independently translated content and UI labels. Translate
  // exact phrases at those boundaries without replacing individual words.
  const pieces=key.split(/( · |\n+|(?<=\.)\s+(?=[A-ZÁÉÍÓÚ]))/u);
  if(pieces.length>1){const mapped=pieces.map(piece=>piece.trim()&&piece.trim()!==key?translateText(piece,depth+1):piece).join('');if(mapped!==key)translated=mapped;}
 }
 return translated===undefined?value:value.slice(0,value.indexOf(key))+translated+value.slice(value.indexOf(key)+key.length);
}
function translateContent(value){
 if(typeof value==='string')return EUSKARA_CASES[value]??EUSKARA_UI[value]??value;
 if(Array.isArray(value)){for(let i=0;i<value.length;i++)value[i]=translateContent(value[i]);}
 else if(value&&typeof value==='object')for(const key of Object.keys(value)){
  // Never rewrite executable code, source provenance, stable IDs or answer keys.
  if(['id','c','course','source','source_path','source_section','source_sha256','source_git_blob','starter','dataset','dataset_name','folder','path','commit','modality','type','kind','version','answer','authorship','difficultyEvidence'].includes(key))continue;
  if(key==='solution'&&/\b(import |from \w+ import|def |class |SELECT |GET |POST |docker |print\(|pd\.|np\.)/.test(value[key]))continue;
  value[key]=translateContent(value[key]);
 }
 return value;
}
function translateElement(element){
 if(!element||element.nodeType!==1||element.closest(I18N_ATTRIBUTE_EXCLUDED))return;
 for(const attr of ['aria-label','title','placeholder','data-label'])if(element.hasAttribute(attr)){
  const original=element.getAttribute(attr),translated=translateText(original);if(original!==translated)element.setAttribute(attr,translated);
 }
}
function translateNode(node){
 if(APP_LOCALE==='es-ES')return;
 if(node.nodeType===3){
  const parent=node.parentElement;if(!parent||parent.closest(I18N_EXCLUDED))return;
  const translated=translateText(node.nodeValue);
  if(translated!==node.nodeValue){if(parent.tagName==='OPTION'&&!parent.hasAttribute('value'))parent.value=parent.value;node.nodeValue=translated;}
 }else if(node.nodeType===1||node.nodeType===9){
  translateElement(node);
  const walker=document.createTreeWalker(node,NodeFilter.SHOW_ELEMENT|NodeFilter.SHOW_TEXT);
  let child;while((child=walker.nextNode())){if(child.nodeType===3)translateNode(child);else translateElement(child);}
 }
}
async function changeLanguage(language){
 const selector=document.getElementById('languageSelect');
 if(!['eu','es-ES'].includes(language)||language===APP_LOCALE)return;
 if(typeof persistDraft==='function'){
  persistDraft();
  if(!storageOkay){if(selector)selector.value=APP_LOCALE;return;}
 }
 // Hosted progress must finish saving before a reload changes language.
 if(typeof cloudStorage!=='undefined'&&typeof cloudStorage.flush==='function'&&!await cloudStorage.flush()){
  if(selector)selector.value=APP_LOCALE;return;
 }
 try{globalThis['local'+'Storage'].setItem('niis-study-language',language);}catch{}
 try{document.cookie='study_language='+language+'; Path=/; Max-Age=31536000; SameSite=Strict'+(location.protocol==='https:'?'; Secure':'');}
 catch{if(selector)selector.value=APP_LOCALE;return;}
 location.reload();
}
function bootLocale(){
 document.documentElement.lang=APP_LOCALE;
 // A language switch must not change the grade of an already answered term.
 if(typeof LEARNING_CONTENT!=='undefined')for(const question of LEARNING_CONTENT.questions.filter(q=>q.type==='term')){
  const localized=EUSKARA_LEARNING.questions.find(q=>q.id===question.id);if(localized)question.answer=[...new Set([...question.answer,...localized.answer])];
 }
 if(APP_LOCALE==='eu'){
  if(typeof LEARNING_CONTENT!=='undefined')Object.assign(LEARNING_CONTENT,structuredClone(EUSKARA_LEARNING));
  if(typeof BANK!=='undefined'){
   translateContent(BANK);translateContent(COURSES);translateContent(PROGRAM_GUIDE);translateContent(STUDY_LESSONS);translateContent(STUDY_ROUTES);translateContent(LEVEL_NAMES);translateContent(STUDY_METHODS);translateContent(DIFFICULTY_LESSONS);
   if(typeof ORANGE_CASE_GUIDES!=='undefined')translateContent(ORANGE_CASE_GUIDES);
   if(typeof THEORY_CASE_GUIDES!=='undefined')translateContent(THEORY_CASE_GUIDES);
   if(typeof CASE_THEORY_FEEDBACK!=='undefined')translateContent(CASE_THEORY_FEEDBACK);
  }
  const originalConfirm=window.confirm.bind(window),originalAlert=window.alert.bind(window);
  window.confirm=message=>originalConfirm(translateText(message));window.alert=message=>originalAlert(translateText(message));
  translateNode(document.documentElement);
  new MutationObserver(changes=>{for(const change of changes){if(change.type==='childList')change.addedNodes.forEach(translateNode);else if(change.type==='attributes')translateElement(change.target);else translateNode(change.target);}}).observe(document.documentElement,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['aria-label','title','placeholder','data-label']});
 }
 const selector=document.getElementById('languageSelect');if(selector){selector.value=APP_LOCALE;selector.addEventListener('change',()=>changeLanguage(selector.value));}
}
