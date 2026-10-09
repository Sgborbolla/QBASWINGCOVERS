# -*- coding: utf-8 -*-
"""Verifica la descarga del poster DENTRO de la carpeta del video:
escritura con el nombre de la carpeta, rechazo por tamano y -- lo mas
importante -- que NUNCA sobrescribe ni borra un archivo existente ni
deja restos de parcial."""
import os
import sys
import shutil
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

import escaneo
import servidor as S

PNG_OK = b"\xff\xd8\xff\xe0" + b"z" * 30000      # 30 KB, valido
PNG_CHICO = b"\xff\xd8\xff\xe0" + b"z" * 100     # 104 bytes, falla


class Fuente(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/ok":
            cuerpo, tipo = PNG_OK, "image/jpeg"
        elif self.path == "/chico":
            cuerpo, tipo = PNG_CHICO, "image/jpeg"
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


srv = ThreadingHTTPServer(("127.0.0.1", 0), Fuente)
srv.daemon_threads = True
puerto = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = "http://127.0.0.1:%d" % puerto

raiz = tempfile.mkdtemp(prefix="qbawing_desc_")

# Nada de lo real se toca: inventario, base de estado y el recuerdo de lo
# descargado apuntan a la carpeta temporal, que se borra al salir.
S.INVENTARIO = Path(os.path.join(raiz, "inventario.csv"))
S.DB_FILE = Path(os.path.join(raiz, "qbawing_covers.db"))
_mapa = {}


def _registrar_mentira(ruta, archivo):
    _mapa[ruta] = archivo
    return True


S.base.registrar_descarga = _registrar_mentira
S.base.descarga_de = lambda ruta: _mapa.get(ruta, "")
S._abrir_carpeta = lambda _ruta: None

cfg = {"idioma": "es", "tipos": [], "unidades": [], "tmdb_api_key": "x"}
S.E = S.Estado(cfg)
E = S.E

ok = []


def check(nombre, cond, detalle=""):
    assert cond, "%s  %s" % (nombre, detalle)
    ok.append(nombre)


def nueva(nombre, url_poster, ruta_rel=None):
    ruta = os.path.join(raiz, ruta_rel or nombre)
    os.makedirs(ruta, exist_ok=True)
    c = {"ruta": ruta, "nombre": nombre, "unidad": raiz, "ya_tiene": False,
         "imagen_existente": "", "videos": 1, "anio": None, "temporada": None,
         "titulo": nombre, "tipo": "pelicula", "descargado": False}
    E.carpetas.append(c)
    E.resultados[ruta] = {"titulo": nombre, "ano": 2020, "tipo": "pelicula",
                          "fuente": "TMDB", "poster_url": url_poster,
                          "id": 1, "puntuacion": 90, "candidatos": []}
    return c


def en_carpeta(c, nombre):
    return os.path.join(c["ruta"], nombre)


def vacia(c):
    """La carpeta de origen no tiene NINGUN archivo nuevo."""
    return not os.listdir(c["ruta"])


def recoger_parciales(d):
    total = []
    for nombre in os.listdir(d):
        hijo = os.path.join(d, nombre)
        if os.path.isdir(hijo):
            total += recoger_parciales(hijo)
        elif nombre.endswith(".qbawing-parcial"):
            total.append(hijo)
    return total


try:
    # 1. descarga normal: acaba DENTRO de la carpeta con su mismo nombre.
    c1 = nueva("Normal", url + "/ok")
    estado, tam = S._descargar_una(c1)
    destino = en_carpeta(c1, "Normal.jpg")
    check("descarga dentro de la carpeta con su mismo nombre",
          estado == "ok" and os.path.isfile(destino) and tam == len(PNG_OK),
          (estado, tam))
    check("contenido intacto", open(destino, "rb").read() == PNG_OK)
    check("queda registrado en la base",
          S.base.descarga_de(c1["ruta"]) == "Normal.jpg", estado)

    # 2. nunca sobrescribe: se tacha el archivo descargado y se reintenta.
    #    Al estar el nombre ocupado, el nuevo queda como -2 y el tuyo se salva.
    marca = b"NO TOCAR"
    with open(destino, "wb") as f:
        f.write(marca)
    estado, tam = S._descargar_una(c1)
    check("no sobrescribe: respeta tu archivo y usa -2",
          estado == "ok"
          and open(destino, "rb").read() == marca
          and os.path.isfile(en_carpeta(c1, "Normal-2.jpg")), estado)

    # 3. imagen con otro nombre ya presente en el origen -> se respeta.
    c2 = nueva("Con Imagen", url + "/ok")
    with open(os.path.join(c2["ruta"], "poster.png"), "wb") as f:
        # Tiene que pesar como una imagen de verdad: por debajo de 8 KB
        # escaneo no la cuenta como poster de la carpeta.
        f.write(b"imagen del usuario" * 900)
    estado, _ = S._descargar_una(c2)
    check("respeta otra imagen", estado == "ya_tiene_imagen"
          and os.listdir(c2["ruta"]) == ["poster.png"], estado)

    # 4. poster de menos de 15 KB -> fallo, sin dejar basura.
    c3 = nueva("Chico", url + "/chico")
    estado, tam = S._descargar_una(c3)
    check("rechaza < 15 KB", estado == "fallo_pequeno" and vacia(c3),
          (estado, tam))

    # 5. sin coincidencia -> sin_poster, sin escribir nada.
    c4 = nueva("Sin match", None)
    estado, _ = S._descargar_una(c4)
    check("sin poster", estado == "sin_poster" and vacia(c4), estado)

    # 6. fallo de red -> no rompe y no deja archivos.
    c5 = nueva("Caida", url + "/no-existe")
    estado, _ = S._descargar_una(c5)
    check("fallo de red controlado", estado == "fallo" and vacia(c5), estado)

    # 7. resumen completo con el hilo de descarga.
    c6 = nueva("Lote", url + "/ok")
    E.progreso = {"activo": False, "hechos": 0, "total": 0, "texto": "",
                  "listo": False}
    S._hilo_descarga([c1, c3, c5, c6], "lote")
    check("hilo de descarga", E.resumen["descargados"] == 1
          and E.resumen["ya_tenian"] >= 1, E.resumen)
    check("inventario escrito", S.INVENTARIO.exists())

    # 8. Descargar solo en las carpetas marcadas.
    c7 = nueva("Seleccionada", url + "/ok")
    # Otra carpeta que NO esta marcada: no debe tocarla.
    c8 = nueva("Sin Marcar", url + "/ok")
    E.marcadas = {c7["ruta"]}
    seleccion = [c for c in E.carpetas if c["ruta"] in E.marcadas]
    S._hilo_descarga(seleccion, "seleccion")
    check("poster guardado solo en la seleccionada",
          os.path.isfile(en_carpeta(c7, "Seleccionada.jpg"))
          and open(en_carpeta(c7, "Seleccionada.jpg"), "rb").read() == PNG_OK
          and vacia(c8))

    # 9. Dos carpetas con el mismo nombre: cada una guarda el suyo en su
    #    propia carpeta, sin colisiones (-2 no hace falta).
    c9 = nueva("Mismo", url + "/ok")
    c10 = nueva("Mismo", url + "/ok", ruta_rel=os.path.join("doble", "Mismo"))
    S._descargar_una(c9)
    S._descargar_una(c10)
    check("mismo nombre en cada carpeta",
          os.path.isfile(en_carpeta(c9, "Mismo.jpg"))
          and os.path.isfile(en_carpeta(c10, "Mismo.jpg"))
          and S.base.descarga_de(c9["ruta"]) == "Mismo.jpg"
          and S.base.descarga_de(c10["ruta"]) == "Mismo.jpg")

    # 10. El programa recuerda lo descargado entre sesiones.
    check("recuerda lo ya descargado", S._ya_descargada(c6["ruta"]))
    #    Si borras el archivo, vuelve a pendiente y se rehace con el
    #    MISMO nombre (no acaba en un -2 fantasma).
    destino_lote = en_carpeta(c6, "Lote.jpg")
    os.remove(destino_lote)
    check("al borrarlo vuelve a ser pendiente",
          not S._ya_descargada(c6["ruta"]))
    estado, _ = S._descargar_una(c6)
    check("rehace con su mismo nombre", estado == "ok"
          and os.path.isfile(destino_lote)
          and S.base.descarga_de(c6["ruta"]) == "Lote.jpg", estado)

    # 11. Nombre generico (T1): se usa el nombre de la carpeta tal cual.
    c11 = nueva("T1", url + "/ok",
                ruta_rel=os.path.join("Series", "One Piece", "T1"))
    estado, _ = S._descargar_una(c11)
    check("usa el nombre de la carpeta tal cual", estado == "ok"
          and os.path.isfile(en_carpeta(c11, "T1.jpg")), estado)

    # 12. Ningun resto de parcial en todo el arbol.
    check("sin restos de parcial", not recoger_parciales(raiz))

finally:
    srv.shutdown()
    srv.server_close()
    # La base de mentira queda abierta por el hilo de descarga: sin
    # cerrarla, el .db no se puede borrar y dejaria basura en %TEMP%.
    try:
        E._db.close()
    except Exception:
        pass
    # La carpeta temporal de mentira no se queda en %TEMP%.
    try:
        shutil.rmtree(raiz, ignore_errors=True)
    except Exception:
        pass

print("DESCARGA OK:", ", ".join(ok))
print("TOTAL:", len(ok), "pruebas de escritura segura")