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


# ---------------------------------------------------------------- capa 1b: seguridad (solo noticias)
REPOS = re.compile(r"^https?://(www\.)?(github\.com|gitlab\.com|codeberg\.org|bitbucket\.org|gist\.github\.com|huggingface\.co)/", re.I)
PELIGRO = re.compile(
    r"\b(exploit\w*|0-?day|zero[- ]day|poc|proof[- ]of[- ]concept|cve-\d{4}-\d+|bypass\w*|rce|lpe|privilege escalation|"
    r"rootkit|(info)?stealer|keylogger|ransomware|botnet|ddos|c2|command and control|backdoor|payload|shellcode|"
    r"crack(ed|s)?|keygen|cheat\w*|aimbot|spoofer|injector|phishing|brute[- ]?force|account checker|"
    r"free premium|unlocked|jailbreak)\b", re.I)
DOMINIOS_BLOQUEADOS = re.compile(
    r"^https?://([^/]*\.)?(mediafire\.com|mega\.nz|anonfiles\.\w+|gofile\.io|pastebin\.com|bit\.ly|tinyurl\.com|"
    r"t\.me|discord\.gg|grabify\.link|iplogger\.\w+)(/|$)", re.I)
BINARIO = re.compile(r"\.(exe|msi|apk|zip|rar|7z|dmg|iso|bat|ps1|scr|jar|bin)(\?|$)", re.I)


def peligro(c: dict) -> str | None:
    """Regla de Juan: seguridad solo como noticia. Nunca repos de ataque ni enlaces peligrosos."""
    url = c["url"]
    if DOMINIOS_BLOQUEADOS.match(url) or BINARIO.search(url.split("#")[0]):
        return "enlace de descarga/acortador/dominio bloqueado"
    if REPOS.match(url):
        m = PELIGRO.search(f"{c['titulo']} {c['contexto'][:600]}")
        if m:
            return f"repo con contenido de ataque ('{m.group(0)}')"
    return None


def urls_publicadas(historial: Path | None, dia: str = "") -> set[str]:
    if not historial or not historial.exists():
        return set()
    urls = set()
    for md in historial.glob("*/diario/*.md"):
        if md.stem == dia:  # regenerar el mismo día no debe excluir sus propios ítems
            continue
        urls.update(u.rstrip("/").lower() for u in re.findall(r'data-url="([^"]+)"', md.read_text(encoding="utf-8")))
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
   SEGURIDAD = SOLO NOTICIAS: un tema de seguridad entra únicamente si la fuente es un medio, blog
   o aviso oficial (parches, incidentes, análisis). NUNCA elijas repos, PoC, exploits, 0-days,
   bypasses, herramientas de ataque ni nada que enseñe a atacar o enlace a código ofensivo.
2. Para cada elegido escribe en español, portugués de Brasil e inglés:
   - "titulo": título claro (traducido/adaptado, sin clickbait).
   - "resumen": 1-2 frases sobre QUÉ es, basadas SOLO en el contexto dado.
   - "importa": 1 frase concreta sobre para quién o para qué sirve. Prohibido el relleno genérico
     ("es importante para los desarrolladores porque...").
3. Veracidad: no inventes fechas, cifras, nombres, versiones ni historia. Copia cada número
   EXACTAMENTE como aparece en el contexto (sin redondear, convertir ni reescribir: "3206", no
   "3,2 mil"). No pongas en el texto las métricas (estrellas, puntos): se muestran aparte.
   Si el contexto es pobre, describe solo lo que el título dice y sé breve. No uses conocimiento externo.
4. "intro": 1 frase CORTA por idioma (máximo 15 palabras) con el panorama del día, sin números.
   Escribe nombres de archivos, comandos o código entre comillas invertidas: `xnu.ko`.
5. Para cada ítem, estilo commit: "tipo" ∈ feat (lanzamiento/novedad), fix (corrección/parche),
   perf (rendimiento), sec (noticia de seguridad), docs (guía/artículo/opinión), release (versión),
   refactor (cambio de proyecto/organización); "area": 1 palabra en minúsculas en inglés (rust, web,
   ai, kernel, java, mail, devops, db, mobile...).

Responde SOLO JSON:
{{"intro":{{"es":"","pt":"","en":""}},
  "items":[{{"id":0,"tipo":"feat","area":"web","es":{{"titulo":"","resumen":"","importa":""}},"pt":{{...}},"en":{{...}}}}]}}
"""

REVISOR = """Eres verificador de hechos. Para cada ítem tienes el CONTEXTO original (única fuente de verdad)
y los textos escritos en es/pt/en. Un ítem está "apoyado" solo si TODAS sus afirmaciones (qué es,
quién lo hizo, qué hace, versiones, cifras, fechas) se desprenden del contexto en los tres idiomas.
Una opinión razonable en "importa" sobre para quién sirve está permitida si no contradice el contexto.
Marca "apoyado": false ante cualquier dato inventado, exagerado, contradictorio o traducido con
otro significado. Marca también "apoyado": false si el ítem enlaza o promueve un exploit, PoC,
0-day, herramienta de ataque, malware, cracks/trampas o descargas sospechosas (en seguridad solo
se aceptan noticias y avisos). Sé estricto y breve.

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


# ---------------------------------------------------------------- Página estilo changelog (capa 1: HTML seguro)
# El resumen se escribe como un bloque HTML propio (sin líneas en blanco, para que Markdown no lo toque).
# TODO texto que viene del modelo o de las fuentes pasa por esc(): sin HTML ni atributos inyectados.
import hashlib
import math

ACTUAL = ' aria-current="page"'
ENCENDIDA = '<i class="on"></i>'
TIPOS = {"feat", "fix", "perf", "sec", "docs", "release", "refactor"}

TXT = {
    "es": {"titulo": "Resumen diario", "idioma": "Idioma", "commits": "commits", "lectura": "lectura", "min": "min",
           "abrir": "abrir", "discusion": "discusión", "reportar": "reportar error", "atajos": "atajos",
           "sig": "siguiente / anterior", "fuente": "abrir fuente", "dia_ant": "día anterior", "trocar": "cambiar idioma",
           "senal": "señal relativa a la fuente", "estrellas": "estrellas", "puntos": "puntos", "comentarios": "coment.",
           "reacciones": "reacciones", "dias": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
           "pie": "// generado automáticamente con IA ({modelo}, revisado por {revisor}) a partir de fuentes públicas (APIs y RSS oficiales). Cada ítem lleva al original; el contenido pertenece a sus autores. ¿Viste un error? usa \"reportar error\"."},
    "pt": {"titulo": "Resumo diário", "idioma": "Idioma", "commits": "commits", "lectura": "leitura", "min": "min",
           "abrir": "abrir", "discusion": "discussão", "reportar": "reportar erro", "atajos": "atalhos",
           "sig": "próximo / anterior", "fuente": "abrir fonte", "dia_ant": "dia anterior", "trocar": "trocar idioma",
           "senal": "sinal relativo à fonte", "estrellas": "estrelas", "puntos": "pontos", "comentarios": "coment.",
           "reacciones": "reações", "dias": ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"],
           "pie": "// gerado automaticamente com IA ({modelo}, revisado por {revisor}) a partir de fontes públicas (APIs e RSS oficiais). Cada item leva ao original; o conteúdo pertence aos autores. Viu um erro? use \"reportar erro\"."},
    "en": {"titulo": "Daily digest", "idioma": "Language", "commits": "commits", "lectura": "read", "min": "min",
           "abrir": "open", "discusion": "discussion", "reportar": "report error", "atajos": "shortcuts",
           "sig": "next / previous", "fuente": "open source", "dia_ant": "previous day", "trocar": "switch language",
           "senal": "signal relative to its source", "estrellas": "stars", "puntos": "points", "comentarios": "comments",
           "reacciones": "reactions", "dias": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
           "pie": "// generated automatically with AI ({modelo}, reviewed by {revisor}) from public sources (official APIs and RSS). Each item links to the original; the content belongs to its authors. Spotted a mistake? use \"report error\"."},
}


def esc(s) -> str:
    return html.escape(re.sub(r"\s+", " ", str(s or "")).strip(), quote=True)


def texto(s) -> str:
    """Texto del modelo ya escapado; `código` -> <code> (seguro: el contenido ya no tiene HTML)."""
    return re.sub(r"`([^`]{1,60})`", r"<code>\1</code>", esc(s))


def intro_corta(s: str, maximo: int = 18) -> str:
    palabras = re.sub(r"\s+", " ", str(s or "")).strip().split(" ")
    if len(palabras) <= maximo:
        return " ".join(palabras)
    return " ".join(palabras[:maximo]).rstrip(",;:—-") + "…"


def un_hash(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:7]


def puntaje(c: dict) -> float | None:
    m = c.get("metricas", {})
    for k in ("estrellas", "puntos", "reacciones"):
        if isinstance(m.get(k), (int, float)):
            return float(m[k])
    return None


def senales(items: list[dict], candidatos: list[dict]) -> None:
    """Señal 1-5 por ítem: posición (log) frente a los candidatos de la MISMA fuente. Blogs/RSS: 3."""
    por_fuente: dict[str, list[float]] = {}
    for c in candidatos:
        p = puntaje(c)
        if p is not None:
            por_fuente.setdefault(c["fuente"], []).append(math.log1p(p))
    for it in items:
        c = candidatos[it["id"]]
        p, lista = puntaje(c), por_fuente.get(c["fuente"], [])
        if p is None or len(lista) < 2:
            it["senal"] = 3
            continue
        lo, hi = min(lista), max(lista)
        it["senal"] = 1 + round(4 * ((math.log1p(p) - lo) / (hi - lo))) if hi > lo else 3


def dia_anterior(historial: Path | None, dia: str) -> str | None:
    if not historial or not historial.exists():
        return None
    dias = sorted({md.stem for md in historial.glob("es/diario/*.md") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", md.stem) and md.stem < dia})
    return dias[-1] if dias else None


MONOGRAMA = ('<svg viewBox="0 0 5 6" aria-hidden="true"><g fill="currentColor">'
             + "".join(f'<rect x="{x}.05" y="{y}.05" width=".9" height=".9"/>' for x, y in
                       [(2, 0), (1, 1), (3, 1), (1, 2), (3, 2), (0, 3), (1, 3), (3, 3), (4, 3), (0, 4), (4, 4), (0, 5), (4, 5)])
             + '</g><rect x="2.05" y="3.05" width=".9" height=".9" class="cursor"/></svg>')

ICONO_SOL = ('<svg class="sol" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4'
             'M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>')
ICONO_LUNA = ('<svg class="luna" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" '
              'stroke-linejoin="round"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg>')

EXTRA = {
    "es": {"tema": "Cambiar entre modo claro y oscuro", "tema_k": "tema claro / oscuro", "saltar": "Saltar al resumen", "inicio": "inicio", "sobre": "sobre este blog", "proximo": "siguiente / anterior",
           "abrir_f": "abrir fuente", "senal_t": "Señal"},
    "pt": {"tema": "Alternar entre modo claro e escuro", "tema_k": "tema claro / escuro", "saltar": "Pular para o resumo", "inicio": "início", "sobre": "sobre este blog", "proximo": "próximo / anterior",
           "abrir_f": "abrir fonte", "senal_t": "Sinal"},
    "en": {"tema": "Switch between light and dark mode", "tema_k": "light / dark theme", "saltar": "Skip to the digest", "inicio": "home", "sobre": "about this blog", "proximo": "next / previous",
           "abrir_f": "open source", "senal_t": "Signal"},
}


def sin_popover(s: str) -> str:
    """Navegación propia sin la vista previa (popover) de Quartz: añade data-no-popover a cada <a>."""
    return re.sub(r"<a (?![^>]*data-no-popover)", '<a data-no-popover="true" ', s)


SITIO = "https://juanalemau.github.io"


def escribir_rss(base: Path, lang: str, maximo: int = 30) -> None:
    """RSS por idioma (/{lang}/diario/feed.xml) con los resúmenes guardados en base/{lang}/diario/*.md."""
    t = TXT[lang]
    dias = sorted((md for md in (base / lang / "diario").glob("*.md") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", md.stem)),
                  key=lambda m: m.stem, reverse=True)[:maximo]
    items = []
    for md in dias:
        texto_md = md.read_text(encoding="utf-8")
        m = re.search(r'^description: "(.*)"$', texto_md, re.M)
        desc = html.unescape(m.group(1)) if m else ""
        fecha_d = dt.datetime.fromisoformat(md.stem).replace(hour=9, tzinfo=dt.timezone.utc)
        url = f"{SITIO}/{lang}/diario/{md.stem}"
        items.append(f"<item><title>{esc(t['titulo'])} — {md.stem}</title><link>{url}</link><guid>{url}</guid>"
                     f"<pubDate>{fecha_d.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate><description>{esc(desc)}</description></item>")
    rss = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
           f"<title>alemau — {esc(t['titulo'])}</title><link>{SITIO}/{lang}/diario/</link>"
           f"<description>{esc(t['titulo'])} · alemau</description><language>{lang}</language>{''.join(items)}</channel></rss>\n")
    (base / lang / "diario" / "feed.xml").write_text(rss, encoding="utf-8")


def k(n: int) -> str:
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def numeros(c: dict, t: dict) -> str:
    m = c.get("metricas", {})
    partes = []
    if isinstance(m.get("estrellas"), int):
        partes.append(f'<span>★ <span class="n">{k(m["estrellas"])}</span></span>')
    if isinstance(m.get("puntos"), int):
        partes.append(f'<span>▲ <span class="n">{m["puntos"]}</span></span>')
    if isinstance(m.get("reacciones"), int):
        partes.append(f'<span>♥ <span class="n">{m["reacciones"]}</span></span>')
    if isinstance(m.get("comentarios"), int):
        partes.append(f'<span>{m["comentarios"]} {esc(t["comentarios"])}</span>')
    if m.get("lenguaje"):
        partes.append(f'<span>{esc(m["lenguaje"])}</span>')
    if m.get("fecha"):
        partes.append(f'<span>{esc(m["fecha"])}</span>')
    return "".join(partes)


def pagina(lang: str, dia: str, datos: dict, candidatos: list[dict], modelo: str, revisor: str, anterior: str | None) -> str:
    """Página completa estilo `git log` (docs/proyecto/mockups/a-changelog.html), sin el marco de Quartz."""
    t, x = TXT[lang], EXTRA[lang]
    intro = texto(intro_corta(datos.get("intro", {}).get(lang, "")))
    items = datos["items"]
    fuentes: dict[str, int] = {}
    for it in items:
        f = candidatos[it["id"]]["fuente"].split(" · ")[0]
        fuentes[f] = fuentes.get(f, 0) + 1
    fecha_d = dt.date.fromisoformat(dia)
    lectura = max(2, round(len(items) * 0.6))
    langs = "".join(
        f'<a href="../../{o}/diario/{dia}" hreflang="{o}" lang="{o}"{ACTUAL if o == lang else ""}>{o}</a>' for o in LANGS)
    ant = f' · <a class="prev" href="./{anterior}">← {esc(anterior)}</a>' if anterior else ""
    h = [
        '<div class="alemau-log">',
        f'<a class="skip" href="#log">{esc(x["saltar"])}</a>',
        '<header class="top"><div class="top-in">',
        f'<a class="brand" href="../" aria-label="alemau — {esc(x["inicio"])}">{MONOGRAMA}<b>alemau</b></a>',
        f'<div class="prompt" aria-hidden="true"><span class="p">~/diario</span> $ git log <span class="flag">--since={dia}</span> --top={len(items)}<span class="cur"></span></div>',
        f'<nav class="langs" aria-label="{esc(t["idioma"])}">{langs}</nav>',
        f'<button class="tema" type="button" aria-label="{esc(x["tema"])}" title="{esc(x["tema"])}">'
        f'{ICONO_SOL}{ICONO_LUNA}</button>',
        "</div></header>",
        '<div class="cl-main">',
        f'<section class="release"><span class="tag">v{dia.replace("-", ".")}</span><h1>{esc(t["titulo"])}</h1>'
        f'<p>{intro}</p><div class="stat"><b>{len(items)} {t["commits"]}</b>'
        + "".join(f' · <span class="add">+{n} {esc(f)}</span>' for f, n in sorted(fuentes.items(), key=lambda y: -y[1]))
        + f' · {t["dias"][fecha_d.weekday()]} · {t["lectura"]} ~{lectura} {t["min"]}{ant}</div></section>',
        f'<ol class="log" id="log" aria-label="{esc(t["titulo"])}">',
    ]
    barras = []
    for n, it in enumerate(items, 1):
        c = candidatos[it["id"]]
        d = it[lang]
        hsh = un_hash(c["url"])
        tipo = it.get("tipo") if it.get("tipo") in TIPOS else "feat"
        area = it.get("area") if isinstance(it.get("area"), str) and re.fullmatch(r"[a-z0-9-]{2,14}", it["area"]) else "dev"
        reporte = "https://github.com/{}/issues/new?{}".format(REPO, urllib.parse.urlencode({
            "labels": "error-resumen", "title": f"Error en el resumen {dia} ({lang}) #{n} {hsh}",
            "body": f"Ítem: {c['url']}\n\n¿Qué está mal?\n"}))
        senal = max(1, min(5, int(it.get("senal", 3))))
        barras.append(f'<li><a href="#c-{hsh}">{hsh[:4]}</a><i style="width:{senal * 20}%"></i></li>')
        enlaces = f'<a class="open" href="{esc(c["url"])}">{t["abrir"]}</a>'
        if c.get("discusion"):
            enlaces += f'<a class="disc" href="{esc(c["discusion"])}">{t["discusion"]}</a>'
        enlaces += f'<a class="err" href="{esc(reporte)}">{t["reportar"]}</a>'
        h.append(
            f'<li class="c{" top1" if n == 1 else ""}" id="c-{hsh}" data-url="{esc(c["url"])}">'
            f'<a class="hash" href="#c-{hsh}">{hsh}</a><span class="node" aria-hidden="true"></span>'
            f'<article class="body"><h2><span class="scope">{tipo}({area}):</span>'
            f'<a href="{esc(c["url"])}">{texto(d["titulo"])}</a></h2>'
            f'<p>{texto(d["resumen"])}</p><p class="why">{texto(d["importa"])}</p>'
            f'<div class="meta"><span class="src">{esc(c["fuente"].lower())}</span>{numeros(c, t)}{enlaces}</div>'
            "</article></li>")
    h += [
        "</ol>",
        f'<aside aria-label="{esc(t["atajos"])}"><section><h3>{esc(t["atajos"])}</h3><ul class="keys">'
        f'<li><span>{esc(x["proximo"])}</span><span><kbd>j</kbd> <kbd>k</kbd></span></li>'
        f'<li><span>{esc(x["abrir_f"])}</span><kbd>o</kbd></li>'
        f'<li><span>{esc(t["discusion"])}</span><kbd>c</kbd></li>'
        f'<li><span>{esc(t["dia_ant"])}</span><kbd>[</kbd></li>'
        f'<li><span>{esc(t["trocar"])}</span><kbd>l</kbd></li>'
        f'<li><span>{esc(x["tema_k"])}</span><kbd>t</kbd></li></ul>'
        f'<h3>{esc(x["senal_t"])}</h3><ul class="bars" title="{esc(t["senal"])}">{"".join(barras)}</ul></section></aside>',
        f'<footer class="cl-foot">{esc(t["pie"].format(modelo=modelo, revisor=revisor))}<br>'
        f'<a href="../sobre">{esc(x["sobre"])}</a> · <a href="https://github.com/jackyzha0/quartz">Quartz (MIT)</a> · '
        '<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> · <a href="https://github.com/juanalemau/juanalemau.github.io">GitHub</a></footer>',
        "</div>",
        f'<div class="statusline" aria-hidden="true"><span class="mode">LOG</span><span class="fill">diario/{dia}.md</span>'
        f'<span class="r hide-sm">{lang} · utf-8</span><span class="r pos">1/{len(items)}</span></div>',
        "</div>",
    ]
    fm = [
        "---", f'title: "{t["titulo"]} — {dia}"', f"date: {dia}", f"lang: {lang}", "publish: true", "cssclasses: [diario-log]",
        f'description: "{esc(intro_corta(datos.get("intro", {}).get(lang, ""))).replace(chr(34), chr(39))}"', "tags: [diario]", "translations:",
        *[f'  {o}: "[[{o}/diario/{dia}]]"' for o in LANGS if o != lang], "---", "",
    ]
    return "\n".join(fm) + sin_popover("".join(h)) + "\n"


def problema_estructura(it: object, total: int) -> str | None:
    """None si el ítem es válido; si no, el motivo exacto. Normaliza variaciones inofensivas."""
    if not isinstance(it, dict):
        return f"no es un objeto: {type(it).__name__}"
    if isinstance(it.get("id"), str) and it["id"].strip().isdigit():
        it["id"] = int(it["id"])
    if not isinstance(it.get("id"), int) or not 0 <= it["id"] < total:
        return f"id inválido: {it.get('id')!r}"
    for l in LANGS:
        bloque = it.get(l)
        if not isinstance(bloque, dict):
            return f"falta el bloque {l} (claves: {sorted(it)[:8]})"
        for k in ("titulo", "resumen", "importa"):
            if not isinstance(bloque.get(k), str) or not bloque[k].strip():
                return f"falta {l}.{k} (claves de {l}: {sorted(bloque)[:6]})"
    return None


# ---------------------------------------------------------------- principal
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-recolectar", action="store_true")
    ap.add_argument("--salida", type=Path, default=Path("content"))
    ap.add_argument("--historial", type=Path)
    ap.add_argument("--items", type=int, default=10)
    ap.add_argument("--dia", default=AHORA.date().isoformat())
    ap.add_argument("--informe", type=Path, help="JSON con lo descartado y por qué")
    ap.add_argument("--rss", type=Path, help="solo regenerar los RSS por idioma sobre este directorio content/")
    a = ap.parse_args()

    if a.rss:  # RSS + índice del diario por idioma, sobre todos los resúmenes guardados
        from paginas import indice_diario  # import local: paginas importa este módulo
        for lang in LANGS:
            escribir_rss(a.rss, lang)
            dias = []
            for md in sorted((a.rss / lang / "diario").glob("*.md"), key=lambda m: m.stem, reverse=True):
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", md.stem):
                    m = re.search(r'^description: "(.*)"$', md.read_text(encoding="utf-8"), re.M)
                    dias.append((md.stem, html.unescape(m.group(1)) if m else ""))
            (a.rss / lang / "diario" / "index.md").write_text(indice_diario(lang, dias), encoding="utf-8")
        print(f"rss e índices escritos en {a.rss}", file=sys.stderr)
        return
    candidatos = recolectar()
    ya = urls_publicadas(a.historial, a.dia)
    candidatos = [c for c in candidatos if c["url"].rstrip("/").lower() not in ya]
    bloqueados = [(c["titulo"], peligro(c)) for c in candidatos if peligro(c)]
    for titulo, motivo in bloqueados:
        avisar(f"bloqueado por seguridad: {titulo} — {motivo}")
    candidatos = [c for c in candidatos if not peligro(c)]
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
        motivo = problema_estructura(it, len(candidatos)) or ("repetido" if it["id"] in ids else None)
        if motivo:
            descartes.append({"id": it.get("id") if isinstance(it, dict) else None, "motivo": f"estructura: {motivo}"})
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
               "propuestos": len(datos["items"]), "publicados": len(finales), "descartes": descartes,
               "muestra_respuesta": json.dumps(datos["items"][:1], ensure_ascii=False)[:1500]}
    print(json.dumps(informe, ensure_ascii=False, indent=1), file=sys.stderr)
    if a.informe:
        a.informe.write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")

    if len(finales) < MIN_ITEMS:  # capa 4: falla cerrada
        print(f"NO SE PUBLICA: solo {len(finales)} ítems válidos (mínimo {MIN_ITEMS})", file=sys.stderr)
        sys.exit(3)
    datos["items"] = finales
    senales(datos["items"], candidatos)
    for lang in LANGS:
        destino = a.salida / lang / "diario" / f"{a.dia}.md"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(pagina(lang, a.dia, datos, candidatos, modelo, revisor, dia_anterior(a.historial, a.dia)), encoding="utf-8")
        print(f"escrito: {destino}", file=sys.stderr)


if __name__ == "__main__":
    main()
