# Cambios

## 12/11/2026 — evolución local desde V1

1. Se conservaron las fuentes y el banco inicial de 53 ejercicios de la entrega ZIP.
2. Se corrigieron persistencia, recuperación de sesión, ayudas, importación y reinicio.
3. Se sustituyó el protagonismo de 5.000 combinaciones por recorridos finitos y métodos de estudio por materia, conforme a la aclaración del propietario.
4. Se añadieron nueve microcasos de Programazioa, ejemplos básicos y ayuda progresiva; total 62.
5. Se contrastaron rutas/temas contra Big_Data/main; se añadieron metadatos, hashes, scripts de auditoría y build reproducible.
6. Se incorporaron QA headless, pruebas de soluciones y documentación de entorno/pendientes. No hay cambios en Big_Data, publicación ni push.

## 12/11/2026 — ampliación autorizada a web privada

- Publicación privada Sites con autenticación gestionada de ChatGPT, sin contraseñas dentro de la app.
- Botón para continuar el recorrido, aviso de progreso por dispositivo, cierre de sesión y CSP del paquete alojado.
- Rama subida a GitHub e issues #1–#3 para pendientes. Documentación de despliegue y límites de Proton Pass.

## 12/11/2026 — revisión de cierre de estudio y usabilidad

- 73 casos y 16 lecciones; ampliación de preprocesamiento/validación, fundamentos/privacidad, mapping/ciclo/formatos y offsets/colas/series temporales.
- Recorrido y catálogo separados, teoría por bloque, filtro de estado, repaso y avance entre casos. Ayudas más específicas para llamadas de Python/ML.
- Corregidos texto de plantilla visible, desbordamiento a 320 px, marca del logotipo, regreso a asignatura incorrecta y final de recorrido. Clase positiva explícita en el ejemplo de cáncer y mutate en Logstash.
- Guardado robusto ante pestañas concurrentes, cuota llena y registro dañado. Accesibilidad de teclado, estados, contraste y motion.
- 30 scripts y 2 soluciones de frameworks comprobados; suite reproducible ampliada. Fuente Git main y secciones versionadas verificadas. Documentación de cobertura y diseño.

## Turno de trabajo hasta las 08:10 — en curso

- Fórmulas y llamadas facilitadas en el enunciado; aplicación práctica de NumPy/métricas/fuzzy sin demostraciones de álgebra universitaria.
- Catálogo versionado de Big_Data, separado por rutas de asignatura, material general y otros módulos; paginación, filtros y procedencia.
- Mirror privado de lectura sin modificar la copia de apuntes; caché y metadatos para evitar descargar datos/binaries al indexar.
- Guardas de sincronización, retomado de publicación y pruebas con repositorios Git temporales, rutas hostiles y commits ajenos.
- Worker mínimo para servir el mismo documento con cabeceras HTTP, manteniendo la autenticación privada de Sites.

- Corrección posterior: importar con cuota llena muestra fallo persistente y conserva el progreso original; recuperar el guardado retira el aviso. Simulacros con secuencia antigua no se reanudan contra un banco cambiado; sus borradores se conservan.
- Selector individual para futuros módulos fuera del calendario, sin mezclar nuevas asignaturas con las cinco pruebas.
- Comprobación HTTPS real de aplicación/cabeceras, con informe separado de la detección inyectada por Cloudflare. Siete pruebas impiden aceptar cambios del HTML como si fueran transformaciones conocidas.

- Recuperación de escritura parcial del catálogo JSON/JS en el siguiente intento; temporales propios se limpian al fallar sin alterar el original. Origen Git de contraste limitado al repositorio exacto, con rechazo de symlinks externos.
- Lectura/escritura UTF-8 explícita en los scripts y QA para evitar depender de la codificación del sistema; Windows real sigue pendiente.
- Extracción de apartados ignora bloques de código Markdown; un notebook con estructura inválida conserva solo su referencia de archivo. Política de catálogo v5 reconstruida y probada, sin mezcla de materias.
- Verificación de publicación compara CSP completa, permisos, referrer, nosniff y caché; rechaza políticas relajadas o cabeceras ausentes.
- Favicon SVG integrado sin petición externa/404; los tests ya no excluyen ese recurso al comprobar errores de consola. Foco accesible al título de página y de pregunta, con regresiones de navegador.
