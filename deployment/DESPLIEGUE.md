# NIIS Study Lab — publicación privada

Actualización autorizada por el propietario el 12/11/2026: se amplía la entrega local para permitir acceso desde internet. La aplicación local sigue disponible.

## Acceso

URL: https://niis-study-lab.ikernistal77.chatgpt.site

Sites aplica autenticación gestionada de ChatGPT y una política privada con un único usuario autorizado: el propietario. No se ha añadido una contraseña compartida ni un formulario de acceso en JavaScript. La restricción está en la plataforma, antes de entregar los archivos de estudio. La app alojada incluye un enlace para cerrar sesión.

No se ha verificado la configuración MFA de la cuenta del propietario y no se afirma que exista seguridad absoluta. El dispositivo y la sesión de ChatGPT siguen formando parte de la protección.

Proton Pass: no hay integración de bóveda disponible en esta sesión. No se ha guardado ni modificado ninguna credencial. El acceso reutiliza la cuenta ChatGPT; si esta usa un proveedor federado, la contraseña que puede autocompletar Proton corresponde a ese proveedor. Verificación pendiente por el propietario: https://github.com/Niistal/examprepare/issues/3

## Datos

Los 73 casos forman parte del paquete privado. No se han copiado los apuntes completos, los proyectos Erronka, `.venv`, credenciales ni archivos de progreso al alojamiento. Las respuestas y valoraciones permanecen en localStorage del navegador y origen. El progreso de localhost no aparece automáticamente en la web: exporta el JSON local e impórtalo en Mi progreso. La sincronización entre dispositivos no está implementada: https://github.com/Niistal/examprepare/issues/1

## Fuente y publicación

- Fuente de desarrollo: repositorio privado https://github.com/Niistal/examprepare, rama `feat/niis-study-lab`.
- Identidad Sites: `deployment/hosting.json`, sin secretos.
- Ejecutar `python study_lab/scripts/build_hosted.py` desde la raíz: reconstruye el standalone y genera `hosted_study_lab/dist/server/index.js` y su manifest de alojamiento.
- `hosted_study_lab/` es un checkout separado del repositorio de publicación Sites y está ignorado en el repositorio principal. Sus credenciales temporales se entregan al helper por stdin, nunca se guardan en archivos ni Git.
- El paquete publicado contiene `.openai/hosting.json` y un Worker que responde con el HTML generado. Solo acepta GET/HEAD de `/` y `/index.html`; no sirve el árbol del repositorio ni ejecuta código del estudiante.
- El build alojado añade aviso sobre progreso por navegador, cierre de sesión, noindex, referrer policy y CSP con hash del JavaScript. `connect-src 'none'` evita llamadas de red desde la app; abrir una fuente de GitHub mediante un enlace sigue siendo posible.
- Commit de publicación Sites: `eba60dad77d8bd36cb12aa76f315151226e739db`.
- Versión: `appgprj_6af50e3969208191aa07f9da6d4fe50e~appgver_7f8b6eae818c819181573b8a9959b3c0`.
- Despliegue: `appgdep_6af530a9084881919e1aaa0226427b93`, estado `succeeded`.

## Pruebas de esta actualización

- Generador, recorridos completos, standalone y hashes de fuentes: PASS.
- Paquete alojado en Chromium headless: PASS. Navegación, ayudas, examen, borradores, recarga, reloj, JSON, vista móvil, enlace de cierre de sesión y CSP sin errores JS.
- Se usó puerto local 18080 para la copia alojada; 8081 estaba ocupado y no se detuvo su servicio.
- Plataforma Sites: publicación confirmada `succeeded`; política `custom`, un usuario y cero grupos.
- Peticiones HTTPS sin credenciales a `/` y `/index.html`: HTTP 403, sin banco ni código de la aplicación en el cuerpo. Esto comprueba la respuesta anónima observada, no sustituye una prueba de acceso del propietario en su navegador.
- No se accedió a Proton Pass ni se probaron credenciales del usuario.
- QA externa pendiente: https://github.com/Niistal/examprepare/issues/2

Para futuras publicaciones, usar la identidad existente y el workflow de Sites; no crear otro Site ni hacerlo público para resolver errores de autenticación.

## Revisión de cierre publicada

73 casos y 16 lecciones por bloques, catálogo separado, filtro de estado, repaso, avance de recorrido, ayudas de funciones e interfaz pulida. Verificación actual: 31 scripts Python, FastAPI con Uvicorn real, Streamlit con fixture y los 73 casos en Chromium a 320/390/768/1440 px. También conflictos de pestaña, cuota llena y recuperación de progreso dañado. El paquete publicado se comparó byte por byte con el probado.

Se conserva la política privada de un usuario y cero grupos. No se han generado ni guardado credenciales en Proton Pass. La primera respuesta de acceso anónimo observada fue 403; no se afirma haber probado un login del propietario ni su configuración MFA.

## Temario conectado y cabeceras HTTP — 12/11, 04:21 Madrid

La publicación indicada incorpora 657 recursos clasificados por carpeta, referencias de fórmulas dadas y avisos si cambia la fuente contrastada de un caso. No copia los cuerpos del repositorio. La automatización de actualización está especificada en [AUTOMATION.md](AUTOMATION.md).

La comprobación HTTPS con acceso de servicio existente devolvió 200 y confirmó todos los bytes de la aplicación y las cabeceras HTTP CSP/frame-ancestors, private/no-store y nosniff. La petición anónima devolvió 403. Cloudflare añade al cierre un script de detección: se detecta y registra separado, sin relajar la CSP ni certificar ese código. Los bytes de la aplicación antes/después de esa inserción coinciden con el artefacto probado. No equivale a probar el login, MFA ni Proton Pass del propietario.

El acceso de servicio se entregó únicamente por stdin oculto al comprobador y al origen exacto del Site, sin seguir redirects. No se generó un token nuevo ni se guardó en archivos/Git.

## Comprobación directa en producción — 12/11, 06:59 Madrid

Navegador temporal contra la URL privada: 11 comprobaciones PASS de banco y temario, referencias, borrador tras recarga, bloqueo/entrega de examen, navegación y asignación de las cinco materias. Cero excepciones de aplicación. Se observaron cuatro avisos de seguridad de la detección de Cloudflare; no se amplió CSP. La cuenta/progreso del propietario no se utilizaron.

El operador entregó el acceso de servicio existente por stdin oculto. La interceptación CDP estuvo limitada al origen exacto del Site y se comprobó en el protocolo local que el override de cabeceras no se propaga a redirects. No se utilizó una cabecera global para todos los dominios ni se registró la credencial. No equivale a verificar el login, MFA ni Proton Pass.

Los identificadores de publicación de este documento corresponden a la revisión manual indicada. Las sincronizaciones posteriores conservan evidencia en el registro privado `prepared-sync.json` y en su resumen T3; no amplían el conjunto de archivos autorizados para tocar documentación en cada actualización.
