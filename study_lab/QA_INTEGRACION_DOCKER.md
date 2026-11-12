# Verificación real antes de fusionar PR #5 · 12/11/2026

El propietario autorizó fusionar y ejecutar las pruebas con Docker. Se inspeccionaron los contenedores y las imágenes instaladas; se crearon contenedores desechables de QA con nombres y etiquetas propios, sin iniciar/parar contenedores existentes, montar sus datos ni leer sus credenciales. No se descargaron imágenes. Todos los puertos publicados de QA se limitaron a 127.0.0.1; las redes, contenedores y sus volúmenes anónimos se eliminaron al terminar.

## Resultados

- Suite completa local: PASS. Build, 1–1000 secuencias por materia, 106 preguntas, migración, importación/exportación, conflictos de guardado, materiales, trazabilidad y **42 soluciones ejecutadas**.
- FastAPI P13 y Streamlit P14: PASS con sus dependencias en un entorno temporal de QA. Salud, creación 201, validación 422, OpenAPI, arranque real de Uvicorn, CSV y filtros de Streamlit AppTest.
- Chromium local: PASS las suites antigua y nueva, perfiles temporales, responsive 320–1440, examen/repaso, JSON, Orange y ausencia de errores JS.
- Paquete alojado generado localmente: PASS Worker, CSP, rutas cerradas y navegador. Se ejecutaron Python, NumPy/Pandas, sklearn Pipeline con CSV completo y field_validator de Pydantic en el navegador; errores y timeout de un bucle infinito comprobados. Esto no es un despliegue de producción.
- Cuentas y sincronización: PASS pruebas de servidor/catálogo, sincronización JS y navegador real con registro/login, dos sesiones, conflictos, recuperación y nueva contraseña. Gunicorn con dos workers: 200/409 ante escrituras concurrentes sin pérdida de actualización. Se conserva el parche OCI worker-src self y su prueba.
- Orange 3.40.0: PASS ocho workflows y esquema de comparación contra registro real; CV real de tres learners; **widgets GUI reales File → Select Columns → Test & Score**, carga de 150 filas y tres resultados válidos. **El puente lanzó el proceso GUI real con M09**, siguió activo tras el arranque y se cerró al terminar. Renderizado Qt offscreen y perfil temporal: no se simula una sesión Windows ni se interactúa con el escritorio personal.
- Elasticsearch 9.5.4: PASS mapping text/keyword/double, indexado, Query DSL de rango, agregaciones terms/sum y rechazo de un precio no numérico.
- Kibana 9.5.4: PASS API disponible, creación/lectura/borrado de data view de QA; parser KQL real del paquete instalado y ejecución del DSL resultante contra Elasticsearch con dos resultados esperados.
- NiFi 2.12.0: PASS API autenticada, grupo nuevo, GetFile → PutFile real, CSV de salida exacto, relationships y backpressure configurados, eventos reales de provenance. Solo se modifica el NiFi desechable.
- Kafka 4.3.1 (imagen local apache/kafka:latest): PASS creación de topic con dos particiones, producción/consumo de tres mensajes JSON, offsets confirmados por partición y reanudación sin releer mensajes confirmados.
- Kafka Connect: PASS source FileStream → topic → sink FileStream con dos líneas de salida exactas. Se ejecuta el worker real incluido en la imagen, sin instalar plugins.
- Logstash 9.5.4: PASS pipeline real con entrada JSON, grok, date, conversión numérica mutate y salida JSON comprobada.

## Alcance y límites

No se ha probado Windows nativo; las rutas de detección Windows tienen pruebas unitarias. El test de Kafka Connect usa los plugins FileStream incluidos en la imagen; no equivale a certificar los conectores JDBC/MongoDB del laboratorio ni a modificar las bases de datos existentes. No se ha ejecutado una práctica humana completa, ni instalado Jupyter ni modificado Big_Data.

Los primeros intentos ajustaron el propio comprobador a esta instalación: sintaxis de env-file Docker, publicación de puertos, ruta del Node incluido en Kibana y refresh sin cuerpo de Elasticsearch. No se relajaron las aserciones de funcionalidad de la aplicación.

## Repetición

```bash
# Suite local (usar un intérprete con requirements-study-qa.txt instalados)
python study_lab/scripts/run_checks.py --repo /ruta/a/Big_Data --frameworks --browser

# Todas las integraciones Docker: solo imágenes existentes, sin pull
python study_lab/test_external_docker.py
# Selección independiente (Kibana incluye su dependencia Elasticsearch)
python study_lab/test_external_docker.py --services kafka logstash

# Orange existente; nunca lo instala el test
/ruta/al/python-de-orange study_lab/test_orange.py
python study_lab/test_orange_bridge.py

# Worker y Python real en navegador, sin publicación
python study_lab/scripts/run_hosted_smoke.py --runner

PYTHONPATH=. python -m unittest distribution.test_server distribution.test_catalog
PYTHONPATH=. python distribution/test_browser.py
PYTHONPATH=. STUDY_GUNICORN=/ruta/a/gunicorn python distribution/test_gunicorn.py
node distribution/test_sync.cjs
```

Las suites de navegador locales requieren un servidor en `NIIS_TEST_URL` y ChromeDriver en `NIIS_DRIVER_URL`; los runners de cuentas y paquete alojado crean y cierran sus propios servidores efímeros. `run_checks.py` admite además `--external-docker` y `--orange-python /ruta/al/python-de-orange`. Los logs locales quedan en `qa-artifacts/` (ignorado por Git).
