# -*- coding: utf-8 -*-
"""Por que AniList devuelve 400. Se prueban varias formas de pregunta."""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fuentes

URL = "https://graphql.anilist.co"

PRUEBAS = [
    ("la del programa", "query($p:Int){Page(perPage:%d){media"
     "(sort:POPULARITY_DESC,type:ANIME,isAdult:false)"
     "{title{romaji}coverImage{large}averageScore}}}" % 12, {}),
    ("sin variable de mas", "query{Page(perPage:12){media"
     "(sort:POPULARITY_DESC,type:ANIME,isAdult:false)"
     "{title{romaji}coverImage{large}averageScore}}}", {}),
    ("variable usada", "query($p:Int){Page(perPage:$p){media"
     "(sort:POPULARITY_DESC,type:ANIME,isAdult:false)"
     "{title{romaji}coverImage{large}averageScore}}}", {"p": 12}),
    ("con titulo y portada", "query{Page(perPage:12){media"
     "(sort:POPULARITY_DESC,type:ANIME,isAdult:false)"
     "{id title{romaji} coverImage{large} averageScore}}}", {}),
]

for nombre, consulta, variables in PRUEBAS:
    cuerpo = json.dumps({"query": consulta, "variables": variables}).encode("utf-8")
    peticion = urllib.request.Request(
        URL, data=cuerpo,
        headers={"Content-Type": "application/json",
                 "Accept": "application/json",
                 "User-Agent": "QBASwing-Covers/1.0"})
    try:
        with urllib.request.urlopen(peticion, timeout=25) as r:
            datos = json.loads(r.read().decode("utf-8"))
        medios = ((datos.get("data") or {}).get("Page") or {}).get("media") or []
        print("%-20s OK   %2d resultados   primero=%s"
              % (nombre, len(medios),
                 (medios[0]["title"]["romaji"] if medios else "-")))
    except Exception as exc:
        detalle = ""
        if hasattr(exc, "read"):
            try:
                detalle = exc.read().decode("utf-8", "replace")[:180]
            except Exception:
                detalle = ""
        print("%-20s FALLO %s  %s" % (nombre, exc, detalle))

print()
print("--- lo que hace el programa ahora mismo ---")
lista = fuentes.portadas_destacadas({"tmdb_api_key": ""}, limite=12)
print("portadas_destacadas sin clave TMDB:", len(lista))
for p in lista[:5]:
    print("   [%s] %s" % (p["tipo"], p["titulo"]))