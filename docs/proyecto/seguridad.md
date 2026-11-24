# Revisión de seguridad y privacidad

Fecha: 2026-11-23 · Alcance: commit `47b4196`, historial de git, archivos públicos, workflows, dependencias, configuración del repositorio en GitHub y el sitio publicado en https://juanalemau.github.io. Revisión de solo lectura: no se cambió nada.

## Resumen

No hay hallazgos **críticos** ni **altos**. No se encontraron secretos, correos personales, rutas locales ni notas privadas en el repositorio ni en el historial. La cadena de suministro está bien cerrada: actions fijadas por SHA (verificado contra los tags oficiales), permisos mínimos, `persist-credentials: false`, ningún uso inseguro de `github.head_ref` y todos los plugins vienen de npm con lockfile e `integrity`. Lo pendiente es de severidad media o baja: scripts de terceros sin SRI, Google Fonts, publicación implícita de todo `content/` y algunos ajustes de GitHub.

## Verificaciones sin hallazgos

| Área | Resultado |
|---|---|
| Autor/committer de `47b4196` | `8999066+juanalemau@users.noreply.github.com` (noreply). Es el único commit de Juan; los demás correos son de autores de upstream (esperado). |
| Diff de `47b4196` | Sin `/home`, `/mnt`, correos, tokens ni claves. Solo menciona tokens en texto de reglas y en workflows de upstream que se borraron. |
| Archivos públicos (README.md, CLAUDE.md, `.claude/agents/`, `content/`, `docs/proyecto/`, `quartz.config.yaml`) | Sin datos personales más allá del nombre público y el enlace a GitHub. |
| `.claude/settings.json`, `.claude/hooks`, `.claude/skills/graphify`, `.claude/skills/ecc`, `.claude/rules`, `.claude/CLAUDE.md` | No están en git (`git ls-files` vacío) e ignorados por `.git/info/exclude` (ver B1). |
| `.github/workflows/deploy.yml` | `permissions: contents: read` global (l. 11-12) y `pages: write` + `id-token: write` solo en `deploy` (l. 50-52); SHAs fijados (l. 22, 26, 30, 43, 59); `persist-credentials: false` (l. 25). El entorno `github-pages` solo acepta la rama `main`. |
| `.github/workflows/pr-checks.yml` | Usa `pull_request` (no `pull_request_target`); `head_ref` y el título del PR pasan por `env:` (l. 16-17, 24-25) y se usan entre comillas, así que no hay inyección de comandos. Token de solo lectura. |
| Plugins de Quartz | Los 45 `@quartz-community/*` vienen de `registry.npmjs.org` y están fijados en `package-lock.json` (lockfile v3, 509 `integrity`). `npx quartz plugin install --dry-run` → "No Git or local plugins to install": no clona nada de git. No hay scripts `preinstall/postinstall` ni paquetes con `hasInstallScript`. |
| `npm audit` | 0 vulnerabilidades. |
| `.npmrc` | `engine-strict=true`, `legacy-peer-deps=true` (heredado de upstream; no afecta la seguridad). |
| PR #1 (Dependabot) | Solo cambia SHAs de actions oficiales: checkout v7.0.1, setup-node v7.1.0, cache v6.1.0, upload-pages-artifact v5.0.0 y deploy-pages v5.0.1. Los cinco SHAs coinciden con los tags de `actions/*` y todas las versiones tienen más de 2 semanas. Checks en verde. Se puede fusionar (ver M4). |
| Repo en GitHub | Ruleset `proteger-main` activo y sin bypass: bloquea borrado y force-push, exige PR (solo squash) y checks `convenciones` + `build`. Secret scanning y push protection activados, Dependabot security updates activado, permisos por defecto del workflow `read` y Actions no puede aprobar PRs. |
| Pages | `https_enforced: true`; HTTP redirige con 301. Build por workflow. |
| Imágenes | No hay imágenes propias en el repo (no hay riesgo de EXIF por ahora). |

## Hallazgos

### Críticos
Ninguno.

### Altos
Ninguno.

### Medios

**M1. Scripts y CSS de CDN sin Subresource Integrity (SRI)**
- Dónde: sitio publicado, `<head>`; lo inyecta el plugin `@quartz-community/latex` (`quartz.config.yaml:83`): `https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/copy-tex.min.js` y `katex.min.css`. Además, el JS del sitio importa en tiempo de ejecución `https://cdnjs.cloudflare.com/ajax/libs/mermaid/11.4.0/mermaid.esm.min.mjs` cuando una página tiene diagramas Mermaid.
- Escenario: si jsDelivr o cdnjs sirven un archivo alterado (CDN comprometido o un error de caché), ese JS se ejecuta con el origen `juanalemau.github.io` en todas las páginas. Ninguna etiqueta tiene `integrity=` ni `crossorigin`.
- Corrección (en orden de preferencia): (a) desactivar `latex` si el blog no va a usar fórmulas: hoy carga JS de terceros en todas las páginas sin necesidad; (b) si se mantiene, pedir que el plugin emita `integrity`/`crossorigin="anonymous"` o servir KaTeX/Mermaid como archivos propios desde `quartz/static`; (c) como red de seguridad, la CSP de M3 limitando los orígenes.

**M2. Google Fonts filtra la IP de cada lector a Google**
- Dónde: `quartz.config.yaml:15-16` (`fontOrigin: googleFonts`, `cdnCaching: true`). El HTML carga `fonts.googleapis.com` y `fonts.gstatic.com`.
- Escenario: cada visita envía la IP y el User-Agent del lector a Google sin consentimiento. Choca con la decisión de "sin analytics de terceros" de `decisiones.md`; en la UE hay jurisprudencia (LG München, 2022) que lo considera un incumplimiento del RGPD, y la LGPD de Brasil apunta en la misma dirección.
- Corrección: auto-hospedar las fuentes. Probar `fontOrigin: local` con los `.woff2` de Unbounded/IBM Plex (licencia OFL) en `quartz/static/fonts` o con el plugin `quartz-fonts` (l. 97) en modo local. Así se quitan además dos orígenes de la CSP.

**M3. Sin Content-Security-Policy**
- Dónde: sitio publicado (0 etiquetas `http-equiv`). GitHub Pages no deja definir cabeceras HTTP.
- Escenario: sin CSP, cualquier XSS (por ejemplo un artículo futuro con HTML incrustado o un plugin vulnerable) o un CDN comprometido (M1) puede cargar scripts de cualquier origen y enviar datos fuera.
- Corrección: añadir un `<meta http-equiv="Content-Security-Policy">` en el `<head>` (componente `Head` o un plugin), con un punto de partida como este:
  `default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'`
  Limitaciones: hay un `<script>` inline, por lo que hace falta `'unsafe-inline'` o su hash `sha256-…`; `frame-ancestors` y `report-uri` no funcionan en una meta tag. Si se aplican M1 y M2, la política queda casi en `'self'`. Probar con `npx quartz build --serve` antes de publicar: el SPA, el grafo y la búsqueda usan `fetch` y workers del mismo origen.

**M4. Todo lo que esté en `content/` se publica (publicación implícita)**
- Dónde: `quartz.config.yaml:104-105` (`explicit-publish` desactivado); solo se excluyen `private`, `templates` y `.obsidian` (l. 10-13).
- Escenario: se copia o sincroniza una nota del Obsidian (por ejemplo de una carpeta personal) a `content/` por error, entra en un PR y queda pública en el sitio y en el historial de git, de donde no se borra.
- Corrección: activar `@quartz-community/explicit-publish` (solo se publica lo que tiene `publish: true` en el frontmatter) y añadirlo a la plantilla de `reporter-blog`. Alternativa: un check en `pr-checks.yml` que falle si algún `.md` de `content/` no lleva `publish: true`.

### Bajos

**B1. Las exclusiones de `.claude/*` solo existen en esta copia local**
- Dónde: `.git/info/exclude` (l. 8, 14, 16, 17), que no se versiona. `.gitignore` no las incluye.
- Escenario: en otro clon o con `git add -A` desde otra máquina, `.claude/settings.json`, `hooks/` y `rules/` (con symlinks a rutas locales y a otros repositorios) entrarían en un commit y quedarían expuestos los nombres de usuario, las rutas y la estructura de los repos privados.
- Corrección: añadir a `.gitignore` las líneas `.claude/settings*.json`, `.claude/hooks/`, `.claude/rules/`, `.claude/skills/` y `.claude/CLAUDE.md` (las rutas por sí solas no revelan nada). Opcional: `gitleaks` en `pr-checks.yml` o como pre-commit.

**B2. Actions: se permiten todas y no se exige SHA a nivel de repo**
- Dónde: `gh api .../actions/permissions` → `allowed_actions: all`, `sha_pinning_required: false`.
- Escenario: un PR futuro (de Juan o de un agente) añade `uses: alguien/accion@v1` con tag mutable y nada lo bloquea.
- Corrección: Settings → Actions → "Allow GitHub-owned/verified actions" (o una lista explícita) y activar "Require actions to be pinned to a full-length commit SHA".

**B3. Checks requeridos sin fijar la fuente**
- Dónde: ruleset `proteger-main`, regla `required_status_checks` (`convenciones`, `build` sin `integration_id`).
- Escenario: cualquier GitHub App o workflow con permiso `checks: write` podría publicar un check llamado `build` en verde. El riesgo es bajo porque no hay Apps de terceros instaladas.
- Corrección: fijar la fuente "GitHub Actions" en cada check del ruleset.

**B4. Funciones de seguridad opcionales desactivadas**
- Dónde: `security_and_analysis`: `secret_scanning_non_provider_patterns` y `secret_scanning_validity_checks` desactivados; `private-vulnerability-reporting` desactivado; no hay `SECURITY.md`.
- Corrección: activarlos (son gratuitos en repos públicos) y añadir un `SECURITY.md` corto que indique cómo reportar por el canal privado de GitHub, sin publicar ningún correo.

**B5. CLAUDE.md revela la estructura del Obsidian personal**
- Dónde: `CLAUDE.md:7` (mencionaba una carpeta personal del Obsidian; corregido).
- Escenario: solo es información de contexto (nombre de la carpeta de gestión personal), pero se puede generalizar sin perder el sentido.
- Corrección: cambiarlo por "notas personales o privadas".

**B6. giscus con placeholders**
- Dónde: `quartz.config.yaml:195-211` (desactivado, `TODO:`). Sin riesgo hoy. Si se activa, sumará `giscus.app` (script e iframe) a la CSP y a la política de privacidad.

**B7. 2FA de la cuenta no verificable desde la API**
- `gh api user` no devuelve `two_factor_authentication` con el token actual. Confirmarlo a mano en github.com/settings/security, junto con passkey y códigos de recuperación guardados (KeePassXC).

## Orden sugerido
1. Fusionar el PR #1 (ya verificado).
2. M4 (explicit-publish) y B1 (`.gitignore`): cambios pequeños que evitan fugas permanentes.
3. M2 + M1 (fuentes locales; quitar `latex` o servir KaTeX/Mermaid localmente), luego M3 (CSP).
4. B2–B4 en la configuración de GitHub (los hace Juan).
