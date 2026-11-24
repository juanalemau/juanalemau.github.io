# UX del blog alemau — propuesta (ux-designer, 2026-11-23)

Estado: **propuesta**. Nada de esto está aplicado; las decisiones que Juan elija se registran en `decisiones.md`.
Base: Quartz v5.1 (`quartz.config.yaml`), docs oficiales en `docs/` y el HTML publicado en https://juanalemau.github.io.

## 0. Diagnóstico (verificado en el sitio publicado)

| Hallazgo | Evidencia | Impacto |
| --- | --- | --- |
| `/pt/` y `/en/` se sirven con `<html lang="es">` | `curl https://juanalemau.github.io/pt/` | Lectores de pantalla leen el portugués con voz española; Google recibe señal de idioma errónea. |
| Textos de la interfaz siempre en español (o inglés): "Recientes", "Explorador", "Vista Gráfica", "Modo oscuro", "Search" | mismo HTML | Un lector en pt/en ve interfaz mezclada. |
| Favicon = cristal por defecto de Quartz (`quartz/static/icon.png`) y `og-image.png` por defecto | archivo 200×200 | La marca no aparece en pestañas ni al compartir. |
| Plantilla de "jardín de notas" completa (grafo, backlinks, explorer, recientes) | config | Ruido para un blog con 0 artículos; en móvil la barra izquierda se comprime. |

**Lo que Quartz permite sin tocar `quartz/` (comprobado en el código/docs):**

- `lang:` en el frontmatter **sí** cambia `<html lang>` por página (`quartz/components/renderPage.tsx`, línea ~368: `frontmatter?.lang ?? cfg.locale`). Es la corrección más barata y de mayor impacto.
- El `locale` global (`es-ES`) es único: los textos de los plugins no cambian por página (`docs/features/i18n.md`). No hay i18n de contenido nativo.
- El `filterFn` del Explorer se serializa y **se ejecuta en el navegador** en cada navegación (`node_modules/@quartz-community/explorer/dist/index.js`), así que puede leer `location.pathname` y mostrar solo la carpeta del idioma actual. Se configura en `quartz.ts` (TS override), no en `quartz/`.
- `note-properties` resuelve enlaces dentro de propiedades del frontmatter: un `translations:` con wikilinks puede mostrarse como enlaces sin escribir código.
- Para un componente nuevo (selector), la vía documentada es un plugin propio (`docs/customizing components.md`, opción 4; `docs/advanced/creating components.md`), instalado con `npx quartz plugin add github:juanalemau/<repo>`.

---

## 1. Navegación entre idiomas

Convención existente (CLAUDE.md): mismo nombre de archivo en `content/{es,pt,en}/<sección>/` y `translations:` en el frontmatter. Propuesta de frontmatter común a todas las opciones:

```yaml
---
title: Cómo elegir un portátil en 2026
lang: es            # obligatorio: corrige <html lang>
translations:
  pt: "[[pt/hardware/como-elegir-portatil]]"
  en: "[[en/hardware/como-elegir-portatil]]"
---
```

### Opción A — Cero código: `translations` vía note-properties + `lang`

```
┌──────────────────────────────────────────┐
│ alemau          [buscar] ◐               │
├──────────────────────────────────────────┤
│ Inicio › Español › Hardware              │
│ CÓMO ELEGIR UN PORTÁTIL EN 2026          │
│ 23 nov 2026 · 6 min                      │
│ ┌ translations ────────────────────────┐ │
│ │ pt: Como escolher…  en: How to pick… │ │
│ └──────────────────────────────────────┘ │
│ Texto del artículo…                      │
```

- Cómo: añadir `translations` a `includedProperties` de note-properties (y quitar `aliases`); estilo en `quartz/styles/custom.scss` para que parezca una barra "ES · PT · EN".
- Pros: nada que mantener; funciona sin JS.
- Contras: la etiqueta de la propiedad es la clave YAML; aspecto de "ficha de Obsidian"; no hay selector en la portada ni en páginas de carpeta.

### Opción B — Selector propio en la barra (plugin pequeño) + Explorer filtrado por idioma ★

```
Móvil (<800px)                          Escritorio (>1200px)
┌──────────────────────────────┐        ┌─────────────┬──────────────────────┬──────────┐
│ ▣ alemau  🔍  ES|pt|en  ◐  ☰ │        │ ▣ alemau    │ Inicio › Hardware    │ Índice   │
├──────────────────────────────┤        │ 🔍 ◐ 📖     │ CÓMO ELEGIR UN…      │ · Precio │
│ Inicio › Hardware            │        │ ES | pt | en│ 23 nov · 6 min       │ · CPU    │
│ CÓMO ELEGIR UN PORTÁTIL      │        │─────────────│                      │ · RAM    │
│ 23 nov 2026 · 6 min          │        │ Hardware ▸  │ Texto del artículo…  │          │
│ Texto…                       │        │ Software ▸  │                      │          │
└──────────────────────────────┘        │ IA ▸        │                      │          │
                                        └─────────────┴──────────────────────┴──────────┘
```

- Selector `ES | PT | EN` en el grupo `toolbar` (junto a búsqueda y modo oscuro). Idioma actual resaltado y con `aria-current="true"`; cada enlace con `lang` y `hreflang`. Lógica: usa `translations` del frontmatter; si falta, cambia el primer segmento de la URL (`/es/x` → `/pt/x`, válido por la regla de mismo nombre de archivo); si la traducción no existe, enlaza al índice del idioma y lo marca atenuado ("aún no traducido").
- Bonus SEO en el mismo plugin: `<link rel="alternate" hreflang="…">` en el `<head>`.
- Explorer filtrado (en `quartz.ts`, no en el núcleo):

  ```ts
  ExternalPlugin.Explorer({
    filterFn: (node) => {
      const lang = location.pathname.split("/").filter(Boolean)[0]
      const langs = ["es", "pt", "en"]
      if (node.slugSegment === "tags") return false
      if (!langs.includes(lang)) return true          // portada: muestra las 3
      return node.slugSegments.length > 1 || node.slugSegments[0] === lang
    },
  })
  ```
  (Ruta relativa al `basepath`; como el sitio está en la raíz del dominio, el primer segmento es el idioma. Validar con `especialista-quartz`.)
- Pros: navegación trilingüe evidente en todas las páginas; móvil primero; no toca `quartz/`; reutilizable (podría contribuirse a la comunidad).
- Contras: un repositorio extra (plugin) que mantener y compilar; trabajo de `especialista-quartz` (~1 tarde).

### Opción C — Enlaces fijos por idioma (sin traducción por artículo)

```
┌──────────────────────────────────────────┐
│ alemau          [buscar] ◐               │
│ Español · Português · English            │  ← enlaces a /es /pt /en
├──────────────────────────────────────────┤
│ Artículo…                                │
```

- Cómo: tres wikilinks en un componente de texto o en el pie (`footer.links`), más el `filterFn` de arriba.
- Pros: trivial. Contras: el lector que cambia de idioma pierde el artículo y vuelve a la portada del idioma.

**Recomendación: B, en dos fases.**
1. Ya (sin código nuevo): `lang:` en todos los `.md` (incluido `content/index.md` → `lang: es`), `translations:` en el frontmatter y Opción A como puente; `filterFn` en `quartz.ts`.
2. Cuando haya los primeros artículos: plugin selector (B) y quitar `translations` de note-properties.

Sobre los textos de interfaz en español: no tienen arreglo limpio con un `locale` global. Mitigación: **reducir componentes con texto** (ver punto 3) para que casi no quede interfaz que traducir. Lo que quede (búsqueda, modo oscuro) son iconos con `title`, de bajo impacto.

---

## 2. Portada (`content/index.md`)

Hoy: párrafo en español + lista con banderas. Las banderas representan países, no idiomas (🇪🇸 excluye a Perú/LatAm; 🇧🇷 a Portugal) — mejor códigos de idioma.

### Opción A — Puerta trilingüe con tres tarjetas ★

```
┌──────────────────────────────────────────┐
│                 ▣ alemau                 │
│  Tecnología explicada con ejemplos claros│
│                                          │
│ ┌──────────────────────────────────────┐ │
│ │ ES  Español                        → │ │
│ │ IA, software y hardware para decidir │ │
│ │ mejor en el día a día.               │ │
│ └──────────────────────────────────────┘ │
│ ┌──────────────────────────────────────┐ │
│ │ PT  Português                      → │ │
│ │ IA, software e hardware para decidir │ │
│ └──────────────────────────────────────┘ │
│ ┌──────────────────────────────────────┐ │
│ │ EN  English                        → │ │
│ │ AI, software and hardware, explained │ │
│ └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
  Escritorio: las 3 tarjetas en fila.
```

- Cada tarjeta en `<div lang="pt">…</div>` (HTML inline en el Markdown) para que el lector de pantalla cambie de voz. Toda la tarjeta es el área de clic (≥ 44 px de alto).
- Sin grafo, sin explorer, sin migas en la portada (`condition: not-index` ya cubre las migas).

### Opción B — Portada en español + franja de idiomas + últimos artículos

```
┌──────────────────────────────────────────┐
│ ▣ alemau            ES | pt | en      ◐  │
│ Tecnología explicada con ejemplos claros │
│ Últimos artículos                        │
│ · Cómo elegir un portátil (23 nov)       │
│ · ¿Vale la pena Copilot? (20 nov)        │
└──────────────────────────────────────────┘
```

- Coherente con "es principal", pero pt/en quedan como ciudadanos de segunda. Necesita `recent-notes` con `filter` por carpeta (TS override).

### Opción C — Redirección automática por `navigator.language`

- Contras: requiere JS, confunde a buscadores y a quien comparte enlaces, y quita control al lector. **Descartar**; como mucho, resaltar la tarjeta del idioma del navegador (mejora progresiva).

**Recomendación: A ahora** (no hay artículos). Cuando existan, añadir bajo cada tarjeta 2–3 títulos recientes de ese idioma. Las portadas de idioma (`/es/`, `/pt/`, `/en/`) son páginas de carpeta y ya listan los artículos: ahí va el texto de bienvenida corto + la lista.

---

## 3. Layout general (blog, móvil primero)

Valoración de cada componente para un **lector de blog**:

| Componente | Hoy | Propuesta | Motivo |
| --- | --- | --- | --- |
| graph | derecha, todas las páginas | **quitar** (`enabled: false`) | Herramienta de jardín de notas; JS pesado; etiqueta en español; poco valor con pocos artículos. |
| backlinks | derecha | **quitar** por ahora; reconsiderar como "Relacionados" en `afterBody` con `condition: has-backlinks` cuando haya >15 artículos | Con enlaces cruzados entre traducciones mostraría "la misma nota en otro idioma" como backlink. |
| explorer | izquierda | **mantener filtrado por idioma** (punto 1); `folderDefaultState: collapsed`; en móvil queda como menú ☰ | Sirve como menú de secciones. |
| recent-notes | izquierda | **quitar** de la barra | Mezcla idiomas, título fijo "Recientes", se comprime en móvil (lo advierte `docs/layout.md`). Su función la cumplen las páginas de carpeta. |
| table-of-contents | derecha | **mantener**, `display: desktop-only`, `condition: has-toc` | Útil en artículos largos; en móvil roba espacio antes del texto. |
| breadcrumbs | beforeBody, not-index | mantener | Orientación; muestra la sección. |
| content-meta | beforeBody | mantener (fecha + tiempo de lectura) | Esencial en blog. |
| note-properties | description/tags/aliases | solo `tags` (y `translations` en fase 1), o `hidePropertiesView: true` + activar `tag-list` | `description` duplica la entradilla; `aliases` es ruido interno. |
| reader-mode, darkmode, search | toolbar | mantener | Lectura cómoda. |
| footer | GitHub + Quartz (MIT) | mantener el crédito; añadir `message` con "Contenido CC BY 4.0" | Cumple CLAUDE.md y la licencia decidida. |
| comments (giscus) | apagado | sigue apagado (decisión ya tomada) | — |

### Opción A — Barra lateral mínima (marco `default`) ★

```
Móvil                                   Escritorio
┌──────────────────────────────┐        ┌────────────┬────────────────────────┬─────────┐
│ ▣ alemau 🔍 ES|pt|en ◐ 📖 ☰ │        │ ▣ alemau   │ Inicio › IA            │ Índice  │
├──────────────────────────────┤        │ 🔍 ◐ 📖    │ TÍTULO DEL ARTÍCULO    │ · …     │
│ Inicio › IA                  │        │ ES|pt|en   │ fecha · min · #tags    │         │
│ TÍTULO                       │        │ ────────── │                        │         │
│ fecha · min                  │        │ IA ▸       │ ~65–75 caracteres por  │         │
│ Texto (ancho completo)       │        │ Software ▸ │ línea                  │         │
│ ── pie: CC BY · Quartz ──    │        │ Hardware ▸ │                        │         │
└──────────────────────────────┘        └────────────┴────────────────────────┴─────────┘
```

Cambios de config: graph/backlinks/recent-notes `enabled: false`; TOC `display: desktop-only`. Mínimo riesgo.

### Opción B — Cabecera horizontal estilo revista (slot `header`)

```
┌───────────────────────────────────────────────────────────┐
│ ▣ alemau     IA · Software · Hardware    🔍 ES|pt|en ◐   │
├───────────────────────────────────────────────────────────┤
│              TÍTULO DEL ARTÍCULO                          │
│              fecha · min                                  │
│              Texto centrado…                              │
└───────────────────────────────────────────────────────────┘
```

- `page-title`, `search`, `darkmode` y selector con `position: header`; sin barras laterales (`positions: { left: [], right: [] }` en `byPageType.content`). Las secciones necesitan enlaces fijos (no hay componente "menú" listo → otro componente propio).
- Más "blog", pero más trabajo; hay que comprobar el aspecto del slot `header` en tablet.

### Opción C — Plantilla actual recortada

Solo quitar el grafo. Rápido, pero sigue pareciendo un jardín de notas y la interfaz en español pesa más.

**Recomendación: A ahora; B como evolución** cuando el plugin selector exista y haya 3+ secciones. Largo de línea: el ancho central por defecto de Quartz (~750 px) con IBM Plex Sans 16–18 px da ~70–80 caracteres; si se nota largo, limitar `article { max-width: 68ch }` en `custom.scss`.

---

## 4. Visual de marca: contraste WCAG y monograma

### Contraste calculado (fórmula WCAG 2.x, luminancia relativa)

Fondo claro `#fbfaf7`, fondo oscuro `#10132f`. AA texto normal ≥ 4,5:1; texto grande/no textual ≥ 3:1.

**Modo claro**

| Uso en Quartz | Color | Contraste | AA |
| --- | --- | --- | --- |
| `dark` (títulos) | #161A44 | 15,90 | ✅ |
| `darkgray` (cuerpo) | #4e4e4e | 7,97 | ✅ |
| `secondary` (enlaces, título del sitio) | #C8102E | 5,64 | ✅ |
| `tertiary` (hover de enlaces) | #B5810F | **3,29** | ❌ texto |
| oro puro | #E5A11C | **2,13** | ❌ (solo decorativo) |
| `gray` (fechas, migas, metadatos) | #b8b8b8 | **1,90** | ❌ |
| `lightgray` (bordes, fondo de código) | #e5e5e5 | 1,21 | decorativo |
| texto `dark` sobre `textHighlight` (#f4dcae) | #161A44 | 12,40 | ✅ |
| enlace sobre `textHighlight` | #C8102E | 4,40 | ⚠️ roza |

**Modo oscuro**

| Uso | Color | Contraste | AA |
| --- | --- | --- | --- |
| `dark` (títulos) | #eef0fb | 15,99 | ✅ |
| `darkgray` (cuerpo) | #d4d4d4 | 12,25 | ✅ |
| `secondary` (enlaces) | #F0566B | 5,40 | ✅ |
| `tertiary` | #E5A11C | 8,17 | ✅ |
| `gray` (metadatos) | #646464 | **3,07** | ❌ |
| `lightgray` (bordes/fondos) | #2a2e5c | 1,42 | decorativo |
| texto sobre `textHighlight` (#49392a) | #d4d4d4 | 7,45 | ✅ |

**Combinaciones de marca (logo, tarjetas, OG)**

| Par | Contraste | Uso |
| --- | --- | --- |
| oro sobre índigo | 7,47 | ✅ texto y logo |
| índigo sobre oro | 7,47 | ✅ botones/etiquetas |
| blanco sobre cochinilla | 5,88 | ✅ botón/etiqueta |
| cochinilla sobre índigo | **2,82** | ❌ incluso como objeto gráfico (<3:1) |
| #F0566B sobre índigo | 4,94 | ✅ alternativa del cursor rojo sobre fondo índigo |

### Ajustes propuestos (mantienen la identidad)

| Token | Modo | Actual → Propuesto | Nuevo contraste | Nota |
| --- | --- | --- | --- | --- |
| `gray` | claro | #b8b8b8 → **#5c6080** | 5,85 | gris azulado (familia índigo) para fechas/migas; sobre `lightgray` 4,85 |
| `gray` | oscuro | #646464 → **#8a8fb0** | 5,74 | mismo tono índigo aclarado; alternativa más suave #9ca0c0 (7,09) |
| `tertiary` | claro | #B5810F → **#8C6200** | 5,21 | ocre oscuro del oro; alternativa #946B0A (4,61) |
| `secondary` sobre resaltado | claro | — | — | bajar `textHighlight` a `#E5A11C40` si se usan enlaces dentro de `==resaltado==` |

Reglas de uso: **oro puro solo en modo oscuro, en fondos índigo o como decoración** (subrayados, bordes de cita); **cochinilla nunca sobre índigo**; en modo claro el rojo es el color de enlace y de acento, no de cuerpo de texto. Bordes `lightgray` quedan decorativos; si el campo de búsqueda depende de su borde para ser visible, darle borde `gray` (≥ 3:1).

### Monograma y favicon

- Sustituir `quartz/static/icon.png` (cristal de Quartz) por el monograma "A" 5×6: **PNG 512×512** (el plugin favicon lo reduce a 48×48). Es un asset, no código: cambio mínimo, documentarlo en `decisiones.md`.
- Versión favicon: **"A" oro sobre cuadrado índigo** (7,47:1) con el cursor en **#F0566B** (4,94:1), no en #C8102E (2,82:1). A 16–32 px la cuadrícula 5×6 se lee si cada celda ≥ 3 px: en 32 px usar celdas de 4 px con margen de 4 px.
- `og-image.png` (y el plugin og-image): fondo índigo, monograma a la izquierda, título en Unbounded oro/blanco. Revisar con `especialista-quartz` si el plugin og-image acepta colores/fuente de la config (usa el tema por defecto).
- Título del sitio (`page-title`): monograma pequeño (24 px) + "alemau" en Unbounded; en móvil, solo monograma + palabra si cabe.

---

## Decisiones pendientes para Juan

1. Selector de idioma: ¿B en dos fases (recomendado), A sola o C?
2. Portada: ¿A (tres tarjetas, recomendado) o B (español primero)?
3. Quitar grafo, backlinks y recientes; TOC solo escritorio: ¿de acuerdo?
4. Layout: ¿A barra lateral mínima (recomendado) o ir directo a B cabecera?
5. Colores: aprobar `gray` #5c6080 / #8a8fb0 y `tertiary` claro #8C6200.
6. Favicon: aprobar oro sobre índigo con cursor #F0566B y proporcionar el monograma en vector/PNG 512.
7. (Para product-owner) RSS: hoy es un único feed con los tres idiomas mezclados; ¿un feed por idioma más adelante?
