# -*- coding: utf-8 -*-
"""Prueba de rutas HTTP. Puerto efimero, se apaga sola. Sin navegador."""
import atexit
import os
import sys
import json
import tempfile
import threading
import time
import shutil
from pathlib import Path
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

import escaneo
import servidor as S
import qbaswing_covers

# El config real del proyecto NO se toca: las rutas /paso2 y /?lang=
# llaman a guardar_config y escribirian en el config.json de verdad
# (asi se contaminaron la clave y el idioma del proyecto).
qbaswing_covers.guardar_config = lambda cfg: None

raiz = tempfile.mkdtemp(prefix="qbawing_http_")
atexit.register(shutil.rmtree, raiz, ignore_errors=True)
# El inventario real del programa NO se toca: al pedir /inventario esta
# prueba genera el suyo dentro de su carpeta temporal.
S.INVENTARIO = Path(os.path.join(raiz, "inventario.csv"))
carpeta_ok = os.path.join(raiz, "Con Poster")
carpeta_no = os.path.join(raiz, "Sin Poster")
carpeta_sin_video = os.path.join(raiz, "Carpeta sin video")
os.makedirs(carpeta_ok, exist_ok=True)
os.makedirs(carpeta_no, exist_ok=True)
os.makedirs(carpeta_sin_video, exist_ok=True)
with open(os.path.join(carpeta_ok, "cover.jpg"), "wb") as f:
    f.write(b"\xff\xd8\xff\xe0" + b"y" * 20000)

cfg = {"idioma": "es", "tipos": [], "unidades": [], "tmdb_api_key": "x",
       "tmdb_api_url": "https://api.themoviedb.org/3/"}
S.E = S.Estado(cfg)
E = S.E
E.unidades = [{"ruta": raiz, "etiqueta": "Test", "sistema": "NTFS",
               "tipo": escaneo.TIPO_LOCAL, "descripcion": "Disco local",
               "total": 10 ** 12, "libre": 10 ** 11}]
E.unidades_elegidas = [raiz]
E.carpetas = [
    {"ruta": carpeta_ok, "nombre": "Con Poster", "unidad": raiz, "ya_tiene": True,
     "imagen_existente": os.path.join(carpeta_ok, "cover.jpg"), "videos": 1,
     "anio": None, "temporada": None, "titulo": "Con Poster",
     "tipo": "pelicula", "descargado": False},
    {"ruta": carpeta_no, "nombre": "Sin Poster", "unidad": raiz, "ya_tiene": False,
     "imagen_existente": "", "videos": 1, "anio": 2011, "temporada": None,
     "titulo": "Sin Poster", "tipo": "pelicula", "descargado": False},
]
E.resultados = {carpeta_no: {"titulo": "Sin Poster", "ano": 2011,
                             "tipo": "pelicula", "fuente": "TMDB",
                             "poster_url": "https://example.invalid/x.jpg",
                             "id": 7, "puntuacion": 75, "candidatos": []}}

httpd = ThreadingHTTPServer(("127.0.0.1", 0), S.Manejador)
httpd.daemon_threads = True
puerto = httpd.server_address[1]
hilo = threading.Thread(target=httpd.serve_forever,
                        kwargs={"poll_interval": 0.1}, daemon=True)
hilo.start()
base = "http://127.0.0.1:%d" % puerto


def pedir(path, datos=None, metodo=None):
    url = base + path
    cuerpo = None
    cab = {}
    if datos is not None:
        cuerpo = json.dumps(datos).encode("utf-8")
        cab["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=cuerpo, headers=cab,
                                 method=metodo)
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, r.read(), dict(r.headers)


ok = []


def check(nombre, cond, detalle=""):
    assert cond, "%s  %s" % (nombre, detalle)
    ok.append(nombre)


try:
    st, cuerpo, _ = pedir("/")
    check("GET /", st == 200 and b"QBASWING COVERS" in cuerpo)

    st, cuerpo, _ = pedir("/paso2?tipo=peliculas")
    check("GET /paso2", st == 200 and b"Escanear" in cuerpo and raiz.encode() in cuerpo)

    st, cuerpo, _ = pedir("/paso3")
    check("GET /paso3 sin unidades", st == 200
          and "Selecciona al menos una unidad".encode() in cuerpo)

    st, cuerpo, _ = pedir("/paso4")
    check("GET /paso4", st == 200 and b"galeria" in cuerpo)

    st, cuerpo, _ = pedir("/galeria")
    check("GET /galeria lista unidades", st == 200
          and "Elige una unidad".encode() in cuerpo
          and "tarjeta-unidad".encode() in cuerpo)

    st, cuerpo, _ = pedir("/galeria?ruta=%d" % E.id_de(raiz))
    check("GET /galeria", st == 200 and "Con Poster".encode() in cuerpo
          and "Sin Poster".encode() in cuerpo and b"/galeria?ruta=" in cuerpo)

    st, cuerpo, _ = pedir("/galeria?ruta=%d" % E.id_de(carpeta_no))
    check("GET /galeria dentro de carpeta", st == 200
          and "Subir".encode() in cuerpo and "Unidades".encode() in cuerpo)

    st, cuerpo, _ = pedir("/galeria?ruta=%d&filtro=sin&orden=za" % E.id_de(raiz))
    check("GET /galeria filtro", st == 200)

    st, cuerpo, _ = pedir("/acerca?volver=/galeria")
    check("GET /acerca", st == 200 and "Freeman".encode() in cuerpo)

    st, cuerpo, _ = pedir("/logo.png")
    check("GET /logo.png", st == 200 and cuerpo[:4] == b"\x89PNG")

    st, cuerpo, _ = pedir("/api/progreso")
    d = json.loads(cuerpo)
    check("GET /api/progreso", st == 200 and "listo" in d)

    st, cuerpo, cab = pedir("/api/cover?id=%d" % E.id_de(carpeta_ok))
    check("GET /api/cover (existe)", st == 200 and cab.get("Content-Type") == "image/jpeg"
          and len(cuerpo) > 1000)

    try:
        pedir("/api/cover?id=%d" % E.id_de(carpeta_no))
        check("GET /api/cover (no existe)", False, "deberia dar 404")
    except urllib.error.HTTPError as e:
        check("GET /api/cover (no existe)", e.code == 404)

    st, cuerpo, _ = pedir("/api/marcar", {"id": E.id_de(carpeta_no)})
    d = json.loads(cuerpo)
    check("POST /api/marcar", st == 200 and d["ok"] and d["marcadas"] == 1
          and d["seleccionada"] is True)
    check("marcada en memoria", carpeta_no in E.marcadas)

    st, cuerpo, _ = pedir("/api/marcar", {"id": E.id_de(carpeta_sin_video)})
    check("no seleccionar carpeta sin video escaneado",
          json.loads(cuerpo)["ok"] is False
          and carpeta_sin_video not in E.marcadas)

    st, cuerpo, _ = pedir("/api/marcar", {"id": E.id_de(carpeta_no)})
    d = json.loads(cuerpo)
    check("POST /api/marcar (desmarcar)", d["marcadas"] == 0
          and d["seleccionada"] is False)

    st, cuerpo, _ = pedir("/api/seleccionar-faltantes", {})
    d = json.loads(cuerpo)
    check("POST /api/seleccionar-faltantes", d["marcadas"] >= 1)

    st, cuerpo, _ = pedir("/api/limpiar", {})
    check("POST /api/limpiar", json.loads(cuerpo)["marcadas"] == 0)

    st, cuerpo, _ = pedir("/api/descargar", {"modo": "seleccion"})
    check("POST /api/descargar vacio", json.loads(cuerpo)["ok"] is False)

    st, cuerpo, _ = pedir("/inventario")
    check("GET /inventario", st == 200)

    try:
        pedir("/ruta-que-no-existe")
        check("404", False)
    except urllib.error.HTTPError as e:
        check("404", e.code == 404)

    # --- idioma (la redireccion es meta-refresh, el navegador la sigue) ---
    st, cuerpo, _ = pedir("/?lang=en")
    check("cambio idioma aplicado", E.lang == "en")
    st, cuerpo, _ = pedir("/")
    check("cambio idioma", b"Every collection deserves its cover" in cuerpo
          or b"About us" in cuerpo)

finally:
    httpd.shutdown()
    httpd.server_close()

print("RUTAS HTTP OK:", ", ".join(ok))
print("TOTAL:", len(ok), "rutas verificadas")
