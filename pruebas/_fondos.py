# -*- coding: utf-8 -*-
"""
El fondo de cada pantalla tiene que ser distinto, y todas las paginas
tienen que montar sin fallos.

Con esto se comprueba que dos pantallas no salen con el mismo reparto de
Posters, que es lo que se quejo: que el fondo se repetia igual en todas.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fondo
import servidor

if servidor.E is None:
    servidor.E = servidor.Estado({"tmdb_api_key": ""})

fallos = []

PANTALLAS = [
    ("portada", lambda: servidor.ventana_portada("es"), True),
    ("discos", lambda: servidor.ventana_discos("es", []), True),
    ("escaneo", lambda: servidor.ventana_escaneo("es", []), True),
    ("pregunta", lambda: servidor.ventana_pregunta("es", False), True),
    ("buscando", lambda: servidor.ventana_buscando("es"), True),
    ("galeria", lambda: servidor.ventana_galeria("es", None), True),
    ("resumen", lambda: servidor.ventana_resumen("es", {
        "descargados": 2, "ya_tenian": 1, "sin_coincidencia": 0,
        "fallos": 0}), True),
    ("acerca", lambda: servidor.ventana_acerca("es", "/"), True),
    ("descargando", lambda: servidor.ventana_descargando("es"), True),
    ("inventario", lambda: servidor.ventana_inventario("es"), True),
]

firmas = {}
print("Pantallas:")
for nombre, fabricar, con_fondo in PANTALLAS:
    html = fabricar()
    semilla = re.search(r'class="fondo" data-semilla="([^"]*)"', html)
    semilla = semilla.group(1) if semilla else None

    if len(html) < 200 or "%s" in html or not html.startswith("<!DOCTYPE"):
        fallos.append("%s: la pagina no monta" % nombre)
    tiene = '<div class="fondo"' in html
    if tiene != con_fondo:
        fallos.append("%s: el fondo deberia ser %s" % (nombre, con_fondo))

    # La firma es donde cae cada cartel: si dos pantallas coinciden,
    # el fondo se ve igual en las dos.
    lugares = re.findall(r'class="f-lienzo f-(?:mur|col)" style="left:([^;]+);'
                         r'top:([^;]+);width:([^;]+);--giro:([^;]+)', html)
    n = html.count("f-lienzo f-")
    print("   %-12s semilla=%-18s carteles=%2d  %6d car."
          % (nombre, semilla or "(sin fondo)", n, len(html)))
    if not semilla:
        # La portada inicial no lleva fondo: ya tiene su propio collage.
        if con_fondo:
            fallos.append("%s: deberia tener fondo y no lo tiene" % nombre)
        continue
    if not lugares:
        fallos.append("%s: el fondo no tiene reparto de carteles" % nombre)
    if semilla in firmas:
        fallos.append("%s y %s comparten la semilla %r: se verian iguales"
                      % (firmas[semilla], nombre, semilla))
    firmas[semilla] = nombre

    # Ninguna pantalla puede tener menos de 40 carteles de fondo.
    if con_fondo and n < 40:
        fallos.append("%s: solo %d carteles de fondo (se pidieron muchos mas)"
                      % (nombre, n))

# El reparto tiene que cambiar de verdad, no solo la semilla.
lugares_por_semilla = {}
for nombre, fabricar, con_fondo in PANTALLAS:
    html = fabricar()
    m = re.search(r'class="fondo" data-semilla="([^"]*)"', html)
    if not m:
        continue
    lugares_por_semilla.setdefault(m.group(1), set()).update(
        re.findall(r'class="f-lienzo f-(?:mur|col)" style="([^"]*)"', html))
repetidos = [s for s, v in lugares_por_semilla.items()
             if len(v) < len(fondo._mural(s) or fondo._tira(s))]
for s in repetidos:
    fallos.append("la pantalla %s no cambio el reparto de carteles" % s)

print()
print("Semillas distintas: %d de %d pantallas" % (len(firmas), len(PANTALLAS)))
print("Carteles por pantalla: %d" % (len(fondo._mural("galeria"))
                                    + len(fondo._tira("galeria"))))
if len(fondo.html("galeria")) > 90000:
    fallos.append("el fondo se ha puesto demasiado pesado: %d car."
                  % len(fondo.html("galeria")))

print()
if fallos:
    print("FALLOS:")
    for f in fallos:
        print("   -", f)
    sys.exit(1)
print("Cada pantalla con su propio fondo, y todas montan bien.")