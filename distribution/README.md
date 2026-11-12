# Distribución con cuentas — estado: implementado y probado localmente, no desplegado en OCI

Registro abierto mediante alias y contraseña, login, logout y progreso por cuenta entre dispositivos. No cambia la audiencia del Site existente. Se aloja en un origen HTTPS propio de OCI; el contenido solo se entrega tras iniciar sesión. Los enlaces a Big_Data siguen requiriendo autorización independiente en GitHub. No se distribuyen apuntes completos, Erronkas ni credenciales.

Cada cuenta tiene un identificador aleatorio; el servidor obtiene su identidad exclusivamente de una sesión HttpOnly. No acepta un identificador de usuario del cliente para leer/escribir progreso. Contraseñas con scrypt (N=131072, r=8, p=1) y salt aleatorio; tokens de sesión almacenados como hash, expiración de 7 días, cookie Secure/SameSite=Strict y validación Origin/CSRF. SQL parametrizado, cuerpos limitados a 2 MB, límite de 100 cuentas y límites persistentes de intentos. No hay correos, registro de contraseñas ni logs de respuestas.

El progreso de esta edición se carga del servidor en memoria; no lee, migra ni sobrescribe el localStorage del propietario. Se puede importar voluntariamente un JSON desde Mi progreso. El servidor usa revisión incremental y actualización atómica: un dispositivo obsoleto recibe conflicto, conserva su respuesta en memoria y ofrece exportar antes de recargar. Una respuesta de red perdida se reconcilia sin duplicar el guardado. El indicador superior distingue pendiente, guardado y error. Cerrar sesión espera al guardado. Ante cierre forzado/crash durante una desconexión, los cambios aún no sincronizados pueden perderse: exportar JSON antes de salir. No hay fusión automática de cambios ni recuperación de contraseña en esta primera versión; el formulario lo indica.

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

La ausencia de `~/.oci/config`, variables OCI o un conector autenticado impide auditar tenancy/región/IAM/coste e identificar una máquina real. No se afirma gratuidad ni despliegue. Antes de cualquier mutación se requiere inventario de solo lectura y preflight de `oci-always-free-guard`, un diff ligado a los recursos reales, reversión y autorización correspondiente. No se instala ningún agente ni se utiliza una clave administradora. Los templates siguientes NO son un plan OCI aprobado.

1. Verificar máquina existente, HOME, shape, discos/uso agregados y coste. Confirmar acceso operativo autorizado, dominio/DNS y puertos; la IP y el dominio no son secretos. Credenciales únicamente por el mecanismo seguro de T3, nunca por chat/Git/argumentos.
2. En la máquina verificada, usar una cuenta de servicio `study-lab` y código inmutable bajo `/opt/niis-study-lab`. Preparar un venv e instalar `distribution/requirements.txt`. La base queda fuera del checkout en `/var/lib/study-lab`, directorio 0700 y archivo 0600. No subirla ni incluirla en un paquete.
3. Configurar `/etc/niis-study-lab.env` con `STUDY_ORIGIN=https://DOMINIO_REAL`. Configurar Nginx y certificados HTTPS existentes/validados usando `nginx.conf.template` y validar con `nginx -t`. El backend escucha **solo** 127.0.0.1:8090; Nginx reemplaza `X-Real-IP`. No exponer 8090. El dominio, certificados, recursos, firewall y DNS deben concretarse antes de aplicar; no ejecutar el template con marcadores.
4. Revisar e instalar `study-lab.service`; iniciar únicamente tras aprobación del cambio concreto y controles OCI. Gunicorn usa dos workers, memoria limitada y SQLite fuera del código. Nginx realiza buffering, limita cuerpos e intentos y termina TLS. No crear balanceadores ni bases administradas de coste desconocido.
5. Verificar HTTPS y cookie Secure, creación de dos cuentas de prueba, aislamiento, segundo dispositivo, conflicto y logout. Eliminar cuentas/datos de prueba solo mediante un procedimiento acordado; no borrar cuentas reales. Conservar el Site privado anterior como alternativa y no redirigirlo todavía.
6. Antes de actualizar, realizar backup consistente de SQLite (`sqlite3.Connection.backup`) a un directorio privado fuera del checkout; no copiar una base activa sin ese mecanismo. No automatizar backups cloud, cron ni alertas sin autorización. Reversión: detener el servicio nuevo y restaurar el código anterior compatible, conservando la base y sin reemplazarla por una copia antigua salvo restauración explícita.

Paquete de allowlist, sin secretos, bases ni progreso (requiere archivos de despliegue ya comiteados):

```sh
python distribution/package.py --output /ruta/privada/distribution-NUEVO.tar.gz
```

El resultado identifica commit y SHA-256; `packaged_not_deployed` nunca significa publicado. La sincronización periódica actual solo publica en Sites: no se ha conectado automáticamente a este servidor OCI. Esa integración requiere el destino verificado y despliegue del mismo paquete probado, no una segunda automatización sin control.

Referencias verificadas: [Gunicorn detrás de proxy](https://gunicorn.org/deploy/) y [condiciones Always Free de Oracle](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm). Las condiciones públicas no sustituyen auditar el consumo real de la cuenta.
