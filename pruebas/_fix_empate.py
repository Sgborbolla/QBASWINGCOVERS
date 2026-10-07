# -*- coding: utf-8 -*-
"""
Fix 3: los empates entre el MISMO titulo no son empates.

"Breaking Bad" venia tres veces (TMDB, AniList, TVmaze) con el mismo
nombre y el programa lo mandaba a revision manual. Tres resultados que
se llaman igual no son una adivinanza: es el mismo contenido, y se
resuelve con la prioridad de la fuente.

Lo que si sigue siendo empate (seccion 16): dos titulos DISTINTOS con
la misma puntuacion. Eso lo revisa la persona.

Ademas se arregla el 400 de MangaDex: la API no acepta "title[]".
"""
import ast
import io

raiz = r"C:\QBASWING-COVERS"
hechos = []

# =====================================================================
# posters.py  - desempate por titulo
# =====================================================================
RUTA = raiz + r"\posters.py"
t = io.open(RUTA, encoding="utf-8").read()

PRIORIDAD = '''
# Si varias fuentes devuelven el MISMO titulo, gana la mejor fuente.
# El orden es el de la seccion 7: primero las和专业, despues las generales.
PRIORIDAD_FUENTE = {
    "TMDB": 90,
    "TMDB (temporada)": 92,
    "AniList": 80,
    "TVmaze": 70,
    "Kitsu": 65,
    "Bangumi": 62,
    "MangaDex": 60,
    "MusicBrainz": 55,
    "Internet Archive": 40,
    "OpenLibrary": 35,
    "GoogleBooks": 30,
    "Wikipedia": 45,
}


def _clave_titulo(titulo):
    """Clave para saber si dos resultados son el mismo contenido."""
    base = quitar_acentos(titulo or "").strip().lower()
    base = re.sub(r"[^a-z0-9\\u00c0-\\uffff ]+", " ", base)
    return re.sub(r"\\s+", " ", base).strip()


def _desempatar(empatados):
    """
    Devuelve el ganador si los empatados son el MISMO titulo,
    o None si son titulos distintos (ahi si hay que revisar).
    """
    claves = set()
    for c in empatados:
        claves.add(_clave_titulo(c.get("titulo")))
    if len(claves) != 1:
        return None
    return sorted(empatados,
                  key=lambda c: (PRIORIDAD_FUENTE.get(c.get("fuente"), 10),
                                 -(c.get("puntuacion") or 0)))[0]

'''
if "_desempatar(" not in t:
    t = t.replace("\ndef elegir_mejor(", PRIORIDAD + "\ndef elegir_mejor(", 1)
    if "_desempatar(" not in t:
        raise SystemExit("no se pudo insertar el desempate")
    hechos.append("posters.py: _desempatar() y prioridad de fuentes")

VIEJO = '''    if len(exactos) == 1:
            exactos[0]["puntuacion"] = max(exactos[0]["puntuacion"],
                                           UMBRAL_ACEPTACION)
            puntuados.sort(key=lambda x: x["puntuacion"], reverse=True)
            return (exactos[0], "aceptado_exacto", puntuados[:10])

        if len(exactos) > 1:
            return (None, "empate", puntuados[:10])
'''
NUEVO = '''    if exactos:
            # Varias fuentes pueden traer el mismo nombre exacto.
            # Si es el mismo contenido, gana la mejor fuente.
            ganador = _desempatar(exactos)
            if ganador is not None:
                ganador["puntuacion"] = max(ganador["puntuacion"],
                                            UMBRAL_ACEPTACION)
                puntuados.sort(key=lambda x: x["puntuacion"], reverse=True)
                return (ganador, "aceptado_exacto", puntuados[:10])
            return (None, "empate", puntuados[:10])
'''
# el bloque real esta indentado con 8 espacios dentro del if not sobre:
VIEJO_REAL = '''        if len(exactos) == 1:
            exactos[0]["puntuacion"] = max(exactos[0]["puntuacion"],
                                           UMBRAL_ACEPTACION)
            puntuados.sort(key=lambda x: x["puntuacion"], reverse=True)
            return (exactos[0], "aceptado_exacto", puntuados[:10])

        if len(exactos) > 1:
            return (None, "empate", puntuados[:10])
'''
if VIEJO_REAL in t:
    t = t.replace(VIEJO_REAL, NUEVO.replace("    if exactos:", "        if exactos:", 1), 1)
    hechos.append("posters.py: el nombre exacto repetido se resuelve por fuente")
elif "if exactos:" not in t:
    raise SystemExit("no se encontro el bloque de exactos")

# El empate del umbral tambien se resuelve si es el mismo titulo.
VIEJO_UMBRAL = '''    if len(sobre) >= 2 and sobre[0]["puntuacion"] == sobre[1]["puntuacion"]:
        return (None, "empate", puntuados[:10])
'''
NUEVO_UMBRAL = '''    if len(sobre) >= 2 and sobre[0]["puntuacion"] == sobre[1]["puntuacion"]:
        # Mismo titulo desde varias fuentes: no es ambiguedad.
        ganador = _desempatar([c for c in sobre
                               if c["puntuacion"] == sobre[0]["puntuacion"]])
        if ganador is not None:
            return (ganador, "aceptado", puntuados[:10])
        # Titulos distintos con la misma puntuacion: revision manual.
        return (None, "empate", puntuados[:10])
'''
if VIEJO_UMBRAL in t:
    t = t.replace(VIEJO_UMBRAL, NUEVO_UMBRAL, 1)
    hechos.append("posters.py: empate del umbral resuelto si es el mismo titulo")
elif "no es ambiguedad" not in t:
    raise SystemExit("no se encontro el empate del umbral")

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(t)
ast.parse(t)

# =====================================================================
# fuentes.py  - MangaDex sin corchetes en title
# =====================================================================
RUTA_F = raiz + r"\fuentes.py"
f = io.open(RUTA_F, encoding="utf-8").read()

VIEJO_MD = '''        datos = _obtener(MANGADEX + "/manga",
                         {"limit": 6, "title[]": titulo,
                          "includes[]": "cover_art"})'''
NUEVO_MD = '''        # La API acepta "title" sin corchetes pero "includes[]" con ellos.
        # Con "title[]" responde 400.
        datos = _obtener(MANGADEX + "/manga",
                         {"limit": 6, "title": titulo,
                          "includes[]": "cover_art"})'''
if VIEJO_MD in f:
    f = f.replace(VIEJO_MD, NUEVO_MD, 1)
    hechos.append("fuentes.py: MangaDex sin 400")
else:
    raise SystemExit("no se encontro la consulta de MangaDex")

io.open(RUTA_F, "w", encoding="utf-8", newline="\n").write(f)
ast.parse(f)

print("Aplicado:")
for h in hechos:
    print("   -", h)
print("sintaxis OK")