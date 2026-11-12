# NIIS Study Lab — publicación privada

Actualización autorizada por el propietario el 12/11/2026: se amplía la entrega local para permitir acceso desde internet. La aplicación local sigue disponible.

## Acceso

URL: https://niis-study-lab.ikernistal77.chatgpt.site

Sites aplica autenticación gestionada de ChatGPT y una política privada con un único usuario autorizado: el propietario. No se ha añadido una contraseña compartida ni un formulario de acceso en JavaScript. La restricción está en la plataforma, antes de entregar los archivos de estudio. La app alojada incluye un enlace para cerrar sesión.

No se ha verificado la configuración MFA de la cuenta del propietario y no se afirma que exista seguridad absoluta. El dispositivo y la sesión de ChatGPT siguen formando parte de la protección.

Proton Pass: no hay integración de bóveda disponible en esta sesión. No se ha guardado ni modificado ninguna credencial. El acceso reutiliza la cuenta ChatGPT; si esta usa un proveedor federado, la contraseña que puede autocompletar Proton corresponde a ese proveedor. Verificación pendiente por el propietario: https://github.com/Niistal/examprepare/issues/3

## Datos

Los 62 casos forman parte del paquete privado. No se han copiado los apuntes completos, los proyectos Erronka, `.venv`, credenciales ni archivos de progreso al alojamiento. Las respuestas y valoraciones permanecen en localStorage del navegador y origen. El progreso de localhost no aparece automáticamente en la web: exporta el JSON local e impórtalo en Mi progreso. La sincronización entre dispositivos no está implementada: https://github.com/Niistal/examprepare/issues/1

## Fuente y publicación

- Fuente de desarrollo: repositorio privado https://github.com/Niistal/examprepare, rama `feat/niis-study-lab`.
- Identidad Sites: `deployment/hosting.json`, sin secretos.
- Ejecutar `python study_lab/scripts/build_hosted.py` desde la raíz: reconstruye el standalone y genera `hosted_study_lab/dist/index.html` y su manifest de alojamiento.
- `hosted_study_lab/` es un checkout separado del repositorio de publicación Sites y está ignorado en el repositorio principal. Sus credenciales temporales se entregan al helper por stdin, nunca se guardan en archivos ni Git.
- El paquete publicado contiene únicamente `.openai/hosting.json` y el HTML estático generado en `dist/`. No sirve el árbol del repositorio.
- El build alojado añade aviso sobre progreso por navegador, cierre de sesión, noindex, referrer policy y CSP con hash del JavaScript. `connect-src 'none'` evita llamadas de red desde la app; abrir una fuente de GitHub mediante un enlace sigue siendo posible.
- Commit de publicación Sites: `a6031d155e008a7d33f36dda34f1e2507967154e`.
- Versión: `appgprj_6af50e3969208191aa07f9da6d4fe50e~appgver_c0cfcdbfdf6881918a2930655b6d9411`.
- Despliegue: `appgdep_6af50ee26f8081919e74c96e504c7c61`, estado `succeeded`.

## Pruebas de esta actualización

- Generador, recorridos completos, standalone y hashes de fuentes: PASS.
- Paquete alojado en Chromium headless: PASS. Navegación, ayudas, examen, borradores, recarga, reloj, JSON, vista móvil, enlace de cierre de sesión y CSP sin errores JS.
- Se usó puerto local 18080 para la copia alojada; 8081 estaba ocupado y no se detuvo su servicio.
- Plataforma Sites: publicación confirmada `succeeded`; política `custom`, un usuario y cero grupos.
- Peticiones HTTPS sin credenciales a `/` y `/index.html`: HTTP 403, sin banco ni código de la aplicación en el cuerpo. Esto comprueba la respuesta anónima observada, no sustituye una prueba de acceso del propietario en su navegador.
- No se accedió a Proton Pass ni se probaron credenciales del usuario.
- QA externa pendiente: https://github.com/Niistal/examprepare/issues/2

Para futuras publicaciones, usar la identidad existente y el workflow de Sites; no crear otro Site ni hacerlo público para resolver errores de autenticación.
