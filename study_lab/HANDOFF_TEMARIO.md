# Traspaso: lector del temario · detenido por petición del propietario

El propietario pidió integrar el contenido del temario de Niistal/Big_Data visualmente en la web, sin obligar a los alumnos a entrar en su GitHub privado. Después pidió dejarlo subido en una PR para que otro agente continúe más adelante. **No fusionar ni desplegar por esta entrega.**

## Implementado

- Lector modal dentro de la app existente: Markdown, tablas, código, fórmulas MathML, índice, anterior/siguiente, guardar lectura y navegación entre documentos. Los enlaces a materiales del GitHub privado se interceptan y abren la copia local del temario.
- Snapshot del repositorio académico `db1561d8b01e8f2f1ff7f085d1264e67c5a732bd`: **657 recursos**, **218 documentos de lectura completos** (127 Markdown más PDF/cuadernos/documentos/presentación/textos), 606 recursos con texto legible. No hubo errores de extracción. Los datasets/configuraciones muy voluminosos llevan una vista previa explícita y descarga completa desde la app.
- Contenido de lectura embebido en `material-reader-data.js`, comprimido; index.html generado mide unos 5 MB y no necesita GitHub para leer. No se ejecuta código de los cuadernos ni HTML activo del repositorio.
- Originales servidos por allowlist con autenticación de la aplicación, streaming, Range/HEAD, hashes y bloqueo de traversal/symlinks. PDF, imágenes, audio/vídeo y descargas no requieren autenticación de GitHub. El acceso de cuentas existente se conserva.
- Se filtran patrones de credenciales en 37 recursos. Los binarios con coincidencias en su texto extraído no se copian literalmente; la vista de lectura sí se conserva filtrada. Revisar estos casos antes de liberar: puede haber ejemplos docentes. No desactivar la protección ni publicar valores reales por rutina.
- Empaquetado incluye el módulo de entrega, manifiesto y originales cuando están instalados. `--require-materials` exige la biblioteca completa. Un entorno CI sin originales genera explícitamente `materials_status=reading_only`, no una supuesta entrega completa.

## Dónde está cada cosa

- `study_lab/material-reader.js`: interacción del lector.
- `study_lab/scripts/build_material_library.py`: importación desde objetos Git, extracción y saneado.
- `study_lab/material-library.json`: manifiesto de archivos y huellas.
- `study_lab/material-reader-data.js`: lectura comprimida, incluida en Git/HTML.
- `study_lab/material_assets.py`: entrega binaria compartida por servidor local y distribución autenticada.
- `study_lab/material-assets/`: **originales preparados localmente, ignorados por Git** (unos 461 MB disponibles). No borrarlos: son necesarios para probar/empaquetar la versión completa. Los alumnos no necesitan el repo académico.
- Copia académica temporal disponible: `/tmp/niis-study-academic-20261112`, con objetos Git del commit fijado. Su checkout sigue en la revisión previa; el importador lee los blobs del commit indicado, no los archivos del checkout. No modificar `/home/admin/Big_Data`.
- Dependencias de importación: `study_lab/requirements-material-reader.txt` y `pdftotext`. El navegador y el servidor no requieren los parsers Python.

## Pruebas ya ejecutadas

- `python study_lab/test_material_reader.py`: **7 pruebas PASS**, cobertura de lectura, HTML inerte, MathML/tablas, integridad de originales, autorización, HEAD/Range, traversal/symlink/tampering y HTML como attachment.
- `python study_lab/test_material_reader_browser.py`: **PASS** en Chromium real. Lectura en las cinco asignaturas, fuentes de casos, enlaces internos, PDF desde el mismo origen con Range real, responsive 320/390/768/1440, editor de Programazioa conservado y cero errores JS. Se corrigió una carrera entre cerrar/reabrir el diálogo.
- `python study_lab/test_artifacts.py /tmp/niis-study-academic-20261112`: PASS antes de la última regeneración equivalente de contenido.
- `python -m unittest distribution.test_server distribution.test_catalog`: **13 PASS**.
- `python study_lab/test_local_tools.py`: **15 PASS**.
- Suite de navegador histórica `test_browser.py`: PASS con el lector integrado antes del último arreglo del cierre del modal.
- No se ha ejecutado aún toda la matriz final de CI, ni creado/probado el archivo de despliegue completo de esta nueva biblioteca. No se ha desplegado.
- Logs locales: `/tmp/niis-material-reader-browser.log`, `/tmp/niis-reader-server-regression.log`, `/tmp/niis-reader-local-regression.log`, `/tmp/niis-reader-old-browser.log`, `/tmp/niis-reader-build-final.log`. Captura: `study_lab/qa-artifacts/material-reader.png`.

## Para retomar

1. Leer estado Git y esta PR. No hacer stash/reset/checkout ni pisar trabajo ajeno.
2. La base es la rama de PR #7 (`feat/niis-study-lab`, commit `b41d8a4`); este trabajo se publica en `feat/material-reader`, sin modificar la rama remota de #7. Coordinar la integración de ambas PRs, sin duplicar los cambios de CI del otro hilo.
3. Revisar el saneado del importador y los casos con credenciales detectadas. Comprobar el lector también con cuentas reales de QA y originales multimedia, y añadir tests de exportación/sincronización necesarios. El original PDF conserva diseño/diagramas; la lectura PDF es texto extraído, no una reproducción de su maquetación.
4. Conectar los nuevos tests al runner/CI. El workflow de #7 no tiene acceso automático al GitHub privado Big_Data; no crear secretos ni prometer que CI tiene todos los originales. El cuerpo de lectura sí está comiteado.
5. Ejecutar regresiones, verificar `build.py`, empaquetar con `python distribution/package.py --require-materials --output /tmp/study-materials-release.tar.gz` desde un commit limpio. Los archivos originales se verifican contra el manifiesto antes de incluirse.
6. Coordinar despliegue completo de runtime/manifest/originales: el publicador de solo HTML bloquea cambios de runtime; no eludirlo. Conservar cuenta/progreso y el parche OCI worker-src self y las mejoras de gráficos/respaldos de PR #6.
7. Las autorizaciones de merge/despliegue deben contrastarse con el propietario o su hilo de publicación; aquí se ha pedido expresamente parar y dejar la PR para otro momento.

Regenerar, si hace falta:

```bash
/ruta/a/python-con-dependencias study_lab/scripts/build_material_library.py \
  --repo /tmp/niis-study-academic-20261112 \
  --ref db1561d8b01e8f2f1ff7f085d1264e67c5a732bd
python study_lab/build.py
python study_lab/local_server.py --port 8097
# ChromeDriver para tests: 127.0.0.1:9515
NIIS_TEST_URL=http://127.0.0.1:8097 python study_lab/test_material_reader_browser.py
```

Se coordinó el worktree con el hilo de revisión/publicación: terminó y dejó sus cambios en PR #7. El lock exclusivo de este trabajo se libera al terminar esta entrega; no quedan agentes hijos ni procesos de QA de este trabajo intencionadamente activos.
