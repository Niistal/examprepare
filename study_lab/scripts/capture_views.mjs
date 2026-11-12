// Capturas reproducibles de todas las vistas a 390, 768 y 1440 px, con comprobación de
// desbordamiento horizontal y errores de consola. No modifica datos: usa un perfil efímero.
// Uso: node scripts/capture_views.mjs <url> <carpeta-salida> [light|dark]
// Requiere Playwright (NODE_PATH o PLAYWRIGHT_MODULE apuntando al paquete instalado).
import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [url = 'http://127.0.0.1:8131', out = 'qa-artifacts/views', scheme = 'dark'] = process.argv.slice(2);
mkdirSync(out, { recursive: true });

// Cada vista se alcanza con las funciones públicas de la aplicación, igual que las pruebas existentes.
const VIEWS = [
  ['01-panel', "navigate('dashboard')"],
  ['02-recorrido-programazioa', "selectCourse('program')"],
  ['03-teoria-indice', "selectCourse('ml')"],
  ['04-teoria-leccion', "selectCourse('ml');document.querySelector('.topic-overview-row')?.click()"],
  ['05-teoria-practicar', "selectCourse('models');learningTab='Practicar';renderModalStudy()"],
  ['06-test-config', "selectCourse('models');learningTab='Test';renderModalStudy()"],
  ['07-test-en-curso', "selectCourse('models');learningTab='Test';startLearningQuiz(5,'practice',1,false,true);renderModalStudy();document.querySelector('#learningBody input[type=radio]')?.click()"],
  ['08-simulacro-config', "selectCourse('systems');learningTab='Simulacro';renderModalStudy()"],
  ['09-repasar', "selectCourse('models');learningTab='Repasar';renderModalStudy()"],
  ['10-recursos', "selectCourse('ml');learningTab='Recursos';renderModalStudy()"],
  ['11-catalogo', "selectCourse('program');setStudyView('catalog')"],
  ['12-temario', "selectCourse('models');setStudyView('materials')"],
  ['13-lector', "selectCourse('models');setStudyView('materials');const r=MATERIALS.resources.find(r=>r.course==='models'&&r.extension==='.md');return loadMaterialReader().then(()=>openMaterialReader(r.id))"],
  ['14-ejercicio-python', "document.getElementById('materialReader').close?.();startSingle('P01')"],
  ['15-ejercicio-ayudas', "startSingle('P01');revealHint();revealSolution()"],
  ['16-ejercicio-orange', "startSingle('M09')"],
  ['17-simulacro-examen', "selectCourse('program');document.getElementById('examMode').value='exam';document.getElementById('examNumber').value='17';startExam()"],
  ['18-progreso', "navigate('progress')"],
  ['19-entorno', "navigate('setup')"],
];

const report = [];
const browser = await chromium.launch();
for (const width of [390, 768, 1440]) {
  const context = await browser.newContext({ viewport: { width, height: width === 390 ? 844 : 1000 }, colorScheme: scheme, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(url, { waitUntil: 'load' });
  await page.evaluate(() => { window.confirm = () => true; });
  for (const [name, action] of VIEWS) {
    let failure = null;
    try {
      await page.evaluate(`(async()=>{${action}})()`);
      await page.waitForTimeout(350);
    } catch (e) { failure = String(e).slice(0, 200); }
    const state = await page.evaluate(() => ({ overflow: document.documentElement.scrollWidth - innerWidth, offenders: document.documentElement.scrollWidth > innerWidth + 1 ? [...document.querySelectorAll('body *')].filter(x => x.getBoundingClientRect().right > innerWidth + 1 && x.offsetParent).slice(0, 5).map(x => x.tagName + '.' + x.className) : [] }));
    await page.screenshot({ path: path.join(out, `${name}-${width}.png`), fullPage: !name.includes('lector') });
    report.push({ view: name, width, overflowPx: Math.max(0, state.overflow), offenders: state.offenders, failure });
  }
  report.push({ width, consoleErrors: errors });
  await context.close();
}
await browser.close();
writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 1));
const bad = report.filter(r => r.overflowPx > 1 || r.failure || r.consoleErrors?.length);
console.log(bad.length ? JSON.stringify(bad, null, 1) : `OK ${report.length - 3} capturas sin desbordamiento ni errores de consola`);
