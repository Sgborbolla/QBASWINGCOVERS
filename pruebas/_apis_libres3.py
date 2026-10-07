# -*- coding: utf-8 -*-
"""Tercera ronda: Kitsu bien impreso, Bangumi, Cinemeta y tamanos de imagen."""
import json
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
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        print("%-28s FALLO %s" % (nombre, e))
        return None


def portada_kitsu(a):
    ci = a.get("coverImage") or {}
    for nivel in ("original", "large", "medium"):
        v = ci.get(nivel)
        if isinstance(v, dict) and v.get("url"):
            return v["url"]
        if isinstance(v, str) and v:
            return v
    return ""


print("=" * 78)
print("KITSU")
print("=" * 78)
for q, tipo in [("naruto", "anime"), ("berserk", "manga"),
                ("one piece", "anime")]:
    url = ("https://kitsu.io/api/edge/%s?filter%%5Btext%%5D=%s&limit=3"
           % (tipo, urllib.parse.quote(q) if False else q.replace(" ", "%20")))
    j = pedir("kitsu %s %s" % (tipo, q), url,
              cabeceras={"Accept": "application/vnd.api+json"})
    if j:
        for d in (j.get("data") or [])[:2]:
            a = d.get("attributes") or {}
            print("      - %-24s %s" % (a.get("canonicalTitle"),
                                       portada_kitsu(a)[:70]))

print()
print("=" * 78)
print("BANGUMI (POST)")
print("=" * 78)
j = pedir("bangumi", "https://api.bgm.tv/v0/search/subjects",
          metodo="POST", cuerpo={"keyword": "eva", "filter": {"type": [2]}})
if j:
    for d in (j.get("data") or [])[:3]:
        print("      - %-24s %s" % (d.get("name"),
                                   (d.get("images") or {}).get("large")))

print()
print("=" * 78)
print("CINEMETA (es)")
print("=" * 78)
for cat in ("movie/top", "series/top"):
    j = pedir("cinemeta %s" % cat,
              "https://v3-cinemeta.strem.io/catalog/%s/1-20.json?language=es" % cat)
    if j:
        metas = j.get("metas") or []
        print("      %d titulos" % len(metas))
        for m in metas[:3]:
            print("      - %-30s %s" % (m.get("name"), m.get("poster")))

print()
print("=" * 78)
print("TAMANOS metahub")
print("=" * 78)
for tam in ("small", "medium", "large"):
    url = "https://images.metahub.space/poster/%s/tt6933238/img" % tam
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            datos = r.read()
        print("   %-8s %8d bytes  %s" % (tam, len(datos),
                                         r.headers.get("Content-Type")))
    except Exception as e:
        print("   %-8s FALLO %s" % (tam, e))