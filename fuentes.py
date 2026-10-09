# -*- coding: utf-8 -*-
"""
QBASWING COVERS - Clientes de las fuentes de posters audiovisuales.

TMDB requiere clave API; AniList y TVmaze no.

7.6 Manejo de fallos: 2 reintentos con espera, se anota en el log
y se continua con las demas carpetas. Un fallo de internet nunca
detiene el escaneo completo.
"""

import os
import re
import json
import time
import socket
import hashlib
import ipaddress
import threading
from pathlib import Path
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

import rutas

BASE_DIR = rutas.base_dir()
CACHE_DIR = BASE_DIR / "cache"

HTTP_TIMEOUT = 15
HTTP_RETRIES = 2
CACHE_DIAS = 30

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QBASWINGCovers/1.0"

TMDB_BASE = "https://api.themoviedb.org/3/"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"
ANILIST_URL = "https://graphql.anilist.co"
TVMAZE_SEARCH = "https://api.tvmaze.com/search/shows"
OPENLIBRARY = "https://openlibrary.org/search.json"
GOOGLEBOOKS = "https://www.googleapis.com/books/v1/volumes"

_cache_memoria = {}


def _log(mensaje, nivel="INFO"):
    try:
        from qbaswing_covers import log
        log(mensaje, nivel)
    except Exception:
        pass


# --------------------------------------------------------------------------
# 7.6 Llamadas medidas: espaciadas y con pausa si una API contesta 429/503
# --------------------------------------------------------------------------

_intervalo_host = {}    # host -> momento de la ultima llamada
_en_pausa = {}           # host -> momento en que se levanta la pausa
_candado_llamadas = threading.Lock()

# Hostes que piden 1 llamada por segundo en su politica de uso.
_HOSTES_LENTOS = {
    "musicbrainz.org": 1.1,
    "coverartarchive.org": 1.1,
    "archive.org": 1.1,
    "web.archive.org": 1.1,
}
INTERVALO_HOST = 0.4     # resto de APIs: poco espacio entre llamadas
PAUSA_LIMITE = 300       # 5 minutos tras un 429/503 persistente


def _host_de(url):
    try:
        return url.split("/")[2].lower().split(":")[0]
    except Exception:
        return ""


def _es_ip_o_local(host):
    """
    True si el host es una IP (127.0.0.1, 192.168.x...) o localhost.
    Para esos no tiene sentido probar primero HTTPS: son servidores
    locales o de red que responden solo por http.
    """
    if not host:
        return True
    if host.lower() in ("localhost", "localhost."):
        return True
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _host_en_pausa(host):
    if not host:
        return False
    with _candado_llamadas:
        pausa = _en_pausa.get(host)
        if not pausa:
            return False
        if time.time() < pausa:
            return True
        _en_pausa.pop(host, None)
        return False


def _esperar_turno(host):
    """Espacia las llamadas al mismo servidor."""
    if not host:
        return
    with _candado_llamadas:
        ultimo = _intervalo_host.get(host, 0.0)
        espera = (ultimo + _HOSTES_LENTOS.get(host, INTERVALO_HOST)
                  - time.time())
    if espera > 0:
        time.sleep(espera)


def _anotar_llamada(host):
    if host:
        with _candado_llamadas:
            _intervalo_host[host] = time.time()


def _pausar_host(host, motivo):
    """429/503: esa API deja de consultarse durante un rato (una vez)."""
    if not host:
        return
    with _candado_llamadas:
        if host in _en_pausa:
            return
        _en_pausa[host] = time.time() + PAUSA_LIMITE
    _log("API %s en pausa %d s (%s)" % (host, PAUSA_LIMITE, motivo),
         "WARNING")


def _espera_servidor(exc, intento):
    """429/503: se respeta Retry-After si el servidor lo manda."""
    try:
        texto = exc.headers.get("Retry-After")
        if texto:
            return min(float(texto), 20.0)
    except Exception:
        pass
    return 2.0 * (intento + 1)


# --------------------------------------------------------------------------
# 8. Cache de 30 dias
# --------------------------------------------------------------------------

def _cache_ruta(clave):
    h = hashlib.sha1(clave.encode("utf-8", "replace")).hexdigest()
    return CACHE_DIR / (h + ".json")


def cache_leer(capa, clave):
    """Devuelve el valor cacheado, o None si no existe o vencio."""
    combinado = "%s|%s" % (capa, clave)
    if combinado in _cache_memoria:
        return _cache_memoria[combinado]

    ruta = _cache_ruta(combinado)
    try:
        if not ruta.exists():
            return None
        edad = time.time() - ruta.stat().st_mtime
        if edad > CACHE_DIAS * 86400:
            ruta.unlink()
            return None
        with open(ruta, "r", encoding="utf-8") as f:
            valor = json.load(f)
        _cache_memoria[combinado] = valor
        return valor
    except Exception:
        return None


def cache_escribir(capa, clave, valor):
    combinado = "%s|%s" % (capa, clave)
    _cache_memoria[combinado] = valor
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(_cache_ruta(combinado), "w", encoding="utf-8") as f:
            json.dump(valor, f, ensure_ascii=False)
    except Exception as exc:
        _log("Cache no escrita: %s" % exc, "ERROR")


# --------------------------------------------------------------------------
# 7.6 HTTP con reintentos
# --------------------------------------------------------------------------

def _obtener(url, params=None, headers=None, binario=False):
    if params:
        limpio = {k: v for k, v in params.items() if v not in (None, "")}
        if limpio:
            url = url + ("&" if "?" in url else "?") + urlencode(limpio)

    cab = {"User-Agent": USER_AGENT, "Accept-Language": "es,en;q=0.8"}
    if headers:
        cab.update(headers)

    host = _host_de(url)
    ultimo = None
    for intento in range(HTTP_RETRIES + 1):
        if _host_en_pausa(host):
            return None
        _esperar_turno(host)
        _anotar_llamada(host)
        try:
            req = Request(url, headers=cab)
            with urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                datos = resp.read()
            if binario:
                return datos
            texto = datos.decode("utf-8", "replace")
            if not texto.strip():
                return None
            try:
                return json.loads(texto)
            except ValueError:
                return None
        except HTTPError as exc:
            ultimo = exc
            if exc.code in (401, 403, 404, 422):
                return None
            if exc.code in (429, 503):
                time.sleep(_espera_servidor(exc, intento))
            else:
                time.sleep(1 + intento)
        except (URLError, socket.timeout, OSError, ValueError) as exc:
            ultimo = exc
            time.sleep(1 + intento)

    if isinstance(ultimo, HTTPError) and ultimo.code in (429, 503):
        _pausar_host(host, "HTTP %d" % ultimo.code)
    _log("Fallo HTTP %s (%s)" % (url[:100], ultimo), "ERROR")
    return None


def _post_json(url, payload, headers=None):
    cab = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}
    if headers:
        cab.update(headers)
    cuerpo = json.dumps(payload).encode("utf-8")
    host = _host_de(url)
    ultimo = None
    for intento in range(HTTP_RETRIES + 1):
        if _host_en_pausa(host):
            return None
        _esperar_turno(host)
        _anotar_llamada(host)
        try:
            req = Request(url, data=cuerpo, headers=cab)
            with urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except HTTPError as exc:
            ultimo = exc
            if exc.code in (401, 403, 404, 422):
                return None
            if exc.code in (429, 503):
                time.sleep(_espera_servidor(exc, intento))
            else:
                time.sleep(1 + intento)
        except (URLError, socket.timeout, OSError, ValueError) as exc:
            ultimo = exc
            time.sleep(1 + intento)
    if isinstance(ultimo, HTTPError) and ultimo.code in (429, 503):
        _pausar_host(host, "HTTP %d" % ultimo.code)
    _log("Fallo POST %s (%s)" % (url[:100], ultimo), "ERROR")
    return None


def descargar_binario(url):
    """
    Descarga la imagen. Devuelve los bytes, o None.
    Se prefiere HTTPS; si el servidor no lo soporta se intenta la URL original.
    En IPs y localhost se usa la URL tal cual: probar HTTPS primero solo
    alarga la espera contra servidores que responden solo por http.
    """
    if not url:
        return None

    candidatos = [url]
    if url.startswith("http://") and not _es_ip_o_local(_host_de(url)):
        candidatos.insert(0, "https://" + url[len("http://"):])

    host = _host_de(url)
    ultimo = None
    for candidato in candidatos:
        for intento in range(HTTP_RETRIES + 1):
            if _host_en_pausa(host):
                return None
            _esperar_turno(host)
            _anotar_llamada(host)
            try:
                req = Request(candidato, headers={"User-Agent": USER_AGENT})
                with urlopen(req, timeout=HTTP_TIMEOUT * 3) as resp:
                    return resp.read()
            except Exception as exc:
                ultimo = exc
                if isinstance(exc, HTTPError) and exc.code in (429, 503):
                    time.sleep(_espera_servidor(exc, intento))
                else:
                    time.sleep(1 + intento)
    if isinstance(ultimo, HTTPError) and ultimo.code in (429, 503):
        _pausar_host(host, "HTTP %d" % ultimo.code)
    _log("Fallo al descargar imagen %s (%s)"
         % (url.split("?", 1)[0][:100], ultimo), "ERROR")
    return None


# --------------------------------------------------------------------------
# 7.1 TMDB
# --------------------------------------------------------------------------

def _tmdb_headers(clave):
    return {"Authorization": "Bearer %s" % clave,
            "Accept": "application/json"}


def _tmdb_peticion(cfg, endpoint, params=None):
    clave = cfg.get("tmdb_api_key") or ""
    if not clave:
        return None
    url = (cfg.get("tmdb_api_url") or TMDB_BASE).rstrip("/") + "/" + endpoint.lstrip("/")
    completo = {"language": "es-ES", "include_adult": "false"}
    if params:
        completo.update(params)
    completo["api_key"] = clave
    return _obtener(url, completo)


def tmdb_pelicula(cfg, titulo, ano=None):
    """7.1 /search/movie"""
    clave_cache = "tmdb_movie|v2|%s|%s" % (titulo, ano or "")
    guardado = cache_leer("tmdb_movie", clave_cache)
    if guardado is not None:
        return guardado

    params = {"query": titulo}
    if ano:
        try:
            params["primary_release_year"] = str(int(ano))
        except (TypeError, ValueError):
            pass

    r = _tmdb_peticion(cfg, "search/movie", params)
    if r is None:
        return None

    resultados = []
    for item in (r.get("results") or [])[:20]:
        poster = item.get("poster_path")
        anio = (item.get("release_date") or "")[:4]
        try:
            anio = int(anio) if anio else None
        except ValueError:
            anio = None
        titulo_loc = item.get("title") or ""
        orig = item.get("original_title") or ""
        resultados.append({
            "titulo": titulo_loc,
            "ano": anio,
            "tipo": "pelicula",
            "fuente": "TMDB",
            "poster_url": (TMDB_IMG + poster) if poster else None,
            "id": item.get("id"),
            "temporadas": [],
            # 6.1 Paso 4: el titulo ORIGINAL en su idioma vale como
            # alias (Matrix / The Matrix). alternative_titles no lo
            # devuelve nunca porque es el titulo primario.
            "alias": ([orig] if orig and orig != titulo_loc else []),
        })
    cache_escribir("tmdb_movie", clave_cache, resultados)
    return resultados


def tmdb_serie(cfg, titulo, ano=None):
    """7.1 /search/tv"""
    clave_cache = "tmdb_tv|v2|%s|%s" % (titulo, ano or "")
    guardado = cache_leer("tmdb_tv", clave_cache)
    if guardado is not None:
        return guardado

    params = {"query": titulo}
    if ano:
        try:
            params["first_air_date_year"] = str(int(ano))
        except (TypeError, ValueError):
            pass

    r = _tmdb_peticion(cfg, "search/tv", params)
    if r is None:
        return None

    resultados = []
    for item in (r.get("results") or [])[:20]:
        poster = item.get("poster_path")
        anio = (item.get("first_air_date") or "")[:4]
        try:
            anio = int(anio) if anio else None
        except ValueError:
            anio = None
        try:
            n_temporadas = int(item.get("number_of_seasons") or 0)
        except (TypeError, ValueError):
            n_temporadas = 0
        resultados.append({
            "titulo": item.get("name") or "",
            "ano": anio,
            "tipo": "serie",
            "fuente": "TMDB",
            "poster_url": (TMDB_IMG + poster) if poster else None,
            "id": item.get("id"),
            "temporadas": list(range(1, n_temporadas + 1)) if n_temporadas else [],
            # 6.1 Paso 4: titulo original como alias, igual que en las
            # peliculas (serie en espanol con nombre original ingles).
            "alias": ([item.get("original_name")]
                      if item.get("original_name")
                      and item.get("original_name") != (item.get("name") or "")
                      else []),
        })
    cache_escribir("tmdb_tv", clave_cache, resultados)
    return resultados


def tmdb_alternativos(cfg, tipo, id_):
    """7.1 /movie/{id}/alternative_titles para los alias multidioma."""
    if not id_:
        return []
    clave_cache = "tmdb_alt|%s|%s" % (tipo, id_)
    guardado = cache_leer("tmdb_alt", clave_cache)
    if guardado is not None:
        return guardado

    r = _tmdb_peticion(cfg, "%s/%s/alternative_titles" % (tipo, id_))
    if r is None:
        return []

    alias = []
    for bloque in (r.get("titles") or [])[:40]:
        titulo = bloque.get("title")
        if titulo and titulo not in alias:
            alias.append(titulo)
    cache_escribir("tmdb_alt", clave_cache, alias)
    return alias


def tmdb_poster_temporada(cfg, id_serie, temporada):
    """
    6.3 Pide el poster de esa temporada, que es distinto del general.
    7.1 /tv/{id}/season/{n}/images
    """
    if not id_serie or temporada is None:
        return None
    clave_cache = "tmdb_temp|%s|%s" % (id_serie, temporada)
    guardado = cache_leer("tmdb_temp", clave_cache)
    if guardado is not None:
        return guardado

    r = _tmdb_peticion(cfg, "tv/%s/season/%s/images" % (id_serie, temporada))
    url = None
    if r:
        posters = r.get("posters") or []
        # 6.7 Si hay varias, la de mayor resolucion.
        if posters:
            mejor = max(posters, key=lambda p: p.get("width") or 0)
            if mejor.get("file_path"):
                url = TMDB_IMG + mejor["file_path"]
    cache_escribir("tmdb_temp", clave_cache, url)
    return url


# --------------------------------------------------------------------------
# 7.2 AniList
# --------------------------------------------------------------------------

ANILIST_QUERY = """
query ($search: String, $tipo: MediaType) {
  Page(page: 1, perPage: 12) {
    media(search: $search, type: $tipo) {
      id
      title { romaji english native }
      startDate { year }
      coverImage { extraLarge large medium }
      format
    }
  }
}
"""


def anilist(titulo, tipo="ANIME"):
    clave_cache = "anilist|%s|%s" % (titulo, tipo)
    guardado = cache_leer("anilist", clave_cache)
    if guardado is not None:
        return guardado

    r = _post_json(ANILIST_URL, {
        "query": ANILIST_QUERY,
        "variables": {"search": titulo, "tipo": tipo},
    })
    if not r:
        return None

    resultados = []
    datos = r.get("data") or {}
    for item in ((datos.get("Page") or {}).get("media") or []):
        titulos = item.get("title") or {}
        nombre = titulos.get("english") or titulos.get("romaji") or titulos.get("native") or ""
        if not nombre:
            continue
        portada = item.get("coverImage") or {}
        imagen = portada.get("extraLarge") or portada.get("large") or portada.get("medium")
        anio = (item.get("startDate") or {}).get("year")
        alias = [v for v in (titulos.get("romaji"), titulos.get("english"),
                             titulos.get("native")) if v]
        resultados.append({
            "titulo": nombre,
            "ano": anio,
            "tipo": "anime",
            "fuente": "AniList",
            "poster_url": imagen,
            "id": item.get("id"),
            "temporadas": [],
            "alias": alias,
        })
    cache_escribir("anilist", clave_cache, resultados)
    return resultados


# --------------------------------------------------------------------------
# 7.3 TVmaze
# --------------------------------------------------------------------------

def tvmaze(titulo):
    clave_cache = "tvmaze|%s" % titulo
    guardado = cache_leer("tvmaze", clave_cache)
    if guardado is not None:
        return guardado

    r = _obtener(TVMAZE_SEARCH, {"q": titulo})
    if r is None:
        return None

    resultados = []
    for item in (r or [])[:12]:
        show = item.get("show") or {}
        imagen = ((show.get("image") or {}).get("original")
                  or (show.get("image") or {}).get("medium"))
        if not imagen:
            continue
        anio = (show.get("premiered") or "")[:4]
        try:
            anio = int(anio) if anio else None
        except ValueError:
            anio = None
        resultados.append({
            "titulo": show.get("name") or "",
            "ano": anio,
            "tipo": "serie",
            "fuente": "TVmaze",
            "poster_url": imagen,
            "id": show.get("id"),
            "temporadas": [],
            "alias": [],
        })
    cache_escribir("tvmaze", clave_cache, resultados)
    return resultados


# --------------------------------------------------------------------------
# 7.4 Open Library
# --------------------------------------------------------------------------

def openlibrary(titulo):
    clave_cache = "openlibrary|%s" % titulo
    guardado = cache_leer("openlibrary", clave_cache)
    if guardado is not None:
        return guardado

    r = _obtener(OPENLIBRARY, {"title": titulo, "limit": 12})
    if r is None:
        return None

    resultados = []
    for doc in (r.get("docs") or [])[:12]:
        # En Open Library, "cover_edition_key" es un texto (p. ej. "OL12345M"),
        # no una lista; "cover_i" es el identificador numerico de la portada.
        cover_i = doc.get("cover_i")
        portada = doc.get("cover_edition_key")
        if isinstance(portada, (list, tuple)):
            portada = portada[0] if portada else None
        isbn = doc.get("isbn") or []
        if cover_i:
            imagen = "https://covers.openlibrary.org/b/id/%s-L.jpg" % cover_i
        elif portada:
            imagen = "https://covers.openlibrary.org/b/olid/%s-L.jpg" % portada
        elif isbn:
            imagen = "https://covers.openlibrary.org/b/isbn/%s-L.jpg" % isbn[0]
        else:
            imagen = None
        alias = [a for a in (doc.get("alternate_titles") or []) if a]
        resultados.append({
            "titulo": doc.get("title") or "",
            "ano": doc.get("first_publish_year"),
            "tipo": "novela",
            "fuente": "OpenLibrary",
            "poster_url": imagen,
            "id": doc.get("key"),
            "temporadas": [],
            "alias": alias[:20],
        })
    cache_escribir("openlibrary", clave_cache, resultados)
    return resultados


# --------------------------------------------------------------------------
# 7.5 Google Books
# --------------------------------------------------------------------------

def googlebooks(titulo):
    clave_cache = "googlebooks|%s" % titulo
    guardado = cache_leer("googlebooks", clave_cache)
    if guardado is not None:
        return guardado

    r = _obtener(GOOGLEBOOKS, {"q": titulo, "maxResults": 12})
    if r is None:
        return None

    resultados = []
    for item in (r.get("items") or [])[:12]:
        info = item.get("volumeInfo") or {}
        enlaces = info.get("imageLinks") or {}
        imagen = enlaces.get("thumbnail") or enlaces.get("smallThumbnail")
        if imagen:
            imagen = imagen.replace("http://", "https://")
            # Pedir la portada grande cuando se puede.
            imagen = imagen.replace("&edge=curl", "")
            if "zoom=" in imagen:
                imagen = re.sub(r"zoom=\d+", "zoom=2", imagen)
        anio = (info.get("publishedDate") or "")[:4]
        try:
            anio = int(anio) if anio else None
        except ValueError:
            anio = None
        titulos_alt = []
        if info.get("subtitle"):
            titulos_alt.append("%s: %s" % (info.get("title", ""), info.get("subtitle")))
        resultados.append({
            "titulo": info.get("title") or "",
            "ano": anio,
            "tipo": "novela",
            "fuente": "GoogleBooks",
            "poster_url": imagen,
            "id": item.get("id"),
            "temporadas": [],
            "alias": titulos_alt,
        })
    cache_escribir("googlebooks", clave_cache, resultados)
    return resultados


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
        # La API acepta "title" sin corchetes pero "includes[]" con ellos.
        # Con "title[]" responde 400.
        datos = _obtener(MANGADEX + "/manga",
                         {"limit": 6, "title": titulo,
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
            # Ojo: si se declara una variable y no se usa, AniList
            # contesta 400 y no llega ni un cartel de anime.
            consulta = ("query($p:Int){Page(perPage:$p){media"
                        "(sort:POPULARITY_DESC,type:ANIME,isAdult:false)"
                        "{title{romaji}coverImage{large}averageScore}}}")
            datos = _post_json(ANILIST_URL, {"query": consulta,
                                             "variables": {"p": limite}})
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


# --------------------------------------------------------------------------
# Orquestador
# --------------------------------------------------------------------------

TIPOS_APIS = {
    "series": ["tmdb_tv", "tvmaze"],
    "peliculas": ["tmdb_movie"],
    "animes": ["anilist", "tmdb_tv", "tmdb_movie"],
    "documentales": ["tmdb_movie", "tmdb_tv", "tvmaze"],
    "novelas": ["tmdb_tv", "tvmaze"],
    "clasicos": ["internetarchive", "tmdb_movie"],
    # Lista completa: solo APIs de video. El programa no busca
    # musica ni manga (el usuario no los guarda) ni libros (7.4, 7.5).
    "todos": ["tmdb_movie", "tmdb_tv", "anilist", "tvmaze",
              "internetarchive"],
    "otros": ["tmdb_movie", "tmdb_tv", "anilist", "tvmaze",
              "internetarchive"],
}


def buscar(cfg, titulo, ano, temporada, tipos):
    """
    Consulta las APIs que corresponden a los tipos elegidos y
    devuelve la lista de candidatos. Nunca lanza excepcion.
    """
    consultas = []
    for t in (tipos or ["todos"]):
        consultas.extend(TIPOS_APIS.get(t, []))

    # Un tipo que no exista no deja la busqueda sin APIs.
    if not consultas:
        consultas = list(TIPOS_APIS["todos"])

    vistos = set()
    orden = []
    for c in consultas:
        if c not in vistos:
            vistos.add(c)
            orden.append(c)

    # Fuente -> tipo de contenido que representa.
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
            if nombre == "tmdb_movie":
                r = tmdb_pelicula(cfg, titulo, ano)
            elif nombre == "tmdb_tv":
                r = tmdb_serie(cfg, titulo, ano)
            elif nombre == "anilist":
                r = anilist(titulo)
            elif nombre == "tvmaze":
                r = tvmaze(titulo)
            elif nombre == "openlibrary":
                r = openlibrary(titulo)
            elif nombre == "googlebooks":
                r = googlebooks(titulo)
            elif nombre == "mangadex":
                r = mangadex(titulo)
            elif nombre == "musicbrainz":
                r = musicbrainz(titulo)
            elif nombre == "internetarchive":
                r = internetarchive(titulo)
            else:
                r = None
            if r:
                pedido = tipo_de_fuente.get(nombre)
                for cand in r:
                    # 6.5 El +10 de "es del tipo pedido" necesita saber
                    # que tipo se pidio cuando se consulto esta fuente.
                    # Se copia: lo que viene de la cache no se toca, para
                    # que una segunda busqueda no pise lo de la primera.
                    nuevo = dict(cand)
                    nuevo["tipo_pedido"] = pedido or cand.get("tipo")
                    nuevo.setdefault("tipo", TIPO_DE_FUENTE.get(nombre))
                    candidatos.append(nuevo)
        except Exception as exc:
            _log("Fallo en %s: %s" % (nombre, exc), "ERROR")
            continue

    # Alias de TMDB. Se piden para los candidatos MAS PARECIDOS al titulo
    # de la carpeta, no solo para los 12 primeros: si no, la pelicula que
    # gana puede quedarse sin alias y no llegar al umbral.
    try:
        def parecido(c):
            a = set(re.findall(r"\w+", titulo.lower()))
            b = set(re.findall(r"\w+", (c.get("titulo") or "").lower()))
            return len(a & b)

        ordenado = sorted(candidatos, key=parecido, reverse=True)
        pedidos = 0
        for c in ordenado:
            if pedidos >= 12:
                break
            if c.get("fuente") != "TMDB" or not c.get("id"):
                continue
            tipo = "tv" if c.get("tipo") == "serie" else "movie"
            alt = tmdb_alternativos(cfg, tipo, c["id"])
            if alt:
                # Se SUMAN a los alias que ya trae (el titulo original
                # de la busqueda): los regionales no lo sustituyen.
                base = c.get("alias") or []
                for a in alt:
                    if a and a not in base:
                        base.append(a)
                c["alias"] = base
            pedidos += 1
    except Exception:
        pass

    return candidatos


def poster_de_temporada(cfg, tipo, id_, temporada):
    """6.3 Poster especifico de la temporada, si la API lo tiene."""
    if tipo != "serie" or temporada is None or not id_:
        return None
    try:
        return tmdb_poster_temporada(cfg, id_, temporada)
    except Exception:
        return None