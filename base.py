# -*- coding: utf-8 -*-
"""
QBASWING COVERS - Base de datos local.

Guarda todo lo que el programa necesita recordar entre sesiones:
  - las carpetas candidatas que ya se escanearon
  - en que carpeta quedo el escaneo, para poder seguir donde se quedo
  - el estado de cada poster (descargado, sin coincidencia, etc.)

Es un archivo SQLite que vive junto al programa: qbawing_covers.db
Nunca sale de tu PC y nunca se envia a ningun sitio.
"""

import hashlib
import json
import sqlite3
import threading
import time

import rutas

ARCHIVO_NOMBRE = "qbawing_covers.db"

_candado = threading.RLock()
_conexion = None

ESQUEMA = (
    """
    CREATE TABLE IF NOT EXISTS carpetas (
        ruta        TEXT PRIMARY KEY,
        nombre      TEXT,
        unidad      TEXT,
        tipo        TEXT,
        anio        INTEGER,
        temporada   TEXT,
        titulo      TEXT,
        videos      INTEGER,
        ya_tiene    INTEGER DEFAULT 0,
        imagen      TEXT DEFAULT '',
        descargado  INTEGER DEFAULT 0,
        estado      TEXT DEFAULT '',
        fuente      TEXT DEFAULT '',
        encontrado  TEXT DEFAULT '',
        url_poster  TEXT DEFAULT '',
        puntuacion  REAL DEFAULT 0,
        vista       INTEGER DEFAULT 0,
        actualizado REAL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS escaneos (
        unidad    TEXT PRIMARY KEY,
        carpeta   TEXT DEFAULT '',
        hechas    INTEGER DEFAULT 0,
        terminado INTEGER DEFAULT 0,
        inicio    REAL DEFAULT 0,
        fin       REAL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vistos (
        h      INTEGER PRIMARY KEY,
        unidad TEXT DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ajustes (
        clave TEXT PRIMARY KEY,
        valor TEXT
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_carpetas_estado ON carpetas(estado)",
    "CREATE INDEX IF NOT EXISTS ix_carpetas_unidad ON carpetas(unidad)",
    "CREATE INDEX IF NOT EXISTS ix_vistos_unidad ON vistos(unidad)",
)


# --------------------------------------------------------------------------
# Conexion
# --------------------------------------------------------------------------

def archivo():
    """Ruta completa de la base de datos local."""
    try:
        base = rutas.base_dir()
    except Exception:
        import os
        base = os.path.dirname(os.path.abspath(__file__))
    from pathlib import Path
    return Path(base) / ARCHIVO_NOMBRE


def conexion():
    """Abre la base una sola vez. Nunca lanza excepcion."""
    global _conexion
    with _candado:
        if _conexion is not None:
            return _conexion
        try:
            ruta = str(archivo())
            # Escaneo, busqueda y descarga corren en hilos distintos y todos
            # usan esta misma conexion; sin esto sqlite se niega en silencio
            # y no se guarda NI UNA fila (toda la escritura devuelve 0).
            con = sqlite3.connect(ruta, timeout=30, check_same_thread=False)
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA synchronous=NORMAL")
            for sql in ESQUEMA:
                con.execute(sql)
            con.commit()
            _conexion = con
        except Exception:
            _conexion = None
        return _conexion


def cerrar():
    global _conexion
    with _candado:
        try:
            if _conexion is not None:
                _conexion.commit()
                _conexion.close()
        except Exception:
            pass
        _conexion = None


def _sql(sql, args=()):
    con = conexion()
    if con is None:
        return None
    try:
        with _candado:
            cur = con.execute(sql, args)
            return cur
    except Exception:
        return None


# --------------------------------------------------------------------------
# Ajustes sueltos (por ejemplo: la ultima carpeta abierta en la galeria)
# --------------------------------------------------------------------------

def ajuste(clave, valor=None):
    """Lee o escribe un valor suelto."""
    if valor is None:
        cur = _sql("SELECT valor FROM ajustes WHERE clave=?", (clave,))
        if cur is None:
            return None
        fila = cur.fetchone()
        if fila is None:
            return None
        try:
            return json.loads(fila["valor"])
        except Exception:
            return fila["valor"]
    _sql("INSERT OR REPLACE INTO ajustes(clave, valor) VALUES(?,?)",
         (clave, json.dumps(valor, ensure_ascii=False)))
    return valor


# --------------------------------------------------------------------------
# Carpetas candidatas
# --------------------------------------------------------------------------

def guardar_carpeta(c):
    """Guarda o actualiza una carpeta candidata."""
    ahora = time.time()
    _sql(
        "INSERT OR REPLACE INTO carpetas("
        "ruta, nombre, unidad, tipo, anio, temporada, titulo, videos,"
        " ya_tiene, imagen, descargado, estado, fuente, encontrado,"
        " url_poster, puntuacion, actualizado)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (c.get("ruta", ""), c.get("nombre", ""), c.get("unidad", ""),
         c.get("tipo", ""), c.get("anio"), c.get("temporada", ""),
         c.get("titulo", ""), int(c.get("videos") or 0),
         1 if c.get("ya_tiene") else 0, c.get("imagen_existente") or "",
         1 if c.get("descargado") else 0, c.get("estado", ""),
         c.get("fuente", ""), c.get("titulo_encontrado", ""),
         c.get("url_poster", ""), float(c.get("puntuacion") or 0), ahora))
    return True


def guardar_carpetas(lista):
    """Guarda muchas de golpe, en una sola transaccion."""
    if not lista:
        return 0
    ahora = time.time()
    filas = []
    for c in lista:
        filas.append((
            c.get("ruta", ""), c.get("nombre", ""), c.get("unidad", ""),
            c.get("tipo", ""), c.get("anio"), c.get("temporada", ""),
            c.get("titulo", ""), int(c.get("videos") or 0),
            1 if c.get("ya_tiene") else 0, c.get("imagen_existente") or "",
            1 if c.get("descargado") else 0, c.get("estado", ""),
            c.get("fuente", ""), c.get("titulo_encontrado", ""),
            c.get("url_poster", ""), float(c.get("puntuacion") or 0), ahora))
    con = conexion()
    if con is None:
        return 0
    try:
        with _candado:
            con.executemany(
                "INSERT OR REPLACE INTO carpetas("
                "ruta, nombre, unidad, tipo, anio, temporada, titulo, videos,"
                " ya_tiene, imagen, descargado, estado, fuente, encontrado,"
                " url_poster, puntuacion, actualizado)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", filas)
            con.commit()
        return len(filas)
    except Exception:
        return 0


def actualizar(ruta, **campos):
    """Cambia campos de una carpeta ya guardada."""
    if not campos or not ruta:
        return False
    permitidos = {"nombre", "unidad", "tipo", "anio", "temporada", "titulo",
                  "videos", "ya_tiene", "imagen", "descargado", "estado",
                  "fuente", "encontrado", "url_poster", "puntuacion", "vista"}
    pares = []
    for clave in campos:
        if clave in permitidos:
            pares.append("%s=?" % clave)
    if not pares:
        return False
    valores = [campos[c] for c in campos if c in permitidos]
    valores.append(time.time())
    valores.append(ruta)
    cur = _sql("UPDATE carpetas SET %s, actualizado=? WHERE ruta=?"
               % ", ".join(pares), tuple(valores))
    return cur is not None


def leer_carpetas(filtro=None):
    """Devuelve las carpetas guardadas como lista de dicts."""
    sql = "SELECT * FROM carpetas"
    args = ()
    if filtro:
        sql += " WHERE %s" % filtro
    cur = _sql(sql, args)
    if cur is None:
        return []
    try:
        return [dict(f) for f in cur.fetchall()]
    except Exception:
        return []


def carpeta(ruta):
    cur = _sql("SELECT * FROM carpetas WHERE ruta=?", (ruta,))
    if cur is None:
        return None
    fila = cur.fetchone()
    return dict(fila) if fila else None


def borrar_carpeta(ruta):
    _sql("DELETE FROM carpetas WHERE ruta=?", (ruta,))


# --------------------------------------------------------------------------
# Descargas: que archivo le toco a cada carpeta
# --------------------------------------------------------------------------

CLAVE_DESCARGA = "descarga|"


def registrar_descarga(ruta, archivo):
    """
    Recuerda que esta carpeta ya tiene su poster en
    Descargas\\QBASWING COVERS, con ese nombre de archivo.
    """
    if not ruta or not archivo:
        return False
    return ajuste(CLAVE_DESCARGA + str(_hash(ruta)), archivo) is not None


def descarga_de(ruta):
    """Nombre del archivo que se descargo para esta carpeta, o ''."""
    if not ruta:
        return ""
    valor = ajuste(CLAVE_DESCARGA + str(_hash(ruta)))
    return valor if isinstance(valor, str) else ""


# --------------------------------------------------------------------------
# Escaneo reanudable
# --------------------------------------------------------------------------

def _hash(ruta):
    """Numero entero de 63 bits para no guardar la ruta completa."""
    d = hashlib.sha1(str(ruta).lower().encode("utf-8", "replace")).digest()
    return int.from_bytes(d[:8], "big") >> 1


def marcar_visto(ruta, unidad=""):
    """Anota que esta carpeta ya se reviso."""
    _sql("INSERT OR IGNORE INTO vistos(h, unidad) VALUES(?,?)",
         (_hash(ruta), unidad))


def vistos_de(unidad=""):
    """Devuelve el conjunto de carpetas ya revisadas de esa unidad."""
    cur = _sql("SELECT h FROM vistos WHERE unidad=?", (unidad,))
    if cur is None:
        return set()
    try:
        return set(f[0] for f in cur.fetchall())
    except Exception:
        return set()


def limpiar_vistos(unidad=""):
    """Olvida las carpetas revisadas, para empezar de cero."""
    _sql("DELETE FROM vistos WHERE unidad=?", (unidad,))


class MarcadorRuta(object):
    """
    Recuerda que carpetas ya se revisaron, en memoria y en la base.
    Sirve para que un escaneo interrumpido siga donde se quedo.
    """

    def __init__(self, unidad="", cargar=True):
        self.unidad = unidad or ""
        self.vistos = vistos_de(self.unidad) if cargar else set()
        self.nuevas = []

    def ya_visto(self, ruta):
        return _hash(ruta) in self.vistos

    def marcar(self, ruta):
        h = _hash(ruta)
        if h in self.vistos:
            return
        self.vistos.add(h)
        self.nuevas.append((h, self.unidad))
        if len(self.nuevas) >= 2000:
            self.vaciar()

    def vaciar(self):
        if not self.nuevas:
            return
        con = conexion()
        if con is None:
            return
        try:
            with _candado:
                con.executemany(
                    "INSERT OR IGNORE INTO vistos(h, unidad) VALUES(?,?)",
                    self.nuevas)
                con.commit()
            self.nuevas = []
        except Exception:
            pass


# --------------------------------------------------------------------------
# Estado del escaneo por unidad
# --------------------------------------------------------------------------

def guardar_escaneo(unidad, carpeta_actual="", hechas=0, terminado=0):
    ahora = time.time()
    _sql("INSERT OR REPLACE INTO escaneos(unidad, carpeta, hechas,"
         " terminado, inicio, fin) VALUES(?,?,?,?,COALESCE((SELECT inicio"
         " FROM escaneos WHERE unidad=?),?),?)",
         (unidad, carpeta_actual, int(hechas or 0), 1 if terminado else 0,
          ahora, unidad, ahora if terminado else 0))


def leer_escaneos():
    cur = _sql("SELECT * FROM escaneos")
    if cur is None:
        return []
    try:
        return [dict(f) for f in cur.fetchall()]
    except Exception:
        return []


def escaneo_de(unidad):
    cur = _sql("SELECT * FROM escaneos WHERE unidad=?", (unidad,))
    if cur is None:
        return None
    fila = cur.fetchone()
    return dict(fila) if fila else None


def borrar_escaneos():
    _sql("DELETE FROM escaneos")
    _sql("DELETE FROM vistos")


# --------------------------------------------------------------------------
# Resumen
# --------------------------------------------------------------------------

def resumen():
    """Cuentas rapidas para la pantalla."""
    cur = _sql("SELECT COUNT(*) n, SUM(ya_tiene) c, SUM(descargado) d"
               " FROM carpetas")
    if cur is None:
        return {"total": 0, "con_poster": 0, "descargados": 0, "tamano": 0}
    fila = cur.fetchone()
    out = {"total": 0, "con_poster": 0, "descargados": 0, "tamano": 0}
    try:
        out["total"] = fila["n"] or 0
        out["con_poster"] = fila["c"] or 0
        out["descargados"] = fila["d"] or 0
    except Exception:
        pass
    try:
        out["tamano"] = archivo().stat().st_size
    except Exception:
        pass
    return out