# -*- coding: utf-8 -*-
"""Sondeo de APIs de posters SIN clave para ver cuales sirven de verdad."""
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "QBASWINGCovers/1.0 (local)", "Accept": "application/json"}


def pedir(nombre, url, metodo="GET", cuerpo=None, cabeceras=None):
    cab = dict(UA)
    if cabeceras:
        cab.update(cabeceras)
    datos = None
    if cuerpo is not None:
        datos = json.dumps(cuerpo).encode("utf-8")
        cab["Content-Type"] = "application/json"
    try:
        req = urllib.request.Request(url, data=datos, headers=cab)
        with urllib.request.urlopen(req, timeout=30) as r:
            crudo = r.read().decode("utf-8", "replace")
        j = json.loads(crudo)
        print("%-26s OK    %s" % (nombre, json.dumps(j, ensure_ascii=False)[:150]))
        return j
    except Exception as e:
        print("%-26s FALLO %s" % (nombre, e))
        return None


print("=" * 78)
print("1) WIKIPEDIA (sin clave) - poster de peliculas/libros/personas")
print("=" * 78)
for titulo in ["Rosario Tijeras (telenovela)", "One Piece",
               "El Senor de los Anillos (film)"]:
    url = ("https://es.wikipedia.org/api/rest_v1/page/summary/"
           + urllib.parse.quote(titulo.replace(" ", "_")))
    j = pedir("es.wikipedia", url)
    if j:
        print("      -> %s | thumb=%s"
              % (j.get("title"),
                 (j.get("thumbnail") or {}).get("source", "SIN PORTADA")))

print()
print("=" * 78)
print("2) CINEMETA / stremio (sin clave) - catalogo con portadas")
print("=" * 78)
j = pedir("cinemeta movie top",
          "https://v3-cinemeta.strem.io/catalog/movie/top/1-10.json")
if j:
    metas = (j.get("metas") or [])
    print("      %d peliculas. ejemplo:" % len(metas))
    for m in metas[:3]:
        print("        -", m.get("name"), "|", m.get("poster"))
j = pedir("cinemeta series top",
          "https://v3-cinemeta.strem.io/catalog/series/top/1-10.json")
if j:
    metas = (j.get("metas") or [])
    print("      %d series. ejemplo:" % len(metas))
    for m in metas[:2]:
        print("        -", m.get("name"), "|", m.get("poster"))

print()
print("=" * 78)
print("3) KITSU (sin clave) - anime y manga")
print("=" * 78)
j = pedir("kitsu anime", "https://kitsu.io/api/edge/anime"
                         "?filter%5Btext%5D=naruto&limit=3")
if j:
    for d in (j.get("data") or [])[:3]:
        a = d.get("attributes") or {}
        cover = (((a.get("coverImage") or {}).get("original")) or {}).get("url")
        print("        -", a.get("canonicalTitle"), "|", cover)

print()
print("=" * 78)
print("4) BANGUMI (sin clave) - anime y libros")
print("=" * 78)
j = pedir("bangumi subjects",
          "https://api.bgm.tv/v0/search/subjects/%s?type=2&responseGroup=small"
          % urllib.parse.quote("进击的巨人"))
if j:
    for d in (j.get("data") or [])[:3]:
        print("        -", d.get("name"), "|", d.get("images", {}).get("large"))

print()
print("=" * 78)
print("5) JIKAN / MyAnimeList (sin clave) - reintento")
print("=" * 78)
j = pedir("jikan anime", "https://api.jikan.moe/v4/anime?q=one%20piece&limit=3")
if j:
    for d in (j.get("data") or [])[:3]:
        print("        -", d.get("title"), "|",
              ((d.get("images") or {}).get("jpg") or {}).get("large_image_url"))

print()
print("=" * 78)
print("6) WIKIDATA (sin clave) - imagen principal de peliculas")
print("=" * 78)
consulta = (
    "SELECT ?item ?itemLabel ?image WHERE {"
    " ?item wdt:P31 wd:Q11424; rdfs:label ?lab."
    " FILTER(CONTAINS(LCASE(?lab), \"godfather\"))"
    " ?item wdt:P18 ?image."
    " SERVICE wikibase:label { bd:serviceParam wikibase:language \"es,en\". }"
    " } LIMIT 3")
url = ("https://query.wikidata.org/sparql?format=json&query="
       + urllib.parse.quote(consulta))
j = pedir("wikidata sparql", url, cabeceras={"Accept": "application/sparql-results+json"})
if j:
    for b in ((j.get("results") or {}).get("bindings") or [])[:3]:
        print("        -", b.get("itemLabel", {}).get("value"),
              "|", b.get("image", {}).get("value", "")[:80])