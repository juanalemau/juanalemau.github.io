import { Fragment, h } from "preact"
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

// alemau: <link rel="alternate" hreflang> entre las versiones es/pt/en de la misma página y RSS por idioma.
const IDIOMAS = ["es", "pt", "en"]
const SITIO = "https://juanalemau.github.io"
const alternos = (pagina: { slug?: string }) => {
  const slug = pagina.slug ?? ""
  const partes = slug.split("/")
  const lang = IDIOMAS.includes(partes[0]) ? partes[0] : null
  const resto = lang ? partes.slice(1).join("/") : ""
  const ruta = (l: string) => `${SITIO}/${l}/${resto.replace(/(^|\/)index$/, "")}`
  return h(
    Fragment,
    null,
    ...(lang || slug === "index"
      ? [
          ...IDIOMAS.map((l) => h("link", { rel: "alternate", hreflang: l, href: ruta(l) })),
          h("link", { rel: "alternate", hreflang: "x-default", href: `${SITIO}/` }),
        ]
      : []),
    lang ? h("link", { rel: "alternate", type: "application/rss+xml", title: `alemau (${lang})`, href: `${SITIO}/${lang}/diario/feed.xml` }) : null,
  )
}

config.plugins.transformers.push({
  name: "AlemauSecurityHead",
  externalResources: () => ({
    additionalHead: [
      h("meta", { "http-equiv": "Content-Security-Policy", content: csp }),
      h("meta", { name: "referrer", content: "strict-origin-when-cross-origin" }),
      // atajos de teclado del resumen diario (archivo propio, servido desde 'self')
      h("script", { src: "/static/js/atajos.js", defer: true }),
      alternos,
    ],
  }),
})

export default config
export const layout = await loadQuartzLayout()
