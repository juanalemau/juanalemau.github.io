# alemau — blog (Quartz v5)

Blog público y trilingüe (es principal, pt, en) de Juan Alemau sobre tecnología: IA y desarrollo, software, hardware y mercado tech, con ejemplos claros para decisiones del día a día. Publicado en https://juanalemau.github.io vía GitHub Actions (`.github/workflows/deploy.yml`).

## Reglas
- **Respeto a la autoría:** Quartz es de jackyzha0 y comunidad (MIT). No borrar `LICENSE.txt`, el historial de upstream ni el crédito del pie de página. Cambios en `quartz/` deben ser mínimos y documentados; preferir configuración (`quartz.config.yaml`) o plugins.
- **Repositorio público:** nada de datos personales, rutas privadas, correos, tokens ni notas privadas. Revisar antes de cada commit.
- **Contenido:** cada artículo existe en los tres idiomas con el mismo nombre de archivo en `content/{es,pt,en}/<sección>/`, enlazados entre sí (`translations:` en el frontmatter). Fuentes citadas con enlace; fecha en `date:`; nada inventado: si un dato no se pudo verificar, se dice.
- **Actualizaciones:** solo versiones de Quartz/actions con ≥ 2 semanas de publicadas. Actions fijadas por SHA.
- **Git:** todo commit y título de PR sigue [Conventional Commits 1.0.0](https://www.conventionalcommits.org/es/v1.0.0/) (`tipo(alcance): descripción`; tipos feat, fix, docs, chore, refactor, perf, ci, build, style, test, revert; `!` o `BREAKING CHANGE:` para cambios incompatibles). Artículo nuevo = `feat(contenido): …`, corrección de artículo = `fix(contenido): …`, cambio del sitio = `feat(sitio)`/`fix(sitio)`. Lo validan el hook local `commit-msg` y el workflow `pr-checks.yml`.
- Nada de commit directo a `main`: rama `<tipo>/<n°-issue>-<descripcion>` → PR → squash. Las versiones las crea **release-please** (`release.yml`) a partir de los commits: abre un PR de release (cerrarlo y reabrirlo para que corran los checks); al hacer merge se crea el tag, el GitHub Release y `docs/proyecto/CHANGELOG.md`.
- Tablero: GitHub Project "Blog alemau" (https://github.com/users/juanalemau/projects/6), Status: A fazer / Dúvida pendente / Em andamento / Feito.
- Disco NTFS: `core.fileMode false`.
- Commits con el email noreply de GitHub; nunca el email personal.

## Agentes del proyecto (`.claude/agents/`)
`product-owner` (prioridades/alcance) · `ux-designer` (navegación, lectura, marca) · `especialista-quartz` (mejoras técnicas del generador) · `seguranca-ciber` (seguridad y privacidad) · `arquitecto-fullstack` (arquitectura y decisiones técnicas) · `documentador` (docs y revisión de textos) · `especialista-ia` (contenido de IA) · `reporter-blog` (redacción de artículos).
Decisiones registradas en `docs/proyecto/decisiones.md`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
