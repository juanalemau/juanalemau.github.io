# Mejoras de Quartz para alemau

Revisión del 2026-11-23 hecha por el agente `especialista-quartz`. Base: Quartz v5.1.0 (`v5.1.0-1-g47b4196`), `quartz.config.yaml` y las docs en `docs/`. Esta lista se mantiene viva: cada mejora aplicada se marca y se anota en `decisiones.md`.

Formato de cada punto: problema → opciones → recomendación → pasos y riesgo.

---

## 1. Estado actual

| Comprobación | Resultado |
| --- | --- |
| `npx quartz plugin doctor` | ✓ Sin problemas en 41 plugins configurados |
| `npx quartz build` | ✓ 4 archivos Markdown, 64 archivos emitidos en ~2 s, sin avisos |
| CI (`pr-checks.yml`) en PR #1, #3 | ✓ `build` y `convenciones` en verde |

El build está limpio, pero revisar el HTML generado (`public/`) muestra lo siguiente:

1. **`<html lang="es">` en todas las páginas**, también en `pt/` y `en/`. `renderPage.tsx` usa `frontmatter.lang` y, si falta, el idioma de `locale` (`docs/plugins/Frontmatter.md`, propiedad `lang`). Ninguna nota tiene `lang`.
2. **Textos de la interfaz siempre en español** (Buscar, Explorador, Recientes, Modo oscuro, "Creado con"), también en las páginas pt/en. Los plugins leen `cfg.locale` (global), no el idioma de la página (`docs/features/i18n.md`).
3. **Cadenas en inglés que se cuelan aunque `locale: es-ES`:**
   - `<title>Search</title>` dentro del SVG del botón de búsqueda (plugin `search`, texto fijo).
   - Descripción del RSS: `"Últimas 10 notas on alemau"`: el `on` está fijo en `quartz/plugins/builtins/contentIndex.ts` (`generateRSSFeed`).
4. **El RSS (`index.xml`) mezcla los tres idiomas** e incluye "Índice de Etiquetas" como si fuera un artículo.
5. **`og:url` termina en `/pt/index`** en vez de `/pt/` (la URL que realmente se sirve). No hay `<link rel="canonical">` ni `hreflang`.
6. `sitemap.xml` es correcto (5 URLs), pero sin anotaciones `xhtml:link` por idioma (el namespace ya está declarado).

---

## 2. i18n (sitio multilingüe)

**Problema.** Quartz v5 traduce la interfaz a **un solo** idioma por sitio (`configuration.locale`). No hay soporte de multilingüe "de verdad" (selector de idioma, interfaz por página, feeds por idioma). Lo confirman los issues upstream #462, #803 y #2297 (cerrados sin una función dedicada) y que **no existe ningún plugin de i18n en `quartz-community`** (revisé los ~70 repos de la organización y `awesome-quartz`).

**Lo que sí hay:**
- `locale` global: `es-ES` y `pt-BR` existen en `quartz/i18n/locales` y en cada plugin; `en-US` es el idioma por defecto.
- `lang` en el frontmatter: cambia solo el `<html lang>` (importante para lectores de pantalla, el corrector del navegador y Google). La interfaz sigue en `locale`.
- Carpetas `content/{es,pt,en}`: el explorador, las carpetas y las migas de pan ya separan los idiomas.

**Opciones:**

| # | Opción | Qué logra | Esfuerzo | Toca `quartz/`? |
| --- | --- | --- | --- | --- |
| A | Poner `lang: pt` / `lang: en` en el frontmatter de cada nota (o en una plantilla de Obsidian por carpeta) | `<html lang>` correcto por página | Muy bajo | No |
| B | Plugin local (`.quartz/plugins` o paquete propio) con `additionalHead` que emite `hreflang` + `canonical` según la carpeta | SEO multilingüe correcto | Bajo-medio | No |
| C | Tres builds con `quartz build --config <archivo>` (nuevo en **5.2.0**), uno por idioma, cada uno con su `locale`, `pageTitle` y `rssSlug`, publicados en `/es`, `/pt`, `/en` | Interfaz, RSS, búsqueda y grafo separados por idioma | Medio (workflow con 3 builds y un artefacto combinado) | No |
| D | Contribuir upstream que los componentes usen `frontmatter.lang` (o un mapa carpeta→locale) para elegir la traducción | Interfaz por página en un solo build | Alto (todos los plugins con texto) | Sí → upstream |

**Recomendación:** **A ya** (gratis, sin riesgo) + **B** cuando se publique el primer artículo. Evaluar **C** después de la actualización a 5.2.x si el blog crece en pt/en y molesta tener la interfaz en español. D solo como contribución upstream, abriendo antes un issue/discusión.

Riesgo de C: el grafo, la búsqueda y los backlinks dejan de cruzar idiomas, y la portada raíz (`content/index.md`) necesitaría su propio build o una página estática.

---

## 3. SEO y compartir

| Tema | Estado | Recomendación |
| --- | --- | --- |
| `description` | Plugin `description` activo; las 4 notas tienen `description` en el frontmatter → `meta description`, `og:description` y `twitter:description` correctos | Mantener la regla: **toda nota con `description`** (y `socialDescription` si hace falta una más corta). Ya está en `note-properties`. |
| og-image | `@quartz-community/og-image` activo; genera `*-og-image.webp` 1200×630 (`colorScheme: lightMode` por defecto) | Probar un diseño propio con la marca (colores `#161A44`/`#C8102E`, Unbounded) vía `imageStructure` en `quartz.ts` (`docs/plugins/CustomOgImages.md`). Traducir `readingTimeText` y `defaultDescription`. Verificar si WhatsApp/LinkedIn muestran WebP; si no, usar `socialImage` PNG en las notas clave. |
| Sitemap | `enableSiteMap: true`, correcto | Registrar el sitio en Google Search Console y Bing Webmaster con `sitemap.xml`. Las anotaciones `hreflang` en el sitemap quedarían para el plugin B o upstream. |
| RSS por idioma | Un solo feed mixto (`index.xml`, 10 entradas, sin contenido completo) | Hoy no hay opción para filtrar por carpeta (`docs/plugins/ContentIndex.md`: solo `rssLimit`, `rssFullHtml`, `rssSlug`). Caminos: (1) build por idioma (opción C) con `rssSlug` distinto; (2) plugin emisor propio que reutilice `ctx.contentIndex` y escriba `es/index.xml`, `pt/index.xml`, `en/index.xml`. Considerar `rssFullHtml: true`. |
| hreflang / canonical | No existen | Plugin B. Mapear `es/x` ↔ `pt/x` ↔ `en/x` por nombre de archivo o con una propiedad `translations` en el frontmatter, y `x-default` → raíz. |
| `og:url` con `/index` | Incorrecto en índices de carpeta | Comprobar si se corrige en 5.2.x; si no, abrir issue/PR upstream (bug pequeño en `Head.tsx`). |

---

## 4. Rutina de actualización

### 4.1 Quartz v5.2.x

Las tres versiones salieron el **2026-11-22**. Según la regla de ≥ 2 semanas: **no antes del 2026-12-07**, y directamente a la última 5.2.x (o 5.3 si ya cumplió dos semanas).

Qué cambia (CHANGELOG upstream) y qué nos afecta:

- **5.2.0**
  - `quartz build --config <ruta>`: habilita la opción C de i18n. ✅ útil
  - **Fuentes integradas** en `configuration.fonts`: el plugin `@quartz-community/quartz-fonts` (lo tenemos activo) pasa a ser built-in y su entrada se aplica sola. ⚠ correr `npx quartz plugin doctor --fix` y revisar que Unbounded / IBM Plex sigan cargando.
  - **Callouts y transclusiones se renderizan como `<div>`**, y los popovers llevan clases de Obsidian. ⚠ hoy no hay CSS propio, así que el riesgo es bajo, pero hay que revisar visualmente.
  - Mejoras de Bases, permalinks en sitios grandes (≥ 192 archivos), ids de transclusiones sin duplicar, y `plugin install` más robusto en CI con caché.
- **5.2.1**: fuentes `interface` y por encabezado cargadas desde Google Fonts, y un arreglo de desbordamiento horizontal en móvil (columna `minmax(0, 1fr)`). ✅ bueno para nosotros (título "alemau" con Unbounded).
- **5.2.2**: arreglo de `@quartz-themes/core` (lo tenemos desactivado). Sin impacto.

**Pasos (en una rama `chore/<n>-quartz-5-2`):**
1. `git fetch upstream --tags` y leer `CHANGELOG.md` de la versión elegida.
2. `npx quartz upgrade`: muestra las notas de cada versión, restaura plugins, corre `plugin doctor` y lista actualizaciones de plugins (`docs/cli/`).
3. `npx quartz plugin doctor --fix` (mueve `quartz-fonts` a `configuration.fonts`).
4. `npx quartz build` + `npx quartz build --serve` y revisar a mano: portada, `es/`, `pt/`, `en/`, modo oscuro, móvil, og-image.
5. PR → CI verde → merge. Anotar en `decisiones.md`.

**Riesgos:** conflictos de merge en archivos que hemos tocado (`quartz.config.yaml`, `.github/`, `package.json`); fuentes que no carguen; cambio visual de callouts. Reversión: revertir el commit del merge.

### 4.2 Dependabot: PRs abiertos

| PR | Contenido | Antigüedad de las versiones | Veredicto |
| --- | --- | --- | --- |
| **#1** actions (ci-dependencies) | checkout 6.1→**7.0.1**, setup-node 6.5→**7.1.0**, cache 5.1→**6.1.0**, upload-pages-artifact 3.0.1→**5.0.0**, deploy-pages 4.0.5→**5.0.1** | Todas ≥ 6 semanas (la más nueva, setup-node 7.1.0, es del 2026-10-08) | **Seguro de aplicar**, con una precaución (abajo) |
| **#3** quartz-ecosystem (10 plugins) | bases-page 1.5, obsidian-flavored-markdown 2.3, types 1.5, explorer 1.1, … | Publicadas 20–21/11/2026 (< 2 semanas); varias acompañan a Quartz 5.2 (callouts en `<div>`, factorías async) | **No hacer merge.** Cerrar o dejar que se reemplace con la subida a 5.2.x, que trae estos plugins ya probados juntos. |
| **#4** typescript 5.9.3→**7.0.2** | Major (compilador nuevo) | — | **No hacer merge.** Upstream tiene el mismo PR (#2562) abierto desde septiembre sin aplicar; `dependabot.yml` lo aísla justamente por eso. Esperar a que upstream migre. |

**Precaución con el PR #1:** el CI del PR solo prueba `pr-checks.yml` (checkout, setup-node). `upload-pages-artifact` y `deploy-pages` **solo se ejecutan con push a `main`**, así que el PR en verde no los prueba. upload-pages-artifact ≥ v4 deja de incluir archivos ocultos (dotfiles); comprobé que `public/` no tiene ninguno, así que no nos afecta. Después del merge hay que vigilar la primera ejecución de "Publicar en GitHub Pages" y, si falla, revertir. Las actions siguen fijadas por SHA (bien).

**Rutina sugerida (mensual, cuando llegue Dependabot):**
1. Actions: aplicar si tienen ≥ 2 semanas, leer los breaking changes, vigilar el deploy.
2. Plugins `@quartz-community/*`: preferir subirlos con `npx quartz upgrade` / `npx quartz plugin update` junto con la versión de Quartz que los declara (`quartzVersion`), no sueltos.
3. Majors (`typescript`, `preact`, `vfile`, `unified`): solo cuando upstream los adopte.
4. Siempre `plugin doctor` + `build` en verde antes del merge.

---

## 5. Lista priorizada de mejoras

Impacto/esfuerzo: A = alto, M = medio, B = bajo.

| Prio | Mejora | Impacto | Esfuerzo | Toca `quartz/`? | Estado |
| --- | --- | --- | --- | --- | --- |
| 1 | `lang: pt` / `lang: en` en el frontmatter de `content/pt/**` y `content/en/**` (plantilla de Obsidian por carpeta) | A (accesibilidad + SEO) | B | No | Pendiente |
| 2 | Aplicar PR #1 (actions) y vigilar el deploy | M (seguridad, Node 24) | B | No | Pendiente |
| 3 | Cerrar/posponer PR #3 y #4 | M (evita romper) | B | No | Pendiente |
| 4 | Subir a Quartz 5.2.x desde el 2026-12-07 (§4.1) | M | M | No (merge upstream) | Esperando |
| 5 | Plugin local `hreflang` + `canonical` | A (SEO multilingüe) | M | No | Idea |
| 6 | Registrar `sitemap.xml` en Search Console / Bing | M | B | No | Pendiente (al tener contenido) |
| 7 | og-image con la marca alemau + textos traducidos | M (al compartir en redes) | M | No (`quartz.ts`) | Idea |
| 8 | RSS por idioma (emisor propio o builds por idioma) | M | M | No | Idea |
| 9 | Evaluar 3 builds con `--config` (interfaz por idioma) | M-A | M-A | No | Tras 5.2 |
| 10 | `rssFullHtml: true` y excluir páginas generadas (tags) del RSS | B | B | No / upstream | Idea |
| 11 | Activar giscus (`comments`) cuando se decida | M | B | No | Decisión pendiente (`decisiones.md`) |

### Posibles contribuciones upstream

Siempre abriendo antes un issue para preguntar al mantenedor, con PRs pequeños, siguiendo `CODE_OF_CONDUCT.md` y las convenciones del repo, y sin presentar como propio lo que es del proyecto.

1. **RSS: `"… on <pageTitle>"` sin traducir** (`contentIndex.ts`): mover la frase completa a `pages.rss` en los locales. Pequeño y claro.
2. **Plugin `search`: `<title>Search</title>` fijo en el SVG**: usar la traducción `searchBar.title`. Va en el repo `quartz-community/search`.
3. **`og:url` con `/index`** en índices de carpeta: verificar primero en 5.2.x.
4. **`ContentIndex`: opción para filtrar el RSS por carpeta** (o feeds por carpeta), útil para sitios multilingües y por secciones.
5. **i18n por página**: que los componentes elijan la traducción por `frontmatter.lang` y que `Head` emita `hreflang`. Es grande: proponerlo como discusión (relacionado con #803 / #2297) antes de escribir código.
6. Revisar las traducciones **pt-BR / es-ES** de los plugins que usamos y corregir lo que suene raro (como se hizo con fr-FR en #2513).
