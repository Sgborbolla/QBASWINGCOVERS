# -*- coding: utf-8 -*-
"""Reproduce los falsos 'no necesita poster' con arboles reales."""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, r"C:\QBASWING-COVERS")
import escaneo

RAIZ = tempfile.mkdtemp(prefix="qbawing_bug_")


def archivo(ruta, mb=12):
    # 12 MB: por encima del filtro de 10 MB (5.3).
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(b"\0" * (mb * 1024 * 1024))


def carpeta(nombre):
    p = os.path.join(RAIZ, nombre)
    os.makedirs(p, exist_ok=True)
    return p


CASOS = []

# 1 - pelicula normal: el video esta en la MISMA carpeta
c = carpeta("Pelicula Normal (2019)")
archivo(os.path.join(c, "Pelicula Normal (2019).mkv"), 12)
CASOS.append(("Pelicula Normal (2019)", "video en la misma carpeta", True))

# 2 - pelicula con subcarpeta de video ( BluRay/, DVD/, 1080p/)
#     5.1: la candidata es la carpeta que tiene el video EN ELLA MISMA,
#     o sea BD/, no la contenedora.
c = carpeta("Pelicula BluRay (2020)")
archivo(os.path.join(c, "BD", "Pelicula BluRay (2020).mp4"), 12)
CASOS.append(("BD", "video dentro de BD/", True))
CASOS.append(("Pelicula BluRay (2020)", "contenedora de BD/ no es candidata", False))

# 3 - serie con carpetas de temporada: cada temporada es candidata
c = carpeta("Serie Completa")
archivo(os.path.join(c, "Season 1", "S01E01.mkv"), 12)
archivo(os.path.join(c, "Season 2", "S02E01.mkv"), 12)
CASOS.append(("Season 1", "videos en Season 1/", True))
CASOS.append(("Season 2", "videos en Season 2/", True))
CASOS.append(("Serie Completa", "contenedora de temporadas no es candidata", False))

# 4 - carpeta con video pero con una imagen suelta dentro (thumbnails)
c = carpeta("Con Thumbs (2021)")
archivo(os.path.join(c, "Pelicula.mkv"), 12)
archivo(os.path.join(c, "thumbs", "frame001.png"), 1)   # imagen NO es poster
CASOS.append(("Con Thumbs (2021)", "video + png de thumbnail", True))

# 5 - video con numero y espacio raro en la extension
c = carpeta("Video Raro")
archivo(os.path.join(c, "Pelicula Final .MP4"), 12)
CASOS.append(("Video Raro", "extension con espacio antes", True))

# 6 - solo audios, no debe salir
c = carpeta("Solo Musica")
archivo(os.path.join(c, "cancion.mp3"), 5)
CASOS.append(("Solo Musica", "sin video (no debe salir)", False))

print("=" * 74)
print("ARBOL DE PRUEBA:", RAIZ)
print("=" * 74)

res = escaneo.escanear_unidad(RAIZ)
por_nombre = {}
for r in res:
    por_nombre.setdefault(r["nombre"], r)

print("\n%-26s %-34s %-6s %-6s %s" % ("CARPETA", "CASO", "PIDE", "YA_TIE", "VEREDICTO"))
print("-" * 74)

fallos = 0
for nombre, caso, debe in CASOS:
    r = por_nombre.get(nombre)
    pide = r is not None
    ya = bool(r and r["ya_tiene"])
    ok = (pide == debe)
    veredicto = "OK" if ok else "FALLO"
    if not ok:
        fallos += 1
    print("%-26s %-34s %-6s %-6s %s" % (
        nombre, caso, "si" if pide else "NO", "si" if ya else "no", veredicto))

print("\n" + "=" * 74)
print("Carpetas detectadas con video: %d de %d esperadas" % (
    len([n for n, c, d in CASOS if d and n in por_nombre]),
    len([1 for n, c, d in CASOS if d])))
print("FALLOS: %d" % fallos)

print("\nDetalle de 'ya_tiene' (imagenes sueltas mal contadas como poster):")
for nombre, caso, debe in CASOS:
    r = por_nombre.get(nombre)
    if r and r["ya_tiene"]:
        print("   %-26s -> ya_tiene=True, imagen_existente=%r  <-- FALSA POSITIVA"
              % (nombre, r["imagen_existente"]))

shutil.rmtree(RAIZ, ignore_errors=True)
sys.exit(1 if fallos else 0)