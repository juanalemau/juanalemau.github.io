#!/usr/bin/env python3
"""Genera las páginas fijas del sitio con el diseño changelog (dirección A):
portada, páginas de idioma, "Sobre" y el índice del diario, en es/pt/en.

Uso: python3 scripts/paginas.py   (reescribe content/index.md y content/{es,pt,en}/{index,sobre,diario/index}.md)
Los textos de "Sobre" viven aquí (SOBRE); el resto del sitio, en el resumen diario.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from resumen_diario import ACTUAL, ICONO_LUNA, ICONO_SOL, LANGS, MONOGRAMA, sin_popover  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent / "content"
NOMBRE = {"es": "Español", "pt": "Português", "en": "English"}
T = {
    "es": {"lema": "Lo más útil del día para devs de todo el mundo, en 2 minutos.",
           "diario": "Resumen diario", "diario_d": "10 ítems por día de GitHub, Hacker News, dev.to, Medium y blogs, con resumen, por qué importa y enlace al original.",
           "sobre": "Sobre este blog", "sobre_d": "Cómo se arma el resumen: fuentes, IA, verificación en 4 capas y transparencia.",
           "hoy": "ver resúmenes", "leer": "leer", "tema": "Cambiar entre modo claro y oscuro", "idioma": "Idioma",
           "diario_txt": "Cada mañana (06:00, hora de Brasil) un nuevo resumen. El más reciente arriba.",
           "pie": "// alemau — resumen diario para devs. Sin analytics ni rastreo."},
    "pt": {"lema": "O mais útil do dia para devs do mundo todo, em 2 minutos.",
           "diario": "Resumo diário", "diario_d": "10 itens por dia do GitHub, Hacker News, dev.to, Medium e blogs, com resumo, por que importa e link para o original.",
           "sobre": "Sobre este blog", "sobre_d": "Como o resumo é montado: fontes, IA, verificação em 4 camadas e transparência.",
           "hoy": "ver resumos", "leer": "ler", "tema": "Alternar entre modo claro e escuro", "idioma": "Idioma",
           "diario_txt": "Toda manhã (06:00, horário de Brasília) um novo resumo. O mais recente no topo.",
           "pie": "// alemau — resumo diário para devs. Sem analytics nem rastreamento."},
    "en": {"lema": "The most useful things of the day for developers worldwide, in 2 minutes.",
           "diario": "Daily digest", "diario_d": "10 items a day from GitHub, Hacker News, dev.to, Medium and blogs, with a summary, why it matters and a link to the original.",
           "sobre": "About this blog", "sobre_d": "How the digest is built: sources, AI, four-layer verification and transparency.",
           "hoy": "see digests", "leer": "read", "tema": "Switch between light and dark mode", "idioma": "Language",
           "diario_txt": "A new digest every morning (06:00 Brasília time). The latest on top.",
           "pie": "// alemau — a daily digest for developers. No analytics or tracking."},
}
SOBRE = {
    "es": """**alemau** es un resumen diario y gratuito para desarrolladores de todo el mundo, en español, portugués e inglés.

## Cómo se hace

1. **Fuentes públicas:** cada mañana se recogen repos nuevos en alta en GitHub, Hacker News, dev.to, Medium y blogs de devs y empresas, solo por APIs y RSS oficiales.
2. **IA que resume:** Gemini elige los ítems más útiles y escribe un resumen y "por qué importa" usando el texto real de cada fuente.
3. **Verificación en 4 capas:** los enlaces salen de los datos (nunca de la IA); toda cifra, fecha o versión tiene que aparecer en la fuente; una segunda IA revisa cada ítem contra el original; y si no quedan suficientes ítems confiables, ese día no se publica.
4. **Seguridad solo como noticia:** nunca se enlazan exploits, herramientas de ataque, descargas sospechosas ni acortadores.
5. **Transparencia:** cada ítem enlaza al original (el contenido es de sus autores) y tiene un enlace para reportar errores.

## Quién está detrás

Lo mantiene Juan Alemau, desarrollador. El sitio usa [Quartz](https://github.com/jackyzha0/quartz) (MIT) y se publica en GitHub Pages, sin analytics ni rastreo. El texto de los resúmenes está bajo CC BY 4.0.""",
    "pt": """**alemau** é um resumo diário e gratuito para desenvolvedores do mundo todo, em espanhol, português e inglês.

## Como é feito

1. **Fontes públicas:** toda manhã são coletados repositórios novos em alta no GitHub, Hacker News, dev.to, Medium e blogs de devs e empresas, apenas por APIs e RSS oficiais.
2. **IA que resume:** o Gemini escolhe os itens mais úteis e escreve um resumo e "por que importa" usando o texto real de cada fonte.
3. **Verificação em 4 camadas:** os links vêm dos dados (nunca da IA); todo número, data ou versão precisa aparecer na fonte; uma segunda IA revisa cada item contra o original; e, se não sobrarem itens confiáveis suficientes, naquele dia não se publica.
4. **Segurança só como notícia:** nunca são publicados exploits, ferramentas de ataque, downloads suspeitos nem encurtadores.
5. **Transparência:** cada item leva ao original (o conteúdo é dos autores) e tem um link para reportar erros.

## Quem está por trás

Mantido por Juan Alemau, desenvolvedor. O site usa o [Quartz](https://github.com/jackyzha0/quartz) (MIT) e é publicado no GitHub Pages, sem analytics nem rastreamento. O texto dos resumos está sob CC BY 4.0.""",
    "en": """**alemau** is a free daily digest for developers worldwide, in Spanish, Portuguese and English.

## How it's made

1. **Public sources:** every morning it collects new trending GitHub repos, Hacker News, dev.to, Medium and blogs from developers and companies, only through official APIs and RSS.
2. **AI that summarizes:** Gemini picks the most useful items and writes a summary and "why it matters" using the real text of each source.
3. **Four-layer verification:** links come from the data (never from the AI); every number, date or version must appear in the source; a second AI checks each item against the original; and if not enough reliable items remain, nothing is published that day.
4. **Security as news only:** exploits, attack tools, suspicious downloads and URL shorteners are never linked.
5. **Transparency:** every item links to the original (the content belongs to its authors) and has a link to report mistakes.

## Who's behind it

Maintained by Juan Alemau, a developer. The site uses [Quartz](https://github.com/jackyzha0/quartz) (MIT) and is published on GitHub Pages, with no analytics or tracking. The digest text is licensed CC BY 4.0.""",
}
PIE_LINKS = ('<a href="https://github.com/jackyzha0/quartz">Quartz (MIT)</a> · '
             '<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> · '
             '<a href="https://github.com/juanalemau/juanalemau.github.io">GitHub</a>')


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def cromo(*, inicio: str, prompt: str, langs: str, tema: str, idioma: str, cuerpo: str, archivo: str, lang: str,
          pie: str) -> str:
    """Marco común: barra superior (marca, prompt, idiomas, tema) + cuerpo + pie + barra de estado.
    `cuerpo` puede contener Markdown entre líneas en blanco (se mantiene fuera de los bloques HTML)."""
    top = (f'<div class="alemau-log"><header class="top"><div class="top-in">'
           f'<a class="brand" href="{inicio}" aria-label="alemau">{MONOGRAMA}<b>alemau</b></a>'
           f'<div class="prompt" aria-hidden="true">{prompt}<span class="cur"></span></div>'
           f'<nav class="langs" aria-label="{esc(idioma)}">{langs}</nav>'
           f'<button class="tema" type="button" aria-label="{esc(tema)}" title="{esc(tema)}">{ICONO_SOL}{ICONO_LUNA}</button>'
           f'</div></header><div class="cl-main solo">')
    fin = (f'<footer class="cl-foot">{esc(pie)}<br>{PIE_LINKS}</footer></div>'
           f'<div class="statusline" aria-hidden="true"><span class="mode">LOG</span><span class="fill">{esc(archivo)}</span>'
           f'<span class="r hide-sm">{lang} · utf-8</span></div></div>')
    return sin_popover(top) + "\n\n" + cuerpo.strip() + "\n\n" + sin_popover(fin) + "\n"


def frontmatter(lang: str, title: str, desc: str, otros: dict[str, str]) -> str:
    tr = "".join(f'  {o}: "[[{v}]]"\n' for o, v in otros.items())
    return (f'---\nlang: {lang}\npublish: true\ntitle: "{title}"\ndescription: "{desc}"\n'
            + (f"translations:\n{tr}" if tr else "") + "---\n\n")


def langs_html(actual: str | None, ruta: str) -> str:
    return "".join(f'<a href="{ruta.format(o=o)}" hreflang="{o}" lang="{o}"{ACTUAL if o == actual else ""}>{o}</a>' for o in LANGS)


def entrada(clave: str, scope: str, titulo: str, href: str, texto: str, meta: str, primero: bool = False) -> str:
    return (f'<li class="c{" top1" if primero else ""}"><span class="hash">{esc(clave)}</span><span class="node" aria-hidden="true"></span>'
            f'<article class="body"><h2><span class="scope">{esc(scope)}</span><a href="{href}">{esc(titulo)}</a></h2>'
            f'<p>{esc(texto)}</p><div class="meta">{meta}</div></article></li>')


def portada() -> str:
    t = T["es"]
    items = "".join(
        entrada(f"{o}/", f"cd {o}/", NOMBRE[o], f"/{o}/", T[o]["lema"],
                f'<span class="src">{o}</span><a href="/{o}/diario/">{esc(T[o]["hoy"])}</a><a href="/{o}/sobre">{esc(T[o]["sobre"].lower())}</a>',
                primero=(o == "es")) for o in LANGS)
    cuerpo = ('<section class="release"><span class="tag">README</span><h1>alemau</h1>'
              f'<p>{esc(t["lema"])} · {esc(T["pt"]["lema"])} · {esc(T["en"]["lema"])}</p>'
              '<div class="stat"><b>es · pt · en</b> · 06:00 BRT · <span class="add">GitHub</span> · <span class="add">Hacker News</span>'
              ' · <span class="add">dev.to</span> · <span class="add">Medium</span> · <span class="add">blogs</span></div></section>'
              f'<ol class="log">{items}</ol>')
    return (frontmatter("es", "alemau", "Resumen diario para devs de todo el mundo — GitHub, Hacker News, dev.to, Medium y blogs. Em português e in English.", {})
            + cromo(inicio="/", prompt='<span class="p">~</span> $ ls', langs=langs_html(None, "/{o}/"),
                    tema=t["tema"], idioma=t["idioma"], cuerpo=sin_popover(cuerpo), archivo="README.md", lang="es", pie=t["pie"]))


def inicio_idioma(lang: str) -> str:
    t = T[lang]
    items = (entrada("diario/", "git log", t["diario"], f"/{lang}/diario/", t["diario_d"],
                     f'<span class="src">diario/</span><a href="/{lang}/diario/">{esc(t["hoy"])}</a>', primero=True)
             + entrada("sobre.md", "cat", t["sobre"], f"/{lang}/sobre", t["sobre_d"],
                       f'<span class="src">sobre.md</span><a href="/{lang}/sobre">{esc(t["leer"])}</a>'))
    cuerpo = (f'<section class="release"><span class="tag">~/{lang}</span><h1>{esc(NOMBRE[lang])}</h1>'
              f'<p>{esc(t["lema"])}</p></section><ol class="log">{items}</ol>')
    otros = {o: f"{o}/index" for o in LANGS if o != lang}
    return (frontmatter(lang, NOMBRE[lang], t["lema"], otros)
            + cromo(inicio="/", prompt=f'<span class="p">~/{lang}</span> $ ls', langs=langs_html(lang, "/{o}/"),
                    tema=t["tema"], idioma=t["idioma"], cuerpo=sin_popover(cuerpo), archivo=f"{lang}/", lang=lang, pie=t["pie"]))


def sobre(lang: str) -> str:
    t = T[lang]
    cuerpo = (f'<section class="release"><span class="tag">sobre.md</span><h1>{esc(t["sobre"])}</h1>'
              f'<p>{esc(t["sobre_d"])}</p></section>\n\n<div class="doc">\n\n{SOBRE[lang]}\n\n</div>')
    otros = {o: f"{o}/sobre" for o in LANGS if o != lang}
    return (frontmatter(lang, t["sobre"], t["sobre_d"], otros)
            + cromo(inicio="/", prompt=f'<span class="p">~/{lang}</span> $ cat sobre.md', langs=langs_html(lang, "/{o}/sobre"),
                    tema=t["tema"], idioma=t["idioma"], cuerpo=cuerpo, archivo=f"{lang}/sobre.md", lang=lang, pie=t["pie"]))


def indice_diario(lang: str, dias: list[tuple[str, str]] | None = None) -> str:
    """Índice del diario. `dias` = [(AAAA-MM-DD, frase del día)], el más reciente primero (lo pasa el
    generador en cada publicación; sin días queda solo la cabecera)."""
    t = T[lang]
    lista = "".join(
        entrada(d[5:], "release", f'{t["diario"]} — {d}', f"/{lang}/diario/{d}", desc,
                f'<span class="src">v{d.replace("-", ".")}</span><a href="/{lang}/diario/{d}">{esc(t["leer"])}</a>', primero=(i == 0))
        for i, (d, desc) in enumerate(dias or []))
    cuerpo = (f'<section class="release"><span class="tag">diario/</span><h1>{esc(t["diario"])}</h1>'
              f'<p>{esc(t["diario_txt"])}</p><div class="stat"><b>{len(dias or [])} releases</b> · <a href="/{lang}/diario/feed.xml">RSS</a></div></section>'
              + (f'<ol class="log">{lista}</ol>' if lista else ""))
    otros = {o: f"{o}/diario/index" for o in LANGS if o != lang}
    return (frontmatter(lang, t["diario"], t["diario_d"], otros)
            + cromo(inicio="/", prompt=f'<span class="p">~/{lang}/diario</span> $ git log --oneline', langs=langs_html(lang, "/{o}/diario/"),
                    tema=t["tema"], idioma=t["idioma"], cuerpo=sin_popover(cuerpo), archivo=f"{lang}/diario/", lang=lang, pie=t["pie"]))


def main() -> None:
    (RAIZ / "index.md").write_text(portada(), encoding="utf-8")
    for lang in LANGS:
        (RAIZ / lang / "diario").mkdir(parents=True, exist_ok=True)
        (RAIZ / lang / "index.md").write_text(inicio_idioma(lang), encoding="utf-8")
        (RAIZ / lang / "sobre.md").write_text(sobre(lang), encoding="utf-8")
        (RAIZ / lang / "diario" / "index.md").write_text(indice_diario(lang), encoding="utf-8")
    print("páginas regeneradas")


if __name__ == "__main__":
    main()
