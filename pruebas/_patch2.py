# -*- coding: utf-8 -*-
"""
Escaneo.py - cambios grandes:
  1) La carpeta candidata es la que tiene el video EN ELLA MISMA.
  2) Se agrega soporte de telefonos/tablets (MTP).
"""
import io
import re
import sys

RUTA = r"C:\QBASWING-COVERS\escaneo.py"
texto = io.open(RUTA, encoding="utf-8").read()


def reemplazar(nombre_funcion, nuevo, archivo=texto):
    """Reemplaza una funcion completa usando sus limites reales."""
    patron = re.compile(r"^def %s\(.*?(?=^def |^# ---|\Z)" % nombre_funcion,
                        re.S | re.M)
    m = patron.search(archivo)
    if not m:
        raise SystemExit("NO SE ENCONTRO: %s" % nombre_funcion)
    return archivo[:m.start()] + nuevo.rstrip("\n") + "\n\n\n" + archivo[m.end():]


# ---------------------------------------------------------------- 1) es_mtp
texto = texto.replace(
    "import rutas\n",
    "import rutas\n\ntry:\n    import mtp\nexcept Exception:      # sin soporte MTP\n    mtp = None\n", 1)

texto = texto.replace(
    'TIPO_CD = "cd"\n',
    'TIPO_CD = "cd"\nTIPO_PORTATIL = "portatil"\n', 1)

texto = texto.replace(
    '    TIPO_CD: "Unidad CD/DVD",\n',
    '    TIPO_CD: "Unidad CD/DVD",\n'
    '    TIPO_PORTATIL: "Telefono o tablet (MTP)",\n', 1)

texto = texto.replace(
    'def _programa_dir():\n    return str(rutas.base_dir())\n',
    'def _programa_dir():\n    return str(rutas.base_dir())\n\n\n'
    'def es_mtp(ruta):\n'
    '    """True si la ruta apunta a un telefono o tablet (mtp://...)."""\n'
    '    if mtp is None or not ruta:\n'
    '        return False\n'
    '    try:\n'
    '        return bool(mtp.es_ruta_mtp(ruta))\n'
    '    except Exception:\n'
    '        return False\n', 1)

# ------------------------------------------------------- 2) nuevo escaneo
NUEVO_ESCANEO = '''def _videos_validos(raiz, archivos, minimo=MIN_VIDEO_SIZE):
    """
    Cuenta los videos validos que estan EN ESTA CARPETA, sin volver a
    recorrerla con scandir (os.walk ya nos dio los nombres).
    """
    total = 0
    for nombre in archivos:
        if os.path.splitext(nombre)[1].lower() not in VIDEO_EXTENSIONS:
            continue
        try:
            if os.stat(os.path.join(raiz, nombre)).st_size >= minimo:
                total += 1
        except OSError:
            continue
    return total


def escanear_unidad(ruta_unidad, progreso=None):
    """
    5. Recorre una unidad en solo lectura y devuelve las carpetas candidatas.

    5.1 Una carpeta es candidata cuando tiene el video EN ELLA MISMA.
    Si el video esta en una subcarpeta (Serie/Season 1/, Pelicula/BD/),
    la candidata es esa subcarpeta: el poster se escribe siempre en la
    carpeta donde esta el video.

    Un telefono o tablet (mtp://) se recorre con el metodo MTP, porque
    Windows no le asigna letra de unidad.

    Devuelve una lista de dicts:
        ruta, nombre, unidad, ya_tiene, imagen_existente, videos
    """
    if es_mtp(ruta_unidad):
        try:
            return mtp.escanear(ruta_unidad, progreso=progreso)
        except Exception:
            return []

    encontradas = []
    raiz_propia = os.path.normcase(_programa_dir())

    if not os.path.isdir(ruta_unidad):
        return encontradas

    for raiz, dirs, archivos in os.walk(ruta_unidad, topdown=True,
                                         followlinks=False):
        try:
            base = os.path.normpath(ruta_unidad)
            nivel = os.path.normpath(raiz)[len(base):].count(os.sep)
        except Exception:
            nivel = 0

        # 5.6 No bajar de 8 niveles.
        if nivel >= PROFUNDIDAD_MAXIMA:
            dirs[:] = []
            continue

        # 5.5 Filtrar carpetas excluidas y la propia carpeta del programa.
        nuevas = []
        for d in dirs:
            if es_excluida(d):
                continue
            completa = os.path.join(raiz, d)
            try:
                if os.path.normcase(os.path.abspath(completa)) == raiz_propia:
                    continue
            except Exception:
                pass
            nuevas.append(d)
        dirs[:] = nuevas

        # 5.1 y 5.4 El video esta aqui mismo -> esta carpeta es candidata.
        videos = _videos_validos(raiz, archivos)
        if videos:
            img = imagen_existente(raiz)
            encontradas.append({
                "ruta": raiz,
                "nombre": os.path.basename(raiz) or raiz,
                "unidad": ruta_unidad,
                "ya_tiene": img is not None,
                "imagen_existente": img or "",
                "videos": videos,
            })
            # Una carpeta con video es una unidad: no se baja dentro de ella.
            dirs[:] = []

        if progreso is not None:
            try:
                progreso(raiz)
            except Exception:
                pass

    return encontradas
'''

texto = reemplazar("escanear_unidad", NUEVO_ESCANEO, texto)

# ------------------------------------------------- 3) portatiles en unidades
texto = texto.replace(
    '    return [u for u in unidades if u.get("ruta")]\n',
    '''    unidades = [u for u in unidades if u.get("ruta")]
    unidades.extend(_unidades_portatiles())
    return unidades
''', 1)

NUEVO_PORTATIL = '''def _unidades_portatiles():
    """
    Telefonos y tablets conectados por USB.

    Windows no les asigna letra de unidad (por eso no aparecen en
    Win32_LogicalDisk): se llegan a ver por MTP, con Shell.Application.
    """
    if mtp is None:
        return []
    try:
        nombres = mtp.dispositivos()
    except Exception:
        return []

    unidades = []
    for nombre in nombres:
        try:
            raiz = mtp.unir(nombre, [])
        except Exception:
            continue
        unidades.append({
            "ruta": raiz,
            "etiqueta": nombre,
            "sistema": "MTP",
            "tipo": TIPO_PORTATIL,
            "descripcion": DESCRIPCIONES[TIPO_PORTATIL],
            "total": 0,
            "libre": 0,
        })
    return unidades


def detectar_unidades():'''

texto = texto.replace("def detectar_unidades():", NUEVO_PORTATIL, 1)

# ------------------------------------------- 4) todo se ofrece para escanear
NUEVO_ES_INTERNA = '''def es_interna(unidad):
    """4. True si la unidad es interna (sirve para la etiqueta de la tabla)."""
    return unidad.get("tipo") in (TIPO_LOCAL, TIPO_RED)


def es_seleccionable(unidad):
    """
    4. Se ofrecen para escanear TODAS las unidades que ve la PC:
    internas, USB, discos externos, unidades de red, telefonos y tablets.
    """
    return bool(unidad.get("ruta"))
'''
texto = reemplazar("es_interna", NUEVO_ES_INTERNA, texto)

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(texto)

import ast
ast.parse(io.open(RUTA, encoding="utf-8").read())
print("escaneo.py actualizado, sintaxis OK")