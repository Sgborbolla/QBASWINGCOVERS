# -*- coding: utf-8 -*-
"""
Rediseño de la galeria: iconos de Explorador de Windows y caratulas reales.

Este archivo fue en su dia una migracion; hoy es una verificacion de
SOLO LECTURA: comprueba que sigue en pie que:

  1. Las carpetas sin póster usan el icono de folder de iconos.py, no el
     dibujo viejo. Ademas les crece el icono del tipo de contenido
     (pelicula, serie, anime...) en la esquina.
  2. Las unidades usan el icono de disco segun el tipo (local, extraible,
     red, CD).
  3. La ruta de abajo no repite el nombre: muestra la ruta de verdad,
     reducida por el medio si es larga (seccion 9.5).
  4. La caratula real ocupa toda la portada de la tarjeta, y si no hay
     imagen se dibuja con el icono de carpeta, no un recuadro vacio.
  5. Rejilla con tamano de tarjeta comodo y sombra al pasar el cursor.

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


tarjeta = cuerpo("_tarjeta")

# ------------------------------------------------------------- 1) iconos
check("icono de carpeta/disco en la portada", "_icono_de_carpeta(" in tarjeta)
check("icono del tipo en la esquina", "_icono_tipo(" in tarjeta)
check("detrás el icono si la imagen no carga",
      '<div class="portada-vacia">' in tarjeta)

# --------------------------------------------------------- 2) unidades
check("icono de disco segun el tipo de unidad",
      "def _dispositivo_de(" in t and t.count("_dispositivo_de(") >= 2)
check("iconos.por_dispositivo se usa", "por_dispositivo" in t)

# ------------------------------------------------------------- 3) ruta
check("ruta de verdad reducida (9.5)",
      "def _ruta_corta(" in t and "_ruta_corta(item[" in tarjeta)

# --------------------------------------------------------- 4) caratula
check("la caratula ocupa la portada", 'class="caratula"' in tarjeta)
check("con la carpeta detras como red", "_icono_de_carpeta(item)" in tarjeta)

# --------------------------------------------------------- 5) rejilla
css = estilos + t
check("rejilla con tarjetas comodas", ".fila{display:grid" in css)
check("sombra al pasar el cursor", ".tarjeta:hover" in css)

# Solo lectura: se comprueba que el fuente sigue bien, sin escribirlo.
ast.parse(t)
print("Galeria:")
for h in hechos:
    print("   -", h)
print("sintaxis OK")
