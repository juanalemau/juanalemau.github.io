// alemau — atajos de teclado del resumen diario (j/k siguiente/anterior, o abrir, c discusión,
// [ día anterior, l cambiar idioma). Solo actúa si la página tiene .alemau-log; ignora campos de texto.
(() => {
  if (window.__alemauAtajos) return
  window.__alemauAtajos = true
  const reducido = () => matchMedia("(prefers-reduced-motion: reduce)").matches
  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return
    const t = e.target
    if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return
    const log = document.querySelector(".alemau-log")
    if (!log) return
    const cs = [...log.querySelectorAll(".c")]
    if (!cs.length) return
    let i = cs.findIndex((c) => c.classList.contains("activo"))
    const ir = (n) => {
      cs.forEach((c) => c.classList.remove("activo"))
      const c = cs[n]
      c.classList.add("activo")
      c.scrollIntoView({ block: "center", behavior: reducido() ? "auto" : "smooth" })
      c.querySelector(".hash")?.focus({ preventScroll: true })
      const pos = log.querySelector(".statusline .pos")
      if (pos) pos.textContent = `${n + 1}/${cs.length}`
    }
    const abrir = (sel) => {
      const a = i >= 0 ? cs[i].querySelector(sel) : null
      if (a) location.href = a.href
    }
    switch (e.key) {
      case "j": ir(Math.min(i + 1, cs.length - 1)); break
      case "k": ir(Math.max(i - 1, 0)); break
      case "o": abrir("a.open"); break
      case "c": abrir("a.disc"); break
      case "[": log.querySelector(".prev")?.click(); break
      case "l": {
        const ls = [...log.querySelectorAll(".langs a")]
        const k = ls.findIndex((a) => a.hasAttribute("aria-current"))
        ls[(k + 1) % ls.length]?.click()
        break
      }
      default: return
    }
    e.preventDefault()
  })
})()
