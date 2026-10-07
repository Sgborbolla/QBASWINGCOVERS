# -*- coding: utf-8 -*-
"""Reemplaza una funcion completa usando sus limites reales en el archivo."""
import io
import re
import sys

RUTA = r"C:\QBASWING-COVERS\escaneo.py"

NUEVO = '''def imagen_existente(ruta_carpeta):
    """
    5.4 Devuelve la ruta de una imagen YA en la MISMA carpeta del video, o None.

    Solo mira la raiz de la carpeta: un .png dentro de thumbs/ no es el poster
    de la pelicula, es una miniatura de Windows.
    """
    mejor = None
    try:
        with os.scandir(ruta_carpeta) as entradas:
            for e in entradas:
                try:
                    if not e.is_file(follow_symlinks=False):
                        continue
                    tam = e.stat(follow_symlinks=False).st_size
                except OSError:
                    continue
                if not _imagen_util(e.name, tam):
                    continue
                if _parece_poster(e.name):
                    return e.path
                if mejor is None:
                    mejor = e.path
    except Exception:
        return None
    return mejor
'''.replace("\r\n", "\n")

texto = io.open(RUTA, encoding="utf-8").read()

patron = re.compile(r"^def imagen_existente\(.*?(?=^def |\Z)", re.S | re.M)
m = patron.search(texto)
if not m:
    print("NO SE ENCONTRO la funcion imagen_existente")
    sys.exit(1)

viejo = m.group(0)
print("--- VIEJO (%d chars) ---" % len(viejo))
print(viejo)

texto = texto[:m.start()] + NUEVO + "\n\n" + texto[m.end():]
io.open(RUTA, "w", encoding="utf-8", newline="\n").write(texto)
print("--- APLICADO ---")

import ast
ast.parse(io.open(RUTA, encoding="utf-8").read())
print("sintaxis OK")