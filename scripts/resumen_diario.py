#!/usr/bin/env python3
"""Resumen diario para devs: recolecta fuentes públicas, Gemini elige y resume en es/pt/en.

Solo usa APIs oficiales y RSS (sin scraping de sitios que lo prohíben). Los enlaces salen
de los datos recolectados, nunca del modelo. Solo biblioteca estándar de Python.

Uso:
  python3 scripts/resumen_diario.py --solo-recolectar            # lista candidatos (sin IA)
  GEMINI_API_KEY=... python3 scripts/resumen_diario.py --salida content --historial content
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

UA = "alemau-resumen-diario/1.0 (+https://juanalemau.github.io)"
AHORA = dt.datetime.now(dt.timezone.utc)
FUENTES = json.loads((Path(__file__).with_name("fuentes.json")).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- utilidades
def pedir(url: str, *, headers: dict | None = None, data: bytes | None = None, timeout: int = 20, limite: int = 2_000_000) -> bytes:
    h = {"User-Agent": UA, **(headers or {})}
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=timeout) as r:
        return r.read(limite)


def json_de(url: str, **kw):
    return json.loads(pedir(url, **kw))


def texto_plano(s: str | None, maximo: int = 600) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"\s+", " ", html.unescape(s)).strip()
    return s[:maximo]


def fecha(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def reciente(d: dt.datetime | None, horas: int) -> bool:
    return d is None or (AHORA - d) <= dt.timedelta(hours=horas)


def avisar(msg: str) -> None:
    print(f"aviso: {msg}", file=sys.stderr)


# ---------------------------------------------------------------- fuentes
def github(token: str | None) -> list[dict]:
    """Repos nuevos con más estrellas en los últimos 7 días (aproximación oficial a 'trending')."""
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    desde = (AHORA - dt.timedelta(days=7)).date().isoformat()
    q = urllib.parse.quote(f"created:>{desde} stars:>50")
    datos = json_de(f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=15", headers=h)
    out = []
    for r in datos.get("items", []):
        readme = ""
        try:
            readme = pedir(f"https://api.github.com/repos/{r['full_name']}/readme",
                           headers={**h, "Accept": "application/vnd.github.raw"}, limite=20_000).decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError):
            pass
        out.append({
            "fuente": "GitHub", "titulo": r["full_name"], "url": r["html_url"],
            "metricas": f"{r['stargazers_count']} estrellas, {r.get('language') or 's/lenguaje'}",
            "puntaje": r["stargazers_count"],
            "contexto": texto_plano(f"{r.get('description') or ''}. Temas: {', '.join(r.get('topics') or [])}. README: {readme}", 1200),
        })
    return out


def contexto_pagina(url: str) -> str:
    try:
        crudo = pedir(url, timeout=10, limite=400_000).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 - cualquier fallo de red deja el ítem solo con título
        return ""
    metas = re.findall(r'<meta[^>]+(?:name|property)=["\'](?:og:description|description|twitter:description)["\'][^>]+content=["\']([^"\']+)', crudo, re.I)
    parrafos = re.findall(r"<p[^>]*>(.*?)</p>", crudo, re.I | re.S)[:4]
    return texto_plano(" ".join(metas[:1] + parrafos), 900)


def hacker_news() -> list[dict]:
    ids = json_de("https://hacker-news.firebaseio.com/v0/topstories.json")[:30]
    out = []
    for i in ids:
        s = json_de(f"https://hacker-news.firebaseio.com/v0/item/{i}.json")
        if not s or s.get("type") != "story" or s.get("dead"):
            continue
        url = s.get("url") or f"https://news.ycombinator.com/item?id={i}"
        out.append({
            "fuente": "Hacker News", "titulo": s.get("title", ""), "url": url,
            "discusion": f"https://news.ycombinator.com/item?id={i}",
            "metricas": f"{s.get('score', 0)} puntos, {s.get('descendants', 0)} comentarios",
            "puntaje": s.get("score", 0),
            "contexto": texto_plano(s.get("text"), 900) or contexto_pagina(url) if "url" in s else texto_plano(s.get("text"), 900),
        })
    return out


def dev_to() -> list[dict]:
    out = []
    for a in json_de("https://dev.to/api/articles?top=1&per_page=15"):
        out.append({
            "fuente": "dev.to", "titulo": a["title"], "url": a["url"],
            "metricas": f"{a.get('positive_reactions_count', 0)} reacciones, {a.get('comments_count', 0)} comentarios",
            "puntaje": a.get("positive_reactions_count", 0),
            "contexto": texto_plano(f"{a.get('description', '')} Tags: {a.get('tag_list')}. Autor: {a.get('user', {}).get('name', '')}", 700),
        })
    return out


def rss(nombre: str, url: str, horas: int, maximo: int) -> list[dict]:
    raiz = ET.fromstring(pedir(url))
    atom = "{http://www.w3.org/2005/Atom}"
    items = raiz.findall(".//item") or raiz.findall(f".//{atom}entry")
    out = []
    for it in items[: maximo * 3]:
        g = lambda tag: (it.findtext(tag) or it.findtext(f"{atom}{tag}") or "")  # noqa: E731
        link = g("link")
        if not link:
            el = it.find(f"{atom}link")
            link = el.get("href", "") if el is not None else ""
        d = fecha(g("pubDate") or g("published") or g("updated"))
        if not link or not reciente(d, horas):
            continue
        cuerpo = g("description") or g("summary") or g("{http://purl.org/rss/1.0/modules/content/}encoded") or g("content")
        out.append({
            "fuente": nombre, "titulo": texto_plano(g("title"), 200), "url": link.split("?source=")[0],
            "metricas": d.strftime("%Y-%m-%d") if d else "", "puntaje": 0,
            "contexto": texto_plano(cuerpo, 700),
        })
        if len(out) >= maximo:
            break
    return out


def recolectar() -> list[dict]:
    token = os.environ.get("GITHUB_TOKEN")
    tareas = [("GitHub", lambda: github(token)), ("Hacker News", hacker_news), ("dev.to", dev_to)]
    for f in FUENTES["rss"]:
        tareas.append((f["nombre"], lambda f=f: rss(f["nombre"], f["url"], f.get("horas", 48), f.get("maximo", 5))))
    todos, vistos = [], set()
    for nombre, fn in tareas:
        try:
            for item in fn():
                clave = item["url"].rstrip("/").lower()
                if clave not in vistos:
                    vistos.add(clave)
                    todos.append(item)
        except Exception as e:  # noqa: BLE001 - una fuente caída no debe tumbar el resumen
            avisar(f"fuente {nombre} falló: {e}")
    return todos


def urls_publicadas(historial: Path | None) -> set[str]:
    if not historial or not historial.exists():
        return set()
    urls = set()
    for md in historial.glob("*/diario/*.md"):
        urls.update(u.rstrip("/").lower() for u in re.findall(r"\]\((https?://[^)\s]+)\)", md.read_text(encoding="utf-8")))
    return urls


# ---------------------------------------------------------------- Gemini
API = "https://generativelanguage.googleapis.com/v1beta"


def modelos_disponibles(clave: str) -> list[str]:
    """Modelos gemini-*-flash (y -flash-lite como respaldo) de esta clave, del mejor al peor."""
    if os.environ.get("GEMINI_MODEL"):
        return [os.environ["GEMINI_MODEL"]]
    modelos = json_de(f"{API}/models?pageSize=200", headers={"x-goog-api-key": clave}).get("models", [])
    candidatos = []
    for m in modelos:
        nombre = m["name"].split("/")[-1]
        if "generateContent" in m.get("supportedGenerationMethods", []) and re.fullmatch(r"gemini-[\d.]+-flash(-lite)?", nombre):
            version = tuple(int(x) for x in re.findall(r"\d+", nombre))
            candidatos.append((0 if nombre.endswith("lite") else 1, version, nombre))
    if not candidatos:
        raise SystemExit("No hay modelo gemini-*-flash disponible para esta clave")
    return [n for *_, n in sorted(candidatos, reverse=True)]


INSTRUCCIONES = """Eres el editor de "alemau", un resumen diario para desarrolladores de todo el mundo
(cualquier especialidad: web, móvil, backend, datos, IA, DevOps, seguridad, herramientas).

Recibes candidatos de fuentes públicas, cada uno con un id y su CONTEXTO real.
1. Elige los {n} más útiles para un dev hoy. Variedad de fuentes y temas; prioriza lanzamientos,
   herramientas, repos, técnicas y noticias de la industria tech. DESCARTA lo que no sea de
   tecnología/desarrollo (ciencia general, política, deportes) y el autobombo sin contenido.
   DESCARTA repos sospechosos (cracks, "emuladores" de consolas o juegos no lanzados, bots de
   trampas, "ultimate/free premium" tools, descargas de binarios sin código): suelen ser malware.
2. Para cada elegido escribe en español, portugués de Brasil e inglés:
   - "titulo": título claro (traducido/adaptado, sin clickbait).
   - "resumen": 1-2 frases sobre QUÉ es, basadas SOLO en el contexto dado.
   - "importa": 1 frase concreta sobre para quién o para qué sirve. Prohibido el relleno genérico
     ("es importante para los desarrolladores porque...").
3. Reglas de veracidad: no inventes fechas, cifras, nombres, versiones ni historia. Si el contexto
   es pobre, describe solo lo que el título dice y sé breve. No uses conocimiento externo.
4. "intro": 1 frase por idioma con el panorama del día.

Responde SOLO JSON:
{{"intro":{{"es":"","pt":"","en":""}},
  "items":[{{"id":0,"categoria":"ia|web|movil|backend|datos|devops|seguridad|herramientas|industria|otros",
            "es":{{"titulo":"","resumen":"","importa":""}},"pt":{{...}},"en":{{...}}}}]}}
"""


def resumir(candidatos: list[dict], clave: str, n: int) -> tuple[dict, str]:
    entrada = [{"id": i, "fuente": c["fuente"], "titulo": c["titulo"], "metricas": c["metricas"], "contexto": c["contexto"]}
               for i, c in enumerate(candidatos)]
    cuerpo = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": INSTRUCCIONES.format(n=n) + "\n\nCANDIDATOS:\n" + json.dumps(entrada, ensure_ascii=False)}]}],
        "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"},
    }).encode()
    modelos = modelos_disponibles(clave)
    print(f"modelos en orden: {modelos[:6]}", file=sys.stderr)
    for modelo in modelos[:6]:
        for intento in range(2):
            try:
                r = json.loads(pedir(f"{API}/models/{modelo}:generateContent", data=cuerpo, timeout=240,
                                     headers={"Content-Type": "application/json", "x-goog-api-key": clave}))
                return json.loads(r["candidates"][0]["content"]["parts"][0]["text"]), modelo
            except urllib.error.HTTPError as e:
                avisar(f"{modelo}: HTTP {e.code} {e.read()[:160]!r}")
                if e.code in (429, 500, 503) and intento == 0:
                    time.sleep(20)
                    continue
                break  # siguiente modelo
            except (KeyError, IndexError, json.JSONDecodeError, TimeoutError) as e:
                avisar(f"{modelo}: respuesta inválida ({e})")
                break
    raise SystemExit("Ningún modelo Gemini respondió")


# ---------------------------------------------------------------- Markdown
TXT = {
    "es": {"titulo": "Resumen diario", "idioma": "Idioma", "importa": "Por qué importa", "fuente": "Fuente",
           "discusion": "discusión", "pie": "Resumen generado automáticamente con IA ({modelo}) a partir de fuentes públicas (APIs y RSS oficiales). Cada ítem enlaza al original; el contenido pertenece a sus autores. Puede contener errores: si ves uno, avísame en GitHub."},
    "pt": {"titulo": "Resumo diário", "idioma": "Idioma", "importa": "Por que importa", "fuente": "Fonte",
           "discusion": "discussão", "pie": "Resumo gerado automaticamente com IA ({modelo}) a partir de fontes públicas (APIs e RSS oficiais). Cada item leva ao original; o conteúdo pertence aos autores. Pode conter erros: se encontrar um, avise no GitHub."},
    "en": {"titulo": "Daily digest", "idioma": "Language", "importa": "Why it matters", "fuente": "Source",
           "discusion": "discussion", "pie": "Digest generated automatically with AI ({modelo}) from public sources (official APIs and RSS). Each item links to the original; the content belongs to its authors. It may contain mistakes: if you spot one, let me know on GitHub."},
}


def limpiar(s: str) -> str:
    """Texto del modelo -> Markdown inofensivo: sin HTML, sin enlaces ni imágenes propios, una línea."""
    s = html.escape(re.sub(r"\s+", " ", s or "").strip(), quote=False)
    return re.sub(r"([\[\]`*_#|])", r"\\\1", s)


def markdown(lang: str, dia: str, datos: dict, candidatos: list[dict], modelo: str) -> str:
    t = TXT[lang]
    otros = [x for x in ("es", "pt", "en") if x != lang]
    linea = " · ".join(x.upper() if x == lang else f"[{x.upper()}](../../{x}/diario/{dia})" for x in ("es", "pt", "en"))
    intro = limpiar(datos.get("intro", {}).get(lang, ""))
    fm = [
        "---", f'title: "{t["titulo"]} — {dia}"', f"date: {dia}", f"lang: {lang}", "publish: true",
        f'description: "{intro.replace(chr(34), chr(39))}"', "tags: [diario]", "translations:",
        *[f'  {o}: "[[{o}/diario/{dia}]]"' for o in otros], "---", "",
        f"**{t['idioma']}:** {linea}", "", intro, "",
    ]
    for n, item in enumerate(datos["items"], 1):
        c = candidatos[item["id"]]
        d = {k: limpiar(v) for k, v in item[lang].items()}
        fuente = f"[{c['fuente']}](<{c['url']}>)"
        if c.get("discusion"):
            fuente += f" · [{t['discusion']}]({c['discusion']})"
        fm += [f"## {n}. {d['titulo']}", "", d["resumen"], "",
               f"**{t['importa']}:** {d['importa']}", "",
               f"{t['fuente']}: {fuente}" + (f" · {c['metricas']}" if c.get("metricas") else ""), ""]
    fm += ["---", "", f"*{t['pie'].format(modelo=modelo)}*", ""]
    return "\n".join(fm)


def validar(datos: dict, total: int) -> None:
    items = datos.get("items")
    if not isinstance(items, list) or not items:
        raise SystemExit("Respuesta sin items")
    for it in items:
        if not isinstance(it.get("id"), int) or not 0 <= it["id"] < total:
            raise SystemExit(f"id inválido en la respuesta: {it.get('id')}")
        for lang in ("es", "pt", "en"):
            if not all(it.get(lang, {}).get(k) for k in ("titulo", "resumen", "importa")):
                raise SystemExit(f"falta texto {lang} en el ítem {it['id']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-recolectar", action="store_true")
    ap.add_argument("--salida", type=Path, default=Path("content"))
    ap.add_argument("--historial", type=Path)
    ap.add_argument("--items", type=int, default=10)
    ap.add_argument("--dia", default=AHORA.date().isoformat())
    a = ap.parse_args()

    candidatos = recolectar()
    ya = urls_publicadas(a.historial)
    candidatos = [c for c in candidatos if c["url"].rstrip("/").lower() not in ya]
    por_fuente: dict[str, int] = {}
    for c in candidatos:
        por_fuente[c["fuente"]] = por_fuente.get(c["fuente"], 0) + 1
    print(f"candidatos: {len(candidatos)} {json.dumps(por_fuente, ensure_ascii=False)}", file=sys.stderr)
    if a.solo_recolectar:
        json.dump(candidatos, sys.stdout, ensure_ascii=False, indent=1)
        return
    clave = os.environ.get("GEMINI_API_KEY")
    if not clave:
        raise SystemExit("Falta GEMINI_API_KEY")
    datos, modelo = resumir(candidatos, clave, a.items)
    validar(datos, len(candidatos))
    for lang in ("es", "pt", "en"):
        destino = a.salida / lang / "diario" / f"{a.dia}.md"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(markdown(lang, a.dia, datos, candidatos, modelo), encoding="utf-8")
        print(f"escrito: {destino}", file=sys.stderr)
    print(f"modelo: {modelo}", file=sys.stderr)


if __name__ == "__main__":
    main()
