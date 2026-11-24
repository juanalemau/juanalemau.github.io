# Decisiones del proyecto

Formato: fecha — decisión — motivo — alternativas descartadas.

- 2026-11-23 — Quartz v5.1.0 (jackyzha0/quartz, MIT) clonado con historial completo; remoto `upstream`. — Respetar autoría y facilitar `npx quartz upgrade`. — Template de GitHub (pierde el vínculo de historial).
- 2026-11-23 — Sitio en `juanalemau.github.io`, idiomas es (principal), pt, en en carpetas `content/{es,pt,en}`. — Pedido de Juan. — Subcarpeta /blog.
- 2026-11-23 — Sin analytics de terceros y comentarios (giscus) apagados hasta decidir. — Privacidad y menos scripts externos.
- 2026-11-23 — Contenido bajo CC BY 4.0, código MIT. — Que el contenido ayude a más gente citando la fuente.

## Propuestas pendientes (product-owner, 2026-11-23) — Juan decide

Detalle en `docs/proyecto/plan-editorial.md`.

- ✅ ACEPTADA (2026-11-23, Juan: "pode realizar todas alterações") — Slugs de secciones y artículos **iguales en los 3 idiomas** (`ia`, `software`, `hardware`, `mercado`; títulos traducidos en `index.md`). — Coherente con la regla de mismo nombre de archivo, selector de idioma simple, menos errores. — Descartada: slugs traducidos (más SEO, triple mantenimiento).
- ✅ ACEPTADA (2026-11-23, Juan: "pode realizar todas alterações") — MVP del sitio (identidad en `quartz.config.yaml` ya hecha): selector de idioma, portada por idioma, página "Sobre", RSS. — Lo mínimo para publicar con coherencia con la decisión de no usar analytics. — Descartado: lanzar sin selector de idioma.
- ✅ ACEPTADA (2026-11-23, Juan: "pode realizar todas alterações") — giscus y newsletter **fuera del MVP**; reevaluar con ≥ 6 artículos. — Público sin cuenta GitHub, scripts externos, datos personales y obligación de cadencia. — Descartado: activarlos desde el inicio.
- ✅ ACEPTADA (2026-11-23, Juan: "pode realizar todas alterações") — Cadencia de 1 artículo trilingüe cada 2 semanas; primer artículo: "Cómo escribo un blog en 3 idiomas con agentes de IA". — Realista para una persona; el 1º se basa en experiencia propia verificable. — Descartado: 1 por semana.
- ✅ ACEPTADA (2026-11-23, Juan: "pode realizar todas alterações") — Métrica: constancia (≥ 80 % de quincenas publicadas) + respuestas reales de lectores registradas a mano; Search Console opcional. — Sin analytics de terceros. — Descartado: Plausible/GA.
- 2026-11-23 — Contraste AA: gris de metadatos #5c6080 (claro) y #8a8fb0 (oscuro), hover dorado #8C6200 en claro. — Los tonos anteriores no pasaban WCAG AA (ver `ux.md`). — Mantener los grises de Quartz.
- 2026-11-23 — `lang:` en el frontmatter de cada nota pt/en. — `<html lang>` correcto para lectores de pantalla y buscadores. — —
- 2026-11-23 — Aplicadas las recomendaciones de UX: layout de barra lateral mínima (sin grafo, backlinks ni recientes; índice solo en escritorio), portada con 3 tarjetas por idioma, explorer limitado al idioma actual (CSS), línea visible de idioma en cada página. Selector propio en la barra + hreflang + RSS por idioma quedan para cuando haya artículos (plugin propio). — Ver `ux.md`. —
- 2026-11-23 — Seguridad M1–M4 aplicadas: sin LaTeX/KaTeX, fuentes autoalojadas (Fontsource, OFL) sin Google, CSP por `<meta>` sin `unsafe-eval` (el explorer usa su orden por defecto), `explicit-publish` (solo se publica lo que tiene `publish: true`). — Ver `seguridad.md`. — Permitir `unsafe-eval` para el filtro del explorer.
- 2026-11-23 — Favicon y og-image con el monograma de la marca alemau. — Identidad propia. —
- 2026-11-23 — release-please arranca en 47b4196 (`bootstrap-sha`). — Sin eso incluía todo el historial de Quartz en el CHANGELOG. —

- 2026-11-23 — Monograma alemau al lado del título del sitio (`monograma.svg`; en oscuro `monograma-oscuro.svg`, versión clara con cursor #F0566B por contraste). — Identidad de marca dentro del sitio, no solo en el favicon. —
- 2026-11-24 — Cambio de rumbo: el blog es un **resumen diario para devs de todo el mundo** (GitHub, HN, dev.to, Medium, blogs; sin X por ahora). Gemini (plan gratis) redacta y revisa; Qwen local descartado tras prueba (inventó datos). Calidad en 4 capas (reglas, números, revisor, falla cerrada). Publicación automática 06:00 BRT con reintentos 09:00/12:00; resúmenes en la rama `resumenes` (main sigue protegida). OmniRoute descartado por ahora (requiere cuentas por proveedor). — Pedido de Juan. — Artículo sobre cómo se hizo el blog (convertido en página Sobre).
- 2026-11-24 — Seguridad solo como noticia: nunca repos de exploit/0-day/PoC/herramientas de ataque; bloqueo de descargas binarias, acortadores y hosts de archivos. Filtro en código (antes de la IA) + reglas en redactor y revisor. — Pedido de Juan. —
