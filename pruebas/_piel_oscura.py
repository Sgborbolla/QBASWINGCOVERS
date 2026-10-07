# -*- coding: utf-8 -*-
"""
El cambio de piel: todo el programa pasa a la casa oscura y dorada.

  - Los estilos salen de estilos.py: fondo casi negro, tipografia
    serif, oro y las perforaciones de la cinta de cine, igual que
    QBASwing MyServer.
  - La galeria usa toda la anchura de la ventana. Nada de columnas
    pequenas con un monton de fondo vacio alrededor.
  - Se arregla el fallo que rompia la galeria al abrir una carpeta de
    verdad: _imagen_util() pide dos datos y le daban uno.
"""
import ast
import io
import re

RUTA = r"C:\QBASWING-COVERS\servidor.py"
t = io.open(RUTA, encoding="utf-8").read()
hechos = []


# ------------------------------------------- 1) los estilos salen de estilos.py
P = re.compile(r'^CSS = """.*?^""" \+ fondo\.CSS$', re.S | re.M)
if not P.search(t):
    raise SystemExit("no se encontro el bloque CSS")
t = P.sub("CSS = estilos.CSS + fondo.CSS", t, count=1)
hechos.append("la hoja de estilo base va ahora en estilos.py")

P = re.compile(r'^CSS_PORTADA = """.*?^"""$', re.S | re.M)
if not P.search(t):
    raise SystemExit("no se encontro el bloque CSS_PORTADA")
t = P.sub("CSS_PORTADA = estilos.CSS_PORTADA", t, count=1)
hechos.append("la hoja de la portada va ahora en estilos.py")

t = t.replace("import iconos\nimport fondo\n",
              "import iconos\nimport fondo\nimport estilos\n", 1)
if "import estilos" not in t:
    raise SystemExit("no se pudo agregar el import de estilos")
hechos.append("el modulo estilos")

# ------------------------------------- 2) el fallo que rompia la galeria real
VIEJO = '''def _mirar_subcarpeta(ruta):
    """
    Una sola pasada por la carpeta: cuantas subcarpetas tiene y si hay
    alguna imagen dentro. Devuelve (hijos, tiene_imagen).
    """
    hijos = 0
    imagen = False
    try:
        with os.scandir(ruta) as entradas:
            for e in entradas:
                try:
                    if e.is_dir(follow_symlinks=False):
                        hijos += 1
                        continue
                except OSError:
                    continue
                if not imagen and escaneo._imagen_util(e.name):
                    # Solo cuenta como caratula una imagen de verdad,
                    # no un thumbs.db ni un icono del sistema.
                    imagen = True
                    if hijos or True:
                        pass
    except OSError:
        return 0, False
    return hijos, imagen'''

NUEVO = '''def _mirar_subcarpeta(ruta):
    """
    Una sola pasada por la carpeta: cuantas subcarpetas tiene y si hay
    alguna imagen utilizable como poster. Devuelve (hijos, imagen).

    La imagen se busca aqui mismo, sin una lectura mas, porque para
    contar los hijos ya hubo que abrir la carpeta.
    """
    hijos = 0
    imagen = False
    try:
        with os.scandir(ruta) as entradas:
            for e in entradas:
                try:
                    if e.is_dir(follow_symlinks=False):
                        hijos += 1
                        continue
                except OSError:
                    continue
                if imagen:
                    continue
                try:
                    tamano = e.stat(follow_symlinks=False).st_size
                except OSError:
                    tamano = 0
                # Solo cuenta una imagen de verdad: nada de thumbs.db,
                # nada de iconos del sistema, nada por debajo del minimo.
                if escaneo._imagen_util(e.name, tamano):
                    imagen = True
    except OSError:
        return 0, False
    return hijos, imagen'''

if VIEJO not in t:
    raise SystemExit("no se encontro _mirar_subcarpeta")
t = t.replace(VIEJO, NUEVO, 1)
hechos.append("arreglado el fallo de _imagen_util() en la galeria")

# -------------------------- 3) las unidades tambien se miran una sola vez
# Las tarjetas de unidad no necesitan buscar imagenes: no la tienen.
if '"tiene_imagen": False,' not in t:
    raise SystemExit("las tarjetas de unidad perdieron tiene_imagen")

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(t)
ast.parse(io.open(RUTA, encoding="utf-8").read())

# ---------------------------------------------------------- 4) comprobaciones
import os
import sys
sys.path.insert(0, os.path.dirname(RUTA))
import estilos  # noqa
import fondo    # noqa

for nombre, css in (("estilos.CSS", estilos.CSS),
                    ("estilos.CSS_PORTADA", estilos.CSS_PORTADA),
                    ("fondo.CSS", fondo.CSS)):
    if not css.strip():
        raise SystemExit("%s esta vacio" % nombre)
    print("   %-22s %6d car." % (nombre, len(css)))

h = fondo.html("es")
print("   fondo                 %6d car.  mural=%d tira=%d"
      % (len(h), h.count("f-mur"), h.count('class="f-lienzo f-col"')))

print()
print("Piel oscura y dorada:")
for h2 in hechos:
    print("   -", h2)
print("sintaxis OK")