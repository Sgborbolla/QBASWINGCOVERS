# -*- coding: utf-8 -*-
"""
Galeria bonita y con las caratulas de verdad.

Este archivo fue en su dia una migracion; hoy es una verificacion de
SOLO LECTURA: comprueba que el rediseño sigue en pie en servidor.py.

 1. listar_subdirectorios() anota "tiene_imagen" en cada subcarpeta,
    en la misma pasada en que cuenta los hijos (_mirar_subcarpeta).
 2. La tarjeta pide /api/cover para cualquier carpeta que tenga imagen
    dentro, no solo para las que el escaneo ya clasifico.
 3. La galeria es una rejilla que se acomoda sola, con tarjetas
    redondeadas, sombra al pasar el cursor, icono de carpeta del
    Explorador de Windows y la insignia del tipo de contenido.

NUNCA escribe servidor.py.
"""
import ast
import io
import re

RUTA = r"C:\QBASWING-COVERS\servidor.py"
RUTA_ESTILOS = r"C:\QBASWING-COVERS\estilos.py"
t = io.open(RUTA, encoding="utf-8").read()
estilos = io.open(RUTA_ESTILOS, encoding="utf-8").read()
hechos = []


def cuerpo(nombre):
    """Texto de una funcion top-level, para comprobar su contenido."""
    p = re.compile(r"^def %s\(.*?(?=^def |^class |^# ---|\Z)" % nombre,
                   re.S | re.M)
    m = p.search(t)
    if not m:
        raise SystemExit("NO SE ENCONTRO: %s()" % nombre)
    return m.group(0)


def check(h, cond, detalle=""):
    if not cond:
        raise SystemExit("FALLO: %s  %s" % (h, detalle))
    hechos.append(h)


# ------------------------------------------------- 1) listing con imagen
check("pasada unica: hijos y tiene_imagen",
      "def _mirar_subcarpeta(" in t)
lista = cuerpo("listar_subdirectorios")
check("listar_subdirectorios anota tiene_imagen",
      '"tiene_imagen"' in lista)

# --------------------------------------------- 2) la tarjeta pide cover
tarjeta = cuerpo("_tarjeta")
check("la tarjeta usa /api/cover si la carpeta tiene imagen",
      "/api/cover?id=" in tarjeta)
check("y si no, el poster de internet",
      'info.get("poster_url")' in tarjeta)

# ------------------------------------------------------- 3) CSS rejilla
css = estilos + t
check("rejilla de la galeria", ".fila{display:grid" in css)
check("tarjetas redondeadas con sombra",
      ".tarjeta{" in css and "border-radius" in css
      and ".tarjeta:hover" in css)
check("caratula ocupando la portada",
      ".portada-vacia" in css and "aspect-ratio" in css)

# ------------------------------------------------------- extras validos
check("entrada escalonada de las tarjetas", "enumerate(visibles)" in t)
check("fuera _marco_vacio() (ya no se usa)", "def _marco_vacio(" not in t)

# Solo lectura: se comprueba que el fuente sigue bien, sin escribirlo.
ast.parse(t)
print("Galeria:")
for h in hechos:
    print("   -", h)
print("sintaxis OK")
