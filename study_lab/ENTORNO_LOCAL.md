# Entorno local — NIIS Study Lab

Ruta de entrega: `/home/admin/.t3/projects/examprepare/study_lab/`.
Fuente académica de solo lectura: `/home/admin/Big_Data`, rama `main`.
La web no necesita paquetes Python: sirve archivos estáticos y guarda el progreso en el navegador.

## Abrir la web

Dentro de `study_lab/`, en Windows PowerShell o Linux:

```sh
python -m http.server 8080 --bind 127.0.0.1
```

En Linux, usa `python3` si `python` no existe. Abre http://127.0.0.1:8080. Mantén la terminal abierta; Ctrl+C detiene el servidor. El progreso pertenece al origen del navegador: usa siempre el mismo navegador y puerto. Exporta JSON antes de cambiar de equipo, origen o limpiar el navegador. La importación reemplaza el progreso solo tras confirmarlo. No guardes ese JSON en Git.

## Python: entorno separado de los apuntes

Recomendado Python 3.11 o 3.12. Desde `study_lab/`:

```sh
python -m venv .venv
```

Linux / Omarchy (Bash):

```sh
source .venv/bin/activate
python -m pip install -r requirements-study.txt
python plantilla_examen.py
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-study.txt
python plantilla_examen.py
```

Si PowerShell bloquea la activación, no necesitas cambiar la política global: ejecuta directamente ` .\.venv\Scripts\python.exe -m pip install -r requirements-study.txt` y ` .\.venv\Scripts\python.exe plantilla_examen.py`.

Guarda cada práctica en una carpeta nueva, por ejemplo `practicas/pandas_01/archivo.py`, y ejecuta `python archivo.py` desde allí. Los CSV/PNG/JSON que produzca deben quedar allí, fuera de los apuntes. Cada solución incluye sus imports; el starter da el punto de partida. Los casos rotulados PSEUDOCÓDIGO, FLUJO, SQL o ANÁLISIS no son scripts Python.

## Extras, solo para el ejercicio que los necesita

```sh
python -m pip install jupyterlab
python -m jupyter lab --ip=127.0.0.1 --no-browser
```

FastAPI: guarda el código del caso P13 como `app.py`:

```sh
python -m pip install fastapi uvicorn
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Prueba http://127.0.0.1:8000/docs. `app:app` significa archivo `app.py`, objeto `app`.

Streamlit: guarda P14 como `app.py` en otra carpeta:

```sh
python -m pip install streamlit
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

CSV de ejemplo para P14:

```csv
categoria,importe
A,10
B,20
A,15
```

Faker: `python -m pip install faker`. Kafka Python: `python -m pip install kafka-python`. `requirements-study-extra.txt` agrupa estos extras por comodidad, pero no es obligatorio instalarlo entero. No se instalan Transformers, PyTorch, LangChain, DVC ni MLflow para usar la web. Los casos conceptuales de estas herramientas se resuelven con datos simulados o pseudocódigo sin servicios IA.

## Elastic / Kafka / NiFi: prácticas opcionales, no requisitos de la web

Los apuntes se conservan intactos. Para practicar infraestructura, copia solo el caso elegido a una carpeta de trabajo separada. Comprueba la configuración antes de arrancar: los compose de clase pueden exponer puertos a todas las interfaces. En la COPIA, usa `127.0.0.1:puerto:puerto` en cada puerto publicado. No ejecutes infraestructura remota.

Elastic: referencia `06_BD_Sistemak/3_Elastic_Stack/compose.yaml`. En la copia de esa carpeta:

```sh
docker compose config
docker compose up -d
docker compose ps
docker compose logs --tail=50
docker compose down
```

9200: API de Elasticsearch; 5601: Kibana. No uses `down -v` si quieres conservar los datos. Las consultas `GET productos/_search` se pegan en Kibana Dev Tools; la primera línea HTTP no forma parte del cuerpo JSON. El mapping de cada microcaso es propio y puede diferir de `produktuak` en clase. Para Logstash utiliza la copia del pipeline y sus plugins; los casos no se ejecutan dentro del editor HTML.

Kafka básico: referencia `07_BD_Aplikatua/3_Apache_Kafka/0-kasua-kafka-kaixo/README.md`. En su copia, revisa puertos y ejecuta:

```sh
docker compose config
docker compose up -d
docker exec iabd-kafka kafka-topics.sh --create --topic sensores --bootstrap-server localhost:9092
docker exec iabd-kafka kafka-topics.sh --describe --topic sensores --bootstrap-server localhost:9092
```

Ejecuta primero el consumidor (Puntos A07, terminal 1) y después el productor (A06, terminal 2), con `python consumidor.py` y `python productor.py`. El productor del banco manda temperaturas 20–22; el consumidor filtra >25, por lo que **no imprime esos registros**. Cambia una temperatura a 27 para comprobar el filtro. El consumidor permanece escuchando hasta Ctrl+C. Los advertised listeners del compose deben permitir el acceso desde el host; sigue el README del caso si difieren del ejemplo. Connect requiere plugins source/sink específicos: el esquema conceptual A09 no es una configuración lista para arrancar.

NiFi: referencia `07_BD_Aplikatua/2_Apache_NiFi_Aurreratua/06_ariketa_mariadb_mongodb/README.md`. Revisa el compose en la copia, ejecuta `docker compose config`, `docker compose up -d` y `docker compose ps`. La guía usa HTTPS 8443. Configura los Controller Services, JDBC driver y relaciones descritos allí; no copies credenciales al código del laboratorio. En QueryRecord del caso A02, `salmentak.csv` usa `;` y la columna numérica `Revenue`, no `importe`. En Docker, Input Directory y PutFile usan rutas del contenedor con volúmenes montados.

No se han arrancado Docker, Elastic, Orange, Kafka, NiFi, conectores ni servicios externos durante esta entrega. Sus comandos se contrastaron con las referencias locales; la ejecución de extremo a extremo queda pendiente. Windows se documentó, pero no se ejecutó desde este entorno Linux.

## QA reproducible de la entrega

Para ejecutar también las pruebas de FastAPI y Streamlit, instala solo en tu venv:

```sh
python -m pip install -r requirements-study-qa.txt
.venv/bin/python scripts/run_checks.py --repo /home/admin/Big_Data --browser --frameworks
```

En Windows sustituye `.venv/bin/python` por `.venv\Scripts\python.exe` y omite `--browser`: el script de Chromium actual usa rutas de Linux. Las pruebas Python crean y eliminan carpetas temporales fuera de los apuntes. La prueba API abre únicamente un puerto efímero en 127.0.0.1 y lo cierra al terminar. AppTest usa un CSV ficticio para probar Streamlit sin publicar una app.

El navegador de QA requiere servidor local 8080 y ChromeDriver 9515. Para el paquete alojado usa `NIIS_TEST_URL=http://127.0.0.1:18080 NIIS_TEST_HOSTED=1 python test_browser.py` después de servir `hosted_study_lab/dist/`. No ejecutes los tests sobre un perfil con tu progreso: el driver crea un perfil temporal propio.
