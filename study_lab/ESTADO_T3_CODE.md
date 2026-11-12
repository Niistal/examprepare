# Estado T3 Code — 12/11/2026

## HECHAS

- Entrega aislada en `/home/admin/.t3/projects/examprepare/study_lab/`, rama `feat/niis-study-lab`. Sin publicación, push ni cambios en los apuntes o Erronkas.
- Se leyó `PROMPT_T3_CODE.md` y se evolucionaron las fuentes originales de la entrega ZIP. `vista_previa.png` corresponde a la versión original, no a la interfaz actual.
- Cambio de objetivo incorporado: recorrido finito por competencias, no mil niveles. 62 microcasos: Programazioa 27, Sistemas ML 9, AA Ereduak 8, BD Sistemak 9, BD Aplikatua 9. Simulacros numerados conservados como repaso opcional, fuera del recorrido principal.
- Calendario de las cinco materias y profesores conservado. Prioridad Programazioa, 16/11/2026.
- Métodos de estudio diferentes por materia; bloques ordenados y progreso por autoevaluación. Teoría mediante análisis, cálculos y explicación; práctica mediante código, consultas, configuraciones y flujos.
- Ayuda progresiva: orientación → ejemplo básico/API y starter con imports → solución voluntaria en guiado. En examen, ayudas y solución permanecen bloqueadas hasta entregar.
- Nueve casos adicionales de Programazioa: serialización/main, álgebra NumPy, loc/iloc/transform, Seaborn, regresión/baseline, GridSearchCV, HF con salidas simuladas, cadenas/memoria y Git/Edge/Cloud.
- Trazabilidad para los 62 casos: `source_path`, `source_section`, `verified`, hash SHA-256 y commit en `sources.json`/`sources.js`. Fuente local `Niistal/Big_Data`, main, commit `5e716edf42e0d1097b5ad2fb911755d97ba3865d`. Consulta acotada de índice, README, apuntes, notebooks, ejercicios, guías, quizzes y flashcards. Sin ingestión masiva de PDFs.
- `verified=true` significa ruta y tema contrastados; no significa enunciado original del profesor, autoría humana del repositorio ni ejecución de todos los sistemas. Los casos de estudio son propios. NotebookLM se usa como apoyo derivado, no como evidencia independiente.
- Bugs corregidos: borrador al revelar ayudas/autovalorar; restauración de sesión/posición/reloj/bloqueo tras recarga; pausa al volver al banco; validación de respaldos; reinicio/importación sin sesión obsoleta; estado de guardado fallido visible.
- Correcciones didácticas: catálogo JSON coherente, NIF solo dígitos ASCII, QueryRecord con Revenue y separador `;`, fuzzy con pertenencias/salida numérica y distinción Sugeno/Mamdani, práctica DVC local y siete V en el caso S01.
- UI oscura y responsive conservada, recorrido principal destacado, foco de teclado visible y etiqueta accesible del editor.
- Build reproducible `python build.py`: `shell.html` + `style.css` + `sources.js` + `app.js` → `index.html` autónomo.
- `.venv` Python 3.12 propio, dependencias básicas instaladas, extras separados y comandos documentados en `ENTORNO_LOCAL.md`. `.venv`, secretos y respaldos de progreso ignorados por Git.

## PRUEBAS

Ejecutadas en Linux:

```sh
python build.py
python test_artifacts.py /home/admin/Big_Data
node test_generador.cjs
python test_browser.py
python test_solutions.py --python .venv/bin/python
.venv/bin/python plantilla_examen.py
.venv/bin/python -m pip check
bash -n iniciar.sh preparar_python.sh
```

- Build y metadatos: PASS. 62 fuentes existentes, secciones registradas y hashes iguales al material leído; HTML sincronizado.
- Generador: PASS. 1.000 secuencias ordenadas únicas y reproducibles por cada materia; cinco ejercicios distintos por prueba. Cada recorrido incluye una vez todos los casos de su materia.
- Chromium headless / ChromeDriver: PASS. Cinco materias, recorrido de Programazioa, búsqueda/nivel, ayudas sin pérdida de borrador, recarga de sesión/respuestas/valoración/reloj, bloqueo en examen, navegación, entrega, reinicio, exportación/importación y rechazo de estructura inválida. Vista móvil 390×844 sin desbordamiento horizontal; sin errores JavaScript. Pruebas con perfil temporal, no con el progreso del usuario.
- Soluciones: PASS, 21 scripts en carpetas temporales con asserts de resultados: P01–P03, P05–P12, P17–P25 y P27 (P26 es pseudocódigo y no se ejecuta). Incluye CSV de prueba, archivos JSON/gráficos, pipeline con categoría desconocida, regresión y CV. Se usó primero el intérprete existente de Big_Data en lectura y luego se repitió en `.venv` propio con instalación limpia.
- Arranque HTTP: PASS en `127.0.0.1:8080`, Chromium carga el standalone. El servidor solo sirve `study_lab/`.
- Plantilla, dependencias y sintaxis Bash: PASS. `git -C /home/admin/Big_Data status --porcelain` vacío al cierre.
- Revisión técnica final realizada por el agente principal: SELF_REVIEW / NOT_INDEPENDENT. Claude no se delegó porque el catálogo T3 no anunciaba modos `full-access` verificables para su proveedor; tampoco devolvió el modelo exacto 5.6 Luna. No se instaló ni se sustituyó silenciosamente ningún agente.

Para repetir QA de navegador, inicia el servidor web y `chromedriver --port=9515 --allowed-ips=127.0.0.1` en terminales separadas. `test_browser.py` requiere Chromium en `/usr/bin/chromium`; no requiere instalar Selenium ni Playwright. Cierra ChromeDriver al terminar.

## PENDIENTES / LÍMITES

- No hay ejecutor ni autocorrección de código dentro de la web: se escribe aquí, se ejecuta en terminal y se compara con criterios. Nunca se expone un endpoint de ejecución arbitraria.
- No se garantiza dominar una materia ni una nota en dos horas. La sesión propuesta de dos horas es una unidad de trabajo; el recorrido completo requiere repetir sesiones y resolver sin copiar. El banco cubre el núcleo solicitado, no todos los detalles de cada PDF o cada ejercicio original.
- No ejecutados en esta entrega: Windows/PowerShell, Orange, API/Streamlit, Docker/Elastic/Logstash, Kafka/NiFi/Connect, RAG con modelos ni DVC/MLflow reales. Los pseudocódigos se etiquetan como tales. Quedan por validar sus flujos de extremo a extremo en la infraestructura del alumno.
- Las soluciones Python comprobadas no abarcan todo el banco; los casos de teoría/configuración requieren comparación manual con la fuente y ejecución cuando corresponda.
- La guía de comandos explica la copia de casos de infraestructura y el bind local de puertos. No se modificaron ni arrancaron los compose originales de clase.
- Persistencia limitada al origen/navegador. Mantener `127.0.0.1:8080`, exportar JSON regularmente. La ampliación del banco de Programazioa cambia sus combinaciones numeradas; no borra respuestas ni valoraciones previas. Una sesión antigua incompatible no se reanuda automáticamente.
- Mejoras futuras opcionales: variantes adicionales verificadas y rúbricas más profundas para las otras cuatro materias. Sin tareas externas ni issues remotas creadas.
