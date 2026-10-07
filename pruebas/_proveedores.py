# -*- coding: utf-8 -*-
"""
Diagnostico de RED (manual, NO va en la bateria):
1) comprueba la conexion con cada proveedor de posters;
2) hace descargas de prueba REALES de peliculas, series, telenovelas
   y animes hasta Descargas\\QBASWING COVERS (el destino normal);
3) verifica cada archivo: tamano >= 15 KB, imagen valida y carpeta de
   origen intacta (ni un byte escrito en los discos).

Las descargas se dejan en la carpeta para revisarlas; con --borrar las
borra el solo al terminar. La base de la prueba vive en %TEMP% y se
borra al salir, asi que no queda ningun registro.
"""
import os
import sys
import shutil
import tempfile
import time
from pathlib import Path

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

import fuentes as F
import posters as post
import servidor as S
from qbaswing_covers import cargar_config

BORRAR = "--borrar" in sys.argv
cfg = cargar_config()

fallos = []

# ------------------------------------------------------------------
# 1) Conexion con cada proveedor
# ------------------------------------------------------------------
print("=" * 74)
print("1) PROVEEDORES (conexion)")
print("=" * 74)

CASOS_RED = [
    ("TMDB pelicula",    lambda: F.tmdb_pelicula(cfg, "The Matrix", 1999)),
    ("TMDB serie",       lambda: F.tmdb_serie(cfg, "Breaking Bad", 2008)),
    ("AniList",          lambda: F.anilist("Naruto")),
    ("TVmaze",           lambda: F.tvmaze("Breaking Bad")),
    ("OpenLibrary",      lambda: F.openlibrary("Harry Potter")),
    ("GoogleBooks",      lambda: F.googlebooks("Harry Potter")),
    ("MangaDex",         lambda: F.mangadex("Naruto")),
    ("MusicBrainz",      lambda: F.musicbrainz("Queen")),
    ("Internet Archive", lambda: F.internetarchive("Charlie Chaplin")),
]

conectados = 0
for nombre, fn in CASOS_RED:
    t0 = time.time()
    try:
        res = fn()
    except Exception as exc:
        print("%-18s SIN CONEXION   %s: %s" % (nombre, type(exc).__name__, exc))
        fallos.append("proveedor " + nombre)
        continue
    dt = time.time() - t0
    n = len(res or [])
    conectados += 1
    estado = "CONECTA" if n else "CONECTA (sin resultados)"
    primer = ""
    if res:
        primer = (res[0].get("poster_url") or "")[:56]
    print("%-18s %-24s %2d res %5.1fs  %s" % (nombre, estado, n, dt, primer))
print("Proveedores que responden: %d de %d" % (conectados, len(CASOS_RED)))

# ------------------------------------------------------------------
# 2) Descargas de prueba por tipo de contenido
# ------------------------------------------------------------------
print()
print("=" * 74)
print("2) DESCARGAS DE PRUEBA (a la carpeta de Descargas real)")
print("=" * 74)

# Nada de lo real se toca: inventario, base de estado y el recuerdo de
# lo descargado apuntan a la carpeta temporal, que se borra al salir.
# La carpeta de Descargas NO se parchea: estas descargas son de verdad.
raiz = tempfile.mkdtemp(prefix="qbawing_red_")
S.INVENTARIO = Path(os.path.join(raiz, "inventario.csv"))
S.DB_FILE = Path(os.path.join(raiz, "qbawing_covers.db"))
_mapa = {}


def _registrar_mentira(ruta, archivo):
    _mapa[ruta] = archivo
    return True


S.base.registrar_descarga = _registrar_mentira
S.base.descarga_de = lambda ruta: _mapa.get(ruta, "")

S.E = S.Estado(cfg)
E = S.E

CASOS = [
    # (tipo,      nombre de carpeta,        APIs,         titulo a buscar,           anio, temporada)
    ("pelicula",   "The Matrix",              ["peliculas"], "The Matrix",             1999, None),
    ("pelicula",   "El Senor de los Anillos", ["peliculas"], "El Senor de los Anillos", None, None),
    ("pelicula",   "Interstellar",            ["peliculas"], "Interstellar",           2014, None),
    ("serie",      "Breaking Bad",            ["series"],    "Breaking Bad",            2008, None),
    ("telenovela", "Rosario Tijeras T1",      ["series"],    "Rosario Tijeras",         None, None),
    ("anime",      "One Piece T20",           ["animes"],    "One Piece",               None, None),
    ("anime",      "Naruto Shippuden",        ["animes"],    "Naruto Shippuden",        None, None),
]

try:
    carpeta_real = S._carpeta_descargas(crear=True)
    if not carpeta_real:
        raise SystemExit("No se pudo abrir la carpeta de Descargas")
    antes = set(os.listdir(carpeta_real))

    print("Carpeta: %s" % carpeta_real)
    print()
    print("%-11s %-24s %-6s %-28s %9s  %s" % (
        "TIPO", "CARPETA", "ESTADO", "ARCHIVO", "TAMANO", "FUENTE"))
    print("-" * 74)

    creados = []
    for tipo, nombre, tipos, titulo, anio, temp in CASOS:
        try:
            candidatos = F.buscar(cfg, titulo, anio, temp, tipos)
        except Exception as exc:
            print("%-11s %-24s fallo  busqueda: %s" % (tipo, nombre, exc))
            fallos.append("busqueda " + nombre)
            continue
        mejor, motivo, _puntos = post.elegir_mejor(
            candidatos or [], titulo, anio, temp)
        if not mejor or not mejor.get("poster_url"):
            print("%-11s %-24s sin_coincidencia (%s)" % (tipo, nombre, motivo))
            fallos.append("sin coincidencia " + nombre)
            continue

        # Carpeta de ORIGEN sintetica y vacia: asi se comprueba que no
        # recibe ni un byte.
        ruta = os.path.join(raiz, "origen", nombre)
        os.makedirs(ruta, exist_ok=True)
        c = {"ruta": ruta, "nombre": nombre, "unidad": raiz,
             "ya_tiene": False, "imagen_existente": "", "videos": 1,
             "anio": anio, "temporada": temp, "titulo": titulo,
             "tipo": tipo, "descargado": False}
        E.carpetas.append(c)
        E.resultados[ruta] = {
            "titulo": mejor.get("titulo") or titulo,
            "ano": mejor.get("ano") or anio,
            "tipo": tipo,
            "fuente": mejor.get("fuente", ""),
            "poster_url": mejor["poster_url"],
            "id": mejor.get("id", 0),
            "puntuacion": mejor.get("puntuacion", 90),
            "candidatos": [],
        }

        estado, tam = S._descargar_una(c)
        archivo = _mapa.get(ruta, "")
        destino = os.path.join(carpeta_real, archivo) if archivo else ""

        problema = ""
        if estado != "ok":
            problema = "ESTADO=" + estado
        elif os.listdir(ruta):
            problema = "ESCRIBIO EN EL ORIGEN"
        elif tam < S.MIN_POSTER_SIZE:
            problema = "pequeno (%d B)" % tam
        else:
            with open(destino, "rb") as f:
                cabeza = f.read(12)
            if cabeza.startswith(b"\xff\xd8\xff"):
                formato = "jpg"
            elif cabeza.startswith(b"\x89PNG"):
                formato = "png"
            elif cabeza.startswith(b"RIFF") and cabeza[8:12] == b"WEBP":
                formato = "webp"
            else:
                formato = "?"
                problema = "no es imagen: %r" % cabeza
        if problema:
            fallos.append("%s: %s" % (nombre, problema))

        if archivo:
            creados.append(os.path.join(carpeta_real, archivo))
        print("%-11s %-24s %-6s %-28s %7.1f KB  %s %s" % (
            tipo, nombre, estado, archivo or "-",
            (tam or 0) / 1024.0,
            E.resultados[ruta]["fuente"],
            ("<< " + problema) if problema else ""))

    nuevos = sorted(set(os.listdir(carpeta_real)) - antes)

    print()
    print("=" * 74)
    print("RESUMEN")
    print("=" * 74)
    print("Archivos creados: %d" % len(nuevos))
    for nombre_arch in nuevos:
        print("  %s" % os.path.join(carpeta_real, nombre_arch))

    if BORRAR:
        for nombre_arch in nuevos:
            try:
                os.remove(os.path.join(carpeta_real, nombre_arch))
            except OSError as exc:
                fallos.append("borrar %s: %s" % (nombre_arch, exc))
        restantes = set(os.listdir(carpeta_real)) - antes
        print("Borrados: %d (quedan %d de antes)" % (
            len(nuevos) - len(restantes), len(antes)))
        if restantes:
            fallos.append("no se borraron: %s" % ", ".join(sorted(restantes)))
    else:
        print("Revisa los archivos y borralos "
              "(o vuelve a lanzar con --borrar).")

    parciales = [n_ for n_ in nuevos if n_.endswith(".qbawing-parcial")]
    if parciales:
        fallos.append("restos de parcial: %s" % ", ".join(parciales))

    if fallos:
        print()
        print("FALLOS: %d" % len(fallos))
        for f_ in fallos:
            print("  - %s" % f_)
        sys.exit(1)
    print()
    print("TODO EN ORDEN: proveedores conectos y descargas verificadas")

finally:
    try:
        E._db.close()
    except Exception:
        pass
    shutil.rmtree(raiz, ignore_errors=True)
