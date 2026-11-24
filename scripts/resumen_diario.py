#!/usr/bin/env python3
"""Resumen diario para devs: recolecta fuentes públicas, Gemini elige y resume en es/pt/en.

Calidad en 4 capas:
  1. Reglas en código: enlaces siempre de los datos (nunca del modelo), sin rastreo (utm),
     sin duplicados (tampoco de días anteriores), puntaje mínimo y texto del modelo sin HTML.
  2. Números verificados: toda cifra/fecha/versión del texto debe aparecer en la fuente.
  3. Revisor: otra llamada a Gemini (temperatura 0) marca lo que el contexto no respalda.
  4. Falla cerrada: con menos de MIN_ITEMS ítems válidos no se publica nada (código 3).

Solo APIs oficiales y RSS. Solo biblioteca estándar de Python.

Uso:
  python3 scripts/resumen_diario.py --solo-recolectar
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
REPO = "juanalemau/juanalemau.github.io"
MIN_ITEMS = 6
LANGS = ("es", "pt", "en")


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


def url_limpia(url: str) -> str:
    """Quita parámetros de rastreo (utm_*, source de Medium, fbclid, gclid...)."""
    p = urllib.parse.urlsplit(url.strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
         if not (k.lower().startswith("utm_") or k.lower() in {"source", "fbclid", "gclid", "ref_src", "mc_cid", "mc_eid"})]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(q), ""))


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


# ---------------------------------------------------------------- fuentes (capa 1: puntaje mínimo)
def github(token: str | None) -> list[dict]:
    """Repos nuevos con más estrellas en los últimos 7 días (aproximación oficial a 'trending')."""
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    desde = (AHORA - dt.timedelta(days=7)).date().isoformat()
    q = urllib.parse.quote(f"created:>{desde} stars:>100")
    out = []
    for r in json_de(f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=15", headers=h).get("items", []):
        readme = ""
        try:
            readme = pedir(f"https://api.github.com/repos/{r['full_name']}/readme",
                           headers={**h, "Accept": "application/vnd.github.raw"}, limite=20_000).decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError):
            pass
        out.append({
            "fuente": "GitHub", "titulo": r["full_name"], "url": r["html_url"],
            "metricas": {"estrellas": r["stargazers_count"], "lenguaje": r.get("language")},
            "contexto": texto_plano(f"{r['full_name']}: {r.get('description') or ''}. Temas: {', '.join(r.get('topics') or [])}. README: {readme}", 1500),
        })
    return out


def contexto_pagina(url: str) -> str:
    try:
        crudo = pedir(url, timeout=10, limite=400_000).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 - un fallo de red deja el ítem solo con título
        return ""
    metas = re.findall(r'<meta[^>]+(?:name|property)=["\'](?:og:description|description|twitter:description)["\'][^>]+content=["\']([^"\']+)', crudo, re.I)
    parrafos = re.findall(r"<p[^>]*>(.*?)</p>", crudo, re.I | re.S)[:5]
    return texto_plano(" ".join(metas[:1] + parrafos), 1200)


def hacker_news() -> list[dict]:
    out = []
    for i in json_de("https://hacker-news.firebaseio.com/v0/topstories.json")[:30]:
        s = json_de(f"https://hacker-news.firebaseio.com/v0/item/{i}.json")
        if not s or s.get("type") != "story" or s.get("dead") or s.get("score", 0) < 40:
            continue
        url = s.get("url") or f"https://news.ycombinator.com/item?id={i}"
        ctx = texto_plano(s.get("text"), 1200) or (contexto_pagina(url) if s.get("url") else "")
        out.append({
            "fuente": "Hacker News", "titulo": s.get("title", ""), "url": url,
            "discusion": f"https://news.ycombinator.com/item?id={i}",
            "metricas": {"puntos": s.get("score", 0), "comentarios": s.get("descendants", 0)},
            "contexto": texto_plano(f"{s.get('title', '')}. {ctx}", 1300),
        })
    return out


def dev_to() -> list[dict]:
    out = []
    for a in json_de("https://dev.to/api/articles?top=1&per_page=15"):
        if a.get("positive_reactions_count", 0) < 10:
            continue
        out.append({
            "fuente": "dev.to", "titulo": a["title"], "url": a["url"],
            "metricas": {"reacciones": a.get("positive_reactions_count", 0), "comentarios": a.get("comments_count", 0)},
            "contexto": texto_plano(f"{a['title']}. {a.get('description', '')} Tags: {a.get('tag_list')}. Autor: {a.get('user', {}).get('name', '')}", 800),
        })
    return out


def rss(nombre: str, url: str, horas: int, maximo: int) -> list[dict]:
    raiz = ET.fromstring(pedir(url))
    atom = "{http://www.w3.org/2005/Atom}"
    items = raiz.findall(".//item") or raiz.findall(f".//{atom}entry")
    out = []
    for it in items[: maximo * 3]:
        def g(tag: str) -> str:
            return it.findtext(tag) or it.findtext(f"{atom}{tag}") or ""
        link = g("link")
        if not link:
            el = it.find(f"{atom}link")
            link = el.get("href", "") if el is not None else ""
        d = fecha(g("pubDate") or g("published") or g("updated"))
        if not link or not reciente(d, horas):
            continue
        cuerpo = g("description") or g("summary") or g("{http://purl.org/rss/1.0/modules/content/}encoded") or g("content")
        titulo = texto_plano(g("title"), 200)
        out.append({
            "fuente": nombre, "titulo": titulo, "url": link,
            "metricas": {"fecha": d.date().isoformat()} if d else {},
            "contexto": texto_plano(f"{titulo}. {texto_plano(cuerpo, 1200)}", 1200),
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
                item["url"] = url_limpia(item["url"])
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
        urls.update(u.rstrip("/").lower() for u in re.findall(r"\]\(<?(https?://[^)>\s]+)>?\)", md.read_text(encoding="utf-8")))
    return urls


# ---------------------------------------------------------------- Gemini
API = "https://generativelanguage.googleapis.com/v1beta"


def modelos_disponibles(clave: str) -> list[str]:
    """gemini-*-flash (y -flash-lite como respaldo) disponibles para esta clave, del mejor al peor."""
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


def gemini(prompt: str, clave: str, modelos: list[str], temperatura: float, evitar: str | None = None) -> tuple[object, str]:
    """Llama a Gemini probando modelos en orden (salta los saturados). Devuelve (json, modelo)."""
    cuerpo = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperatura, "responseMimeType": "application/json"},
    }).encode()
    orden = [m for m in modelos if m != evitar] + ([evitar] if evitar in modelos else [])
    for modelo in orden[:6]:
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
                break
            except (KeyError, IndexError, json.JSONDecodeError, TimeoutError, urllib.error.URLError) as e:
                avisar(f"{modelo}: respuesta inválida ({e})")
                break
    raise SystemExit("Ningún modelo Gemini respondió")


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
3. Veracidad: no inventes fechas, cifras, nombres, versiones ni historia. Copia cada número
   EXACTAMENTE como aparece en el contexto (sin redondear, convertir ni reescribir: "3206", no
   "3,2 mil"). No pongas en el texto las métricas (estrellas, puntos): se muestran aparte.
   Si el contexto es pobre, describe solo lo que el título dice y sé breve. No uses conocimiento externo.
4. "intro": 1 frase por idioma con el panorama del día (sin números).

Responde SOLO JSON:
{{"intro":{{"es":"","pt":"","en":""}},
  "items":[{{"id":0,"es":{{"titulo":"","resumen":"","importa":""}},"pt":{{...}},"en":{{...}}}}]}}
"""

REVISOR = """Eres verificador de hechos. Para cada ítem tienes el CONTEXTO original (única fuente de verdad)
y los textos escritos en es/pt/en. Un ítem está "apoyado" solo si TODAS sus afirmaciones (qué es,
quién lo hizo, qué hace, versiones, cifras, fechas) se desprenden del contexto en los tres idiomas.
Una opinión razonable en "importa" sobre para quién sirve está permitida si no contradice el contexto.
Marca "apoyado": false ante cualquier dato inventado, exagerado, contradictorio o traducido con
otro significado. Sé estricto y breve.

Responde SOLO JSON: [{{"id":0,"apoyado":true,"motivo":""}}]

ITEMS:
{items}
"""


# ---------------------------------------------------------------- capa 2: números
NUM = re.compile(r"\d+(?:[.,:]\d+)*")


def normalizar_numeros(s: str) -> set[str]:
    out = set()
    for n in NUM.findall(s):
        out.add(n)
        out.add(n.replace(",", "."))
        out.add(re.sub(r"[.,](?=\d{3}\b)", "", n))  # 1,519 / 1.519 -> 1519
    return out


def numeros_ok(item: dict, c: dict) -> str | None:
    fuente = f"{c['titulo']} {c['contexto']} {json.dumps(c.get('metricas', {}))}"
    permitidos = normalizar_numeros(fuente)
    for lang in LANGS:
        texto = " ".join(item[lang].values())
        for n in NUM.findall(texto):
            variantes = {n, n.replace(",", "."), re.sub(r"[.,](?=\d{3}\b)", "", n)}
            if not variantes & permitidos:
                return f"número '{n}' ({lang}) no aparece en la fuente"
    return None


# ---------------------------------------------------------------- Markdown (capa 1: texto inofensivo)
def limpiar(s: str) -> str:
    """Texto del modelo -> Markdown inofensivo: sin HTML, sin enlaces ni formato propio, una línea."""
    s = html.escape(re.sub(r"\s+", " ", s or "").strip(), quote=False)
    s = re.sub(r"([\[\]`*_#|<>])", r"\\\1", s)
    return re.sub(r"(https?):(//)", r"\1:\\/\\/", s)  # sin autoenlaces


TXT = {
    "es": {"titulo": "Resumen diario", "idioma": "Idioma", "importa": "Por qué importa", "fuente": "Fuente",
           "discusion": "discusión", "reportar": "reportar un error", "estrellas": "estrellas", "puntos": "puntos",
           "comentarios": "comentarios", "reacciones": "reacciones",
           "pie": "Resumen generado automáticamente con IA ({modelo}, revisado por {revisor}) a partir de fuentes públicas (APIs y RSS oficiales). Cada ítem enlaza al original; el contenido pertenece a sus autores. Puede contener errores: usa \"reportar un error\" en el ítem."},
    "pt": {"titulo": "Resumo diário", "idioma": "Idioma", "importa": "Por que importa", "fuente": "Fonte",
           "discusion": "discussão", "reportar": "reportar um erro", "estrellas": "estrelas", "puntos": "pontos",
           "comentarios": "comentários", "reacciones": "reações",
           "pie": "Resumo gerado automaticamente com IA ({modelo}, revisado por {revisor}) a partir de fontes públicas (APIs e RSS oficiais). Cada item leva ao original; o conteúdo pertence aos autores. Pode conter erros: use \"reportar um erro\" no item."},
    "en": {"titulo": "Daily digest", "idioma": "Language", "importa": "Why it matters", "fuente": "Source",
           "discusion": "discussion", "reportar": "report an error", "estrellas": "stars", "puntos": "points",
           "comentarios": "comments", "reacciones": "reactions",
           "pie": "Digest generated automatically with AI ({modelo}, reviewed by {revisor}) from public sources (official APIs and RSS). Each item links to the original; the content belongs to its authors. It may contain mistakes: use \"report an error\" on the item."},
}


def metricas(c: dict, t: dict) -> str:
    m = c.get("metricas", {})
    partes = [f"{m[k]} {t[k]}" for k in ("estrellas", "puntos", "reacciones", "comentarios") if m.get(k) is not None]
    if m.get("lenguaje"):
        partes.append(m["lenguaje"])
    if m.get("fecha"):
        partes.append(m["fecha"])
    return ", ".join(partes)


def markdown(lang: str, dia: str, datos: dict, candidatos: list[dict], modelo: str, revisor: str) -> str:
    t = TXT[lang]
    linea = " · ".join(x.upper() if x == lang else f"[{x.upper()}](../../{x}/diario/{dia})" for x in LANGS)
    intro = limpiar(datos.get("intro", {}).get(lang, ""))
    fm = [
        "---", f'title: "{t["titulo"]} — {dia}"', f"date: {dia}", f"lang: {lang}", "publish: true",
        f'description: "{intro.replace(chr(34), chr(39))}"', "tags: [diario]", "translations:",
        *[f'  {o}: "[[{o}/diario/{dia}]]"' for o in LANGS if o != lang], "---", "",
        f"**{t['idioma']}:** {linea}", "", intro, "",
    ]
    for n, item in enumerate(datos["items"], 1):
        c = candidatos[item["id"]]
        d = {k: limpiar(v) for k, v in item[lang].items()}
        fuente = f"[{c['fuente']}](<{c['url']}>)"
        if c.get("discusion"):
            fuente += f" · [{t['discusion']}](<{c['discusion']}>)"
        reporte = "https://github.com/{}/issues/new?{}".format(REPO, urllib.parse.urlencode({
            "labels": "error-resumen", "title": f"Error en el resumen {dia} ({lang}) #{n}",
            "body": f"Ítem: {c['url']}\n\n¿Qué está mal?\n"}))
        met = metricas(c, t)
        fm += [f"## {n}. {d['titulo']}", "", d["resumen"], "",
               f"**{t['importa']}:** {d['importa']}", "",
               f"{t['fuente']}: {fuente}" + (f" · {met}" if met else "") + f" · [{t['reportar']}](<{reporte}>)", ""]
    fm += ["---", "", f"*{t['pie'].format(modelo=modelo, revisor=revisor)}*", ""]
    return "\n".join(fm)


def estructura_ok(it: dict, total: int) -> bool:
    return (isinstance(it.get("id"), int) and 0 <= it["id"] < total
            and all(isinstance(it.get(l), dict) and all(isinstance(it[l].get(k), str) and it[l][k].strip()
                                                       for k in ("titulo", "resumen", "importa")) for l in LANGS))


# ---------------------------------------------------------------- principal
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-recolectar", action="store_true")
    ap.add_argument("--salida", type=Path, default=Path("content"))
    ap.add_argument("--historial", type=Path)
    ap.add_argument("--items", type=int, default=10)
    ap.add_argument("--dia", default=AHORA.date().isoformat())
    ap.add_argument("--informe", type=Path, help="JSON con lo descartado y por qué")
    a = ap.parse_args()

    candidatos = recolectar()
    ya = urls_publicadas(a.historial)
    candidatos = [c for c in candidatos if c["url"].rstrip("/").lower() not in ya]
    conteo: dict[str, int] = {}
    for c in candidatos:
        conteo[c["fuente"]] = conteo.get(c["fuente"], 0) + 1
    print(f"candidatos: {len(candidatos)} {json.dumps(conteo, ensure_ascii=False)}", file=sys.stderr)
    if a.solo_recolectar:
        json.dump(candidatos, sys.stdout, ensure_ascii=False, indent=1)
        return
    clave = os.environ.get("GEMINI_API_KEY")
    if not clave:
        raise SystemExit("Falta GEMINI_API_KEY")
    modelos = modelos_disponibles(clave)
    print(f"modelos: {modelos[:6]}", file=sys.stderr)

    entrada = [{"id": i, "fuente": c["fuente"], "titulo": c["titulo"], "contexto": c["contexto"]} for i, c in enumerate(candidatos)]
    datos, modelo = gemini(INSTRUCCIONES.format(n=a.items + 2) + "\n\nCANDIDATOS:\n" + json.dumps(entrada, ensure_ascii=False),
                           clave, modelos, 0.3)
    if not isinstance(datos, dict) or not isinstance(datos.get("items"), list):
        raise SystemExit("Respuesta del redactor sin items")

    descartes, validos, ids = [], [], set()
    for it in datos["items"]:
        if not estructura_ok(it, len(candidatos)) or it["id"] in ids:
            descartes.append({"id": it.get("id"), "motivo": "estructura inválida o repetido"})
            continue
        ids.add(it["id"])
        motivo = numeros_ok(it, candidatos[it["id"]])  # capa 2
        if motivo:
            descartes.append({"id": it["id"], "titulo": candidatos[it["id"]]["titulo"], "motivo": motivo})
        else:
            validos.append(it)

    # capa 3: revisor (otro modelo si hay, temperatura 0)
    revisar = [{"id": it["id"], "contexto": candidatos[it["id"]]["contexto"], **{l: it[l] for l in LANGS}} for it in validos]
    veredictos, revisor = gemini(REVISOR.format(items=json.dumps(revisar, ensure_ascii=False)), clave, modelos, 0.0, evitar=modelo)
    apoyados = {v["id"] for v in veredictos if isinstance(v, dict) and v.get("apoyado") is True} if isinstance(veredictos, list) else set()
    for v in veredictos if isinstance(veredictos, list) else []:
        if isinstance(v, dict) and v.get("apoyado") is not True:
            descartes.append({"id": v.get("id"), "titulo": candidatos[v["id"]]["titulo"] if isinstance(v.get("id"), int) and v["id"] < len(candidatos) else "",
                              "motivo": f"revisor: {v.get('motivo', '')}"})
    finales = [it for it in validos if it["id"] in apoyados][: a.items]

    informe = {"dia": a.dia, "redactor": modelo, "revisor": revisor, "candidatos": len(candidatos),
               "propuestos": len(datos["items"]), "publicados": len(finales), "descartes": descartes}
    print(json.dumps(informe, ensure_ascii=False, indent=1), file=sys.stderr)
    if a.informe:
        a.informe.write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")

    if len(finales) < MIN_ITEMS:  # capa 4: falla cerrada
        print(f"NO SE PUBLICA: solo {len(finales)} ítems válidos (mínimo {MIN_ITEMS})", file=sys.stderr)
        sys.exit(3)
    datos["items"] = finales
    for lang in LANGS:
        destino = a.salida / lang / "diario" / f"{a.dia}.md"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(markdown(lang, a.dia, datos, candidatos, modelo, revisor), encoding="utf-8")
        print(f"escrito: {destino}", file=sys.stderr)


if __name__ == "__main__":
    main()
