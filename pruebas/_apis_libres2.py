# -*- coding: utf-8 -*-
"""Segunda ronda: variantes de las APIs que fallaron."""
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "QBASWINGCovers/1.0 (local; qbaswing)"}


def pedir(nombre, url, cabeceras=None, metodo="GET", cuerpo=None):
    cab = dict(UA)
    cab["Accept"] = "application/json"
    if cabeceras:
        cab.update(cabeceras)
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    if datos is not None:
        cab["Content-Type"] = "application/json"
    try:
        req = urllib.request.Request(url, data=datos, headers=cab, method=metodo)
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.loads(r.read().decode("utf-8", "replace"))
        print("%-30s OK" % nombre)
        return j
    except Exception as e:
        print("%-30s FALLO %s" % (nombre, e))
        return None


print("=" * 78)
print("1) WIKIPEDIA pageimages  (clave-free, por titulo)")
print("=" * 78)
for titulo in ["Rosario Tijeras", "One Piece", "Chocolate (película)",
               "Cien años de soledad"]:
    url = ("https://es.wikipedia.org/w/api.php?action=query&format=json"
           "&prop=pageimages&piprop=thumbnail&pithumbsize=500&redirects=1&titles="
           + urllib.parse.quote(titulo))
    j = pedir("wiki: " + titulo[:22], url)
    if j:
        paginas = ((j.get("query") or {}).get("pages") or {})
        for _id, p in paginas.items():
            th = ((p.get("thumbnail") or {}).get("source")) or ""
            print("      %-28s -> %s" % (p.get("title"), th[:76] or "SIN PORTADA"))

print()
print("=" * 78)
print("2) KITSU con Accept correcto (JSON:API)")
print("=" * 78)
j = pedir("kitsu anime",
          "https://kitsu.io/api/edge/anime?filter%5Btext%5D=naruto&limit=3",
          cabeceras={"Accept": "application/vnd.api+json"})
if j:
    for d in (j.get("data") or [])[:3]:
        a = d.get("attributes") or {}
        url = (((a.get("coverImage") or {}).get("original")) or {}).get("url")
        print("      -", a.get("canonicalTitle"), "|", url)

print()
print("=" * 78)
print("3) BANGUMI por POST")
print("=" * 78)
j = pedir("bangumi POST",
          "https://api.bgm.tv/v0/search/subjects?type=2&responseGroup=small"
          "&platform=web",
          metodo="POST",
          cuerpo={"keyword": "进击的巨人", "filter": {"type": [2]}})
if j:
    for d in (j.get("data") or [])[:3]:
        print("      -", d.get("name"), "|", (d.get("images") or {}).get("large"))

print()
print("=" * 78)
print("4) CINEMETA tamanos de poster")
print("=" * 78)
j = pedir("cinemeta series top ES", "https://v3-cinemeta.strem.io/catalog/"
                                     "series/top/1-20.json?language=es")
if j:
    metas = j.get("metas") or []
    print("      %d series en español" % len(metas))
    for m in metas[:3]:
        print("      -", m.get("name"), "|", m.get("poster"))

print()
print("=" * 78)
print("5) THE MOVIE DATABASE via cinemeta: series por genero")
print("=" * 78)
j = pedir("cinemeta series/sci-fi", "https://v3-cinemeta.strem.io/catalog/"
                                     "series/genre/sci-fi.json?skip=0")
if j:
    metas = j.get("metas") or []
    print("      %d series sci-fi" % len(metas))
    for m in metas[:2]:
        print("      -", m.get("name"), "|", m.get("poster"))

print()
print("=" * 78)
print("6) TAMAÑO real de las imagenes de metahub")
print("=" * 78)
for tam in ("small", "medium", "large"):
    url = "https://images.metahub.space/poster/%s/tt6933238/img" % tam
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            datos = r.read()
        print("   %-8s %s bytes  %s" % (tam, len(datos), r.headers.get("Content-Type")))
    except Exception as e:
        print("   %-8s FALLO %s" % (tam, e))