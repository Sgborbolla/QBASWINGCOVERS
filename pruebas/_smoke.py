# -*- coding: utf-8 -*-
"""Prueba de humo: arma cada pantalla sin abrir socket ni navegador."""
import atexit
import os
import sys
import tempfile
import shutil
from pathlib import Path
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

import escaneo
import posters as post
import servidor as S

raiz = tempfile.mkdtemp(prefix="qbawing_smoke_")
atexit.register(shutil.rmtree, raiz, ignore_errors=True)
# El inventario real del programa NO se toca: esta prueba escribe el suyo
# dentro de su carpeta temporal, que se borra al salir.
S.INVENTARIO = Path(os.path.join(raiz, "inventario.csv"))
pelis = os.path.join(raiz, "Peliculas")
series = os.path.join(raiz, "Series")
sinposter = os.path.join(raiz, "Sin poster")
sin_escanear = os.path.join(raiz, "Carpeta sin escanear")
for d in (pelis, series, sinposter, sin_escanear):
    os.makedirs(d, exist_ok=True)
# Una imagen real y pequena en "Peliculas"
with open(os.path.join(pelis, "cover.jpg"), "wb") as f:
    f.write(b"\xff\xd8\xff\xe0" + b"x" * 20000)
sub = os.path.join(pelis, "Matrix (1999)")
os.makedirs(sub, exist_ok=True)

cfg = {"idioma": "es", "tipos": ["peliculas"], "unidades": [],
       "tmdb_api_key": "x", "tmdb_api_url": "https://api.themoviedb.org/3/"}
S.E = S.Estado(cfg)
E = S.E
E.unidades = [{"ruta": raiz, "etiqueta": "Prueba", "sistema": "NTFS",
               "tipo": escaneo.TIPO_LOCAL, "descripcion": "Disco local",
               "total": 10 ** 12, "libre": 5 * 10 ** 11}]
E.unidades_elegidas = [raiz]

carpetas = [
    {"ruta": pelis, "nombre": "Peliculas", "unidad": raiz, "ya_tiene": True,
     "imagen_existente": os.path.join(pelis, "cover.jpg"), "videos": 2,
     "anio": None, "temporada": None, "titulo": "Peliculas",
     "tipo": "pelicula", "descargado": False},
    {"ruta": series, "nombre": "Series", "unidad": raiz, "ya_tiene": False,
     "imagen_existente": "", "videos": 5,
     "anio": 2010, "temporada": 1, "titulo": "Series",
     "tipo": "serie", "descargado": False},
    {"ruta": sinposter, "nombre": "Sin poster", "unidad": raiz, "ya_tiene": False,
     "imagen_existente": "", "videos": 1,
     "anio": None, "temporada": None, "titulo": "Sin poster",
     "tipo": "pelicula", "descargado": False},
]
E.carpetas = carpetas
E.resultados = {
    series: {"titulo": "Series", "ano": 2010, "tipo": "serie",
             "fuente": "TVmaze", "poster_url": "https://x/p.jpg",
             "id": 1, "puntuacion": 80, "temporada_encontrada": 1,
             "candidatos": [{"titulo": "Series", "ano": 2010,
                             "poster_url": "https://x/p.jpg", "tipo": "serie"}]},
    sinposter: {"poster_url": None, "candidatos": []},
}
E.marcadas = {series}
E.resumen = {"descargados": 3, "ya_tenian": 2, "sin_coincidencia": 1, "fallos": 0}

lang = "es"
pruebas = []

def probar(nombre, html, debe_tener):
    assert isinstance(html, str) and len(html) > 200, "%s: HTML corto" % nombre
    for marca in debe_tener:
        assert marca in html, "%s: falta %r" % (nombre, marca)
    assert "%s" not in html and "%d" not in html, \
        "%s: quedo un %% sin sustituir" % nombre
    pruebas.append(nombre)

probar("bienvenida", S.ventana_bienvenida(lang, E.tipos),
       ["QBASWING", "Acerca de nosotros", "QBASwing Designer", "Freeman"])
probar("discos", S.ventana_discos(lang, E.unidades),
       ["Escanear", raiz, "Disco local"])
probar("escaneo", S.ventana_escaneo(lang, [raiz]),
       ["/api/progreso", "barra"])
probar("pregunta", S.ventana_pregunta(lang, 2), ["buscar", "galeria"])
probar("pregunta_vacia", S.ventana_pregunta(lang, 0), ["galeria"])
probar("buscando", S.ventana_buscando(lang), ["/api/progreso"])
probar("galeria_unidades", S.ventana_galeria(lang, None),
       ["Elige una unidad", raiz, "tarjeta-unidad", "Unidad de disco"])
probar("galeria", S.ventana_galeria(lang, raiz, "todas", "az", ""),
       ["Peliculas", "Series", "Sin poster", "descargar", "revision",
        "/galeria?ruta=", "orden=az", "https://x/p.jpg",
        "marcarClick(event", "ondblclick=\"entrar(",
        "filtro='+f+'&orden=", 'href="/galeria?vista=unidades"'])
probar("estado_carpeta_sin_escanear",
       S.ventana_galeria(lang, raiz, "todas", "az", ""),
       ["Carpeta sin escanear"])
probar("galeria_filtro", S.ventana_galeria(lang, raiz, "con", "za", "pel"),
       ["orden=za"])
probar("revision", S.ventana_revision(lang, E.id_de(series)),
       ["Aceptar", "Saltar", "TVmaze", "https://x/p.jpg"])
_guardar_resultados = E.resultados
E.resultados = {}
probar("revision_vacia", S.ventana_revision(lang, None),
       ["Revisar uno por uno", "No queda nada"])
E.resultados = _guardar_resultados
probar("descargando", S.ventana_descargando(lang), ["/api/progreso"])
probar("resumen", S.ventana_resumen(lang, E.resumen),
       ["3", "2", "1", "inventario"])
S.escribir_inventario()
probar("inventario", S.ventana_inventario(lang), ["inventario.csv"])
probar("acerca", S.ventana_acerca(lang, "/galeria"),
       ["Nuestra historia", "Freeman y Diseños", "galeria"])
probar("acerca_en", S.ventana_acerca("en", "/"),
       ["Our story", "Freeman y Diseños"])

# Redireccion
rd = S._redir("/revision?carpeta=3&accion=aceptar")
assert "url=/revision?carpeta=3&amp;accion=aceptar" in rd, rd[:200]
pruebas.append("_redir")

# Inventario CSV
n = S.escribir_inventario()
assert n == 3, n
with open(S.INVENTARIO, "rb") as f:
    cab = f.read(3)
assert cab == b"\xef\xbb\xbf", "falta BOM utf-8-sig"
texto = open(S.INVENTARIO, encoding="utf-8-sig").read()
assert "RutaCarpeta" in texto and "TamanoBytes" in texto
pruebas.append("inventario.csv (%d filas, con BOM)" % n)

# Deteccion de tipo
assert S._tipo_de_carpeta("Breaking Bad S01") == "serie"
assert S._tipo_de_carpeta("Matrix") == "pelicula"
assert S._tipo_de_carpeta("La Reina del Sur novela") == "serie"
pruebas.append("_tipo_de_carpeta")

assert S._estado_de_carpeta(series) == S.SIN_POSTER
_resultados_sin_busqueda = E.resultados
E.resultados = {}
assert S._estado_de_carpeta(series) == S.PENDIENTE
E.resultados = _resultados_sin_busqueda
pruebas.append("estados pendiente y poster encontrado")

# El escaneo debe ir actualizando el avance mientras recorre carpetas.
_escanear_original = S.escaneo.escanear_unidad
def _escanear_falso(unidad, progreso=None, control=None, marcador=None):
    if progreso:
        progreso(os.path.join(unidad, "carpeta-de-prueba"))
    return []

S.escaneo.escanear_unidad = _escanear_falso
E.unidades_elegidas = [raiz]
E.carpetas = []
try:
    S._hilo_escaneo()
    assert E.progreso["listo"] and E.progreso["hechos"] == 1 \
        and E.progreso["total"] == 1
    assert "carpeta-de-prueba" in E.progreso["texto"] or \
        "Escaneo terminado" in E.progreso["texto"]
finally:
    S.escaneo.escanear_unidad = _escanear_original
pruebas.append("_hilo_escaneo progreso")

print("PANTALLAS OK:", ", ".join(pruebas))
print("TOTAL:", len(pruebas), "pruebas")
