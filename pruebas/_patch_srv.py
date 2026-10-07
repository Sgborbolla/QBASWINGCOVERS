# -*- coding: utf-8 -*-
"""servidor.py - hace que las carpetas del telefono no revienten nada."""
import io
import re

RUTA = r"C:\QBASWING-COVERS\servidor.py"
texto = io.open(RUTA, encoding="utf-8").read()
cambios = []


def reemplazar(nombre, nuevo, exigir=True):
    global texto
    patron = re.compile(r"^def %s\(.*?(?=^def |^class |^# ---|\Z)" % nombre,
                        re.S | re.M)
    m = patron.search(texto)
    if not m:
        if exigir:
            raise SystemExit("NO SE ENCONTRO: %s" % nombre)
        return
    texto = texto[:m.start()] + nuevo.rstrip("\n") + "\n\n\n" + texto[m.end():]
    cambios.append("%s() actualizado" % nombre)


# ------------------------------------------------------------- import mtp
if "\nimport mtp\n" not in texto:
    texto = texto.replace("import escaneo\n",
                          "import escaneo\n\ntry:\n    import mtp\nexcept Exception:\n    mtp = None\n", 1)
    cambios.append("import mtp agregado")

# -------------------------------------------- 1) listar_subdirectorios
NUEVO_LISTAR = '''def listar_subdirectorios(ruta_actual):
    """Lee la carpeta y devuelve las subcarpetas reales de la ruta."""
    # Telefono o tablet: se listan por MTP, no hay letra de unidad.
    if escaneo.es_mtp(ruta_actual):
        salida = []
        try:
            encontradas = mtp.listar_subcarpetas(ruta_actual)
        except Exception:
            encontradas = []
        for s in encontradas:
            salida.append({
                "ruta": s["ruta"],
                "nombre": s["nombre"],
                "hijos": s.get("hijos", 0),
                "id": E.id_de(s["ruta"]),
                "estado": _estado_de_carpeta(s["ruta"]),
            })
        return salida

    try:
        entradas = sorted(os.scandir(ruta_actual), key=lambda e: e.name.lower())
    except Exception:
        return []

    salida = []
    for e in entradas:
        try:
            if not e.is_dir(follow_symlinks=False):
                continue
        except OSError:
            continue
        nombre = e.name
        if escaneo.es_excluida(nombre):
            continue
        try:
            hijos = sum(1 for h in os.scandir(e.path)
                        if h.is_dir(follow_symlinks=False))
        except Exception:
            hijos = 0
        salida.append({
            "ruta": e.path,
            "nombre": nombre,
            "hijos": hijos,
            "id": E.id_de(e.path),
            "estado": _estado_de_carpeta(e.path),
        })
    return salida'''
reemplazar("listar_subdirectorios", NUEVO_LISTAR)

# ------------------------------------------------- 2) _unidad_de_ruta
NUEVO_UNIDAD = '''def _unidad_de_ruta(ruta, unidades):
    if not ruta:
        return None

    # Telefonos: se comparan por prefijo mtp://<dispositivo>
    if escaneo.es_mtp(ruta):
        destino = str(ruta).lower().rstrip("/")
        mejor = None
        for unidad in unidades or []:
            raiz = str(unidad or "").lower().rstrip("/")
            if not raiz or not destino.startswith(raiz):
                continue
            if mejor is None or len(raiz) > len(mejor):
                mejor = unidad
        return mejor

    try:
        candidata = os.path.normcase(os.path.abspath(ruta))
    except (OSError, ValueError):
        return None
    coincidentes = []
    for unidad in unidades or []:
        try:
            raiz = os.path.normcase(os.path.abspath(unidad))
            if os.path.commonpath((raiz, candidata)) == raiz:
                coincidentes.append(unidad)
        except (OSError, ValueError, TypeError):
            continue
    return max(coincidentes, key=len) if coincidentes else None'''
reemplazar("_unidad_de_ruta", NUEVO_UNIDAD)

# ---------------------------------------------------- 3) _abrir_carpeta
NUEVO_ABRIR = '''def _abrir_carpeta(ruta):
    """Abre la carpeta en el explorador de Windows. Si no puede, no pasa nada."""
    # En un telefono se abre el dispositivo, que es lo que Windows entiende.
    if escaneo.es_mtp(ruta):
        try:
            import subprocess
            dispositivo, _partes = mtp.partir(ruta)
            subprocess.Popen(["explorer", mtp.unir(dispositivo, [])])
        except Exception:
            _log("No se pudo abrir el telefono: %s" % ruta, "ERROR")
        return
    try:
        os.startfile(ruta)          # noqa: F821  (solo Windows)
    except Exception:
        try:
            import subprocess
            subprocess.Popen(["explorer", ruta])
        except Exception:
            pass'''
reemplazar("_abrir_carpeta", NUEVO_ABRIR)

# --------------------------------------------------- 4) _descargar_una
NUEVO_DESCARGAR = '''def _descargar_una_mtp(c):
    """Descarga el poster en una carpeta de un telefono o tablet."""
    ruta = c["ruta"]
    try:
        est = mtp.estado_carpeta(ruta) or {}
    except Exception:
        est = {}
    if not est.get("carpeta"):
        return "fallo", 0
    if est.get("cover"):
        return "ya_existe", 0
    if est.get("imagenes"):
        return "ya_tiene_imagen", 0

    info = E.resultados.get(ruta) or {}
    url = info.get("poster_url")
    if not url:
        return "sin_poster", 0

    datos = fuentes.descargar_binario(url)
    if not datos:
        return "fallo", 0
    if len(datos) < MIN_POSTER_SIZE:
        return "fallo_pequeno", len(datos)

    ok, total = mtp.escribir_cover(ruta, datos)
    if not ok:
        return "fallo", total

    c["descargado"] = True
    c["ya_tiene"] = True
    E.guardar_estado(ruta, estado=DESCARGADO, marcada=0,
                     fuente=info.get("fuente", ""),
                     titulo=info.get("titulo", ""),
                     url_poster=url,
                     puntuacion=info.get("puntuacion", 0))
    _log("Descargado en el telefono: %s" % ruta, "OK")
    return "ok", len(datos)


def _descargar_una(c):
    """
    Descarga el poster de UNA carpeta.
    Devuelve (estado, tamano). Nunca sobrescribe ni borra nada.
    """
    ruta = c["ruta"]

    # Telefono o tablet: se escribe por MTP.
    if escaneo.es_mtp(ruta):
        return _descargar_una_mtp(c)

    destino = os.path.join(ruta, COVER_NAME)'''
m = re.search(r"^def _descargar_una\(.*?^    destino = os\.path\.join\(ruta, COVER_NAME\)",
              texto, re.S | re.M)
if not m:
    raise SystemExit("NO SE ENCONTRO _descargar_una")
texto = texto[:m.start()] + NUEVO_DESCARGAR.rstrip("\n") + texto[m.end():]
cambios.append("_descargar_una() con rama MTP")

# ------------------------- 5) se ofrecen TODAS las unidades para escanear
vIEJO = '        marcada = " checked" if interna else ""'
nuevo = '        marcada = " checked"'
if texto.count(vIEJO) == 1:
    texto = texto.replace(vIEJO, nuevo)
    cambios.append("todas las unidades salen marcadas para escanear")

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(texto)

import ast
ast.parse(io.open(RUTA, encoding="utf-8").read())
print("servidor.py parcheado:")
for c in cambios:
    print("   -", c)
print("   sintaxis OK")