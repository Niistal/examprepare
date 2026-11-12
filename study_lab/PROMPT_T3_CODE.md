# PROMPT MAESTRO — T3 CODE (CLAUDE + CODEX)

Actúa como un equipo pequeño de ingeniería y diseño educativo. **Claude = implementador**, **Codex = revisor técnico**. Si uno no está disponible, usa el que funcione sin instalar agentes nuevos. Proyecto: **NIIS STUDY LAB**, web local de entrenamiento académico intensivo para los exámenes **16–20/11/2026** del curso de Big Data e IA. Objetivo: **una aplicación funcional y pulida, terminable idealmente en menos de dos horas**, con consumo limitado de tokens. Prioriza una versión completa y verificable por encima de funciones sofisticadas incompletas.

## CONTEXTO Y REGLAS INNEGOCIABLES

1. Fuente académica PRINCIPAL: repositorio privado `Niistal/Big_Data`, rama `main`, local si existe. No confundir con `T2-erronka1` ni con los proyectos `02_Erronka_1_CNC_Guard`/`08_Erronka_2_RetailEUS`. Estos sirven solo como referencias secundarias, porque fueron resueltos con asistencia IA y el examen se hace sin ella.
2. Existe una primera versión entregada por ChatGPT con `index.html` autónomo, `app.js`, `style.css`, `shell.html`, `README.md`, `requirements-study*.txt`, `plantilla_examen.py`, scripts y este prompt. **Conservar y evolucionar**, no reescribir sin motivo ni borrar progreso.
3. Crear un subproyecto AISLADO `study_lab/` en Big_Data o utilizar la carpeta de esta entrega y documentar la ruta final. **No modificar** apuntes originales, ejercicios resueltos, `AGENTS.md`, `CLAUDE.md`, `PROJECT_GOAL.md`, `.agents`, `.claude`, `.codex`, sin autorización expresa. No commitear secretos ni datos personales.
4. Las 5 asignaturas, exactamente:
   - **16/11 lunes**: `05_AA_Programazioa` — Aitor.
   - **17/11 martes**: `04_Ikaskuntza_Automatikorako_Sistemak` — Lander.
   - **18/11 miércoles**: `03_AA_Ereduak` — Xabat.
   - **19/11 jueves**: `06_BD_Sistemak` — Janire.
   - **20/11 viernes**: `07_BD_Aplikatua` — Janire.
5. Consumir fuentes REALES, no alucinar enunciados atribuyéndolos al profesor: `ARIKETAK_AURKIBIDEA.md`, README de cada módulo, `05_AA_Programazioa/Apuntes_Estudio_Programazioa.md`, los `.ipynb`, `.md` de ariketak, `NotebookLM_Material_Estudio/<asignatura>/Guias_de_Estudio/`, `Quizzes_y_Examenes/` y flashcards. Revisar ejemplos y extraer microcasos originales propios de estudio. En cada microcaso registrar `source_path`, `source_section` y `verified=true/false`.
6. Idioma de UI español, conceptos del examen en euskera entre paréntesis. UI profesional, modo oscuro, responsive, sin dependencia de servicios de IA; **no desarrollar un chatbot**. Los ejercicios requieren **escribir código, SQL, configuraciones JSON/Logstash, flujos o análisis**, no preguntas tipo test como actividad principal.
7. No publicar/desplegar en internet; solo `127.0.0.1`. El progreso se almacena en cliente (localStorage o IndexedDB) con exportación/importación JSON. No subir progreso a GitHub.
8. Mantener 1.000 IDs deterministas por asignatura, con secuencias reproducibles, sin confundir *combinaciones de un banco* con *1.000 enunciados originales*. Aumentar variedad de tareas verificadas si da tiempo.
9. **Optimización de tokens**: no enviar al modelo notebooks completos ni PDFs de cientos de páginas, ficheros binarios, screenshots masivos ni todo el árbol del repo. Listar y filtrar rutas automáticamente con scripts locales; leer fragmentos objetivo. Máximo **dos pasadas de implementación y una revisión final**. Evitar debates de diseño, herramientas SaaS, complejos backends o infraestructura remota.
10. Si existen problemas de entorno, resolverlos con scripts/reintentos acotados; no hacer instalaciones globales ni borrar datos. No solicitar confirmación salvo acciones destructivas o externas.

## FASE P0 — PRIMERA HORA: FUNCIONALIDAD QUE NO SE PUEDE ROMPER

- Auditar primero los archivos existentes (`index.html`, `app.js`, `style.css`) y su prueba de arranque. Mantener navegación, 5 materias, panel de calendario, catálogo, temas, filtros y buscador.
- Mantener 2 modos: **guiado** (pistas y solución) y **examen sin ayudas** (soluciones bloqueadas hasta entregar); editor con autoguardado; temporizador; navegación entre preguntas; reinicio de examen; autoevaluación 0/1/2; estadísticas y JSON de respaldo.
- Comprobar que los **1.000 números de examen generan 1.000 secuencias ordenadas únicas por asignatura**, sin repeticiones dentro de cada prueba. Añadir test automático de esta propiedad.
- Corregir bugs de UI, accesibilidad y flujo. No introducir autenticación, cloud, DB remota, Docker obligatorio ni dependencias JS pesadas.
- Conectar cada ejercicio a una ruta real del repositorio; nunca presentar una solución del repo como si fuera producción humana del alumno.

## FASE P1 — SIGUIENTES 40 MIN: ENRIQUECIMIENTO DIDÁCTICO

Priorizar **Programazioa**, primer examen. 18 microejercicios ya presentes deben cubrir Python, JSON, .venv, comprehensions, NumPy (axis, máscaras, broadcasting), Pandas (limpieza, groupby, merge, concat), Matplotlib, Scikit-Learn (Pipeline, leakage, métricas), FastAPI, Streamlit, RAG, Git/DVC/MLflow.

Después revisar las otras materias sin pasarse de temario:

- Sistemas ML: Orange (flujos CR7, Iris, Wine), KNN, regresión lineal/logística, árbol/forest, SVM, validación, K-Fold y matriz de confusión.
- AA Ereduak: fuzzy logic, selección y confirmación de sesgos, COMPAS, fairness, AI Act, ALTAI, auditoría de CV y ética.
- BD Sistemak: 7 V, ciclo de datos, ETL/ELT, Faker, Docker Elastic Stack, Elasticsearch Query DSL, aggregations, Kibana Discover/KQL, Logstash grok/date/mutate.
- BD Aplikatua: NiFi GetFile/PutFile, QueryRecord, UpdateAttribute, ReplaceText, provenance, MariaDB→MongoDB, Kafka topics/partitions/offsets/producer/consumer, Kafka Connect y AEMET Bronze/Silver/Gold.

Criterios de calidad por pregunta: enunciado con datos concretos, objetivo alcanzable en 10–25 min, starter mínimo, criterios de éxito, pista progresiva, solución válida y explicación de errores comunes. No usar respuestas generadas por IA como fuente de verdad: contrastar contra el material existente o prueba de ejecución.

## FASE P2 — ÚLTIMOS 20 MIN: ENTORNO Y QA

- Documentar con exactitud `python -m venv .venv`, activación Windows PowerShell / Linux Omarchy, `python -m pip install -r requirements-study.txt`, `python archivo.py`, `python -m jupyter lab`, `uvicorn`, `streamlit`, `docker compose` para Elastic y el flujo Kafka/NiFi. **Los imports deben aparecer en el código de cada ejercicio** y existir una plantilla copy-paste; no pedir al usuario que adivine librerías.
- Separar dependencias básicas de extras para no instalar PyTorch, Transformers, LangChain, DVC, MLflow, etc. salvo cuando realmente se usen. Para ML sin GPU, preferir scikit-learn/datasets incorporados.
- Pruebas locales del generador, persistencia, modos, filtros y navegación usando navegador headless si está disponible; comandos de arranque validados. Ejecutar el código real de varios ejercicios Python representativos, en entorno preparado, cuando sea viable.
- Detectar y corregir soluciones inconsistentes (nombres de módulos, clases y parámetros, datos del ejercicio, versiones). Verificar requisitos y salida en ambos SO cuando sea posible; indicar qué no se pudo probar.
- Mantener la versión standalone `index.html` sincronizada con sus fuentes JS/CSS mediante un script de build reproducible si se modifica la estructura.

## OPCIONAL, SOLO SI SOBRA TIEMPO

Un ejecutor local de Python con límite de tiempo/salida y directorio de trabajo aislado para tests de funciones simples. **No crear un endpoint que ejecute código arbitrario con permisos del usuario ni sobre el repositorio de los apuntes.** Si no cabe en el plazo, conservar el editor y la ejecución manual por terminal; documentar la limitación en vez de fingir autocorrección.

## DEFINICIÓN DE HECHO

Entregar `study_lab/` utilizable en `http://127.0.0.1:8080` con la interfaz visual cuidada, al menos el banco inicial completo, sin corrupción de los apuntes ni del progreso; historial de cambios documentado; comandos simples para abrir y trabajar con Python, y fichero `ESTADO_T3_CODE.md` con tareas HECHAS, PENDIENTES y PRUEBAS. Si se usa Git, trabajar en rama `feat/niis-study-lab` y commits pequeños **sin push a main**. Solo cuando todo esté verificado dar un resumen compacto. No consumas tokens en recontar el árbol del repo ni en generar planes gigantes: **ejecuta y prueba**.
