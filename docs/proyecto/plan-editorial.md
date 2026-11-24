# Plan editorial — alemau

Estado: **propuesta del product-owner (2026-11-23)**. Las decisiones de alcance son de Juan; las marcadas como "propuesta" en `decisiones.md` no están decididas.

## 1. Público y propuesta de valor

**Persona A — "La que decide sola" (principal).** Profesional de 25–45 años en Latinoamérica o Brasil, técnico o semi-técnico (dev junior/mid, soporte, analista, emprendedor). Usa IA a diario pero no sabe si está pagando lo correcto, si su PC aguanta o qué aprender. Lee en el celular, quiere la respuesta en 5 minutos y un "depende de X" explicado.

**Persona B — "El curioso que compra".** Gamer o aficionado a la tecnología que va a gastar dinero (GPU, suscripción, notebook) y quiere una opinión honesta y sin patrocinio antes de decidir.

**Propuesta de valor (1 frase):**
> Tecnología explicada con ejemplos reales para que decidas hoy qué usar, comprar o aprender — sin humo y con fuentes.

Regla de oro de cada artículo: **termina con una decisión** ("si eres X, haz Y; si eres Z, espera") y una tabla o checklist.

## 2. Secciones

| Slug (igual en los 3) | es | pt | en |
|---|---|---|---|
| `ia` | IA y desarrollo | IA e desenvolvimento | AI & development |
| `software` | Software | Software | Software |
| `hardware` | Hardware | Hardware | Hardware |
| `mercado` | Mercado tech | Mercado tech | Tech market |

- Cada sección tiene `content/{es,pt,en}/<slug>/index.md` con el título traducido (es lo que ve el lector).
- El **formato** va en etiquetas, no en carpetas: `comparativa`, `guia`, `opinion`, `experiencia`. Así un artículo no tiene que "elegir" entre ser guía o comparación.
- Máximo 4 secciones en el MVP; crear una nueva solo cuando haya ≥ 5 artículos que no encajen.

**Slugs: recomendación = iguales en los 3 idiomas** (carpetas y nombres de archivo).
- A favor: coincide con la regla de `CLAUDE.md` (mismo nombre de archivo en los 3 idiomas), el selector de idioma es un simple cambio de prefijo `/es/` → `/pt/`, menos errores con agentes, enlaces `translations:` triviales.
- En contra: algo menos de SEO en pt/en por URL en español. Impacto bajo: título, descripción y contenido sí van traducidos.
- Alternativa descartada: slugs traducidos (más SEO, pero triplica el mantenimiento y rompe la regla actual).
- Para artículos: slug corto en español sin tildes (`que-ia-pagar-2026`), reutilizado en pt/en.

## 3. Backlog del sitio (MoSCoW)

### Must (MVP, antes o junto con el 1er artículo)
1. ✅ **Configuración básica de identidad** (hecho 2026-11-23: `pageTitle: alemau`, `baseUrl: juanalemau.github.io`, `locale: es-ES`, `analytics: null`; `quartz.config.default.yaml` es solo la plantilla original de Quartz).
   - Dado el sitio publicado, cuando se abre cualquier página, entonces el título es "alemau", los enlaces usan `juanalemau.github.io` y **no se carga ningún script de analytics** (coherente con la decisión 2026-11-23).
2. **Selector de idioma** es/pt/en en cada página.
   - Dado un artículo en `/es/ia/x`, cuando hago clic en "pt", entonces llego a `/pt/ia/x`; si no existe la traducción, llego a la portada pt (nunca a un 404).
3. **Portada por idioma** con los últimos artículos y las 4 secciones.
   - Dado `/es/`, cuando entro, entonces veo la propuesta de valor, las secciones y los 5 artículos más recientes.
4. **Página "Sobre" / "Sobre mim" / "About"** (quién escribe, cómo se usa IA para escribir, sin patrocinios, licencia CC BY 4.0, cómo contactar sin exponer email personal — p. ej. issues del repo o redes de la marca).
5. **Crédito y licencias visibles** (Quartz en el pie, CC BY 4.0 del contenido).
6. **RSS** (Quartz ya genera `index.xml`).
   - Dado un lector de RSS, cuando me suscribo, entonces recibo los artículos nuevos. Ideal: un feed por idioma — a validar con `especialista-quartz` (si no es nativo, pasa a Should).

### Should (primer mes)
7. Plantilla de artículo (frontmatter `title`, `date`, `description`, `tags`, `translations:`, bloque "Decisión rápida" al inicio y "Fuentes" al final).
8. Fecha de "última revisión" visible (los artículos de mercado envejecen).
9. Imagen Open Graph por defecto (para que se vea bien al compartir en IG/WhatsApp/X).
10. Páginas de etiquetas por formato (`comparativa`, `guia`…).

### Could (cuando haya ≥ 6 artículos)
11. **Comentarios giscus — recomendación: todavía no.** Exige cuenta de GitHub al lector (el público A/B muchas veces no la tiene), añade un script externo y moderación. Reevaluar con 6+ artículos; mientras tanto, "¿dudas? abre un issue / escríbeme en redes".
12. **Newsletter — recomendación: no en el MVP.** Implica servicio externo, datos personales (emails) y obligación de cadencia. Alternativa barata: RSS-a-email más adelante, o un resumen mensual si hay demanda real (≥ 20 personas pidiéndolo).
13. Serie "Qué cambió este mes" en `mercado`.

### Won't (por ahora)
- Analytics de terceros, anuncios, banners de cookies, afiliados sin aviso.

## 4. Primeros 6 artículos (en orden)

| # | Título (es) | Sección / formato | Decisión que ayuda a tomar | Por qué ahora |
|---|---|---|---|---|
| 1 | **Cómo escribo un blog en 3 idiomas con agentes de IA (y qué hago yo)** | `ia` / experiencia | ¿Vale la pena usar agentes de IA para un proyecto personal? Qué delegar y qué no. | Es el caso real que Juan está viviendo hoy; no depende de datos externos difíciles de verificar y presenta el blog y su método (transparencia). **Escribir ya.** |
| 2 | ¿Pagar una suscripción de IA o usar lo gratis? Cuándo vale la pena | `ia` / comparativa | Gratis vs plan pago según uso (estudio, trabajo, programación). | Precios y planes cambian seguido y la duda es universal; Juan ya pasó por esa decisión. |
| 3 | IA local vs en la nube: qué puedes correr en tu PC de verdad | `hardware` / guia | ¿Mi GPU sirve para IA local o pago la nube? | Muchos tienen GPUs de gama media (como una RTX 2060); ejemplo concreto con hardware propio. |
| 4 | ¿Actualizar la GPU ahora o esperar? Guía para jugar y para IA | `hardware` / comparativa | Comprar ahora, comprar usado o esperar. | Temporada de ofertas de fin de año: decisión de compra inminente. |
| 5 | Linux en el escritorio hoy: cuándo sí y cuándo no | `software` / experiencia | ¿Cambio de Windows a Linux para trabajar/jugar? | Experiencia directa de Juan; tema recurrente con mucho mito. |
| 6 | Cómo está el mercado para desarrolladores con la IA: qué aprender en 2027 | `mercado` / opinion + datos | Qué habilidad estudiar los próximos 6 meses. | Cierre de año = planificación; requiere fuentes (encuestas públicas) — a cargo de `especialista-ia` + `reporter-blog`. |

Criterio de aceptación común (Dado/Cuando/Entonces):
- Dado un artículo listo, cuando se publica, entonces existe en es/pt/en con el mismo slug, tiene "Decisión rápida" al inicio, al menos una tabla o checklist, fuentes enlazadas, `date:` y ningún dato sin verificar presentado como hecho.

## 5. Cadencia y métrica

**Cadencia realista:** **1 artículo cada 2 semanas** (cada uno son 3 versiones + revisión). Flujo por artículo: Juan define tesis y experiencia → `reporter-blog` redacta es → `especialista-ia`/`arquitecto-fullstack` revisan lo técnico → `documentador` revisa y traduce pt/en → Juan aprueba. Margen: si una quincena falla, no se compensa con dos de golpe; se mantiene la calidad.
- Los 6 primeros: noviembre 2026 – febrero 2027.
- Opcional: 1 reel corto (IG/TikTok "alemau") por artículo, que enlaza al blog.

**Métrica de éxito (sin analytics de terceros):**
1. **Constancia (principal, 3 meses):** ≥ 80 % de las quincenas con artículo publicado en los 3 idiomas.
2. **Utilidad declarada:** nº de respuestas reales de lectores (mensajes en redes, issues, menciones) que digan que el artículo les ayudó a decidir. Meta: ≥ 5 en los 3 primeros meses. Registrar a mano en un archivo del repo, sin datos personales (solo fecha + artículo + canal).
3. **Opcional, sin script en el sitio:** Google Search Console (clics e impresiones de búsqueda; no instala nada en las páginas). Decide Juan si lo usa.

Revisión del plan: tras el artículo 3 y tras el 6.
