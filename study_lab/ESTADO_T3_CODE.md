# Estado de NIIS Study Lab — revisión de cierre, 12/11/2026

## HECHAS

- Enfoque práctico: referencias de fórmula/API dadas en ocho casos, visibles incluso en examen. NumPy y métricas se resuelven con llamadas e interpretación; fuzzy Sugeno tiene datos y fórmula facilitados.
- Catálogo conectado de **657 recursos**: 187 Programazioa, 117 Sistemas ML, 48 Modelos, 95 BD Sistemak, 196 BD Aplikatua y 14 generales. Asignación estricta por carpetas; nuevos módulos y ambigüedades separados. Erronkas excluidas. Metadatos y encabezados únicamente.
- Sincronización desde un mirror privado independiente. Fuente nueva o modificada se señala; las soluciones existentes no se revalidan por implicación. Preparación reanudable con hashes y tres archivos permitidos, sin stash/reset ni alteración de trabajo ajeno.
- Paquete alojado como Worker sin dependencias, con CSP HTTP por hash, frame-ancestors limitado, no-store, nosniff, no-referrer y permisos deshabilitados. Solo GET/HEAD del documento; sin APIs de ejecución.


- Una aplicación de estudio con las cinco asignaturas, fechas y profesores solicitados. Recorridos finitos: Programazioa 27 casos, Sistemas ML 11, AA Ereduak 11, BD Sistemak 12 y BD Aplikatua 12. Total: **73 microcasos y 16 lecciones breves**. Las combinaciones numeradas son repaso opcional, no mil niveles.
- Teoría por bloque con ejemplo desplegable, pregunta de recuerdo y error habitual. Ayudas en dos pasos con APIs/imports; casos de desarrollo, análisis, configuraciones y flujos. No se sustituyen por tests tipo quiz.
- Ruta principal y catálogo separados, búsqueda por ID/tema/texto, filtros de dificultad y estado, vacíos recuperables y avance real al siguiente caso. Los botones principales abren el siguiente caso pendiente, no un simulacro arbitrario.
- Repaso ordenado por autoevaluación. Los casos dominados reaparecen a partir de dos días para comprobar recuerdo; la app no cambia notas automáticamente.
- Editor con autoguardado, ayudas guiadas y soluciones bloqueadas en examen hasta entregar. Reloj de 15 min para un caso y 50 min para un simulacro. Navegación, reinicio y JSON compatibles con V1.
- Protección de progreso: conflicto visible entre pestañas, rechazo de importaciones inválidas, estado de guardado fallido, aviso antes de salir si no se pudo guardar, recuperación de un registro dañado sin sobrescribir sus bytes. Exportar progreso actual y recuperar el original dañado son acciones distintas.
- Interfaz oscura conservada y pulida; navegación legible en móvil, bloques desplegables, contraste de texto secundario mejorado, iconos SVG, foco visible, skip link, salida del editor con Esc, Mayús+Tab disponible, reduced-motion y ajuste de texto técnico.
- Fuente académica confirmada: `/home/admin/Big_Data`, origin `https://github.com/Niistal/Big_Data.git`, rama `main`, commit `5e716edf42e0d1097b5ad2fb911755d97ba3865d`. El commit coincide con `origin/main` consultado por Git. El working tree de los apuntes sigue limpio.
- Trazabilidad de 73 casos con ruta, sección real y hash. La auditoría exige origen/rama correctos y que cada archivo leído coincida con su contenido versionado en HEAD. No se modificaron apuntes, Erronkas ni instrucciones del repositorio académico.
- Build autónomo sincronizado y empaquetado separado para la web privada. El alojamiento conserva acceso exclusivo al propietario mediante autenticación gestionada de ChatGPT; no hay contraseñas en JS/Git ni endpoint que ejecute código arbitrario.
- Historial y código en la rama `feat/niis-study-lab`; PR #4 y seguimiento en issues #1–#3. No merge ni push a la rama principal.

## PRUEBAS

Suite ejecutada desde el entorno propio del laboratorio:

```sh
.venv/bin/python scripts/run_checks.py --repo /home/admin/Big_Data --browser --frameworks
```

Resultados de esta revisión:

- Sintaxis JS, build y standalone: PASS.
- Generador: PASS, 1.000 secuencias ordenadas únicas/reproducibles por materia, cinco casos distintos por prueba y cobertura completa de las rutas.
- Aprendizaje/persistencia: PASS. Teoría y métodos reales en todos los bloques, sin `${…}` visible; orden de repaso; compatibilidad de JSON; conflictos, cuota llena y datos dañados sin sobrescritura.
- Fuentes: PASS, 73 rutas/secciones/hashes del repositorio conectado.
- Catálogo: PASS, 13 pruebas de Git con asignación exacta, códigos ambiguos, derivados huérfanos, nuevas materias, fuentes hostiles, symlinks y fallos atómicos. 657 registros con huella y JSON/JS coherentes.
- Guardas de automatización: PASS, 9 pruebas con repositorios temporales; trabajo/staging ajeno conservado, reanudación de commit/publicación y rechazo de cambios posteriores.
- Worker: PASS, bytes exactos, cabeceras HTTP, HEAD sin cuerpo, rutas ocultas 404 y métodos de escritura 405.
- Chromium: además, referencias visibles en examen, temario por materia, paginación, vacíos recuperables y protección ante títulos/IDs hostiles, a cuatro tamaños.
- Python: PASS, **31 soluciones** con comprobaciones de resultado en directorios temporales. Incluye JSON, NumPy, Pandas, gráficos, clasificación, regresión, CV, Faker y ventanas temporales.
- FastAPI P13: PASS, salud, producto 201, validación 422, OpenAPI y arranque HTTP real de `python -m uvicorn` en loopback/puerto efímero.
- Streamlit P14: PASS, CSV de fixture, métrica y filtro de categoría mediante AppTest. Se sustituye únicamente el control de carga por un archivo de prueba; la lógica del caso es la publicada.
- Chromium headless: PASS. Flujos, ayudas, borradores, recarga, reloj, examen/entrega/reinicio, filtros, repaso, teclado e importación/exportación. **Los 73 casos con ayudas y solución abiertas** no desbordan a 320, 390, 768 y 1440 px.
- Paquete alojado: misma suite de navegador más cierre de sesión y CSP por hash, sin errores JS. Perfil de prueba temporal; no se toca el progreso del propietario.
- Inspección visual de panel, recorrido y editor; correcciones del método que mostraba código de plantilla, desbordamiento de un enunciado largo y marca de navegación.
- El navegador compartido T3 falló dos veces con timeout de snapshot; la comprobación visual y de interacción se completó en Chromium local. No se atribuye a ese navegador una verificación que no hizo.

Para repetir QA: instalar opcionalmente `requirements-study-qa.txt` en el venv; iniciar la web en 127.0.0.1:8080 y ChromeDriver en 127.0.0.1:9515. La suite no instala paquetes, publica ni modifica apuntes. Último log local en `qa-artifacts/last-checks.txt` (ignorado por Git).

## PENDIENTES Y LÍMITES REALES

- **Proton Pass**: sin integración de bóveda en esta sesión. No se ha guardado ninguna credencial ni comprobado autocompletado/MFA del propietario. Seguimiento: issue #3.
- **Progreso entre dispositivos**: almacenamiento cliente conforme al requisito original; se mueve con exportación/importación JSON. Sincronización automática es una mejora opcional, no implementada: issue #1.
- **Infraestructura académica externa**: no se han ejecutado Windows/PowerShell, Orange ni clústeres Docker/Elastic/Logstash/Kafka/NiFi/Connect. Sus casos son de práctica manual con fuentes contrastadas; no se presentan simulaciones como pruebas de extremo a extremo. Seguimiento: issue #2.
- El editor no ejecuta ni autocorrige código; permite escribir, copiar y comparar con criterios. La ejecución se hace en terminal/herramienta local, como se explica en la UI y en `ENTORNO_LOCAL.md`.
- Los 73 casos cubren áreas representativas del temario documentadas en `COBERTURA.md`, no cada detalle de cada PDF. `verified` no atribuye enunciados al profesor ni certifica autoría humana de las soluciones del repo. NotebookLM es apoyo derivado.
- Revisión realizada por el agente principal: SELF_REVIEW / NOT_INDEPENDENT. No se utilizó 5.6 Luna ni Claude: el catálogo no permitió verificar la ruta full-access exigida para esa delegación. No se instaló un sustituto.
- No se promete nota, aprendizaje completo en dos horas, ausencia absoluta de fallos ni observación indefinida. La aplicación queda con una suite reproducible y sin fallos conocidos abiertos en los flujos comprobados.

La publicación y su identidad se registran en `../deployment/DESPLIEGUE.md`; el historial de evolución está en `CHANGELOG.md`.
