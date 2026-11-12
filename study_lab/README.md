# NIIS STUDY LAB — Big Data Intensivo · Versión 1

**Objetivo:** practicar antes de los exámenes del **16 al 20 de noviembre de 2026**, con ejercicios de **desarrollo real** en lugar de tests memorísticos. La herramienta es local, gratuita y no tiene servicios externos ni llamadas a IA. Solo el enlace de cada fuente abre GitHub, que requiere autorización al tratarse de un repositorio privado.

## 1. Qué contiene esta primera versión

- `index.html`: **archivo único autónomo**. Contiene todos los estilos, la aplicación JavaScript y el banco inicial de **62 ejercicios**. Se puede abrir mediante doble clic; para mayor compatibilidad se recomienda `localhost`.
- `app.js`, `style.css`, `shell.html`: fuentes editables para que T3 Code continúe sin tener que modificar 100 KB de HTML en cada iteración.
- `requirements-study.txt`: dependencias Python comunes para los ejercicios de datos.
- `requirements-study-extra.txt`: dependencias adicionales opcionales (API, Streamlit, Kafka y Faker). Se instalan solo si se van a practicar esas materias.
- `plantilla_examen.py`: plantilla de código con imports explícitos y punto de entrada.
- `iniciar.ps1`, `iniciar.sh`: arranque rápido del servidor estático. **No hace falta `.venv` para usar la web.**
- `preparar_python.ps1`, `preparar_python.sh`: creación y preparación del entorno Python independiente.
- `PROMPT_T3_CODE.md`: propuesta de evolución acotada para Claude/Codex mediante T3 Code.

### Exámenes numerados

Cada asignatura tiene los números **1 a 1000**. Cada número genera una secuencia determinista de cinco ejercicios diferentes dentro de la prueba. El orden de los cinco ejercicios cambia y el algoritmo evita repetir *la misma secuencia ordenada* dentro de los 1000 números de una asignatura. **Esto NO significa que existan 1000 enunciados originales distintos**: la diversidad depende de la amplitud del banco. El recorrido principal es finito: 27 casos de Programazioa y 8–9 por cada otra materia. Los números son una herramienta secundaria de repaso, no niveles que debas completar.

Modo **Guiado**: pistas y corrección por ejercicio. Modo **Sin ayudas**: enunciados, editor y reloj; se desbloquean las soluciones al finalizar el examen. No hay evaluación automática de la exactitud del código todavía: se utiliza rúbrica y autoevaluación. El HTML no ejecuta Python ni DSL; el desarrollo se prueba en terminal/VS Code/Orange/Elastic/Kafka según corresponda.

## 2. Calendario por orden de urgencia

| Día | Profesor | Asignatura | Carpeta real de Big_Data |
|---|---|---|---|
| Lunes 16/11 | Aitor | AA Programazioa | `05_AA_Programazioa/` |
| Martes 17/11 | Lander | Ikaskuntza Automatikorako Sistemak | `04_Ikaskuntza_Automatikorako_Sistemak/` |
| Miércoles 18/11 | Xabat | AA Ereduak | `03_AA_Ereduak/` |
| Jueves 19/11 | Janire | BD Sistemak | `06_BD_Sistemak/` |
| Viernes 20/11 | Janire | BD Aplikatua | `07_BD_Aplikatua/` |

Fuente troncal: [`ARIKETAK_AURKIBIDEA.md`](https://github.com/Niistal/Big_Data/blob/main/ARIKETAK_AURKIBIDEA.md). Recursos secundarios: `NotebookLM_Material_Estudio/<asignatura>/Guias_de_Estudio/` y `Quizzes_y_Examenes/` más los cuadernos `.ipynb` y PDFs de la carpeta de cada asignatura. **No utilizar las Erronkas CNC Guard y RetailEUS como referencia principal del nivel del examen**: sus soluciones integradas superan el nivel esperado de práctica autónoma en esta semana.

## 3. Arranque de la web — ninguna instalación de librerías

**Windows (PowerShell):** abre una terminal dentro de la carpeta extraída y ejecuta:

```powershell
.\iniciar.ps1
```

**Linux / Omarchy:**

```bash
bash iniciar.sh
```

Abre **http://127.0.0.1:8080**.

Alternativa sin scripts: `python -m http.server 8080 --bind 127.0.0.1` (Windows) o `python3 -m http.server 8080 --bind 127.0.0.1` (Linux) desde la carpeta. Si el puerto está ocupado, usa otro libre, por ejemplo `8081`, tanto en el comando como en la dirección del navegador.

## 4. Preparar Python para ejecutar los ejercicios

**Objetivo:** un solo `.venv` por laboratorio. Tener todos los paquetes comunes en `requirements-study.txt`; los imports de los ejercicios siguen siendo **explícitos y documentados**. Se recomienda Python **3.11** por compatibilidad con el stack académico. Si tu equipo no tiene 3.11, instala una versión compatible y ajusta el intérprete; los scripts intentan usar un Python disponible.

### Windows PowerShell

```powershell
# Desde la carpeta BigData_Intensivo_V1
.\preparar_python.ps1
.\.venv\Scripts\Activate.ps1
python -m pip list
python plantilla_examen.py
```

Si la política de PowerShell bloquea la activación, puedes ejecutar `.venv\Scripts\python.exe` directamente sin activarla; no es necesario cambiar políticas del equipo.

### Linux / Omarchy

```bash
# Desde la carpeta BigData_Intensivo_V1
bash preparar_python.sh
source .venv/bin/activate
python -m pip list
python plantilla_examen.py
```

Para añadir los paquetes opcionales:

```bash
python -m pip install -r requirements-study-extra.txt
```

Para verificar instalaciones:

```bash
python -c "import numpy, pandas, matplotlib, sklearn; print('DATA OK')"
python -c "import fastapi, streamlit, faker; print('EXTRAS OK')"  # si instalaste extras
python -m pip freeze > requirements-installed.txt
```

`requirements-installed.txt` es un **snapshot de tu máquina**, útil para diagnosticar, no un fichero que tengas que subir al repositorio académico.

### Recordatorio de ejecución según el ejercicio

| Caso | Comando / ubicación |
|---|---|
| Script normal | `python archivo.py` |
| Jupyter Notebook | `python -m jupyter lab` (instalando primero `jupyterlab` si lo necesitas) |
| FastAPI | `python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000` y `http://127.0.0.1:8000/docs` |
| Streamlit | `python -m streamlit run app.py --server.address 127.0.0.1` y `http://127.0.0.1:8501` |
| Elastic Stack de clase | Desde `06_BD_Sistemak/3_Elastic_Stack`: `docker compose up -d` y Kibana en `http://127.0.0.1:5601` si el stack está configurado |
| Kafka/NiFi | Usa los compose y configuraciones concretos de `07_BD_Aplikatua/`; sus servicios **no** vienen instalados con el HTML |

### Tabla de imports importantes

| Tema | Import y paquete |
|---|---|
| JSON / archivos | `import json`; `from pathlib import Path` — biblioteca estándar |
| NumPy | `import numpy as np` — `numpy` |
| Pandas | `import pandas as pd` — `pandas` |
| Matplotlib | `import matplotlib.pyplot as plt` — `matplotlib` |
| Seaborn | `import seaborn as sns` — `seaborn` |
| Scikit-Learn | `from sklearn.model_selection import train_test_split` — `scikit-learn` |
| FastAPI | `from fastapi import FastAPI` — `fastapi`; servidor `uvicorn` |
| Streamlit | `import streamlit as st` — `streamlit` |
| Faker | `from faker import Faker` — `faker` |
| Kafka | `from kafka import KafkaProducer, KafkaConsumer` — `kafka-python` |
| Hugging Face | `from transformers import pipeline` — `transformers`, descarga modelos aparte; *no instalado por defecto* |
| LangChain / FAISS | Dependencias adicionales del ejercicio original; consultar sus ficheros de requisitos para evitar incompatibilidades de versiones |

> Nota: `import numpy` **no instala** NumPy. Primero se instala con pip y después se importa en el archivo. Para aprender de verdad, escribe el import correspondiente en cada ejercicio; la plantilla está disponible para copiar sin tener que memorizar rutas complejas.

## 5. Cómo estudiar desde el jueves 12 al viernes 20

La propuesta es **70 % desarrollo / 30 % revisión de teoría**. El orden está diseñado para maximizar lo que se puede practicar de forma autónoma sin IA:

- **12/11:** Python, entorno, JSON, funciones, NumPy y Pandas; un simulacro guiado y otro sin ayudas.
- **13/11:** Limpieza, groupby, merge, visualizaciones, Scikit-Learn, FastAPI y Git/DVC.
- **14/11:** Simulacros de Programazioa y prácticas cortas de Orange/KNN/Logística. Solo consultar NotebookLM tras intentar cada ejercicio.
- **15/11:** Dos simulacros de Programazioa sin ayudas; última revisión de fallos repetidos.
- **16/11:** examen Programazioa; después, ML y Orange para el martes.
- **17/11:** examen ML; después, AA Ereduak (sesgos, fairness, ética, AI Act y fuzzy).
- **18/11:** examen Modelos; después, Elasticsearch, Query DSL, aggregations y Logstash.
- **19/11:** examen Sistemas; después, NiFi, Kafka, MariaDB→MongoDB y AEMET.
- **20/11:** examen Aplicada.

Una sesión corta: 5 min leer problema + 15 min implementar + 5 min ejecutar + 5 min autocorregir. Usa la puntuación **No aún / Con ayuda / Solo/a** y repite los ejercicios no dominados. No uses las soluciones originales mientras intentas resolver; el código de tu repo contiene entregas completas que pueden dar una falsa sensación de dominio.

## 6. Estado de entrega y límites

- **Listo**: interfaz autónoma, calendario, 62 ejercicios escritos, enlaces de fuentes, modo guiado/simulacro, puntuación manual, temporizador, 1000 secuencias numeradas por materia, progreso en `localStorage`, exportación/importación JSON.
- **No realizado**: ejecución real y tests automáticos de Python desde la web, importación masiva de notebooks/PDF, integración directa con NotebookLM y extracción/validación completa de cada ejercicio del repositorio. El estado actualizado y sus limitaciones están en `ESTADO_T3_CODE.md`.
- **No toca** GitHub, archivos de notas, materiales de compañeros, ni archivos de los proyectos Erronka. No se han enviado cambios a `main`.

© Uso personal, local y académico.

## Entrega T3 actualizada

Recorrido finito por competencias y ayudas en dos pasos: orientación, luego ejemplo/API e imports. Sigue la ruta de cada materia y repite lo que no puedas explicar sin mirar; no hay que completar mil niveles. Programazioa contiene 27 casos, Sistemas ML 9, AA Ereduak 8, BD Sistemak 9 y BD Aplikatua 9.

Consulta [ENTORNO_LOCAL.md](ENTORNO_LOCAL.md) para comandos exactos y [ESTADO_T3_CODE.md](ESTADO_T3_CODE.md) para pruebas y pendientes. El build integra `sources.js`, `app.js` y `style.css` en el standalone: `python build.py`. `sources.json` conserva ruta, sección, hash y commit de contraste. `verified` confirma ruta y tema, no certifica una respuesta como obra del profesor ni como solución exhaustiva.

La clave de progreso de V1 se conserva. Al ampliar el banco cambia la composición de los simulacros numerados de Programazioa; las respuestas anteriores siguen guardadas por ejercicio. Un simulacro antiguo cuya secuencia ya no coincide no se reanuda automáticamente. Exporta tu progreso antes de futuras actualizaciones.
