# -*- coding: utf-8 -*-
"""
QBASWING COVERS v1.0
QBASwing Designer

Recorre los discos de la PC, encuentra carpetas con video y descarga
el poster oficial. Todo el trabajo se hace en el navegador local
(http://localhost:8080). No borra nada. No sobrescribe nada.

Este archivo es el punto de entrada. La logica esta en modulos aparte:
    i18n.py         Diccionario de traducciones ES / EN
    servidor.py     Servidor web local y toda la interfaz
    escaneo.py      Reglas de escaneo de carpetas
    fuentes.py      Cliente de las 5 APIs de posters
    posters.py      Limpieza de nombres, anio, temporada y puntuacion
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
import webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer

# Algunas instalaciones de Python (con archivo python3xx._pth) no anaden la
# carpeta del script a sys.path. Se hace aqui, antes de importar los modulos
# propios, para que el programa arranque siempre desde su propia carpeta.
if not getattr(sys, "frozen", False):
    _AQUI = os.path.dirname(os.path.abspath(__file__))
    if _AQUI not in sys.path:
        sys.path.insert(0, _AQUI)

import rutas

BASE_DIR = rutas.base_dir()

APP_NAME = "QBASWING COVERS"
APP_VERSION = "1.0"
SLOGAN_ES = "Cada coleccion merece su portada"
SLOGAN_EN = "Every collection deserves its cover"

PUERTO_INICIAL = 8080
PUERTO_MAXIMO = 8099


def elegir_puerto(inicial=PUERTO_INICIAL, maximo=PUERTO_MAXIMO):
    """Primer puerto libre en localhost, desde 8080 hacia arriba."""
    for puerto in range(inicial, maximo + 1):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", puerto))
            s.close()
            return puerto
        except OSError:
            continue
    return None


def _clave_valida(clave):
    """Las claves TMDB v3 tienen 32 caracteres hexadecimales."""
    return (isinstance(clave, str) and len(clave) == 32
            and all(c in "0123456789abcdefABCDEF" for c in clave))


def cargar_config():
    ruta = BASE_DIR / "config.json"
    defecto = {
        "tmdb_api_key": "",
        "tmdb_api_url": "https://api.themoviedb.org/3/",
        "usar_tmdb": True,
        "idioma": "es",
        "tipos": [],
        "unidades": [],
    }
    # El archivo manda, pero solo si esta bien formado: lo que le falte
    # se completa con el valor por defecto.
    if ruta.exists():
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
            if isinstance(datos, dict):
                defecto.update(datos)
        except Exception:
            pass
    # La clave TMDB NO va en el codigo: vive solo en config.json, un
    # archivo local que no se sube al repositorio. Una clave ausente
    # o corrupta (p. ej. "x" escrita por un archivo de pruebas) se
    # deja vacia y la interfaz avisa con "Clave de TMDB no valida".
    if not _clave_valida(defecto.get("tmdb_api_key")):
        defecto["tmdb_api_key"] = ""
    return defecto


def guardar_config(cfg):
    ruta = BASE_DIR / "config.json"
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        print("No se pudo guardar config: %s" % exc)


def log(mensaje, nivel="INFO"):
    """Escribe en qbawing_covers.log y muestra en la terminal."""
    from datetime import datetime
    sello = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = "[%s] %-7s %s" % (sello, nivel, mensaje)
    try:
        with open(BASE_DIR / "qbawing_covers.log", "a", encoding="utf-8") as f:
            f.write(linea + "\n")
    except Exception:
        pass
    color = ""
    reset = ""
    if nivel == "ERROR":
        color = "\033[38;5;196m"
    elif nivel == "OK":
        color = "\033[38;5;39m"
    elif nivel == "INFO":
        color = "\033[38;5;117m"
    try:
        if sys.stdout.isatty():
            print(color + linea + reset)
        else:
            print(linea)
    except UnicodeEncodeError:
        print(linea.encode("ascii", "replace").decode("ascii"))


def mostrar_cabecera():
    ancho = 72
    print()
    print("\033[38;5;33m" + "=" * ancho + "\033[0m")
    print("\033[1m\033[38;5;33m" + APP_NAME + " v" + APP_VERSION + "\033[0m")
    print("\033[38;5;117m" + SLOGAN_ES + "\033[0m")
    print("\033[38;5;33m" + "=" * ancho + "\033[0m")
    print("\033[38;5;245m" + "Un producto de QBASwing Designer" + "\033[0m")
    print("\033[38;5;245m" + "Todos los derechos reservados (c) 2026" + "\033[0m")
    print()


def diagnostico():
    """Comprueba que todo lo necesario esta en su sitio. No abre nada."""
    print()
    print("  QBASWING COVERS - diagnostico")
    print("  " + "-" * 40)
    problemas = []

    print("  Python:      %s" % sys.version.split()[0])
    print("  Empaquetado: %s" % ("si" if getattr(sys, "frozen", False)
                                 else "no (corriendo como .py)"))

    import rutas
    base = rutas.base_dir()
    print("  Carpeta de datos: %s" % base)
    try:
        prueba = base / ".escritura-prueba"
        with open(prueba, "w", encoding="utf-8") as f:
            f.write("ok")
        prueba.unlink()
        print("  Escritura:   OK")
    except Exception as exc:
        problemas.append("No se puede escribir en la carpeta: %s" % exc)

    logo = rutas.recurso("logo-qbaswing.png")
    if logo.exists():
        print("  Logo:        %s" % logo)
    else:
        print("  Logo:        no encontrado (se usara el texto)")

    try:
        cfg = cargar_config()
        print("  config.json: OK (idioma %s)" % cfg.get("idioma", "es"))
    except Exception as exc:
        problemas.append("config.json: %s" % exc)

    for nombre in ("i18n", "rutas", "posters", "escaneo", "fuentes",
                   "servidor"):
        try:
            __import__(nombre)
            print("  modulo %-9s OK" % nombre)
        except Exception as exc:
            problemas.append("modulo %s: %s" % (nombre, exc))

    try:
        import escaneo
        unidades = escaneo.detectar_unidades()
        print("  Unidades:    %d detectadas" % len(unidades))
    except Exception as exc:
        problemas.append("deteccion de unidades: %s" % exc)

    print("  " + "-" * 40)
    if problemas:
        print("  RESULTADO: con problemas")
        for p in problemas:
            print("   - %s" % p)
    else:
        print("  RESULTADO: TODO EN ORDEN")
    print()
    return 0 if not problemas else 1


def main():
    try:
        try:
            if os.name == "nt":
                os.system("")
            if sys.stdout.isatty():
                sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

        if "--check" in sys.argv or "--diagnostico" in sys.argv:
            sys.exit(diagnostico())

        cfg = cargar_config()
        mostrar_cabecera()

        # Importar los modulos del programa
        try:
            from servidor import ServidorGaleria
        except Exception as exc:
            log("No se pudo cargar el servidor: %s" % exc, "ERROR")
            print()
            print("  Revisa qbawing_covers.log para ver el detalle.")
            print()
            input("  Presiona Enter para salir...")
            return

        puerto = elegir_puerto()
        if puerto is None:
            log("No hay puertos libres en localhost", "ERROR")
            print("  No hay puertos libres disponibles.")
            input("  Presiona Enter para salir...")
            return

        url = "http://localhost:%d" % puerto
        log("Servidor local en %s" % url)

        servidor = ServidorGaleria(cfg, puerto)
        servidor.arrancar()

        print("  \033[38;5;39mAbre en el navegador:\033[0m %s" % url)
        if puerto != PUERTO_INICIAL:
            print("  \033[38;5;203mEl puerto %d esta ocupado, se uso el %d.\033[0m"
                  % (PUERTO_INICIAL, puerto))
        print()
        print("  \033[38;5;245mLa terminal solo muestra el registro.")
        print("  Todo se elige con clic en el navegador.\033[0m")
        print()
        print("  \033[38;5;240mPara detenerlo: Ctrl+C o cierra esta ventana.\033[0m")
        print()

        # Se abre en modo aplicacion, sin pestanas ni barra de
        # direcciones, y con la ventana al tamano de la pantalla. Asi
        # el programa se ve como lo que es: una aplicacion de escritorio.
        try:
            import pantalla
            como = pantalla.abrir(url)
        except Exception:
            como = "nada"
            try:
                webbrowser.open(url, new=1, autoraise=True)
                como = "pestana"
            except Exception:
                pass

        if como == "app":
            ancho, alto = pantalla.tamano_pantalla()
            print("  \033[38;5;39mVentana abierta a pantalla completa:\033[0m "
                  "%dx%d px" % (ancho, alto))

        servidor.esperar()

    except KeyboardInterrupt:
        print()
        print("  \033[38;5;33mPrograma detenido.\033[0m")
    except Exception as exc:
        log("Error general: %s" % exc, "ERROR")
        print()
        print("  Ocurrio un error. Revisa qbawing_covers.log")
        input("  Presiona Enter para salir...")


if __name__ == "__main__":
    main()