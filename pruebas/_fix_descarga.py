# -*- coding: utf-8 -*-
"""
Corrige los dos bugs que impiden descargar un solo poster:

  BUG A  TIPOS_APIS no tenia la clave "todos" -> no se consultaba NINGUNA API.
  BUG B  El +10 de "es del tipo pedido" nunca se daba (tipo_pedido sin
         definir y singular/plural sin normalizar), y ademas el nombre
         exacto de la carpeta se quedaba en 50 puntos, bajo el umbral de
         60. Como las carpetas se llaman igual que el video, todas
         acababan en "sin coincidencia".

  Ademas: el nombre exacto sin ambiguedad se acepta aunque no llegue a 60,
  porque un titulo identico no es una adivinanza (seccion 16).
"""
import ast
import io
import re

raiz = r"C:\QBASWING-COVERS"
hechos = []

# =====================================================================
# posters.py
# =====================================================================
RUTA_POSTERS = raiz + r"\posters.py"
t = io.open(RUTA_POSTERS, encoding="utf-8").read()

# --- 1) Helper de normalizacion de tipo y de titulo ---
AYUDANTE = '''
# Los tipos llegan en singular ("serie") desde las fuentes y en plural
# ("series") desde la eleccion del usuario. Para compararlos se quitan
# las diferencias de forma.
def _tipo_base(tipo):
    """'series' -> 'serie', 'novelas' -> 'novela'. Sin tildes."""
    if not tipo:
        return ""
    base = quitar_acentos(str(tipo)).strip().lower()
    if base.endswith("es") and len(base) > 4:
        base = base[:-2]
    elif base.endswith("s") and len(base) > 3:
        base = base[:-1]
    return base


# Tipos de contenido que cuentan como la misma familia.
FAMILIAS = (
    (("serie", "novela", "documental", "clasico", "anime"), "serie"),
    (("pelicula",), "pelicula"),
    (("manga", "comic"), "manga"),
    (("musica", "album", "cancion"), "musica"),
)


def _familia(tipo):
    """Agrupa los tipos parecidos: anime con serie, novela con serie."""
    base = _tipo_base(tipo)
    if not base:
        return ""
    for grupo, destino in FAMILIAS:
        if base in grupo:
            return destino
    return base


def _comparar_titulos(titulo_carpeta, ano_carpeta, titulo_resultado):
    """
    Devuelve (carpeta, resultado, exacto) ya normalizados y sin el ano.
    'exacto' es True cuando los dos titulos son el mismo nombre.
    """
    c = quitar_acentos(titulo_carpeta or "").strip().lower()
    r = quitar_acentos(titulo_resultado or "").strip().lower()

    # El ano no cuenta: "Matrix (1999)" y "Matrix" son el mismo titulo.
    ano_compara = ano_carpeta
    if not ano_compara:
        try:
            ano_compara = int(titulo_resultado or 0)
        except (TypeError, ValueError):
            ano_compara = None
    if ano_compara and 1888 <= int(ano_compara) <= ANIO_MAX:
        c = re.sub(r"\\b%d\\b" % int(ano_compara), " ", c).strip(" ()[]-.")
        r = re.sub(r"\\b%d\\b" % int(ano_compara), " ", r).strip(" ()[]-.")

    c = re.sub(r"\\s+", " ", c).strip()
    r = re.sub(r"\\s+", " ", r).strip()
    return c, r, (bool(c) and c == r)

'''
if "_familia(" not in t:
    t = t.replace("\ndef _palabras(texto):", AYUDANTE + "\ndef _palabras(texto):", 1)
    if "_familia(" not in t:
        raise SystemExit("no se pudo insertar el ayudante en posters.py")
    hechos.append("posters.py: _tipo_base() y _familia()")

# --- 2) puntuar(): usar el ayudante y dar bien el +10 del tipo ---
VIEJO_PUNTUAR_INICIO = '''    c = quitar_acentos(titulo_carpeta or "").strip().lower()
    r = quitar_acentos(titulo_resultado).strip().lower()

    # Para comparar longitudes y palabras el ano no cuenta:
    # "Matrix (1999)" y "Matrix" son el mismo titulo.
    ano_compara = ano_carpeta or ano_resultado
    if ano_compara:
        c_sin = re.sub(r"\\b%d\\b" % ano_compara, " ", c).strip(" ()[]-")
        r_sin = re.sub(r"\\b%d\\b" % ano_compara, " ", r).strip(" ()[]-")
        if c_sin:
            c = c_sin
        if r_sin:
            r = r_sin

    # Exacto o por comparacion sin acentos.
    if (titulo_carpeta or "").strip().lower() == titulo_resultado.strip().lower():
        puntos += 50
    elif c == r:
        puntos += 35
'''
NUEVO_PUNTUAR_INICIO = '''    # Los titulos se comparan sin el ano: "Matrix (1999)" y "Matrix"
    # son el mismo nombre, y el ano ya se puntua aparte.
    c, r, exacto = _comparar_titulos(titulo_carpeta, ano_carpeta,
                                      titulo_resultado)

    if exacto:
        # El nombre de la carpeta es EXACTAMENTE el del resultado.
        puntos += 50
    elif c == r:
        puntos += 35
'''
if VIEJO_PUNTUAR_INICIO in t:
    t = t.replace(VIEJO_PUNTUAR_INICIO, NUEVO_PUNTUAR_INICIO, 1)
    hechos.append("posters.py: el nombre exacto de la carpeta suma 50")
elif NUEVO_PUNTUAR_INICIO not in t:
    raise SystemExit("no se encontro el bloque de titulos en puntuar()")

# --- 3) el +10 del tipo pedido, que nunca se daba ---
VIEJO_TIPO = '''    # Tipo pedido.
    if resultado.get("tipo") in (resultado.get("tipo_pedido"), None):
        puntos += 10
'''
NUEVO_TIPO = '''    # Tipo pedido (+10). Se comparan por familia para que "anime" cuente
    # como "serie" y "novelas" como "serie". Antes esta comparacion no
    # se hacia nunca y el bonus se perdia siempre.
    tipo_pedido = resultado.get("tipo_pedido")
    if tipo_pedido:
        f_real = _familia(resultado.get("tipo"))
        f_pedido = _familia(tipo_pedido)
        if f_real and f_pedido and f_real == f_pedido:
            puntos += 10
'''
if VIEJO_TIPO in t:
    t = t.replace(VIEJO_TIPO, NUEVO_TIPO, 1)
    hechos.append("posters.py: el +10 por tipo ahora se concede")
elif NUEVO_TIPO not in t:
    raise SystemExit("no se encontro el bloque del tipo en puntuar()")

# --- 4) elegir_mejor(): aceptar el nombre exacto sin ambiguedad ---
VIEJO_SOBRE = '''    puntuados.sort(key=lambda x: x["puntuacion"], reverse=True)

    sobre = [c for c in puntuados if c["puntuacion"] >= UMBRAL_ACEPTACION]

    if not sobre:
        return (None, "bajo_puntaje", puntuados[:10])
'''
NUEVO_SOBRE = '''    puntuados.sort(key=lambda x: x["puntuacion"], reverse=True)

    sobre = [c for c in puntuados if c["puntuacion"] >= UMBRAL_ACEPTACION]

    if not sobre:
        # El nombre de la carpeta es el mismo que el del resultado y no
        # hay otro igual: no es una adivinanza, asi que se acepta aunque
        # no llegue al umbral. Sin ano ni temporada el titulo identico se
        # queda en 50 puntos, y revisar 50 carpetas que si son esa misma
        # pelicula seria absurdo.
        exactos = []
        for c in puntuados:
            _c, _r, exacto = _comparar_titulos(titulo_carpeta, ano_carpeta,
                                                c.get("titulo"))
            if exacto:
                exactos.append(c)

        if len(exactos) == 1:
            exactos[0]["puntuacion"] = max(exactos[0]["puntuacion"],
                                           UMBRAL_ACEPTACION)
            puntuados.sort(key=lambda x: x["puntuacion"], reverse=True)
            return (exactos[0], "aceptado_exacto", puntuados[:10])

        if len(exactos) > 1:
            return (None, "empate", puntuados[:10])

        return (None, "bajo_puntaje", puntuados[:10])
'''
if VIEJO_SOBRE in t:
    t = t.replace(VIEJO_SOBRE, NUEVO_SOBRE, 1)
    hechos.append("posters.py: nombre exacto y unico se acepta")
elif NUEVO_SOBRE not in t:
    raise SystemExit("no se encontro elegir_mejor()")

io.open(RUTA_POSTERS, "w", encoding="utf-8", newline="\n").write(t)
ast.parse(t)

# =====================================================================
# fuentes.py
# =====================================================================
RUTA_FUENTES = raiz + r"\fuentes.py"
f = io.open(RUTA_FUENTES, encoding="utf-8").read()

TODAS = ('"tmdb_movie", "tmdb_tv", "anilist", "tvmaze", "openlibrary",\n'
         '              "googlebooks", "mangadex", "musicbrainz", "internetarchive"')
f = f.replace('    "otros": [', '    "todos": [%s],\n    "otros": [' % TODAS, 1)
hechos.append('fuentes.py: TIPOS_APIS["todos"] con todas las fuentes')

# Marcar cada candidato con el tipo que se pidio (para el +10).
VIEJO_BUSCAR = '''    candidatos = []
    for nombre in orden:
        try:
            if nombre == "tmdb_movie":'''
NUEVO_BUSCAR = '''    # Fuente -> tipo de contenido que representa.
    TIPO_DE_FUENTE = {
        "tmdb_movie": "pelicula",
        "tmdb_tv": "serie",
        "anilist": "anime",
        "tvmaze": "serie",
        "openlibrary": "libro",
        "googlebooks": "libro",
        "mangadex": "manga",
        "musicbrainz": "musica",
        "internetarchive": "pelicula",
    }

    # Que tipo pidio el usuario para cada fuente consultada.
    tipo_de_fuente = {}
    for t2 in (tipos or ["todos"]):
        for nombre in TIPOS_APIS.get(t2, []):
            tipo_de_fuente.setdefault(nombre, t2)

    candidatos = []
    for nombre in orden:
        try:
            if nombre == "tmdb_movie":'''
if VIEJO_BUSCAR in f:
    f = f.replace(VIEJO_BUSCAR, NUEVO_BUSCAR, 1)
    hechos.append("fuentes.py: tabla fuente -> tipo")
else:
    raise SystemExit("no se encontro buscar()")

VIEJO_EXTEND = '''            if r:
                candidatos.extend(r)
        except Exception as exc:
            _log("Fallo en %s: %s" % (nombre, exc), "ERROR")
            continue
'''
NUEVO_EXTEND = '''            if r:
                pedido = tipo_de_fuente.get(nombre)
                for cand in r:
                    # 6.5 El +10 de "es del tipo pedido" necesita saber
                    # que tipo se pidio cuando se consulto esta fuente.
                    cand["tipo_pedido"] = pedido or cand.get("tipo")
                    cand.setdefault("tipo", TIPO_DE_FUENTE.get(nombre))
                candidatos.extend(r)
        except Exception as exc:
            _log("Fallo en %s: %s" % (nombre, exc), "ERROR")
            continue
'''
if VIEJO_EXTEND in f:
    f = f.replace(VIEJO_EXTEND, NUEVO_EXTEND, 1)
    hechos.append("fuentes.py: cada candidato lleva el tipo pedido")
else:
    raise SystemExit("no se encontro la extension de candidatos")

# Alias: buscar por titulo parecido, no solo los 12 primeros de una fuente.
VIEJO_ALIAS = '''    # Alias de TMDB para los resultados queGanaron. Barato y util.
    try:
        for c in candidatos[:12]:
            if c.get("fuente") == "TMDB" and not c.get("alias") and c.get("id"):
                tipo = "tv" if c.get("tipo") == "serie" else "movie"
                alt = tmdb_alternativos(cfg, tipo, c["id"])
                if alt:
                    c["alias"] = alt
    except Exception:
        pass
'''
NUEVO_ALIAS = '''    # Alias de TMDB. Se piden para los candidatos MAS PARECIDOS al titulo
    # de la carpeta, no solo para los 12 primeros: si no, la pelicula que
    # gana puede quedarse sin alias y no llegar al umbral.
    try:
        def parecido(c):
            a = set(re.findall(r"\\w+", titulo.lower()))
            b = set(re.findall(r"\\w+", (c.get("titulo") or "").lower()))
            return len(a & b)

        ordenado = sorted(candidatos, key=parecido, reverse=True)
        pedidos = 0
        for c in ordenado:
            if pedidos >= 12:
                break
            if c.get("fuente") != "TMDB" or c.get("alias") or not c.get("id"):
                continue
            tipo = "tv" if c.get("tipo") == "serie" else "movie"
            alt = tmdb_alternativos(cfg, tipo, c["id"])
            if alt:
                c["alias"] = alt
            pedidos += 1
    except Exception:
        pass
'''
if VIEJO_ALIAS in f:
    f = f.replace(VIEJO_ALIAS, NUEVO_ALIAS, 1)
    hechos.append("fuentes.py: alias para los candidatos mas parecidos")
else:
    raise SystemExit("no se encontro el bloque de alias")

io.open(RUTA_FUENTES, "w", encoding="utf-8", newline="\n").write(f)
ast.parse(f)

print("Correcciones aplicadas:")
for h in hechos:
    print("   -", h)
print("sintaxis OK en posters.py y fuentes.py")