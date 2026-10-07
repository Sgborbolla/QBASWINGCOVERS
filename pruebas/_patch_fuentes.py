# -*- coding: utf-8 -*-
"""fuentes.py - agrega MangaDex, MusicBrainz, Internet Archive y las portadas de la portada."""
import io
import re

RUTA = r"C:\QBASWING-COVERS\fuentes.py"
texto = io.open(RUTA, encoding="utf-8").read()
hechos = []

if "def mangadex(" in texto:
    print("ya estaba aplicado")
    raise SystemExit(0)

NUEVAS = '''

# --------------------------------------------------------------------------
# Fuentes nuevas: MangaDex, MusicBrainz + Cover Art Archive, Internet Archive
# --------------------------------------------------------------------------

MANGADEX = "https://api.mangadex.org"
MANGADEX_CUBIERTA = "https://uploads.mangadex.org/covers"
MUSICBRAINZ = "https://musicbrainz.org/ws/2/release"
COVERART = "https://coverartarchive.org/release"
INTERNETARCHIVE = "https://archive.org/advancedsearch.php"


def _candidato(fuente, titulo, anio, url, tipo, extra=None):
    """Arma un resultado con la misma forma que usan las demas fuentes."""
    if not url or not titulo:
        return None
    c = {
        "fuente": fuente,
        "titulo": (titulo or "").strip(),
        "anio": anio or None,
        "poster_url": url,
        "tipo": tipo,
        "puntuacion": 0,
        "id": "",
        "alias": [],
        "temporadas": [],
        "descripcion": "",
    }
    if extra:
        c.update(extra)
    return c


def mangadex(titulo):
    """Manga y comics. Sin clave. Devuelve lista de candidatos."""
    if not titulo:
        return []
    clave = "mangadex|%s" % titulo.lower().strip()
    datos = cache_leer("fuente", clave)
    if datos is None:
        datos = _obtener(MANGADEX + "/manga",
                         {"limit": 6, "title[]": titulo,
                          "includes[]": "cover_art"})
        cache_escribir("fuente", clave, datos if datos is not None else [])

    salida = []
    for item in (datos or {}).get("data") or []:
        try:
            attrs = item.get("attributes") or {}
            nombres = attrs.get("title") or {}
            nombre = nombres.get("en") or nombres.get("ja") or ""
            if not nombre and attrs.get("altTitles"):
                alt = attrs["altTitles"]
                nombre = (alt[0].get("en") or alt[0].get("ja") or "")
            if not nombre:
                continue
            rel = item.get("relationships") or []
            archivo = ""
            for r in rel:
                if r.get("type") == "cover_art":
                    archivo = (r.get("attributes") or {}).get("fileName") or ""
            if not archivo:
                continue
            url = "%s/%s/%s" % (MANGADEX_CUBIERTA, item.get("id"), archivo)
            anio = None
            fy = ((attrs.get("year") or None))
            if fy:
                anio = fy
            c = _candidato("MangaDex", nombre, anio, url, "otro")
            if c:
                c["descripcion"] = "Manga"
                salida.append(c)
        except Exception:
            continue
    return salida[:4]


def musicbrainz(titulo):
    """Musica: MusicBrainz para el album y Cover Art Archive para la caratula."""
    if not titulo:
        return []
    clave = "musicbrainz|%s" % titulo.lower().strip()
    datos = cache_leer("fuente", clave)
    if datos is None:
        datos = _obtener(MUSICBRAINZ,
                         {"query": 'release:"%s"' % titulo, "fmt": "json",
                          "limit": 5},
                         headers={"User-Agent": USER_AGENT})
        cache_escribir("fuente", clave, datos if datos is not None else [])

    salida = []
    for rel in (datos or {}).get("releases") or []:
        try:
            rid = rel.get("id")
            if not rid:
                continue
            nombre = ((rel.get("title") or "").strip())
            if not nombre:
                continue
            anio = None
            fecha = rel.get("date") or ""
            if len(fecha) >= 4 and fecha[:4].isdigit():
                anio = fecha[:4]
            arte = ", ".join(
                (a.get("artist") or {}).get("name", "")
                for a in (rel.get("artist-credit") or [])[:2] if a.get("artist"))
            if arte:
                nombre = "%s - %s" % (arte, nombre)
            c = _candidato("MusicBrainz", nombre, anio,
                           "%s/%s/front" % (COVERART, rid), "otro")
            if c:
                c["descripcion"] = "Musica"
                salida.append(c)
        except Exception:
            continue
    return salida[:3]


def internetarchive(titulo):
    """Peliculas clasicas y documentales de dominio publico."""
    if not titulo:
        return []
    clave = "internetarchive|%s" % titulo.lower().strip()
    datos = cache_leer("fuente", clave)
    if datos is None:
        datos = _obtener(INTERNETARCHIVE,
                         {"q": 'title:"%s" AND mediatype:movies' % titulo,
                          "fl[]": ["identifier", "title", "year"],
                          "rows": 4, "output": "json"})
        cache_escribir("fuente", clave, datos if datos is not None else [])

    docs = (((datos or {}).get("response") or {}).get("docs")) or []
    salida = []
    for d in docs:
        try:
            ident = d.get("identifier")
            nombre = (d.get("title") or "").strip()
            if not ident or not nombre:
                continue
            c = _candidato("Internet Archive", nombre, d.get("year"),
                           "https://archive.org/services/img/%s" % ident,
                           "pelicula")
            if c:
                c["descripcion"] = "Cine clasico"
                salida.append(c)
        except Exception:
            continue
    return salida[:3]


# --------------------------------------------------------------------------
# Portadas para la portada del programa
# --------------------------------------------------------------------------

def portadas_destacadas(cfg, limite=12):
    """
    Posters reales para la pantalla de bienvenida.

    Se piden a TMDB (tendencia de la semana) y a AniList (anime popular).
    Se guardan en cache 7 dias. Si no hay internet se devuelve [] y la
    portada se dibuja sola con los iconos del programa.
    """
    clave = "portadas|v1|%d" % limite
    datos = cache_leer("portadas", clave)
    if datos is not None:
        return datos

    lista = []

    # --- TMDB: tendencia de la semana ---
    clave_api = (cfg or {}).get("tmdb_api_key") or ""
    if clave_api:
        try:
            datos = _obtener(TMDB_BASE + "trending/all/week",
                             {"api_key": clave_api, "language": "es"})
            for item in (datos or {}).get("results") or []:
                poster = item.get("poster_path")
                if not poster:
                    continue
                lista.append({
                    "url": TMDB_IMG + poster,
                    "titulo": item.get("title") or item.get("name") or "",
                    "tipo": "serie" if item.get("media_type") == "tv"
                            else "pelicula",
                    "puntuacion": item.get("vote_average") or 0,
                    "fuente": "TMDB",
                })
                if len(lista) >= limite:
                    break
        except Exception:
            pass

    # --- AniList: anime popular ---
    if len(lista) < limite:
        try:
            consulta = ("query($p:Int){Page(perPage:%d){media"
                        "(sort:POPULARITY_DESC,type:ANIME,isAdult:false)"
                        "{title{romaji}coverImage{large}averageScore}}}" % limite)
            datos = _post_json(ANILIST_URL, {"query": consulta, "variables": {}})
            for item in (((datos or {}).get("data") or {}).get("Page") or {}).get("media") or []:
                url = ((item.get("coverImage") or {}).get("large")) or ""
                if not url:
                    continue
                lista.append({
                    "url": url,
                    "titulo": (item.get("title") or {}).get("romaji") or "",
                    "tipo": "anime",
                    "puntuacion": (item.get("averageScore") or 0) / 10.0,
                    "fuente": "AniList",
                })
        except Exception:
            pass

    lista = lista[:limite]
    cache_escribir("portadas", clave, lista)
    return lista

'''

# insertar antes del bloque "Orquestador"
marcador = "# --------------------------------------------------------------------------\n# Orquestador"
if marcador not in texto:
    raise SystemExit("no se encontro la seccion Orquestador")
texto = texto.replace(marcador, NUEVAS.strip("\n") + "\n\n\n" + marcador, 1)
hechos.append("3 fuentes nuevas + portadas_destacadas()")

# --- registrar en TIPOS_APIS ---
texto = texto.replace(
    '    "novelas": ["tmdb_tv", "tvmaze"],\n'
    '    "otros": ["tmdb_movie", "tmdb_tv", "anilist", "tvmaze"],\n',
    '    "novelas": ["tmdb_tv", "tvmaze"],\n'
    '    "manga": ["mangadex"],\n'
    '    "musica": ["musicbrainz"],\n'
    '    "clasicos": ["internetarchive", "tmdb_movie"],\n'
    '    "otros": ["tmdb_movie", "tmdb_tv", "anilist", "tvmaze",\n'
    '              "mangadex", "musicbrainz", "internetarchive"],\n', 1)
hechos.append("TIPOS_APIS con manga, musica y clasicos")

# --- despacho en buscar() ---
texto = texto.replace(
    '            elif nombre == "googlebooks":\n'
    '                r = googlebooks(titulo)\n',
    '            elif nombre == "googlebooks":\n'
    '                r = googlebooks(titulo)\n'
    '            elif nombre == "mangadex":\n'
    '                r = mangadex(titulo)\n'
    '            elif nombre == "musicbrainz":\n'
    '                r = musicbrainz(titulo)\n'
    '            elif nombre == "internetarchive":\n'
    '                r = internetarchive(titulo)\n', 1)
hechos.append("buscar() despacha a las 3 fuentes nuevas")

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(texto)

import ast
ast.parse(io.open(RUTA, encoding="utf-8").read())
print("fuentes.py:")
for h in hechos:
    print("   -", h)
print("   sintaxis OK")