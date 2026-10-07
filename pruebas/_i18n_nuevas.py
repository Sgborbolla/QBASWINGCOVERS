# -*- coding: utf-8 -*-
"""Agrega a i18n.py las claves de la portada, los controles y el cierre."""
import ast
import io
import re

RUTA = r"C:\QBASWING-COVERS\i18n.py"
t = io.open(RUTA, encoding="utf-8").read()

existentes = set(re.findall(r'["\']([a-zA-Z0-9_]+)["\']\s*:\s*\{\s*["\']es', t))

NUEVAS = {
    # ---------------------------------------------------- portada
    "portada_titulo_1": ("QBASWING COVERS", "QBASWING COVERS"),
    "portada_titulo_2": ("Cada coleccion merece su portada",
                         "Every collection deserves its cover"),
    "portada_sub": ("Escanea tus discos, tu telefono y tus unidades extraibles, "
                    "y ponle el poster oficial a cada pelicula, serie, anime "
                    "y telenovela que aun no lo tiene.",
                    "Scans your disks, your phone and your removable drives, and "
                    "puts the official cover on every movie, series, anime and "
                    "telenovela that does not have one yet."),
    "btn_escanear_ya": ("ESCAVEAR AHORA", "SCAN NOW"),
    "btn_seguir_escaneo": ("Continuar el escaneo anterior",
                           "Continue the previous scan"),
    "portada_t1_titulo": ("Ve tus carpetas como el Explorador de Windows",
                          "Your folders like Windows Explorer"),
    "portada_t1_texto": ("Iconos de carpeta reales, caratulas reales y "
                         "navegacion con clic, sin escribir nada.",
                         "Real folder icons, real covers and click navigation, "
                         "without typing anything."),
    "portada_t2_titulo": ("El poster va donde esta el video",
                          "The cover goes where the video is"),
    "portada_t2_texto": ("La carpeta de cada temporada y cada capitulo recibe "
                         "su propia caratula. No se toca ningun archivo tuyo.",
                         "The folder of each season and each episode gets its "
                         "own cover. None of your files are touched."),
    "portada_t3_titulo": ("Discos, USB y telefono",
                          "Disks, USB drives and phones"),
    "portada_t3_texto": ("Ve los discos internos, los externos, las unidades "
                         "de red y los celulares conectados por cable.",
                         "See internal disks, external drives, network units "
                         "and phones connected by cable."),
    "portada_demo_titulo": ("Asi se ve tu coleccion",
                            "This is how your collection looks"),
    "portada_demo_texto": ("Carga real de peliculas, series y animes.",
                           "Real movie, series and anime artwork."),
    "portada_cifra_carpetas": ("carpetas con video", "folders with video"),
    "portada_cifra_posters": ("carpetas con poster", "folders with a cover"),
    "portada_cifra_descargados": ("posters descargados", "covers downloaded"),
    "aviso_tmdb": ("This product uses the TMDB API but is not endorsed or "
                   "certified by TMDB.",
                   "This product uses the TMDB API but is not endorsed or "
                   "certified by TMDB."),
    "portada_pie": ("Los posters de la portada se consultan a TMDB, AniList y "
                    "otras fuentes publicas. Se guardan en cache y el programa "
                    "sigue funcionando sin internet.",
                    "The covers on this page come from TMDB, AniList and other "
                    "public sources. They are cached and the program keeps "
                    "working without internet."),

    # --------------------------------------------------- escaneo
    "msg_escaneando_ruta": ("Escaneando %s", "Scanning %s"),
    "msg_escaneo_listo": ("Escaneo terminado: %d carpetas con video.",
                          "Scan finished: %d folders with video."),
    "msg_escaneo_pausado": ("Escaneo pausado con %d carpetas encontradas. "
                            "Puedes continuarlo cuando quieras.",
                            "Scan paused with %d folders found. You can "
                            "continue it whenever you want."),
    "msg_escaneo_detenido": ("Escaneo detenido con %d carpetas encontradas. "
                             "Puedes continuarlo donde se quedo.",
                             "Scan stopped with %d folders found. You can "
                             "continue it where it stopped."),
    "msg_escaneo_error": ("El escaneo se detuvo por un error. Revisa el archivo "
                          "qbawing_covers.log.",
                          "The scan stopped because of an error. Check the "
                          "qbawing_covers.log file."),
    "btn_pausar": ("Pausar", "Pause"),
    "btn_seguir": ("Continuar", "Resume"),
    "btn_detener": ("Detener", "Stop"),
    "btn_cancelar": ("Cancelar", "Cancel"),
    "btn_reanudar": ("Continuar el escaneo anterior",
                     "Continue the previous scan"),
    "aviso_telefono_lento": ("Los telefonos van mas lento que los discos. Si "
                             "aparece algo raro, el telefono esta notifying: "
                             "desconecta el cable y vuelve a conectarlo.",
                             "Phones are slower than disks. If something odd "
                             "appears, the phone is probably busy: unplug the "
                             "cable and plug it back in."),

    # ----------------------------------------------------- cierre
    "btn_cerrar": ("Cerrar", "Close"),
    "btn_cerrar_ayuda": ("Cerrar el programa por completo, servidor incluido",
                         "Close the whole program, server included"),
    "msg_cerrar_confirmar": ("¿Cerrar QBASWING COVERS? Se apagara el servidor "
                             "y la ventana del programa. Lo que ya descargaste "
                             "se queda donde esta.",
                             "Close QBASWING COVERS? The server and the program "
                             "window will close. Everything you already "
                             "downloaded stays where it is."),
    "titulo_cerrado": ("Programa cerrado", "Program closed"),
    "msg_cerrado_nota": ("Ya puedes cerrar esta pestana del navegador.",
                         "You can close this browser tab now."),
    "msg_cerrando": ("Cerrando el programa...", "Closing the program..."),
}

faltan = [(k, v) for k, v in NUEVAS.items() if k not in existentes]
if not faltan:
    print("Las claves ya estaban todas.")
    raise SystemExit(0)

lineas = "".join(
    '    "%s": {"es": %r, "en": %r},\n' % (k, v[0], v[1]) for k, v in faltan)

# Se meten justo despues de la apertura del diccionario.
m = re.search(r"^I18N\s*=\s*\{", t, re.M)
if not m:
    raise SystemExit("no se encontro el diccionario")
corte = t.index("\n", t.index("{", m.start())) + 1
t = t[:corte] + lineas + t[corte:]

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(t)
ast.parse(t)

print("Claves agregadas a i18n.py (%d):" % len(faltan))
for k, _v in faltan:
    print("   -", k)
print("sintaxis OK")