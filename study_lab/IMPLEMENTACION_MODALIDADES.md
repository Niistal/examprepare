# Modalidades y herramientas · entrega 12/11/2026

Trabajo sobre `feat/niis-study-lab`, posterior al HEAD `b865eb1` de PR #4. No se modifica Big_Data, no se despliega la web y no se altera el parche OCI de `distribution/server.py` ni su prueba.

## Auditoría y evidencia

Se inspeccionaron app.js, style.css, shell.html, index.html generado, build.py, README.md, COBERTURA.md, ESTADO_T3_CODE.md, sources.json, materials.json, test_learning.cjs, test_browser.py y distribution/server.py. El banco real contiene **84 casos**, incluidos P01–P38; se preservan sus IDs, contenido original, respuestas y simulacros numerados.

Repositorio académico consultado en copia temporal de solo lectura: `Niistal/Big_Data`, commit `5e716edf42e0d1097b5ad2fb911755d97ba3865d`. Se revisaron el índice ARIKETAK, las carpetas 03–07, los README de sesgos/fairness/auditoría/riesgos, los ejercicios Orange y validación, los laboratorios de NiFi/Kafka/Connect, sus compose y el apoyo NotebookLM. Se extrajo texto del PDF `03_AA_Ereduak/1_Sarrera_eta_Ereduak/E1-Ereduak-Sarrera.pdf`; la presentación confirma paradigmas, reglas y lógica difusa. La guía de Programazioa 3+7 incorporada permanece intacta. No se presume haber leído exhaustivamente cada PDF/notebook del repositorio.

- **Confirmado:** rutas y contenidos usados como fuente, instrucciones Orange de las prácticas, configuraciones de puertos de los compose, instalación Orange 3.40.0 y resultados de las pruebas descritas abajo. Cada pregunta nueva lleva ruta, commit y SHA256 de su fuente.
- **Inferido:** dificultad pedagógica, agrupación en 20 temas, redacción de ejemplos, rúbricas y preguntas propias. No son preguntas oficiales ni transcripciones de un examen.
- **Derivado:** las lecciones que dependen de NotebookLM se identifican como tales. La síntesis del AI Act/RGPD es académica: no certifica obligaciones vigentes ni excepciones legales de un caso real.
- **Pendiente de verificar:** formato exacto de los exámenes distintos de la guía aportada de Programazioa, ejecución GUI en el escritorio del estudiante y disponibilidad real de sus servicios externos.

## Cambios reales

- Motor explícito THEORY, QUIZ, DEVELOPMENT, EXTERNAL_TOOL y MIXED. Asignación por ID de caso; los bloques registran modalidad y modalidades componentes. Xabat combina únicamente teoría y quiz. Programazioa conserva editor, Pyodide, CSV, notebook, P01–P38 y guía 3+7.
- Nueva experiencia contextual dentro de la aplicación existente: Aprender, Practicar, Test, Simulacro, Repasar y Recursos. Alt+1…6 cambia pestañas fuera de campos de respuesta. No se muestran imports, plantillas ni ejecución Python en teoría. Se conserva un campo de razonamiento, no un editor de programación.
- **20 temas / 106 preguntas propias**, con IDs Q-* independientes de los casos históricos: Xabat 49, ML 20, BD Sistemak 21 y BD Aplikatua 16. Incluye cuatro opciones, verdadero/falso, múltiples respuestas, completar, ordenar, relacionar, comparar y casos breves con criterios personales.
- Tests de 5/10/20/30 o banco completo; el tamaño efectivo nunca supera el banco disponible. Selección reproducible por semilla; modo examen con plazo y soluciones al terminar; corrección inmediata opcional en práctica. Las respuestas abiertas no reciben calificación automática.
- Flashcards con No lo sé / Con ayuda / Lo sé y repaso a los 10 minutos / un día / intervalos crecientes. Historial, aciertos, pendientes y repetición de fallos por tema. El dominio autocorregido no equivale a la autoevaluación de las tarjetas.
- Migración idempotente del campo opcional `learning.version=1`, conservando la clave LocalStorage y el sobre JSON schema 1. Importación/exportación incluye las nuevas respuestas, sesiones, tarjetas e historial; conserva también campos de progreso existentes. Versiones de preguntas separan el dominio actual del historial anterior; un test de otra versión se archiva al arrancar.
- Ocho workflows Orange específicos: M01/M02/M03/M04/M05/M06/M09/M10. CSV completos: goles académico (979 registros), Diabetes (442), Breast Cancer (569), Wine (178), Iris (150) y cuatro registros sintéticos originales de M10. File requiere seleccionar el CSV descargado; k, kernel, normalización y evaluación se configuran explícitamente según la guía. No se distribuyen settings pickle ni se promete una configuración invisible ya ejecutada.
- Los casos M02–M06 se presentan en Orange manteniendo IDs y borradores históricos. Las soluciones Python originales siguen en el banco para compatibilidad, pero no se muestran ni se exigen en su interfaz Orange.
- BD Sistemak conserva casos originales y ofrece editor JSON específico con validación de sintaxis. Las consultas se ejecutan en Dev Tools; validar JSON no certifica la semántica ni simula Elasticsearch.
- BD Aplikatua enlaza los laboratorios y compose reales de NiFi/Kafka/Connect y ofrece pasos de configuración, inspección de errores, colas y provenance. No crea servicios ni arranca Docker automáticamente.

## Puente local

`local_server.py` es voluntario y sirve la misma aplicación en **127.0.0.1**. Detecta SO y lanzadores ya instalados; no instala Orange. Solo admite una acción de proceso: Orange con uno de los ocho workflows permitidos. No admite shell, comandos, argumentos, rutas ni URLs del cliente. Usa `shell=False`, Host exacto, origen exacto en POST y token aleatorio del proceso. No permite CORS ni ejecución desde la web alojada. Las descargas funcionan también en standalone/alojado porque están incluidas en el HTML.

Los puertos 9200, 5601, 8443 y 9092 proceden de los compose consultados. Un listener no acredita identidad del servicio; la interfaz lo indica. La detección no prueba autenticación ni el funcionamiento de un laboratorio. No se añade ningún endpoint de ejecución a distribution/server.py.

## Arranque

Desde la raíz del proyecto, en Linux:

```bash
python3 study_lab/build.py
python3 study_lab/local_server.py --port 8080
# Abrir http://127.0.0.1:8080 (usar 127.0.0.1, no localhost)
```

En Windows:

```powershell
py study_lab/build.py
py study_lab/local_server.py --port 8080
```

Si 8080 está ocupado, elegir por ejemplo 8086. Para una versión sin puente basta servir `study_lab/index.html` con un servidor estático; se mantienen las descargas, pero no la apertura de aplicaciones.

Orange existente en esta máquina Linux:

```bash
orange-canvas study_lab/resources/orange-M09.ows
# Alternativa verificada por importación en el entorno instalado:
/home/admin/.local/share/uv/tools/orange3/bin/python -m Orange.canvas study_lab/resources/orange-M09.ows
```

El Python del sistema no tiene Orange; no se debe afirmar que `python -m Orange.canvas` funcione con cualquier intérprete. En otro equipo hay que localizar su instalación. Windows se cubre con detección de `orange-canvas.exe` y fallback al módulo solo si está instalado en el intérprete activo.

## Pruebas y límites

Evidencia local reproducible de esta entrega:

- Suite `scripts/run_checks.py --repo <copia-académica>`: **PASS**, build, generador 1–1000, aprendizaje histórico, modalidades, puente, materiales, sincronización, publicación, trazabilidad y **42 soluciones ejecutadas**. Se usó un entorno QA existente; el Python del sistema carece de sklearn.
- `test_local_tools.py`: **15 tests PASS**. Host/origen/token, comandos y rutas rechazadas, herramienta ausente, fallo de proceso, allowlist, detección Windows/Linux simulada y rutas públicas restringidas. La creación del proceso se sustituye por un mock en estas pruebas de transporte.
- `test_orange.py` con el Python existente de Orange: **PASS**, los ocho esquemas específicos y el esquema de comparación cargan mediante el registro real de Orange; CSV Iris completo y evaluación real de tres learners con 5-fold. Avisos de deprecación de scikit-learn permanecen; no son fallos de prueba.
- `test_browser.py`: **PASS**, suite existente en Chromium real con perfil temporal, incluida Programazioa y persistencia.
- `test_learning_browser.py`: **PASS**, teoría sin Python, razonamiento persistido, Programazioa con editor, respuestas incorrectas, rúbricas, examen bloqueado, sesión reproducible, importación, Orange y editor JSON; responsive 320/390/768/1440; cero errores JS; standalone sin puente rechaza apertura local.
- `distribution.test_server` y `distribution.test_catalog`: **12 tests PASS**; `distribution/test_sync.cjs`: **PASS**. Se mantiene el parche y la prueba worker-src self de OCI.

No se han ejecutado NiFi, Kafka, Elasticsearch, Kibana ni contenedores Docker. No se ha verificado un escritorio Windows ni una sesión Orange GUI interactiva de extremo a extremo. La validación Orange usa Qt offscreen y motor real. Jupyter se detecta si está en PATH; no se instala ni se arranca automáticamente. Estos límites siguen en el alcance de la issue #2. No se ha redeplegado study.gripuno.com.

La ruta multiagente quedó **BLOCKED_FULL_ACCESS_UNSUPPORTED**: el catálogo T3 confirmó `gpt-5.6-luna`, pero los proveedores Codex/Claude no anunciaron `runtimeModes`, requisito obligatorio del router para delegar. No se lanzó ningún subagente ni se sustituyó Luna silenciosamente. Implementación, revisión y validación realizadas por el principal: **SELF_REVIEW / NOT_INDEPENDENT**. No se reclaman resultados de una revisión externa.
