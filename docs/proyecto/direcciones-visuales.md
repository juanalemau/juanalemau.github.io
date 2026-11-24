# Direcciones visuales del resumen diario

Fecha: 2026-11-24 · Autor: ux-designer · Estado: **propuesta, Juan decide**

Problema: el resumen diario se ve como el Quartz por defecto (explorer a la izquierda, índice a la derecha). Funciona, pero es un "jardín digital" genérico; no dice "esto es un parte diario para devs". Se proponen 3 direcciones con mockups autocontenidos en `docs/proyecto/mockups/` (abrir en el navegador, probar a 1280 px y 390 px; respetan claro/oscuro con `prefers-color-scheme`).

Base común a las tres:

- Marca alemau: índigo #161A44, cochinilla #C8102E (oscuro #F0566B), oro #E5A11C (como texto en claro se usa #8C6200, el oro puro no llega a AA sobre fondo claro); Unbounded / IBM Plex Sans / IBM Plex Mono locales; monograma 5×6 en SVG inline.
- Contraste medido (WCAG 2.x): metadatos #5c6080 sobre #fbfaf7 = 5,85:1; #8a8fb0 sobre #10132f = 5,74:1; #F0566B sobre #10132f = 5,4:1; #8C6200 sobre papel #f6f3ec = 4,91:1; oro sobre índigo = 7,47:1. Todo ≥ 4,5:1.
- Sin JS obligatorio, sin CDNs: compatible con la CSP actual. Enlace "saltar al contenido", `:focus-visible` visible, objetivos táctiles ≥ 44 px en idioma y acciones, `hreflang` en el selector.
- Se usaron los ítems reales del 2026-11-24 **excepto FastUnlock** (0-day), que según la decisión del 2026-11-24 no debería haber entrado al resumen: conviene revisar el filtro.
- Herramientas: búsquedas de `ui-ux-pro-max` (estilos "data-dense dashboard", "brutalism/editorial", guías de UX de escaneo, tipografía y números) y la regla anti-genérico de `taste-skill` (la idea sale del tema: un parte diario de código → log de commits, periódico, radar de señales).

---

## A — "git log" / changelog · `mockups/a-changelog.html`

**Concepto.** El día es un release: `v2026.11.24`, y cada noticia es un commit con hash, scope tipo *conventional commits* (`perf(rust):`, `feat(web):`), una línea `why:` y metadatos en mono. Barra de estado tipo vim/tmux abajo y atajos de teclado (`j/k`, `o`, `c`, `[`) a la derecha.

**Por qué funciona para devs.** Usa un formato que todo dev lee a diario sin pensar (git log, release notes), así que se escanea rápido; el hash da un permalink corto por ítem (`#c3`) que se puede pegar en un chat. Es la dirección más "propia": casi nadie presenta noticias como un log.

**Riesgos.**
- Puede leerse como disfraz si se exagera (cursor que parpadea, statusline). Mantener el chiste en 2–3 detalles.
- Los hashes son decorativos: hay que generarlos de forma estable (p. ej. sha1 de la URL) para que no cambien entre builds.
- Los atajos `j/k` necesitan un script pequeño propio (no externo); sin JS el sitio funciona igual con anclas.
- Para no-devs (o devs junior) el scope `perf(rust):` puede ser ruido; se puede ocultar en móvil.

**Accesibilidad.** Lista ordenada semántica (`<ol>`), un `<article>` por ítem con `<h2>`. El prompt y la statusline son `aria-hidden` (decorativos). El parpadeo del cursor solo con `prefers-reduced-motion: no-preference`. Atajos de teclado: deben ignorarse cuando el foco está en un campo (búsqueda) y documentarse con `?`.

**Camino técnico.**
1. *Dentro de Quartz actual:* **viable, esfuerzo bajo-medio (1–2 días).** CSS en `quartz/styles/custom.scss` scoped a las páginas del diario (`body[data-slug*="/diario/"]`), ocultar explorer e índice en esas páginas desde el layout de `quartz.config.yaml`, y que el generador del resumen emita marcado con clases (o datos en frontmatter, ver recomendación) en vez de depender de la secuencia `h2 + p + p`. Los atajos `j/k`: un script inline propio (~40 líneas) registrado como recurso del componente; revisar que la CSP lo permita (script propio, sin `unsafe-eval`).
2. *Migrar a Astro + Astryx/21st.dev:* no aporta. Esta dirección es tipografía + una lista; no necesita componentes de un design system.

---

## B — "La Gaceta del Dev" / periódico · `mockups/b-jornal.html`

**Concepto.** Un periódico impreso: cabecera gigante "alemau" con el monograma, línea de fecha y número de edición, **manchete del día** (el ítem con más señal) con capitular y cita "Por qué importa", un "Marcador del día" con los números, y el resto en grilla de 3 columnas con filetes.

**Por qué funciona para devs.** La jerarquía es explícita: lo más importante se ve primero sin leer los 10. Tiene una personalidad fuerte y poco vista en sitios dev (que suelen ser oscuros y mono). El "marcador" separa estrellas de puntos y dice que no son comparables, lo que da confianza.

**Riesgos.**
- Requiere **elegir manchete** cada día: el generador tiene que marcar un ítem como principal (por señal) y producir un texto un poco más largo para él; más trabajo para la IA, más superficie de error.
- Unbounded en titulares grandes es muy ancha: con títulos largos en español puede romper feo; limitar largo de titular (≈ 70 caracteres) en el prompt.
- La grilla de 3 columnas pide número de ítems múltiplo de 3 para verse completa (10 = 1 manchete + 9 ✔).
- Estética de "papel" puede sentirse menos "técnica" a algunos.

**Accesibilidad.** Orden de lectura del DOM = orden visual (manchete → marcador → resto). Los números grandes "02, 03…" son `aria-hidden`; la información está en el texto. Columnas CSS solo en escritorio; en móvil una columna con número a la izquierda. Itálicas solo en frases cortas.

**Camino técnico.**
1. *Dentro de Quartz actual:* **viable, esfuerzo medio (2–3 días).** El masthead reemplaza al header de Quartz en las páginas del diario (componente Preact pequeño o CSS sobre el `PageTitle` existente). La manchete y el marcador necesitan datos estructurados → frontmatter `items:` + un componente Preact `ResumenDiario` que renderiza la página en el build (cero JS en el cliente).
2. *Migrar:* tampoco hace falta; es CSS Grid y tipografía.

---

## C — "Radar" / panel de señales · `mockups/c-radar.html`

**Concepto.** El día como un panel: arriba una **matriz de señales** construida con la misma grilla de píxeles del monograma (una columna por ítem, 1–5 cuadrados según su fuerza), debajo tarjetas densas con fuente, categoría y medidor de 5 cuadrados, y un filtro por fuente (GitHub / Hacker News) hecho **solo con CSS** (radios + `:checked`).

**Por qué funciona para devs.** Es lo más rápido de escanear: en 2 segundos se ve qué fue fuerte hoy y de dónde viene. Convierte el monograma en sistema visual (no solo logo), lo que da identidad sin adornos. El filtro sin JS respeta la CSP.

**Riesgos.**
- Es la que más se parece a "dashboard SaaS" si se descuida: evitar sombras, gradientes, íconos en cuadraditos de color.
- La "señal 1–5" es una **cifra inventada por nosotros** (percentil dentro de cada fuente): hay que explicarla (está en la leyenda) y calcularla en código, nunca por la IA.
- Las tarjetas comprimen el texto: menos espacio para el "por qué importa".
- El filtro con radios funciona sin JS pero no cambia la URL (no se puede compartir "solo GitHub").

**Accesibilidad.** Matriz con `aria-label` por columna ("2 Ladybird, señal 5") y enlace a cada tarjeta; medidores con `role="img"` + `aria-label="Señal 4 de 5"`. El color nunca es el único canal (también cantidad de cuadrados y número). Radios reales, enfocables con teclado, con foco visible en su etiqueta. Toda la tarjeta es clicable, pero "discusión" y "reportar error" siguen siendo enlaces independientes.

**Camino técnico.**
1. *Dentro de Quartz actual:* **viable, esfuerzo medio (2–3 días).** Igual que B: frontmatter `items:` (con `fuente`, `metrica`, `senal`, `categoria`) + componente Preact que pinta matriz, filtro y tarjetas; estilos en `custom.scss`. Los `<input type="radio">` no salen de Markdown: necesitan el componente.
2. *Migrar a Astro + Astryx/21st.dev:* es la dirección donde más "tienta" un design system (tarjetas, chips, badges), pero no lo necesita: son ~150 líneas de CSS.

---

## Sobre migrar a Astro para usar Astryx o 21st.dev (honesto)

- **Quartz no ejecuta componentes React, Tailwind ni StyleX.** Sus componentes son Preact (JSX) renderizados en el build, y los estilos son SCSS. Se puede copiar la *idea visual* de un componente de Astryx o 21st.dev y reescribirla en Preact + SCSS, pero no importarlo tal cual. `preact/compat` cubre algo de React, pero los componentes de 21st.dev dependen de Tailwind (habría que agregar PostCSS/Tailwind al pipeline de Quartz) y Astryx de StyleX (requiere su plugin de compilación) — ninguno de los dos está soportado por Quartz.
- **Astro sí podría** renderizar componentes React en el build (salida HTML estática, sin JS si no se hidratan), con Tailwind oficial; StyleX necesitaría un plugin de Vite aparte.
- **Costo de migrar:** rehacer el sitio entero: i18n es/pt/en, `translations`, RSS por idioma, búsqueda, sitemap, og-image, `explicit-publish`, CSP, despliegue en Pages y el flujo del generador de resúmenes. Estimado: **1–2 semanas** de trabajo y un período con dos sitios a mantener. Además, cualquier componente que necesite hidratarse trae React al cliente (≈ 40–50 kB) y hay que revisar la CSP.
- **Beneficio:** acceso a componentes ya hechos. Pero ninguna de las 3 direcciones los necesita: su personalidad viene de la idea y la tipografía, no de una librería. Un design system de terceros además empuja hacia el *look* genérico que queremos evitar.

**Conclusión:** quedarse en Quartz. Reevaluar Astro solo si en el futuro el sitio necesita interacción rica (cuentas, preferencias, búsqueda por filtros con URL), no por el estilo visual.

---

## Recomendación

**Dirección A ("git log") como página del día, tomando de C el medidor de señal de 5 cuadrados**, dentro de Quartz:

1. El generador escribe los ítems también como datos en el frontmatter (`items:` con título, resumen, por qué, fuente, url, discusión, métrica, señal calculada en código, scope/categoría) y mantiene el cuerpo Markdown como respaldo legible (RSS, buscadores).
2. Un componente Preact `ResumenDiario` renderiza la lista en el build (cero JS); en páginas del diario se ocultan explorer e índice desde el layout.
3. Estilos en `custom.scss`, scoped al diario; el resto del sitio (Sobre, portada) adopta solo cabecera y colores.
4. Fase 2 opcional: script propio de `j/k` (sin dependencias, compatible con la CSP).

Por qué A: es la más distintiva para el público dev, la más barata de implementar (es una lista bien tipografiada) y la que mejor aguanta 365 días de contenido automático sin depender de que la IA elija una "manchete" (B) ni de densidad de tarjetas (C). Esfuerzo estimado: 1–2 días.

Si Juan prefiere algo menos "nerd" y más amplio, **B** es la segunda opción (2–3 días, requiere elegir manchete en el generador).
