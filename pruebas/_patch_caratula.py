# -*- coding: utf-8 -*-
"""
Agrega a escaneo.py:
  imagen_para_mostrar(ruta)   la mejor imagen para la caratula de la tarjeta
                               (puede estar en una subcarpeta tipo Posters/)
"""
import io

RUTA = r"C:\QBASWING-COVERS\escaneo.py"
texto = io.open(RUTA, encoding="utf-8").read()

if "def imagen_para_mostrar" in texto:
    print("ya estaba aplicada")
    raise SystemExit(0)

FUNCION = '''

# --------------------------------------------------------------------------
# 5.4-bis Que imagen se ve en la tarjeta
# --------------------------------------------------------------------------

def imagen_para_mostrar(ruta_carpeta, profundidad=2):
    """
    Devuelve la mejor imagen para la caratula de esta carpeta, o None.

    A diferencia de imagen_existente(), esta SI busca en subcarpetas
    (Pelicula/Posters/matrix.jpg), porque lo que se busca aqui es que la
    tarjeta se vea bien, no decidir si hay que descargar.

    Prioridad:
      1. cover.jpg / poster.jpg en la propia carpeta
      2. la imagen mas grande de la propia carpeta
      3. la imagen mas grande de una subcarpeta llamada Posters, Cover,
         caratulas, thumbs... (hasta 'profundidad' niveles)
    """
    mejor = None            # (puntaje, tamano, ruta)
    nivel_actual = [0]

    def visitar(d, nivel, en_subcarpeta):
        nonlocal mejor
        if nivel > profundidad:
            return
        try:
            entradas = list(os.scandir(d))
        except Exception:
            return
        subcarpetas = []
        for e in entradas:
            try:
                if e.is_dir(follow_symlinks=False):
                    if e.name.lower() in CARPETAS_NO_POSTER:
                        continue
                    subcarpetas.append(e)
                    continue
                if not e.is_file(follow_symlinks=False):
                    continue
                try:
                    tam = e.stat(follow_symlinks=False).st_size
                except OSError:
                    continue
                if not _imagen_util(e.name, tam):
                    continue
                if _parece_poster(e.name):
                    puntaje = 1000000000 if not en_subcarpeta else 900000000
                else:
                    # a mas tamano, mejor; y en la raiz mejor que abajo
                    puntaje = (tam if not en_subcarpeta else tam // 4)
                if mejor is None or puntaje > mejor[0]:
                    mejor = (puntaje, tam, e.path)
            except OSError:
                continue

        for s in subcarpetas:
            visitar(s.path, nivel + 1, True)

    visitar(ruta_carpeta, 0, False)
    return mejor[2] if mejor else None
'''

texto = texto.rstrip("\n") + "\n" + FUNCION
io.open(RUTA, "w", encoding="utf-8", newline="\n").write(texto)

import ast
ast.parse(io.open(RUTA, encoding="utf-8").read())
print("imagen_para_mostrar() agregada, sintaxis OK")