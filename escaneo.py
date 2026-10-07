# -*- coding: utf-8 -*-
"""
QBASWING COVERS - Escaneo de carpetas.

Reglas del documento de especificacion, seccion 5.
Solo lectura: este modulo nunca borra, mueve ni modifica archivos.
"""

import os
import string
import shutil
import subprocess
import json
import threading

import rutas

try:
    import mtp
except Exception:      # sin soporte MTP
    mtp = None

MIN_VIDEO_SIZE = 10 * 1024 * 1024         # 5.3 - 10 MB (lo pidio el usuario)
PROFUNDIDAD_MAXIMA = 8                     # 5.6
PROFUNDIDAD_BUSQUEDA_VIDEO = 3             # busca video hasta 3 niveles
MIN_POSTER_SIZE = 8 * 1024                 # una imagen menor no es poster

VIDEO_EXTENSIONS = {
    ".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
    ".mpg", ".mpeg", ".m2ts", ".ts", ".vob", ".rmvb", ".rm", ".3gp",
    ".divx", ".asf", ".ogv", ".f4v", ".mts", ".m2v", ".dat",
}

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif", ".jfif",
}

# 5.4-bis Archivos que jamas son un poster.
NO_ES_POSTER = {"thumbs.db", "desktop.ini", "ehthumbs.db", "folder.jpg.tmp"}

# Carpetas tipicas de miniaturas: lo que hay dentro no es el poster.
CARPETAS_NO_POSTER = {
    "thumbs", "thumbnails", "thumbsdb", "sample", "samples",
    "capturas", "screenshots", "wallpapers", "extras", "$recycle.bin",
}

# Nombres que delatan un poster real.
POSTER_FAVORITOS = {
    "cover", "poster", "folder", "caratula", "portada", "front",
    "movie", "serie", "album", "book", "libro", "capa",
}

# 5.5 Carpetas excluidas del escaneo.
EXCLUIDAS = {
    "$recycle.bin", "system volume information", "windows", "$windows.~bt",
    "$windows.~ws", "program files", "program files (x86)", "programdata",
    "appdata", "recovery", "perflogs", "config.msi", "msocache",
    "node_modules", ".git", ".svn", "__pycache__", ".cache", ".vscode",
}

TIPO_LOCAL = "local"
TIPO_REMOVIBLE = "removible"
TIPO_RED = "red"
TIPO_CD = "cd"
TIPO_PORTATIL = "portatil"

DESCRIPCIONES = {
    TIPO_LOCAL: "Disco local",
    TIPO_REMOVIBLE: "Unidad extraible",
    TIPO_RED: "Unidad de red",
    TIPO_CD: "Unidad CD/DVD",
    TIPO_PORTATIL: "Telefono o tablet (MTP)",
}


def _programa_dir():
    return str(rutas.base_dir())


def es_mtp(ruta):
    """True si la ruta apunta a un telefono o tablet (mtp://...)."""
    if mtp is None or not ruta:
        return False
    try:
        return bool(mtp.es_ruta_mtp(ruta))
    except Exception:
        return False


def es_excluida(nombre):
    """5.5 True si la carpeta no debe escanearse."""
    n = (nombre or "").strip().lower()
    if n in EXCLUIDAS:
        return True
    return False


def _es_la_propia_carpeta(ruta):
    """5.5 No escanear la carpeta donde vive el programa."""
    try:
        return os.path.normcase(os.path.abspath(ruta)) == \
               os.path.normcase(_programa_dir())
    except Exception:
        return False


# --------------------------------------------------------------------------
# 4. Deteccion de unidades
# --------------------------------------------------------------------------

def _unidades_windows_wmi():
    comando = [
        "powershell", "-NoProfile", "-NonInteractive", "-Command",
        "Get-CimInstance Win32_LogicalDisk | "
        "Select-Object DeviceID,VolumeName,DriveType,FileSystem,Size,FreeSpace | "
        "ConvertTo-Json -Compress",
    ]
    try:
        salida = subprocess.check_output(
            comando, stderr=subprocess.DEVNULL, timeout=30)
    except Exception:
        return None

    texto = salida.decode("utf-8", "replace").strip()
    if not texto:
        return None
    try:
        datos = json.loads(texto)
    except ValueError:
        return None
    if isinstance(datos, dict):
        datos = [datos]

    tipos = {
        2: TIPO_REMOVIBLE,
        3: TIPO_LOCAL,
        4: TIPO_RED,
        5: TIPO_CD,
        6: TIPO_LOCAL,
    }

    unidades = []
    for d in datos:
        letra = (d.get("DeviceID") or "").strip()
        if not letra:
            continue
        ruta = letra if letra.endswith("\\") else letra + "\\"

        try:
            tipo = tipos.get(d.get("DriveType"), TIPO_LOCAL)
        except Exception:
            tipo = TIPO_LOCAL

        try:
            total = int(d.get("Size") or 0)
            libre = int(d.get("FreeSpace") or 0)
        except (TypeError, ValueError):
            total = libre = 0

        if not total:
            try:
                uso = shutil.disk_usage(ruta)
                total, libre = uso.total, uso.free
            except Exception:
                pass

        unidades.append({
            "ruta": ruta,
            "etiqueta": (d.get("VolumeName") or "").strip(),
            "sistema": (d.get("FileSystem") or "").strip(),
            "tipo": tipo,
            "descripcion": DESCRIPCIONES.get(tipo, "Disco local"),
            "total": total,
            "libre": libre,
        })
    return unidades or None


def _unidades_fallback():
    """Sin WMI: recorre A: hasta Z:."""
    unidades = []
    for letra in string.ascii_uppercase:
        raiz = "%s:\\" % letra
        if not os.path.exists(raiz):
            continue
        try:
            uso = shutil.disk_usage(raiz)
        except Exception:
            continue
        unidades.append({
            "ruta": raiz,
            "etiqueta": "",
            "sistema": "",
            "tipo": TIPO_LOCAL,
            "descripcion": DESCRIPCIONES[TIPO_LOCAL],
            "total": uso.total,
            "libre": uso.free,
        })
    return unidades


def _unidades_portatiles():
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


def detectar_unidades():
    """4. Lista todas las unidades que ve la PC. Sin cantidades fijas."""
    if os.name == "nt":
        unidades = _unidades_windows_wmi()
        if not unidades:
            unidades = _unidades_fallback()
    else:
        unidades = []
        for base in ("/",):
            try:
                uso = shutil.disk_usage(base)
                unidades.append({
                    "ruta": base,
                    "etiqueta": "/",
                    "sistema": "",
                    "tipo": TIPO_LOCAL,
                    "descripcion": "Disco local",
                    "total": uso.total,
                    "libre": uso.free,
                })
            except Exception:
                pass
        for base in ("/mnt", "/media", "/Volumes"):
            if os.path.isdir(base):
                try:
                    for nombre in os.listdir(base):
                        ruta = os.path.join(base, nombre)
                        if os.path.isdir(ruta):
                            uso = shutil.disk_usage(ruta)
                            unidades.append({
                                "ruta": ruta,
                                "etiqueta": nombre,
                                "sistema": "",
                                "tipo": TIPO_REMOVIBLE,
                                "descripcion": DESCRIPCIONES[TIPO_REMOVIBLE],
                                "total": uso.total,
                                "libre": uso.free,
                            })
                except Exception:
                    pass
    unidades = [u for u in unidades if u.get("ruta")]
    unidades.extend(_unidades_portatiles())
    return unidades


def es_interna(unidad):
    """4. True si la unidad es interna (sirve para la etiqueta de la tabla)."""
    return unidad.get("tipo") in (TIPO_LOCAL, TIPO_RED)


def es_seleccionable(unidad):
    """
    4. Se ofrecen para escanear TODAS las unidades que ve la PC:
    internas, USB, discos externos, unidades de red, telefonos y tablets.
    """
    return bool(unidad.get("ruta"))


# --------------------------------------------------------------------------
# 5. Reglas de escaneo
# --------------------------------------------------------------------------

def _es_video_valido(completa, nombre, minimo):
    """True si el archivo es un video de extension aceptada y 10 MB o mas."""
    if os.path.splitext(nombre)[1].lower() not in VIDEO_EXTENSIONS:
        return False
    try:
        return os.stat(completa).st_size >= minimo
    except OSError:
        return False


def video_directo(ruta, minimo=MIN_VIDEO_SIZE):
    """
    5.1 True si la MISMA carpeta contiene un video valido.
    Esta es la carpeta donde se va a escribir el poster.
    """
    try:
        with os.scandir(ruta) as entradas:
            for e in entradas:
                try:
                    if not e.is_file(follow_symlinks=False):
                        continue
                except OSError:
                    continue
                if _es_video_valido(e.path, e.name, minimo):
                    return True
    except Exception:
        return False
    return False


def videos_directos(ruta, minimo=MIN_VIDEO_SIZE):
    """Cantidad de videos validos de la MISMA carpeta."""
    total = 0
    try:
        with os.scandir(ruta) as entradas:
            for e in entradas:
                try:
                    if not e.is_file(follow_symlinks=False):
                        continue
                except OSError:
                    continue
                if _es_video_valido(e.path, e.name, minimo):
                    total += 1
    except Exception:
        return total
    return total


def tiene_video(ruta, minimo=MIN_VIDEO_SIZE,
                profundidad=PROFUNDIDAD_BUSQUEDA_VIDEO):
    """
    5.1 True si la carpeta tiene video, ya sea en ella misma o dentro de
    una subcarpeta (Series/Temporada 1/, Peliculas/BD/...).
    El poster se escribe siempre en la carpeta donde esta el video.
    """
    if video_directo(ruta, minimo):
        return True
    if profundidad <= 0:
        return False
    try:
        with os.scandir(ruta) as entradas:
            for e in entradas:
                try:
                    if not e.is_dir(follow_symlinks=False):
                        continue
                except OSError:
                    continue
                if es_excluida(e.name) or e.name.lower() in CARPETAS_NO_POSTER:
                    continue
                if tiene_video(e.path, minimo, profundidad - 1):
                    return True
    except Exception:
        return False
    return False


def _imagen_util(nombre, tamano):
    """True si el archivo de la entrada puede ser un poster."""
    bajo = nombre.lower()
    if bajo in NO_ES_POSTER:
        return False
    if os.path.splitext(bajo)[1] not in IMAGE_EXTENSIONS:
        return False
    try:
        return tamano >= MIN_POSTER_SIZE
    except (TypeError, OSError):
        return False


def _parece_poster(nombre):
    """True si el nombre es el de un poster (cover.jpg, poster.png...)."""
    return os.path.splitext((nombre or "").lower())[0] in POSTER_FAVORITOS


def tiene_imagen(ruta, profundidad=1, nivel=0):
    """
    5.4 True si hay una imagen utilizable como poster.
    No cuenta miniaturas de thumbs/, capturas pequenas ni thumbs.db.
    """
    try:
        with os.scandir(ruta) as entradas:
            for e in entradas:
                try:
                    if e.is_file(follow_symlinks=False):
                        try:
                            tam = e.stat(follow_symlinks=False).st_size
                        except OSError:
                            continue
                        if _imagen_util(e.name, tam):
                            return True
                    elif (e.is_dir(follow_symlinks=False) and nivel < profundidad
                            and e.name.lower() not in CARPETAS_NO_POSTER):
                        if tiene_imagen(e.path, profundidad, nivel + 1):
                            return True
                except OSError:
                    continue
    except Exception:
        return False
    return False


def contar_videos(ruta, minimo=MIN_VIDEO_SIZE):
    """Para las estadisticas del escaneo."""
    total = 0
    try:
        with os.scandir(ruta) as entradas:
            for e in entradas:
                try:
                    if e.is_file(follow_symlinks=False):
                        ext = os.path.splitext(e.name)[1].lower()
                        if ext in VIDEO_EXTENSIONS:
                            if e.stat(follow_symlinks=False).st_size >= minimo:
                                total += 1
                except OSError:
                    continue
    except Exception:
        return total
    return total


def imagen_existente(ruta_carpeta):
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


def _videos_validos(raiz, archivos, minimo=MIN_VIDEO_SIZE):
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


def _control_progreso(control, marcador, progreso):
    """
    Envuelve la funcion de progreso para que cada carpeta sea un punto de
    control: respeta la pausa, corta si se detiene y anota lo ya revisado.
    """
    def revisar(ruta):
        if control is not None:
            if not control.es_seguro():
                raise Detenido(control.estado())
            if control.es_pausado() and not control.espera():
                raise Detenido(control.estado())
        if marcador is not None:
            try:
                marcador.marcar(ruta)
            except Exception:
                pass
        if progreso is not None:
            progreso(ruta)
    return revisar


def escanear_unidad(ruta_unidad, progreso=None, control=None, marcador=None):
    """
    5. Recorre una unidad en solo lectura y devuelve las carpetas candidatas.

    5.1 Una carpeta es candidata cuando tiene el video EN ELLA MISMA.
    Si el video esta en una subcarpeta (Serie/Season 1/, Pelicula/BD/),
    la candidata es esa subcarpeta: el poster se escribe siempre en la
    carpeta donde esta el video.

    Un telefono o tablet (mtp://) se recorre con el metodo MTP, porque
    Windows no le asigna letra de unidad.

    control  : objeto Control. Permite pausar, seguir, detener y cancelar.
    marcador : objeto con .marcar(ruta) y .ya_visto(ruta). Permite no
               volver a revisar las carpetas que ya se miraon, para que un
               escaneo interrumpido siga donde se quedo.

    Si se detiene o se cancela, devuelve las candidatas que lleva hasta ese
    momento y no se pierde nada.
    """
    if es_mtp(ruta_unidad):
        fn = _control_progreso(control, marcador, progreso)
        try:
            # El control se le pasa tambien al proceso de PowerShell, para
            # que pausar, detener y cancelar corten el recorrido del
            # telefono en el momento y no cuando acabe solo.
            return mtp.escanear(ruta_unidad, progreso=fn, control=control)
        except Detenido:
            return []
        except Exception:
            return []

    encontradas = []
    raiz_propia = os.path.normcase(_programa_dir())
    fn = _control_progreso(control, marcador, progreso)

    if not os.path.isdir(ruta_unidad):
        return encontradas

    try:
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
                # 5.9 Al reanudar, no volver a bajar a carpetas ya revisadas.
                if marcador is not None and getattr(marcador, "prunar", False):
                    try:
                        if marcador.ya_visto(completa):
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
                # Una carpeta con video es una unidad: no se baja dentro.
                dirs[:] = []

            fn(raiz)
    except Detenido:
        return encontradas
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        return encontradas

    return encontradas


def formatear_bytes(num):
    """Para la tabla de unidades."""
    valor = float(num or 0)
    for unidad in ("B", "KB", "MB", "GB", "TB"):
        if valor < 1024 or unidad == "TB":
            if unidad == "B":
                return "%d %s" % (int(valor), unidad)
            return "%.1f %s" % (valor, unidad)
        valor /= 1024.0
    return "%.1f TB" % valor


# --------------------------------------------------------------------------
# 5.9 Controles del escaneo:  pausar / seguir / detener / cancelar
# --------------------------------------------------------------------------

class Detenido(Exception):
    """Se lanza para salir del recorrido cuando el usuario detiene o cancela."""


class Control(object):
    """
    Los botones del escaneo.

    es_seguro()          -> True mientras se puede seguir escaneando
    esperar()            -> si esta en pausa, espera a que le digan "seguir"
    estado()             -> "corriendo" | "pausado" | "detenido" | "cancelado"
    pausar() / seguir() / detener() / cancelar()
    """

    def __init__(self):
        self._pausa = threading.Event()      # puesto = hay que esperar
        self._parar = threading.Event()
        self._cancelar = threading.Event()

    # ---------------------------------------------------------- botones
    def pausar(self):
        self._pausa.set()

    def seguir(self):
        self._pausa.clear()
        self._parar.clear()

    def detener(self):
        """Se detiene el escaneo pero se guarda lo que ya se encontro."""
        self._parar.set()
        self._pausa.clear()

    def cancelar(self):
        """Se abandona el escaneo y se cierra la pantalla."""
        self._cancelar.set()
        self._parar.set()
        self._pausa.clear()

    # ---------------------------------------------------------- consultas
    def estado(self):
        if self._cancelar.is_set():
            return "cancelado"
        if self._parar.is_set():
            return "detenido"
        if self._pausa.is_set():
            return "pausado"
        return "corriendo"

    def es_pausado(self):
        return self._pausa.is_set()

    def terminado(self):
        return self._parar.is_set() or self._cancelar.is_set()

    def es_seguro(self):
        """False si el usuario detuvo o cancelo."""
        return not self.terminado()

    # ---------------------------------------------------------- espera
    def esperar(self, timeout_max=86400):
        """
        Si esta en pausa, espera a que el usuario pulse "seguir".
        Devuelve False si mientras tanto se detiene o se cancela.
        """
        if not self._pausa.is_set():
            return self.es_seguro()
        if self._pausa.wait(timeout_max):
            return self.es_seguro()
        return self.es_seguro()

    # Dos nombres para lo mismo. El recorrido llama a espera() y el
    # telefono llama a esperar(); si falta uno, la pausa revienta con
    # AttributeError y el escaneo se corta solo, que era el fallo.
    def espera(self, timeout_max=86400):
        return self.esperar(timeout_max)

    def punto_control(self):
        """
        Se llama antes de cada carpeta.
        Lanza Detenido si el usuario detuvo o cancelo.
        """
        if not self.es_seguro():
            raise Detenido(self.estado())
        if not self.espera():
            raise Detenido(self.estado())


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
