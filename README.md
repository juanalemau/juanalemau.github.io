# alemau — blog de tecnología

Blog personal y público sobre **tecnología**: IA y desarrollo, software, hardware y cómo está el mercado hoy, con ejemplos claros para decidir mejor en el día a día. Escrito en **español, português e English**.

🌐 https://juanalemau.github.io

## Créditos

Este sitio está construido con **[Quartz](https://github.com/jackyzha0/quartz)** v5.1.0, creado por [Jacky Zhao](https://github.com/jackyzha0) y su comunidad, bajo licencia **MIT** (ver [`LICENSE.txt`](LICENSE.txt)). Todo el mérito del generador es de ellos: el historial de git original se mantiene en este repositorio y el pie de página de cada página enlaza al proyecto.

Si te gusta Quartz, apoya a sus autores: https://github.com/sponsors/jackyzha0

## Licencias

- **Código** (Quartz y sus modificaciones): MIT — [`LICENSE.txt`](LICENSE.txt).
- **Contenido** (`content/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es) — puedes compartir y adaptar citando la fuente.

## Cómo funciona

| Carpeta | Qué hay |
|---|---|
| `content/es`, `content/pt`, `content/en` | Artículos en Markdown (compatible con Obsidian), uno por idioma |
| `quartz.config.yaml` | Configuración: título, colores de la marca, plugins |
| `docs/` | Documentación original de Quartz + decisiones del proyecto (`docs/proyecto/`) |
| `.github/workflows/deploy.yml` | Publica en GitHub Pages en cada push a `main` |

```bash
npm ci                      # instalar
npx quartz build --serve    # vista previa en http://localhost:8080
```

Actualizar Quartz: `npx quartz upgrade` (remoto `upstream` = jackyzha0/quartz). Usar solo versiones con ≥ 2 semanas.
