# -*- coding: utf-8 -*-
"""
QBASWING COVERS - Abrir el programa a pantalla completa.

El programa se maneja desde el navegador. Para que se vea como una
aplicacion de escritorio y no como una pagina mas, se abre el navegador
en MODO APLICACION: sin pestanas, sin barra de direcciones y con la
ventana puesta justo en el tamano de la pantalla.

Si el navegador en modo aplicacion no se encuentra, se cae a la via
normal (una pestana) y el boton de pantalla completa de la barra
sigue estando ahi.
"""
import os
import subprocess
import sys
import webbrowser

# Rutas habituales de los navegadores de Windows 7, 8, 10 y 11.
_RELATIVOS = (
    r"Microsoft\Edge\Application\msedge.exe",
    r"Google\Chrome\Application\chrome.exe",
    r"BraveSoftware\Brave-Browser\Application\brave.exe",
    r"Opera\launcher.exe",
    r"Vivaldi\Application\vivaldi.exe",
    r"Mozilla Firefox\firefox.exe",
)

# Firefox no entiende --app, asi que no sirve para esto.
_SIN_APP = ("firefox.exe",)

# Las carpetas de donde se buscan los navegadores.
_CARPETAS = ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")


def tamano_pantalla():
    """
    (ancho, alto) en pixeles de la pantalla principal.

    En Windows se pregunta a la API de verdad. Si no se puede, se
    devuelve un tamano de pantalla grande y el navegador se maximiza
    solo, que tambien queda bien.
    """
    try:
        if os.name == "nt":
            import ctypes
            ancho = ctypes.windll.user32.GetSystemMetrics(0)
            alto = ctypes.windll.user32.GetSystemMetrics(1)
            if ancho > 800 and alto > 600:
                return int(ancho), int(alto)
    except Exception:
        pass
    return 1920, 1080


def buscar_navegador():
    """Ruta del primer navegador que admita el modo aplicacion."""
    override = os.environ.get("QBASWING_NAVEGADOR")
    if override and os.path.isfile(override):
        return override

    for var in _CARPETAS:
        base = os.environ.get(var)
        if not base:
            continue
        for relativo in _RELATIVOS:
            nombre = os.path.basename(relativo)
            if nombre.lower() in _SIN_APP:
                continue
            ruta = os.path.join(base, relativo)
            if os.path.isfile(ruta):
                return ruta

    # Chrome y Edge se pueden instalar en la carpeta del usuario.
    perfil = os.environ.get("LOCALAPPDATA")
    if perfil:
        for carpeta in ("Google\\Chrome\\Application\\chrome.exe",
                        "Microsoft\\Edge\\Application\\msedge.exe"):
            ruta = os.path.join(perfil, carpeta)
            if os.path.isfile(ruta):
                return ruta
    return None


def abrir(url):
    """
    Abre el programa. Devuelve 'app' si salio en modo aplicacion a
    pantalla completa, 'pestana' si se abierto en una pestana normal, o
    'nada' si no se pudo abrir de ninguna manera.
    """
    ruta = buscar_navegador()
    if ruta:
        ancho, alto = tamano_pantalla()
        # Se deja el alto en casi toda la pantalla para que se vea la
        # barra de tareas, que es donde se cambia de ventana.
        args = [
            ruta,
            "--app=%s" % url,
            "--window-position=0,0",
            "--window-size=%d,%d" % (ancho, max(alto - 60, 600)),
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=Translate,TranslateUI",
            # Que no salga el cartelito de "estoy en modo pruebas".
            "--test-type",
        ]
        try:
            subprocess.Popen(args, close_fds=True)
            return "app"
        except Exception:
            pass

    try:
        # new=1: reutiliza la pestana actual, no apila ventanas.
        webbrowser.open(url, new=1, autoraise=True)
        return "pestana"
    except Exception:
        return "nada"