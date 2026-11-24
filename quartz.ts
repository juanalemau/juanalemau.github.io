import { h } from "preact"
import { loadQuartzConfig, loadQuartzLayout } from "./quartz/plugins/loader/config-loader"

const config = await loadQuartzConfig()

// alemau: Content-Security-Policy como <meta> (GitHub Pages no permite cabeceras HTTP).
// 'unsafe-inline' es necesario por los scripts inline de Quartz; cdnjs solo se usa
// si un artículo tiene diagramas Mermaid. Ver docs/proyecto/seguridad.md (M3).
const csp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self'",
  "img-src 'self' data: https:",
  "connect-src 'self'",
  "worker-src 'self' blob:",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ")

config.plugins.transformers.push({
  name: "AlemauSecurityHead",
  externalResources: () => ({
    additionalHead: [
      h("meta", { "http-equiv": "Content-Security-Policy", content: csp }),
      h("meta", { name: "referrer", content: "strict-origin-when-cross-origin" }),
    ],
  }),
})

export default config
export const layout = await loadQuartzLayout()
