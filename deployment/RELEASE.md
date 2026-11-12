# Publicación tras merge

La fuente de producción con cuentas es `Niistal/examprepare/master`. La PR se valida en GitHub Actions; al hacer merge se vuelve a ejecutar `release.yml` sobre el commit definitivo. Solo si termina correctamente se conserva `study-release-<sha>/release.tar.gz` durante 14 días. El workflow tiene permisos de lectura y no recibe claves SSH. Los PR de forks nunca publican paquetes de producción.

El publicador local consulta cada cinco minutos el HEAD actual de `master` y exige una ejecución `push` correcta de ese mismo SHA. Descarga su artefacto y compara cada archivo con el blob del árbol Git de ese commit, además de comprobar la lista de archivos permitidos. Un commit nuevo con CI pendiente o fallida conserva la versión anterior. Recomprueba HEAD antes de enviar e instalar. No depende de la rama ni de archivos sin commit del checkout de desarrollo.

La instalación reutiliza la VM, el servicio y el SSH del operador existentes. No crea recursos OCI, credenciales ni runners de GitHub. Antes de sustituir el código hace una copia consistente SQLite y del código bajo `/var/lib/study-lab-releases`, accesible solo por root. Detiene Study Lab, sustituye los archivos con escrituras atómicas, inicia el servicio y comprueba salud. Solo actualiza los dos límites de cuerpo del bloque Study Lab de Caddy a 11 MB; valida antes de reiniciarlo. Las rutas de otros servicios se conservan. Si falla, revierte código y proxy; nunca restaura automáticamente una base antigua sobre las respuestas actuales. Cambios de dependencias o de unidad systemd se bloquean y requieren instalación explícita.

## Activación en el equipo del propietario

Instalar desde un commit revisado; las copias fuera del checkout evitan ejecutar código de una rama en revisión:

```sh
install -d -m 700 ~/.local/lib/niis-study-release
install -m 600 distribution/sync_release.py distribution/deploy_release.py ~/.local/lib/niis-study-release/
install -m 644 distribution/niis-study-release.service distribution/niis-study-release.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user disable --now niis-study-oci-sync.timer
systemctl --user enable --now niis-study-release.timer
systemctl --user start niis-study-release.service
```

Se sustituye el timer de catálogo que seguía `feat/niis-study-lab`; dejarlo activo podría volver a entregar HTML antiguo. El nuevo publicador comparte su lock para excluir instalaciones concurrentes. La indexación del temario y el Site privado son procesos independientes; no se cambia su audiencia ni se publica en Sites desde este workflow.

Requisitos locales: `gh` autenticado con lectura del repo/Actions, SSH existente en `~/.ssh/product_radar_admin_20261106`, host conocido y acceso sudo no interactivo ya configurado. No copiar claves a GitHub. Si el equipo está apagado o no tiene acceso, producción conserva la versión instalada; la próxima ejecución retoma el HEAD actual. Fallos se consultan con `journalctl --user -u niis-study-release.service`. El estado confirmado queda en `~/.local/state/niis-study-lab/release-published.json`; en el servidor, `/var/lib/study-lab-releases/current.json` conserva SHA y hashes instalados.

El paquete tiene una lista explícita en `package.py` y `deploy_release.py`. Si una versión necesita nuevos archivos (por ejemplo un bundle de materiales), actualizar y revisar ambos, sus pruebas y la copia instalada del publicador antes de desplegarla. Cambios futuros de estos scripts no sustituyen automáticamente el instalador privilegiado aprobado. Las copias de seguridad permanecen en el volumen existente; su retención se gestiona por el operador.

## Comprobación y reversión

Tras una publicación, comprobar `/health` y `/login` por HTTPS y el acceso autenticado con una cuenta temporal. No leer progreso del propietario. Las pruebas del PR verifican arranque fallido, reversión conservando escrituras posteriores al backup, rechazo de rutas/enlaces, identidad de blobs y modificación acotada del proxy. Los tests simulan el control de systemd; el despliegue real se informa por separado.

Para pausar publicaciones: `systemctl --user disable --now niis-study-release.timer`. Para revertir manualmente, parar solo Study Lab, recuperar el código de la copia indicada en `current.json` y arrancar de nuevo. Mantener `/var/lib/study-lab/study.sqlite3`; no reemplazarla por el backup salvo una restauración de datos explícita.

## Biblioteca de estudio y archivos originales

El runtime contiene el lector completo comprimido y su manifiesto; se valida contra Git igual que el resto del código. Los originales voluminosos **no se añaden al artefacto automático de runtime**, para conservar sus límites y verificación de origen.

Para preparar la entrega completa desde un commit limpio con `study_lab/material-assets/` instalado:

```bash
python distribution/package.py --require-materials \
  --output /tmp/study-runtime.tar.gz \
  --materials-output /tmp/study-materials.tar.gz
```

El resultado devuelve hashes SHA256 independientes. Instalar primero el runtime mediante el publicador revisado y luego ejecutar en el host existente:

```bash
python3 /opt/niis-study-lab/distribution/install_materials.py \
  /ruta/study-materials.tar.gz SHA256_DEVUELTO \
  --root /opt/niis-study-lab
```

El instalador lee el manifiesto ya instalado, valida cada nombre/tamaño/hash y escribe por streaming en staging. Rechaza enlaces, rutas ajenas, duplicados, archivos incompletos o manifiestos que cambian durante la instalación. Sustituye únicamente el directorio de materiales y conserva el anterior. No modifica SQLite, usuarios, servicios ni proxy. La copia binaria local no está en Git; no asumir que GitHub Actions puede acceder al repositorio académico privado. CI comprueba todo el contenido de lectura embebido y usa fixtures para los originales cuando no están instalados.

La entrega de originales exige la sesión de la aplicación; no exige sesión de GitHub ni cambia la audiencia o el registro existentes. Los documentos se leen sin ejecutar código. HTML y SVG originales se descargan como attachments, nunca como páginas activas del mismo origen. Los PDF y medios se entregan con Range/HEAD. Los patrones de credenciales detectados se filtran en las vistas y archivos de texto; los binarios afectados no se distribuyen literalmente.
