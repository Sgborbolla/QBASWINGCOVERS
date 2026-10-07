# -*- coding: utf-8 -*-
"""
Verifica las reglas de escaneo con arboles reales de coleccion.

Reglas comprobadas:
  5.1  la carpeta candidata es la que tiene el video EN ELLA MISMA
  5.4  una miniatura en thumbs/ NO cuenta como poster
  5.4  el poster va a la carpeta donde esta el video
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, r"C:\QBASWING-COVERS")
import escaneo

RAIZ = tempfile.mkdtemp(prefix="qbawing_scan_")
fallos = []


def archivo(ruta, mb=12):
    # 12 MB: por encima del filtro de 10 MB (5.3).
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(b"\0" * (mb * 1024 * 1024))


def carpeta(nombre):
    p = os.path.join(RAIZ, nombre)
    os.makedirs(p, exist_ok=True)
    return p


def img(ruta, kb=60):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(b"\0" * (kb * 1024))


# ------------------------------------------------------------------ casos
archivo(os.path.join(carpeta("Pelicula Normal (2019)"),
                     "Pelicula Normal (2019).mkv"), 12)

archivo(os.path.join(carpeta("Pelicula BluRay (2020)"), "BD",
                     "Pelicula BluRay (2020).mp4"), 12)

serie = carpeta("Serie Completa")
archivo(os.path.join(serie, "Season 1", "S01E01.mkv"), 12)
archivo(os.path.join(serie, "Season 2", "S02E01.mkv"), 12)

thumbs = carpeta("Con Thumbs (2021)")
archivo(os.path.join(thumbs, "Pelicula.mkv"), 12)
img(os.path.join(thumbs, "thumbs", "frame001.png"), 1)      # NO es poster
img(os.path.join(thumbs, "thumbs.db"), 1)                    # NO es poster

ya = carpeta("Ya Tiene Poster (2018)")
archivo(os.path.join(ya, "movie.mkv"), 12)
img(os.path.join(ya, "cover.jpg"), 200)                       # SI es poster

chico = carpeta("Video Chiquito (2022)")
archivo(os.path.join(chico, "sample.mkv"), 0)                # menos de 10 MB

archivo(os.path.join(carpeta("Solo Musica"), "cancion.mp3"), 5)

print("=" * 78)
print("ESCANEO:", RAIZ)
print("=" * 78)

res = escaneo.escanear_unidad(RAIZ)
por_nombre = {}
for r in res:
    por_nombre.setdefault(r["nombre"], r)

print("\n%-24s %-9s %-8s %-6s" % ("CARPETA", "VIDEOS", "YA TIENE", "IMAGEN"))
print("-" * 78)
for r in sorted(res, key=lambda x: x["ruta"]):
    print("%-24s %-9s %-8s %-6s" % (
        r["nombre"], r["videos"], r["ya_tiene"],
        os.path.basename(r["imagen_existente"]) or "-"))


def comprobar(descripcion, condicion):
    print("  %-58s %s" % (descripcion, "OK" if condicion else "FALLO"))
    if not condicion:
        fallos.append(descripcion)


print("\nCOMPROBACIONES")
comprobar("Pelicula con video en la misma carpeta",
          "Pelicula Normal (2019)" in por_nombre)
comprobar("Pelicula con video en BD/ -> candidata es BD",
          "BD" in por_nombre and "Pelicula BluRay (2020)" not in por_nombre)
comprobar("Serie con Season 1/ y Season 2/ -> 2 candidatas",
          "Season 1" in por_nombre and "Season 2" in por_nombre)
comprobar("Serie Completa NO es candidata (no tiene video propio)",
          "Serie Completa" not in por_nombre)
comprobar("thumbs/frame001.png y thumbs.db NO cuentan como poster",
          "Con Thumbs (2021)" in por_nombre
          and por_nombre["Con Thumbs (2021)"]["ya_tiene"] is False)
comprobar("cover.jpg SI cuenta como poster",
          "Ya Tiene Poster (2018)" in por_nombre
          and por_nombre["Ya Tiene Poster (2018)"]["ya_tiene"] is True)
comprobar("video menor de 10 MB no cuenta",
          "Video Chiquito (2022)" not in por_nombre)
comprobar("carpeta sin video no aparece",
          "Solo Musica" not in por_nombre)
comprobar("todas las rutas son absolutas y existen",
          all(os.path.isdir(r["ruta"]) for r in res))

print("\n" + "=" * 78)
print("Candidatas detectadas: %d" % len(res))
print("FALLOS: %d" % len(fallos))
shutil.rmtree(RAIZ, ignore_errors=True)
sys.exit(1 if fallos else 0)