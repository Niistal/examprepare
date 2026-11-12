# Distribución con cuentas — desplegado y verificado en OCI

Registro abierto mediante alias y contraseña, login, logout y progreso por cuenta entre dispositivos. No cambia la audiencia del Site existente. Se aloja en un origen HTTPS propio de OCI; el contenido solo se entrega tras iniciar sesión. Los enlaces a Big_Data siguen requiriendo autorización independiente en GitHub. No se distribuyen apuntes completos, Erronkas ni credenciales.

Cada cuenta tiene un identificador aleatorio; el servidor obtiene su identidad exclusivamente de una sesión HttpOnly. No acepta un identificador de usuario del cliente para leer/escribir progreso. Contraseñas con scrypt (N=131072, r=8, p=1) y salt aleatorio; tokens de sesión almacenados como hash, expiración de 7 días, cookie Secure/SameSite=Strict y validación Origin/CSRF. SQL parametrizado, cuerpos limitados a 2 MB, límite de 100 cuentas y límites persistentes de intentos. No hay correos, registro de contraseñas ni logs de respuestas.

El progreso de esta edición se carga del servidor en memoria; no lee, migra ni sobrescribe el localStorage del propietario. Se puede importar voluntariamente un JSON desde Mi progreso. El servidor usa revisión incremental y actualización atómica: un dispositivo obsoleto recibe conflicto, conserva su respuesta en memoria y ofrece exportar antes de recargar. Una respuesta de red perdida se reconcilia sin duplicar el guardado. El indicador superior distingue pendiente, guardado y error. Cerrar sesión espera al guardado. Ante cierre forzado/crash durante una desconexión, los cambios aún no sincronizados pueden perderse: exportar JSON antes de salir. No hay fusión automática de cambios. La recuperación utiliza un código personal de un solo uso: al restablecer contraseña se renueva el código y se revocan las sesiones, conservando el progreso. Los usuarios existentes pueden obtener/renovar el código desde su sesión confirmando la contraseña actual. El servidor almacena solo el hash del código. Sin código guardado no se puede demostrar la propiedad de una cuenta; no hay recuperación por correo ni preguntas de seguridad.

## Pruebas

Desde la raíz:

```sh
python -m unittest distribution.test_server -v
node distribution/test_sync.cjs
python -m distribution.test_browser
STUDY_GUNICORN=/ruta/al/venv/bin/gunicorn python -m distribution.test_gunicorn
```

Las pruebas crean bases y cuentas temporales. No usan el Site ni perfiles o progreso reales. Comprueban aislamiento entre usuarios, persistencia en otra sesión/reinicio, conflicto sin sobrescritura, sesión cambiada en otra pestaña, cookies y expiración, CSRF/Origin, rutas privadas, contraseñas, límites y guardado concurrente con los dos workers reales de Gunicorn. Chromium también comprueba registro, login, respuesta sincronizada, logout y vista móvil. Los 401 al comprobar acceso después de logout y 409 al provocar conflicto son respuestas esperadas; no errores JavaScript.

## Preparación para OCI, sin aprovisionar recursos

La consola Chrome autenticada permitió identificar el destino y consultar HOME, suscripción, capacidad y costes. No se configuró OCI CLI ni se entregaron credenciales cloud al servidor. No se crearon ni redimensionaron recursos OCI ni se modificaron IAM, cuotas, presupuestos, redes o facturación. La instalación de aplicación utilizó el acceso SSH operativo existente, sin copiar claves. Para futuras mutaciones de recursos OCI sigue siendo obligatorio el inventario completo y preflight de `oci-always-free-guard`, con un diff ligado a los recursos reales y aprobación correspondiente. Los templates siguientes NO son un plan de aprovisionamiento OCI aprobado.

1. Verificar máquina existente, HOME, shape, discos/uso agregados y coste. Confirmar acceso operativo autorizado, dominio/DNS y puertos; la IP y el dominio no son secretos. Credenciales únicamente por el mecanismo seguro de T3, nunca por chat/Git/argumentos.
2. En la máquina verificada, usar una cuenta de servicio `study-lab` y código inmutable bajo `/opt/niis-study-lab`. Preparar un venv e instalar `distribution/requirements.txt`. La base queda fuera del checkout en `/var/lib/study-lab`, directorio 0700 y archivo 0600. No subirla ni incluirla en un paquete.
3. El despliegue actual reutiliza Caddy y `Caddyfile.template`; el template Nginx es solo una alternativa para otros destinos. Configurar `/etc/niis-study-lab.env` con `STUDY_ORIGIN=https://DOMINIO_REAL`. Configurar Nginx y certificados HTTPS existentes/validados usando `nginx.conf.template` y validar con `nginx -t`. El backend escucha **solo** 127.0.0.1:8090; Nginx reemplaza `X-Real-IP`. No exponer 8090. El dominio, certificados, recursos, firewall y DNS deben concretarse antes de aplicar; no ejecutar el template con marcadores.
4. Revisar e instalar `study-lab.service`; iniciar únicamente tras aprobación del cambio concreto y controles OCI. Gunicorn usa dos workers, memoria limitada y SQLite fuera del código. Nginx realiza buffering, limita cuerpos e intentos y termina TLS. No crear balanceadores ni bases administradas de coste desconocido.
5. Verificar HTTPS y cookie Secure, creación de dos cuentas de prueba, aislamiento, segundo dispositivo, conflicto y logout. Eliminar cuentas/datos de prueba solo mediante un procedimiento acordado; no borrar cuentas reales. Conservar el Site privado anterior como alternativa y no redirigirlo todavía.
6. Antes de actualizar, realizar backup consistente de SQLite (`sqlite3.Connection.backup`) a un directorio privado fuera del checkout; no copiar una base activa sin ese mecanismo. No automatizar backups cloud, cron ni alertas sin autorización. Reversión: detener el servicio nuevo y restaurar el código anterior compatible, conservando la base y sin reemplazarla por una copia antigua salvo restauración explícita.

Paquete de allowlist, sin secretos, bases ni progreso (requiere archivos de despliegue ya comiteados):

```sh
python distribution/package.py --output /ruta/privada/distribution-NUEVO.tar.gz
```

El resultado identifica commit y SHA-256; `packaged_not_deployed` nunca significa publicado. La sincronización existente de Big_Data conserva sus guardas y publicación en Sites. Un timer local independiente comprueba cada 30 minutos si el catálogo comiteado y subido debe actualizarse también en OCI. Lee el mismo checkout y requiere árbol limpio, rama y commit remoto exactos. Ejecuta integridad de artefactos/materiales, aprendizaje/generador y smoke alojado antes de enviar los bytes; repite hashes y base al terminar. No crea ejercicios, commits, push ni recursos cloud. Depende de que este equipo y su conexión estén disponibles.

Referencias verificadas: [Gunicorn detrás de proxy](https://gunicorn.org/deploy/) y [condiciones Always Free de Oracle](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm). Las condiciones públicas no sustituyen auditar el consumo real de la cuenta.

## Evidencia de publicación — 12/11/2026

URL: https://niis-study-lab.51-170-37-119.sslip.io/login

Destino existente: `server-bots`, Madrid (HOME y única región suscrita observada), A1 de 2 OCPU/12 GB y volumen de arranque de 200 GB. Antes de instalar se observaron unos 190 GB libres y más de 9 GB de memoria disponible. La consola confirmó PAYG y mostró 0,00 EUR en el análisis del 1 al 12 de noviembre y en cargos actuales. Oracle advierte retraso de consumo; esta observación no certifica costes futuros ni sustituye una auditoría completa del tenancy.

No se crearon VM, discos, backups, IP, DNS OCI, balanceadores, bases administradas ni servicios cloud adicionales. Se reutilizaron CPU, memoria, disco e IP existentes y Caddy. Se añadieron el paquete oficial Python venv (tres paquetes nuevos, sin actualizaciones/eliminaciones), un venv con Gunicorn, un usuario de sistema sin login y el servicio `study-lab` con límite de 512 MB. Caddy no admitía reload por systemd: se validó su configuración y se efectuó un reinicio controlado; Caddy, Product Radar y Study Lab quedaron activos. Las rutas de Product Radar se conservaron; el nuevo host solo apunta a 127.0.0.1:8090.

La dirección temporal usa resolución pública sslip.io basada en la IP, sin compra ni cambio de DNS del dominio del propietario. Caddy obtuvo un certificado HTTPS válido. No implica disponibilidad garantizada de ese proveedor DNS; se puede sustituir por un subdominio propio cuando se configure.

Paquete instalado: commit `4b0d936522e91414c61fd15e18b4f41797d08b6e`, SHA-256 `b819ca5b57d21dd205e11c397ccfbdac0c7bbaf4b876f6bec2ef4645379ab842`. Se verificó el hash antes de extraer el paquete. No contiene datos de cuentas ni credenciales.

Pruebas locales: seis casos de seguridad/persistencia; sincronización y recuperación de respuesta perdida; Chromium con cuentas aisladas y conflicto entre sesiones; Gunicorn real con dos escrituras simultáneas (200/409). Producción: HTTPS verificado y formulario visible en Chrome; registro/login con dos cuentas temporales, cookies Secure/HttpOnly, persistencia en otra sesión, aislamiento, conflicto 409, logout y acceso anónimo 401 al documento/Worker. Se eliminaron exclusivamente las cuentas, sesiones y respuestas temporales creadas por esa prueba. No se abrió ni modificó el progreso real del propietario. La primera cuenta personal la crea el propietario desde el formulario; no hay contraseña compartida ni cuenta administradora precreada.

Reversión operativa: detener/deshabilitar solo `study-lab.service`, retirar exclusivamente el bloque entre `# BEGIN NIIS STUDY LAB` y `# END NIIS STUDY LAB` de Caddyfile, validar Caddy y reiniciar de forma controlada. Conservar `/var/lib/study-lab` y las rutas anteriores. No eliminar cuentas ni reemplazar la base al revertir código. El Site anterior sigue privado y disponible, sin cambiar audiencia.

## Recuperación y automatización del catálogo

El registro muestra un código de recuperación y espera a que el usuario lo guarde antes de entrar. «He olvidado mi contraseña» requiere usuario, código y nueva contraseña. Cada recuperación rota el código y revoca todas las sesiones; el código nunca se almacena en claro. Desde la barra de cuenta, «Código de recuperación» permite obtener uno nuevo tras reautenticarse. No enviar estos códigos al propietario, por chat ni a logs.

El timer local `niis-study-oci-sync.timer` invoca `distribution/sync_catalog.py`, compartiendo el lock de la sincronización existente. Ante trabajo sin commit, rama/base distinta, runtime pendiente de desplegar o fallo de prueba/red, no publica. La tarea siguiente vuelve a comprobarlo; `oci-catalog-pending.json` conserva el estado y el hash sin incluir progreso ni credenciales. La clave privada de publicación se genera y conserva solo en el equipo del propietario, con modo 0600. No se copia a OCI ni se usa un ssh-agent nuevo.

En OCI, el usuario `study-publisher` tiene un único comando SSH forzado y sin PTY/forwarding: el receptor `catalog_receiver.py`. Su regla sudo permite exclusivamente ejecutar ese archivo inmutable como root, sin argumentos añadidos. Solo puede consultar hashes de despliegue o publicar un documento HTML de hasta 8 MB, con hash, SHA de fuente y runtime exactos. No interpreta comandos, ejecuta JavaScript ni acepta rutas de destino. Sustituye atómicamente únicamente `study_lab/index.html`; no accede a la base de cuentas ni reinicia servicios. La entrega repetida devuelve unchanged y no vuelve a escribir el documento. Una nueva versión de servidor/login/sync requiere despliegue explícito y bloquea el timer hasta que coincidan los hashes.

El origen HTTPS de la edición OCI se conserva para no cambiar el enlace compartido ni las sesiones. Un dominio propio estable requiere controlar su registro DNS; no se compra ni se modifica un dominio ajeno automáticamente.
