# -*- coding: utf-8 -*-
"""
Prueba del camino completo: carpeta -> buscar -> puntuar ->決定 poster.
Nombres de carpeta reales, como los del usuario (nombre + temporada).
"""
import sys

sys.path.insert(0, r"C:\QBASWING-COVERS")

import fuentes
import posters as post
# La clave TMDB vive solo en config.json (local, no se versiona).
from qbaswing_covers import cargar_config

cfg = cargar_config()

CASOS = [
    ("Rosario Tijeras T1", None),        # telenovela, con temporada
    ("One Piece T20", None),             # anime, con temporada
    ("Chocolate (2008)", None),          # pelicula, con ano
    ("El Senor de los Anillos", None),   # pelicula, sin ano
    ("Breaking Bad", None),              # serie, sin ano ni temporada
    ("Naruto Shippuden", None),
]

print("=" * 78)
print("BUG A: TIPOS_APIS.get('todos')  ->  cuantas fuentes se consultan")
print("=" * 78)
print("   claves en TIPOS_APIS:", sorted(fuentes.TIPOS_APIS))
print("   TIPOS_APIS.get('todos') =", fuentes.TIPOS_APIS.get("todos", "<< NO EXISTE >>"))
print("   TIPOS_APIS.get('todos', []) =", fuentes.TIPOS_APIS.get("todos", []),
      "  <-- lista de consultas que se manda a buscar()")

print()
print("=" * 78)
print("BUG B/C: puntuacion real con 'todos' y con las APIs una por una")
print("=" * 78)

for nombre, _ in CASOS:
    anio = post.extraer_anio(nombre)
    temp = post.extraer_temporada(nombre)
    # Igual que _hilo_escaneo(): nombre limpio y SIN el ano.
    titulo = post.quitar_anio_del_titulo(post.limpiar_nombre(nombre), anio)
    print()
    print("CARPETA : %s" % nombre)
    print("  titulo = %r  anio=%s  temporada=%s" % (titulo, anio, temp))
    print("  umbral de aceptacion = %d" % post.UMBRAL_ACEPTACION)

    for etiqueta, tipos in (("todos", ["todos"]),
                            ("series", ["series"]),
                            ("animes", ["animes"]),
                            ("peliculas", ["peliculas"])):
        try:
            cand = fuentes.buscar(cfg, titulo, anio, temp, tipos)
        except Exception as exc:
            print("   %-10s ERROR %s" % (etiqueta, exc))
            continue
        if not cand:
            print("   %-10s 0 candidatos" % etiqueta)
            continue
        mejor, motivo, puntuados = post.elegir_mejor(cand, titulo, anio, temp)
        top = puntuados[0] if puntuados else {}
        puntos = ", ".join("%s=%d" % (c.get("titulo", "")[:22], c.get("puntuacion", 0))
                           for c in puntuados[:3])
        print("   %-10s %2d cand | mejor=%s motivo=%s"
              % (etiqueta, len(cand), "SI" if mejor else "NO", motivo))
        print("              puntos: %s" % puntos)
        if mejor:
            print("              -> %s (%s) %s"
                  % (mejor["titulo"], mejor["fuente"], mejor["poster_url"][:60]))