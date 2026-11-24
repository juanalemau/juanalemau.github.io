# Marketing para devs: nombre, posicionamiento y difusión

Fecha: 2026-11-24 · Autor: marketing-dev · Estado: **propuesta, Juan decide** (nombre, gasto en dominio y cuentas nuevas).

Producto actual: resumen diario trilingüe (es/pt/en) para devs, con estética changelog/`git log` (`v2026.11.24`, cada noticia = un commit), generado con IA y revisado en 4 capas, publicado a las 06:00 BRT en https://juanalemau.github.io (RSS por idioma en `/{es,pt,en}/diario/feed.xml`).

Estado del repo verificado hoy (`gh repo view`): descripción todavía de "blog de tecnología", **sin topics**, Discussions apagado, 0 estrellas, no existe el repo de perfil `juanalemau/juanalemau`.

---

## 1. Naming

### 1.1 Opciones verificadas

Método (2026-11-24): `gh api users/<n>` y `orgs/<n>` (¿cuenta u organización ocupada?), `gh api search/repositories?q=<n>+in:name` (repos homónimos), `https://registry.npmjs.org/<n>` (404 = libre), `dig NS <n>.{dev,io,com}` (NXDOMAIN = sin DNS, **probablemente** libre; solo un registrador lo confirma) y WebSearch del nombre como producto/newsletter. **No verificado:** marcas registradas (USPTO/EUIPO/INPI) y redes sociales (Bluesky, Mastodon, X, Instagram).

| Nombre | Idea | Cuenta/org GitHub | Repos homónimos | npm | .dev | .io | .com | Producto homónimo (web) |
|---|---|---|---|---|---|---|---|---|
| **headcommit** | `HEAD` = lo último; cada mañana es el commit de cabeza | libre | 0 | libre | NXDOMAIN | NXDOMAIN | NXDOMAIN | nada encontrado |
| **morningdiff** | el diff del mundo dev desde ayer | libre | 0 | libre | NXDOMAIN | NXDOMAIN | ocupado | nada; existe "The Diff" (Byrne Hobart, finanzas/tech) |
| **diffdaily** | diff diario | libre | 0 | libre | ocupado | NXDOMAIN | ocupado | confusión con "The Diff" y "StackDiff" |
| **pulldaily** | `git pull` diario | libre | 0 | libre | NXDOMAIN | NXDOMAIN | ocupado | nada encontrado |
| **stdoutdaily** | la salida estándar del día | libre | 0 | libre | NXDOMAIN | NXDOMAIN | NXDOMAIN | nada; largo de escribir |
| dailydiff | diff diario | libre | 11 (máx. 3★) | libre | ocupado | ocupado | ocupado | — |
| commitday | el día como commit | libre | 5 | libre | NXDOMAIN | NXDOMAIN | ocupado | — |
| ~~gitpulse~~, ~~daylog~~, ~~devdiff~~ | — | **organización existente** | 500+ / 26 | devdiff y daylog ocupados | — | — | — | descartados |

Notas:
- **"alemau" como organización no es posible**: la cuenta `AleMau` existe en GitHub (creada en 2013, 0 repos; los logins no distinguen mayúsculas). Por eso la marca-madre sigue en el usuario `juanalemau`.
- `alemau.dev`, `alemau.io`, `alemau.com`: NXDOMAIN (probablemente libres; confirmar en registrador).
- Competidor directo detectado: **Dev Digest** (https://jerryni.github.io/dev-digest/en/), diario en en/zh/ja, también en GitHub Pages, fuentes HN + GitHub Trending. Refuerza que el diferencial debe ser el formato changelog + español/português + transparencia de la IA.

### 1.2 Restricción técnica y opciones de estructura

El sitio raíz **tiene que** vivir en el repo `juanalemau.github.io` para servir en `https://juanalemau.github.io/`. Un repo con otro nombre se sirve en una subruta (`juanalemau.github.io/<repo>/`).

| Opción | Qué cambia | URL / SEO | Costo |
|---|---|---|---|
| **A. Mantener repo, cambiar solo el branding** ("headcommit · by alemau") | título del sitio, descripción, topics, social preview, README | URLs intactas, cero pérdida de SEO | 0 |
| B. Organización `headcommit` + repo `headcommit.github.io` | sitio pasa a `headcommit.github.io` | URL nueva; GitHub Pages **no** hace 301 entre dominios github.io: solo meta-refresh + `canonical` desde el sitio viejo → se pierde parte del posicionamiento y los RSS suscritos se rompen si no se mantienen | 0 € pero mantener 2 sitios; org separada del perfil personal |
| C. Dominio propio (`headcommit.dev` o `alemau.dev`) apuntando al **mismo repo** | archivo `CNAME`; GitHub Pages redirige `juanalemau.github.io` → dominio propio | buena: redirección automática de Pages; .dev exige HTTPS (Pages lo da) | ~US$ 12–20/año + mantener DNS (y protegerlo: verificación de dominio en GitHub contra takeover) |
| D. (Complementaria) repo `juanalemau/headcommit` con el **generador** abierto (scripts + workflow) | el sitio sigue igual; el motor tiene repo propio con nombre de mercado | suma un repo "estrellable" que sí califica para Show HN/awesome-lists de herramientas | trabajo de separar código; mantener 2 repos |

### 1.3 Recomendación

**Nombre: `headcommit`** — el único con todo libre (usuario/org GitHub, repos, npm, .dev/.io/.com sin DNS), corto, pronunciable en los 3 idiomas y 100 % coherente con la dirección visual A (el resumen *es* el `HEAD` del día). Firma: **headcommit · by alemau**.

**Estructura: A ahora, C cuando haya tracción** (p. ej. ≥ 100 estrellas o ≥ 30 días seguidos publicados). A no cuesta nada ni toca URLs; C se puede hacer después sin perder SEO porque Pages redirige solo. Antes de cualquier anuncio público, Juan puede **reservar el usuario/organización `headcommit` en GitHub** (gratis) para evitar que lo tomen, sin usarlo todavía. D queda como fase 2 si se quiere un Show HN.

Alternativa si no gusta: `morningdiff` (pero el .com está ocupado).

---

## 2. Posicionamiento

**Frase (en):** *"headcommit — the dev world's `git log`, every morning: 10 verified commits from GitHub, HN and dev blogs, in English, Español and Português."*

**Frase (es):** *"El `git log` del mundo dev, cada mañana: 10 commits verificados, en español, português e English."*

Público: devs que leen en es/pt (LatAm, España, Brasil, Portugal) y devs en inglés que quieren algo escaneable en 3 minutos, sin cuenta ni email.

| | Formato | Frecuencia | Idiomas | Cuenta/email | alemau/headcommit se diferencia en… |
|---|---|---|---|---|---|
| daily.dev | feed personalizado / extensión del navegador, 2000+ fuentes | continuo | en | cuenta para personalizar | curaduría corta y cerrada (10 ítems), sin infinite scroll |
| TLDR | email | diario (6:00 ET) | en | email | sin suscripción obligatoria (RSS/web), es/pt nativos, open source |
| Hacker Newsletter | email curado a mano (Kale Davis, desde 2010, 60k+) | semanal (viernes) | en | email | diario, más fuentes que HN |
| Changelog News | newsletter + podcast (Jerod Santo) | semanal | en | email/podcast | diario y trilingüe; formato changelog literal |

Diferencial honesto: **(1)** formato `git log` que se escanea como un changelog; **(2)** trilingüe con es/pt de primera clase; **(3)** transparencia: hecho con IA (Gemini) con 4 capas de verificación, código y prompts públicos, fuentes enlazadas; **(4)** sin tracking, sin cuenta, RSS. Debilidad a asumir públicamente: es IA y puede equivocarse → canal visible de correcciones (ver Discussions).

---

## 3. Difusión dentro de GitHub (legítima, sin spam)

### 3.1 Descripción, website y topics
- **Descripción** (≤ 350 caracteres, en inglés porque es lo que indexa la búsqueda global): `headcommit — the dev world's git log, every morning. Daily AI-written, fact-checked digest of GitHub, Hacker News & dev blogs in English, Español, Português. RSS, no tracking. Built with Quartz.`
- **Website:** ya apunta a https://juanalemau.github.io (mantener, o `/en/diario/`).
- **Topics** (máx. 20, minúsculas y guiones): `developer-news`, `daily-digest`, `tech-news`, `changelog`, `hacker-news`, `github-trending`, `rss`, `newsletter`, `news-aggregator`, `ai-summarization`, `gemini`, `multilingual`, `spanish`, `portuguese`, `github-pages`, `github-actions`, `quartz`, `static-site`. Los topics son la puerta a `github.com/topics/<topic>` y a la búsqueda.

### 3.2 Social preview (Settings → Social preview)
PNG/JPG < 1 MB, **1280×640** (mínimo 640×320), fondo sólido (verificado en docs.github.com). Contenido: monograma "A" + `headcommit` en Unbounded, debajo un fragmento real estilo terminal (`$ git log --since=today --top=10` y 3 líneas `60fd17d release(web): …`), colores índigo #161A44 / oro #E5A11C / cochinilla #C8102E. Se reutiliza como `og-image.png` del sitio para que los enlaces compartidos se vean igual.

### 3.3 README estilo landing (qué cambiar en el actual)
El README actual habla de "blog personal de tecnología" y de cómo construir con Quartz: no vende el producto. Propuesta (en inglés primero, con enlaces a es/pt):
1. Título `headcommit · by alemau` + frase de posicionamiento.
2. Badges: último resumen (workflow `resumen-diario.yml` passing), licencia contenido CC BY 4.0, RSS.
3. **Captura** (o GIF corto) del resumen del día en claro y oscuro.
4. "Read today's digest" → 3 enlaces (en / es / pt) + 3 enlaces RSS.
5. "How it works" en 5 líneas: fuentes → filtro → Gemini redacta → revisor + reglas numéricas → falla cerrada; enlace a la página Sobre. Honesto sobre límites de la IA.
6. "Suggest a source / report an error" → Discussions.
7. Al final, mantener intactos **Créditos a Quartz/jackyzha0** y licencias (regla de CLAUDE.md).
8. Opcional y automatizable: bloque "Today's HEAD" con los 3 primeros ítems, actualizado por el mismo workflow diario (entre marcadores `<!-- HEAD:START -->`/`<!-- HEAD:END -->`). Ojo: un commit diario a `main` choca con la protección de rama; hacerlo solo en el profile README (3.5) o vía PR automático.

### 3.4 GitHub Discussions
Activar con categorías: **Announcements** (solo hitos/semanal, no cada día), **Corrections** (reportar un error en un ítem: refuerza la confianza en la IA), **Source suggestions** (feeds RSS para `scripts/fuentes.json`), **Ideas**, **Q&A**. Enlazar "report an error" desde cada ítem del resumen (`?category=corrections&title=<fecha>#<hash>`). Sin scripts externos en el sitio (a diferencia de giscus).

### 3.5 Profile README de juanalemau (automatizable)
Crear el repo público `juanalemau/juanalemau` (repo especial: su README aparece en el perfil). **Sí se automatiza con Actions:** `gautamkrishnar/blog-post-workflow` (★3.4k, última release 1.9.7 de 2026-08-10, cumple la regla de ≥ 2 semanas; fijarlo por SHA) lee `https://juanalemau.github.io/en/diario/feed.xml` (verificado: responde 200) y reescribe la lista entre `<!-- BLOG-POST-LIST:START -->` y `<!-- BLOG-POST-LIST:END -->`, con cron 09:30 UTC (06:30 BRT). Alternativa sin dependencias: un script Python de 30 líneas en el mismo workflow. Además: **pin** del repo del sitio (y de D si existe) en el perfil.

### 3.6 Releases
release-please ya publica Releases del **código** (`vX.Y.Z`): no mezclar los resúmenes diarios ahí. Lo que sí da distribución nativa: un Release por día (`v2026.11.24`, notas = el resumen) llega a quien marque **Watch → Custom → Releases** y tiene feed Atom (`/releases.atom`). Para no ensuciar el CHANGELOG del sitio, hacerlo en el repo D (`juanalemau/headcommit`) o descartarlo. Es la idea más "GitHub-native" del plan, pero requiere decisión.

### 3.7 Awesome-lists (verificadas hoy con `gh api`)
| Lista | Estado | Reglas de contribución verificadas | ¿Cuándo? |
|---|---|---|---|
| [jackyzha0/quartz → `docs/showcase.md`](https://github.com/jackyzha0/quartz/blob/v5/docs/showcase.md) | ★13.6k, activo (2026-11-23) | Lista simple `- [Nombre](url)` de sitios hechos con Quartz; PR que añade una línea | Ya: el sitio es un uso real y lucido de Quartz (además respeta el crédito) |
| [Infrasity-Labs/awesome-tech-newsletter](https://github.com/Infrasity-Labs/awesome-tech-newsletter) | ★10, activo (2026-11-23) | Editar el archivo de categoría en `directory/` (no el README, que se genera); fila `\| **Nombre** \| [↗](link) \| Descripción. \| Frequency \|`; PR | Ya (baja audiencia, poco riesgo) |
| [plenaryapp/awesome-rss-feeds](https://github.com/plenaryapp/awesome-rss-feeds) | ★2.9k, activo (2026-10-05) | Feeds nuevos **por formulario de Google o issue con plantilla** (no PR); categorías Programming / Tech / Web Development | Tras ~30 días publicados sin fallos |
| [zudochkin/awesome-newsletters](https://github.com/zudochkin/awesome-newsletters) | ★4.5k, activo (2026-10-01) | 1 PR por sugerencia, formato `[Nombre](link). Descripción.` al final de la categoría, buscar duplicados; el README pide recursos "very well-known" | Solo con tracción; hoy no hay email, solo RSS (podría no encajar) |
| ~~jondot/awesome-weekly~~ | sin pushes desde 2024-06 | — | no |

`sindresorhus/awesome` no aplica (lista de listas).

### 3.8 GitHub Trending: qué influye de verdad
GitHub **no documenta** el algoritmo. Lo observable: ordena repos por **estrellas ganadas en el periodo** (día/semana/mes) en relación con su historial, por lenguaje. Consecuencias: (1) lo que cuenta es un pico concentrado de estrellas reales en 24–48 h, que solo llega de un lanzamiento externo (HN, Reddit, dev.to) **con el repo listo antes**; (2) el sitio no es "código interesante" para quien llega del Trending: el repo D (generador reutilizable) tiene muchas más opciones; (3) comprar estrellas o intercambiarlas viola los Términos de GitHub y GitHub las elimina: **nunca**.

---

## 4. Fuera de GitHub

| Canal | Reglas verificadas / a revisar | Qué publicar | Momento |
|---|---|---|---|
| **Show HN** | Verificado (news.ycombinator.com/showhn.html): solo cosas que se puedan **probar**; *"blog posts, sign-up pages, newsletters, lists, and other reading material"* **no** son Show HN; prohibido pedir votos a amigos | **No** el resumen en sí. Sí el **generador open source** (repo D: "Show HN: I built a fact-checked, trilingual daily dev digest with free Gemini and GitHub Actions") | Cuando D exista y lleve ≥ 30 días estable; martes–jueves por la mañana en EE.UU.; Juan disponible para responder |
| HN normal | Enlace a un artículo con sustancia (no al índice del diario) | Artículo "Cómo evitamos que la IA invente datos en un resumen diario" (página Sobre en en) | Cualquier momento, una vez |
| **Reddit** | **No pude verificar** las reglas (reddit bloquea la lectura automática). Según guías de terceros: r/programming solo admite autopromoción de proyectos sustanciales y con restricciones; r/webdev tiene "Showoff Saturday"; r/SideProject la acepta. **Leer la sidebar/wiki de cada sub antes** y no publicar el mismo día en varios | r/SideProject y r/webdev (sábado) con captura y explicación técnica; r/brdev y r/programacion para es/pt (verificar reglas) | Tras tener README landing y social preview |
| **dev.to** | Permite publicar con `canonical_url` apuntando al original (no penaliza SEO del sitio) e importar por RSS (Settings → Extensions); revisar sus normas de contenido con IA (exigen declararlo) | Serie semanal "This week's HEAD" (resumen de la semana) + artículo técnico del pipeline, en inglés y español | Desde ya, semanal, no diario (evitar parecer spam) |
| **Product Hunt** | Guía oficial (help.producthunt.com, "Launch guide") existe; no pude leer el detalle de cada artículo. Conocido: el día de lanzamiento empieza a las 00:01 PT; no pedir votos directos | Lanzamiento único "headcommit" | Al final (fase 3), con dominio propio y ≥ 60 días de historial |
| **Bluesky / Mastodon** | Cuentas nuevas (decisión de Juan). En Mastodon, instancias como fosstodon.org exigen contenido FOSS/no comercial: leer reglas de la instancia; usar hashtags (#dev #programming #opensource); permitir bots solo si se marca la cuenta como bot | Post diario automático con el título del día + 3 ítems + enlace (cuenta marcada como **bot**) | Tras 2 semanas de calidad estable |

Métricas sin rastreo invasivo: estrellas, Insights → Traffic del repo (visitas y referentes, 14 días), suscriptores de Discussions, correcciones recibidas, Search Console (opcional, ya contemplado).

---

## 5. Backlog para el tablero (priorizado)

| # | Prioridad | Tarea | Criterio de aceptación |
|---|---|---|---|
| 1 | P0 | **Decidir nombre** (headcommit u otra) y registrar en `decisiones.md` | Entrada con fecha, decisión, motivo y alternativas |
| 2 | P0 | Reservar usuario/org `headcommit` en GitHub (sin usar) | La org existe y no tiene repos públicos; Juan es owner |
| 3 | P0 | Descripción + 18 topics en el repo | `gh repo view --json description,repositoryTopics` muestra los nuevos valores |
| 4 | P0 | README landing (sección 3.3) | Frase, captura, enlaces de lectura y RSS en 3 idiomas, "how it works", créditos Quartz intactos; revisado por documentador |
| 5 | P1 | Social preview 1280×640 (< 1 MB) y nuevo `og-image.png` | Imagen subida en Settings; el enlace del repo compartido en un chat muestra la tarjeta |
| 6 | P1 | Branding "headcommit · by alemau" en el sitio (`quartz.config.yaml`, portada, Sobre) | Título nuevo en las 3 lenguas; URLs sin cambios; build del deploy en verde |
| 7 | P1 | Activar Discussions con categorías Corrections / Source suggestions / Ideas / Q&A / Announcements | Categorías creadas; enlace "report an error" en cada resumen abre la categoría Corrections |
| 8 | P1 | Profile README `juanalemau/juanalemau` con últimos resúmenes automáticos | Workflow con action fijada por SHA; tras las 06:30 BRT el perfil muestra el resumen del día |
| 9 | P2 | PR al showcase de Quartz y a awesome-tech-newsletter | 2 PRs abiertos siguiendo el formato de cada repo |
| 10 | P2 | Serie semanal en dev.to con `canonical_url` | Primer post publicado con canonical al sitio y aviso de uso de IA |
| 11 | P3 | Evaluar repo D (generador open source) + Releases diarios | Documento de decisión (arquitecto-fullstack) con costo y riesgos |
| 12 | P3 | Plan de lanzamiento (Show HN del generador, Reddit, Product Hunt) y dominio propio | Calendario con fechas y criterios de tracción (≥ 30 días estables, ≥ 100★) aprobados por Juan |

---

Fuentes: GitHub REST API (consultas del 2026-11-24), registry.npmjs.org, DNS (`dig`), https://news.ycombinator.com/showhn.html, https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview, https://hackernewsletter.com/, https://changelog.com/news, https://jerryni.github.io/dev-digest/en/, https://daily.dev/blog/daily-dev-vs-tldr-developer-news-which-fits-you/, https://help.producthunt.com/en/collections/19793093-launch-guide, READMEs y CONTRIBUTING de las listas citadas.
