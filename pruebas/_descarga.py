# -*- coding: utf-8 -*-
"""Verifica la descarga a Descargas\\QBASWING COVERS: escritura con el
nombre de la carpeta, rechazo por tamano y -- lo mas importante -- que
NUNCA escribe en el origen, NUNCA sobrescribe ni borra un archivo
existente ni deja restos de parcial."""
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

# Nada de lo real se toca: inventario, base de estado, carpeta de
# Descargas y el recuerdo de lo descargado apuntan a la carpeta
# temporal, que se borra al salir.
S.INVENTARIO = Path(os.path.join(raiz, "inventario.csv"))
S.DB_FILE = Path(os.path.join(raiz, "qbawing_covers.db"))
DESCARGAS = os.path.join(raiz, "Descargas")
_mapa = {}


def _carpeta_descargas_mentira(crear=True):
    if crear:
        try:
            os.makedirs(DESCARGAS, exist_ok=True)
        except OSError:
            return None
    return DESCARGAS


def _registrar_mentira(ruta, archivo):
    _mapa[ruta] = archivo
    return True


S._carpeta_descargas = _carpeta_descargas_mentira
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


def en_descargas(nombre):
    return os.path.join(DESCARGAS, nombre)


def vacia(c):
    """La carpeta de origen no tiene NADA: asi tiene que quedar siempre."""
    return not os.listdir(c["ruta"])


try:
    # 1. descarga normal: acaba en Descargas con el nombre de la carpeta
    #    y el origen NO recibe ni un byte.
    c1 = nueva("Normal", url + "/ok")
    estado, tam = S._descargar_una(c1)
    destino = en_descargas("Normal.jpg")
    check("descarga en Descargas con el nombre de la carpeta",
          estado == "ok" and os.path.isfile(destino) and tam == len(PNG_OK),
          (estado, tam))
    check("contenido intacto", open(destino, "rb").read() == PNG_OK)
    check("el origen queda vacio", vacia(c1))
    check("queda registrado en la base",
          S.base.descarga_de(c1["ruta"]) == "Normal.jpg", estado)

    # 2. nunca sobrescribe: se tacha el archivo descargado y se reintenta.
    marca = b"NO TOCAR"
    with open(destino, "wb") as f:
        f.write(marca)
    estado, tam = S._descargar_una(c1)
    check("no sobrescribe en Descargas", estado == "ya_existe"
          and open(destino, "rb").read() == marca, estado)

    # 3. imagen con otro nombre ya presente en el origen -> se respeta.
    c2 = nueva("Con Imagen", url + "/ok")
    with open(os.path.join(c2["ruta"], "poster.png"), "wb") as f:
        # Tiene que pesar como una imagen de verdad: por debajo de 8 KB
        # escaneo no la cuenta como poster de la carpeta.
        f.write(b"imagen del usuario" * 900)
    estado, _ = S._descargar_una(c2)
    check("respeta otra imagen", estado == "ya_tiene_imagen"
          and not os.path.exists(en_descargas("Con Imagen.jpg"))
          and os.path.isfile(os.path.join(c2["ruta"], "poster.png")),
          estado)

    # 4. poster de menos de 15 KB -> fallo, sin dejar basura.
    c3 = nueva("Chico", url + "/chico")
    estado, tam = S._descargar_una(c3)
    check("rechaza < 15 KB", estado == "fallo_pequeno"
          and not os.path.exists(en_descargas("Chico.jpg")) and vacia(c3),
          (estado, tam))

    # 5. sin coincidencia -> sin_poster, sin escribir nada.
    c4 = nueva("Sin match", None)
    estado, _ = S._descargar_una(c4)
    check("sin poster", estado == "sin_poster" and vacia(c4)
          and not os.path.exists(en_descargas("Sin match.jpg")), estado)

    # 6. fallo de red -> no rompe y no deja archivos.
    c5 = nueva("Caida", url + "/no-existe")
    estado, _ = S._descargar_una(c5)
    check("fallo de red controlado", estado == "fallo" and vacia(c5)
          and not os.path.exists(en_descargas("Caida.jpg")), estado)

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
          os.path.isfile(en_descargas("Seleccionada.jpg"))
          and open(en_descargas("Seleccionada.jpg"), "rb").read() == PNG_OK
          and not os.path.exists(en_descargas("Sin Marcar.jpg"))
          and vacia(c7) and vacia(c8))

    # 9. Dos carpetas con el mismo nombre -> la segunda lleva -2.
    c9 = nueva("Mismo", url + "/ok")
    c10 = nueva("Mismo", url + "/ok", ruta_rel=os.path.join("doble", "Mismo"))
    S._descargar_una(c9)
    S._descargar_una(c10)
    check("nombres repetidos con -2",
          os.path.isfile(en_descargas("Mismo.jpg"))
          and os.path.isfile(en_descargas("Mismo-2.jpg"))
          and S.base.descarga_de(c9["ruta"]) == "Mismo.jpg"
          and S.base.descarga_de(c10["ruta"]) == "Mismo-2.jpg")

    # 10. El programa recuerda lo descargado entre sesiones.
    check("recuerda lo ya descargado", S._ya_descargada(c1["ruta"]))
    #    Si borras el archivo, vuelve a pendiente y se rehace con el
    #    MISMO nombre (no acaba en un -2 fantasma).
    os.remove(destino)
    check("al borrarlo vuelve a ser pendiente",
          not S._ya_descargada(c1["ruta"]))
    estado, _ = S._descargar_una(c1)
    check("rehace con el mismo nombre", estado == "ok"
          and os.path.isfile(destino)
          and S.base.descarga_de(c1["ruta"]) == "Normal.jpg", estado)

    # 11. Carpeta generica (T1): el nombre lleva la serie delante.
    c11 = nueva("T1", url + "/ok",
                ruta_rel=os.path.join("Series", "One Piece", "T1"))
    estado, _ = S._descargar_una(c11)
    check("carpeta generica lleva la serie",
          estado == "ok" and os.path.isfile(en_descargas("One Piece T1.jpg"))
          and vacia(c11), estado)

    # 12. Descargas contiene exactamente lo esperado, sin restos.
    esperado = {"Normal.jpg", "Lote.jpg", "Seleccionada.jpg", "Mismo.jpg",
                "Mismo-2.jpg", "One Piece T1.jpg"}
    existentes = set(os.listdir(DESCARGAS))
    check("Descargas limpia y completa", existentes == esperado,
          existentes ^ esperado)
    check("sin restos de parcial",
          not [f for f in existentes if f.endswith(".qbawing-parcial")])

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
