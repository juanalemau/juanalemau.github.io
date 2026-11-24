# Decisiones del proyecto

Formato: fecha — decisión — motivo — alternativas descartadas.

- 2026-11-23 — Quartz v5.1.0 (jackyzha0/quartz, MIT) clonado con historial completo; remoto `upstream`. — Respetar autoría y facilitar `npx quartz upgrade`. — Template de GitHub (pierde el vínculo de historial).
- 2026-11-23 — Sitio en `juanalemau.github.io`, idiomas es (principal), pt, en en carpetas `content/{es,pt,en}`. — Pedido de Juan. — Subcarpeta /blog.
- 2026-11-23 — Sin analytics de terceros y comentarios (giscus) apagados hasta decidir. — Privacidad y menos scripts externos.
- 2026-11-23 — Contenido bajo CC BY 4.0, código MIT. — Que el contenido ayude a más gente citando la fuente.

## Propuestas pendientes (product-owner, 2026-11-23) — Juan decide

Detalle en `docs/proyecto/plan-editorial.md`.

- PROPUESTA — Slugs de secciones y artículos **iguales en los 3 idiomas** (`ia`, `software`, `hardware`, `mercado`; títulos traducidos en `index.md`). — Coherente con la regla de mismo nombre de archivo, selector de idioma simple, menos errores. — Descartada: slugs traducidos (más SEO, triple mantenimiento).
- PROPUESTA — MVP del sitio (identidad en `quartz.config.yaml` ya hecha): selector de idioma, portada por idioma, página "Sobre", RSS. — Lo mínimo para publicar con coherencia con la decisión de no usar analytics. — Descartado: lanzar sin selector de idioma.
- PROPUESTA — giscus y newsletter **fuera del MVP**; reevaluar con ≥ 6 artículos. — Público sin cuenta GitHub, scripts externos, datos personales y obligación de cadencia. — Descartado: activarlos desde el inicio.
- PROPUESTA — Cadencia de 1 artículo trilingüe cada 2 semanas; primer artículo: "Cómo escribo un blog en 3 idiomas con agentes de IA". — Realista para una persona; el 1º se basa en experiencia propia verificable. — Descartado: 1 por semana.
- PROPUESTA — Métrica: constancia (≥ 80 % de quincenas publicadas) + respuestas reales de lectores registradas a mano; Search Console opcional. — Sin analytics de terceros. — Descartado: Plausible/GA.
- 2026-11-23 — Contraste AA: gris de metadatos #5c6080 (claro) y #8a8fb0 (oscuro), hover dorado #8C6200 en claro. — Los tonos anteriores no pasaban WCAG AA (ver `ux.md`). — Mantener los grises de Quartz.
- 2026-11-23 — `lang:` en el frontmatter de cada nota pt/en. — `<html lang>` correcto para lectores de pantalla y buscadores. — —
