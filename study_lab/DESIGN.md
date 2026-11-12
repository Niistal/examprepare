# Diseño NIIS Study Lab · Study Cockpit

Cuaderno de estudio con instrumentos de cabina: la teoría se lee como un libro y la práctica se trabaja como en un banco de pruebas. El alumno debe encontrar su asignatura, comprender un concepto, resolver un caso y saber qué repetir, sin que la interfaz compita con la tarea.

Todo el sistema vive en `style.css` como custom properties de `:root`. Los componentes no llevan colores ni tamaños sueltos: si falta un valor, se añade un token.

## Restricciones del proyecto

- Sin fuentes, hojas ni scripts externos: la CSP de producción es `default-src 'none'` con `style-src 'unsafe-inline'`. Solo pilas de fuentes del sistema.
- Sin framework ni dependencias: `build.py` inserta `style.css` y los JS en `shell.html`.
- Los ids, las clases que consultan las pruebas, las funciones globales y la clave de progreso no cambian con el diseño.
- La edición alojada sustituye el almacenamiento de la página por el progreso de la cuenta. La preferencia de tema se guarda en la cookie `study_theme`, nunca en ese almacenamiento.

## Tokens

| Grupo | Tokens | Uso |
|---|---|---|
| Superficies | `--bg`, `--rail`, `--surface-1`, `--surface-2`, `--code-bg` | Página, navegación, elementos elevados, hover y selección, código |
| Líneas | `--line` (decorativa), `--line-control` (≥ 3:1) | Separadores; bordes de todo lo que se manipula |
| Texto | `--text-1`, `--text-2`, `--text-3` | Principal, secundario, metadatos. Los tres cumplen AA sobre las tres superficies |
| Acento | `--accent`, `--on-accent`, `--accent-strong`, `--accent-soft` | Solo acción principal, selección y foco |
| Modalidad | `--theory`, `--practice` y sus `-soft`; `--mode` | Teoría (azul tinta) y práctica (ámbar) |
| Estado | `--success`, `--warning`, `--error` y sus `-soft` | Corrección, avisos, errores |
| Tipografía | `--font-read`, `--font-ui`, `--font-mono`; `--fs-meta` 12, `--fs-small` 13, `--fs-ui` 15, `--fs-read` 17, `--fs-h3` 20, `--fs-h2` 26, `--fs-h1` 34, `--fs-display` 56 | |
| Espacio | `--s1`…`--s8` = 4, 8, 12, 16, 24, 32, 48, 64; `--gutter`, `--rail-width`, `--measure` | |
| Forma | `--r-chip` 4, `--r-control` 6, `--r-float` 10; `--control-h` 40 | |
| Movimiento | `--t-fast` 120 ms, `--t-mid` 160 ms, `--t-slow` 220 ms; `--ease` | |

Tema claro por defecto y oscuro por `prefers-color-scheme` o por `data-theme` en `<html>` (botón de la barra superior). El oscuro conserva la identidad anterior: fondo `#0c101a` y acento menta `#a8f0c4`; en claro el acento es verde botella `#0f6b4c`. Los fondos semánticos se derivan con `color-mix` (10 % en claro, 14 % en oscuro) y llevan el texto en `--text-1`.

## Tipografía

- Lectura y títulos: `Charter, "Bitstream Charter", "Sitka Text", Cambria, "Noto Serif", "DejaVu Serif", Georgia, serif`, peso 600 en títulos e interletra −0,015em.
- Interfaz: `system-ui` y equivalentes. Código, identificadores, fechas y reloj: `ui-monospace` y equivalentes, con cifras tabulares.
- Pesos 400, 500 y 600. Etiquetas en minúscula normal; sin mayúsculas espaciadas.
- Lectura de teoría a 17/1,65 con medida de 68ch; lector de apuntes a 18/1,65 con 72ch; enunciados a 16/1,65 con 75ch. En teléfono los campos usan 16 px para evitar el zoom.

## Reglas de composición

- **Nada** alrededor de la lectura y de las secciones del panel: las separan el espacio y reglas de 1 px.
- **Borde** de 1 px en `--line-control` solo en lo que se manipula: campos, editor, opciones de test.
- **Sombra** solo en lo que flota: menú de cuenta, avisos, lector y barra inferior móvil.
- **Regla de margen de 3 px** para indicar la modalidad: `--theory` en lecciones, `--practice` en bloques y ejercicios. Siempre acompañada de icono y palabra (`modeTag()`): libro «Teoría», terminal «Práctica», ajustes «Práctica con herramienta».
- El acento no decora: una acción primaria por vista. En listas largas (temario) la acción de cada tarjeta es secundaria.

## Componentes

| Componente | Clases | Estados |
|---|---|---|
| Botón | `.btn` + `.btn-primary`/`.btn-light`, `.btn-outline`, `.btn-ghost`, `.btn-danger`, `.btn-small`, `.full` | hover, active, focus-visible, disabled, `aria-busy` |
| Botón de icono y enlace | `.icon-btn`, `.text-link`, `.text-back` | hover, focus-visible |
| Campo | `input`, `select`, `textarea` | hover, focus-visible, placeholder, disabled |
| Etiquetas | `.chip`, `.chip.subtle`, `.mode-tag` | — |
| Pestañas | `.study-view-switch`, `.learning-tabs` (`aria-pressed`), `.question-tabs` (`.active`, `.completed`) | subrayado de acento en la activa |
| Navegación | `.nav-item`, `.subject-nav button` (`.selected`, `aria-current`) | barra de acento de 3 px, fondo y peso |
| Fila de agenda | `.subject-card`, `.topic-overview-row`, `.review-item`, `.progress-item` | hover; la fila completa es el objetivo |
| Tarjeta de catálogo | `.exercise-list article`, `.material-item`, `.route-step` | hover, `.mastered` |
| Desplegable | `details.route-block`, `.mini-example`, `.flashcard`, `.dataset-panel` | abierto y cerrado con indicador |
| Test | `.quiz-option`, `.quiz-feedback` (`.incorrect`, `.manual`) | seleccionada, corregida con icono y texto |
| Autoevaluación | `.rating-row` > `.rating` | selector de tres segmentos, `.active` |
| Editor y salida | `#answerEditor`, `.editor-toolbar`, `#runOutput` | autoguardado, ejecución, error |
| Avisos | `.storage-notice`, `.account-notice`, `.source-update`, `.setup-tip`, `#toast` | aviso, error, información |
| Vacío | `.empty-state` | con acción de recuperación |
| Diálogos | `.material-reader`, `#accountRecoveryDialog` | fondo atenuado, foco devuelto al cerrar |
| Progreso | `.track`, `.metric`, `.countdown` | — |

Iconos: SVG de trazo en línea, `viewBox` 24, grosor 1,75, `currentColor`, clase `.ico`. En plantillas JS se generan con `icon(nombre)` de `app.js`. No se usan emojis ni flechas de texto como iconos.

## Pantallas

- **Panel:** próximo examen con cuenta atrás calculada de la fecha real, una acción primaria, franja de cuatro métricas y las cinco asignaturas como agenda de filas.
- **Estudiar:** selector de asignatura, pestañas de vista y contenido. Programazioa muestra el recorrido por bloques; las demás, lecciones, tests, simulacro, repaso y recursos.
- **Ejercicio:** enunciado y editor a la izquierda con regla de modalidad; ayudas escalonadas, solución, autoevaluación y fuentes a la derecha. En tablet y teléfono las ayudas pasan debajo.
- **Lector:** columna de lectura centrada con índice lateral; a pantalla completa en teléfono.
- **Progreso:** métricas, próximo repaso y tabla por asignatura. Recoge la autoevaluación de casos; aciertos y tarjetas están en «Repasar».
- **Cuenta (alojada):** menú `details/summary` en la barra superior, estado de guardado discreto y avisos visibles fuera del menú.

## Adaptación y accesibilidad

- ≥ 1181 px: rail de 248 px. 681–1180 px: rail de 72 px solo con iconos. ≤ 680 px: barra inferior fija de cuatro destinos con etiqueta visible; el contenido reserva su altura y el área segura.
- Foco: `outline: 2px solid var(--accent)` con separación de 2 px en todo control. Los títulos que reciben foco por script al cambiar de vista no lo dibujan.
- Estado nunca solo por color: icono y texto en corrección, modalidad y guardado.
- `prefers-reduced-motion` anula animaciones y transiciones. Solo se animan opacidad, transformaciones de hasta 6 px y colores.
- Editor: Tab inserta sangría, Mayús+Tab no se intercepta y Esc saca el foco. Ayudas bloqueadas en modo examen.

## No hacer

1. Envolver cada bloque en una tarjeta con borde y radio.
2. Usar el acento como decoración o distinguir teoría y práctica solo por color.
3. Añadir fuentes web, bibliotecas, degradados, desenfoques o imágenes decorativas.
