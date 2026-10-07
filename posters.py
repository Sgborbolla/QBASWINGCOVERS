# -*- coding: utf-8 -*-
"""
QBASWING COVERS - Limpieza de nombres, anio, temporada y puntuacion.

Reglas del documento de especificacion, seccion 6.
"""

import re
import unicodedata
from datetime import datetime

ANIO_MIN = 1888
ANIO_MAX = datetime.now().year + 2

UMBRAL_ACEPTACION = 60

# 6.1 Tags tecnicos que se eliminan antes de buscar en internet.
TAGS_TECNICOS = {
    "1080p", "720p", "480p", "576p", "4k", "8k", "hd", "fhd", "uhd",
    "x264", "x265", "h264", "h265", "hevc", "avc", "xvid", "divx",
    "bluray", "blu-ray", "bdrip", "brrip", "webrip", "web-dl", "webdl",
    "web", "dvdrip", "dvd", "dvdscr", "remux", "rip", "aac", "ac3",
    "hdtv", "hdrip", "10bit", "8bit", "hdr", "remastered", "repack",
    "eac3", "dts", "dts-hd", "truehd", "atmos", "flac", "mp3", "aac2",
    "subs", "sub", "dub", "dubbed", "latino", "lat", "espanol", "castellano",
    "spanish", "english", "eng", "spa", "multi", "multisub", "korsub",
    "am", "cam", "ts", "tc", "r5", "hc", "korsub", "vostfr", "vf",
}

# 6.3 Patrones de temporada reconocidos.
PATRONES_TEMPORADA = [
    re.compile(r"\btemporada[\s._-]*(\d{1,3})\b", re.IGNORECASE),
    re.compile(r"\bseason[\s._-]*(\d{1,3})\b", re.IGNORECASE),
    re.compile(r"\btemp[\s._-]*(\d{1,3})\b", re.IGNORECASE),
    re.compile(r"(?:^|[\s._\-\[(])[Tt](\d{1,3})(?:[\s._\-\])]|$)"),
    re.compile(r"(?:^|[\s._\-\[(])[Ss](\d{1,3})(?:[\s._\-\])]|$)"),
    re.compile(r"\b(\d{1,2})x(\d{1,3})\b"),
]

# Articulos que se pueden quitar o agregar al generar alias.
ARTICULOS = ("el", "la", "los", "las", "un", "una", "unos", "unas",
             "the", "a", "an")


def quitar_acentos(texto):
    """Sin tildes y sin enye. Base de toda comparacion."""
    if not texto:
        return ""
    normal = unicodedata.normalize("NFKD", texto)
    sin = "".join(c for c in normal if not unicodedata.combining(c))
    return sin.replace("\u00f1", "n").replace("\u00d1", "N")


def solo_emoji(nombre):
    """True si el nombre NO tiene letras ni digitos, solo simbolos."""
    if not nombre:
        return False
    limpio = re.sub(r"[\s\.\(\)\[\]\-_]+", "", nombre)
    if not limpio:
        return False
    for c in limpio:
        categoria = unicodedata.category(c)
        if categoria[0] in ("L", "N"):
            return False
    return True


def quitar_emoji(texto):
    """Elimina emojis y simbolos, deja letras, digitos y espacios."""
    if not texto:
        return ""
    # Emojis y similares por rango Unicode.
    sin_emoji = re.sub(
        "[\U0001F000-\U0001FAFF\U00002600-\U000027BF"
        "\U0001F1E6-\U0001F1FF\uFE0F\u200D]+",
        " ",
        texto,
    )
    # Emojis de banderas (pares de indicadores regionales).
    sin_emoji = re.sub(r"[\U0001F1E6-\U0001F1FF]{2}", " ", sin_emoji)
    return sin_emoji


def limpiar_nombre(carpeta):
    """
    6.1 Limpia el nombre de la carpeta.
        Entrada:  Matrix (1999) 1080p x264 Blu-Ray
        Salida:   Matrix (1999)
    """
    if not carpeta:
        return ""
    texto = quitar_emoji(carpeta)

    # Tags con guion: "Blu-Ray", "Web-DL", "DTS-HD". Se quitan enteros
    # ANTES de quitar los guiones, o se romperian en dos palabras.
    for tag in ("blu-ray", "web-dl", "dts-hd", "half-scd"):
        texto = re.sub(r"(?i)\b%s\b" % re.escape(tag), " ", texto)

    texto = re.sub(r"[^\w\s\(\)\[\]\.\-]", " ", texto, flags=re.UNICODE)
    texto = re.sub(r"[.\-_]+", " ", texto)

    palabras = texto.split()
    limpias = [p for p in palabras if quitar_acentos(p).lower() not in TAGS_TECNICOS]

    # Tags pegados al titulo: "Matrix2019", "Matrix1080p"
    if not limpias:
        limpias = palabras
    else:
        pegados = []
        for p in limpias:
            q = re.sub(r"(?i)(1080p|720p|480p|4k|x264|x265|h264|h265|"
                       r"bluray|blu-ray|bdrip|brrip|webrip|web-dl|webdl|"
                       r"hd|rip)$", "", p)
            if q and q != p:
                pegados.append(q)
            else:
                pegados.append(p)
        limpias = pegados

    texto = " ".join(limpias)

    # 6.3 El numero de temporada NO forma parte del titulo que se busca.
    # Se separa con extraer_temporada() y aqui se quita del texto.
    for patron in PATRONES_TEMPORADA:
        texto = patron.sub(" ", texto)
    texto = re.sub(r"[\(\[\s\-_]*(temporada|season|temp)[\s._\-]*[\(\[\s]*\d{1,3}[\s\)\]]*",
                   " ", texto, flags=re.IGNORECASE)

    texto = re.sub(r"\(\s*\)|\[\s*\]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.strip(" .-_") if texto else carpeta.strip()


def extraer_anio(carpeta):
    """
    6.2 Busca un ano de 4 digitos entre 1888 y el ano actual + 2.
        Primero entre parentesis, luego en cualquier parte.
    """
    if not carpeta:
        return None
    limite = ANIO_MAX

    for patron in (
        r"\((\d{4})\)",
        r"\[(\d{4})\]",
        r"(?:^|[\s._\-])(\d{4})(?:[\s._\-]|$)",
        r"\b(\d{4})\b",
    ):
        for m in re.finditer(patron, carpeta):
            try:
                ano = int(m.group(1))
            except (ValueError, IndexError):
                continue
            if ANIO_MIN <= ano <= limite:
                return ano
    return None


def quitar_anio_del_titulo(titulo, ano):
    """Saca el ano del titulo para buscar solo por el nombre."""
    if not titulo or ano is None:
        return titulo
    limpio = re.sub(r"\(\s*%d\s*\)" % ano, " ", titulo)
    limpio = re.sub(r"\[\s*%d\s*\]" % ano, " ", limpio)
    limpio = re.sub(r"\b%d\b" % ano, " ", limpio)
    limpio = re.sub(r"\s+", " ", limpio).strip(" .-_[]()")
    return limpio or titulo


def extraer_temporada(carpeta):
    """
    6.3 Detecta el numero de temporada.
        Acepta T1, S1, T1-S1, Temporada 01, Season 1, 1x2.
    """
    if not carpeta:
        return None
    for patron in PATRONES_TEMPORADA:
        m = patron.search(carpeta)
        if not m:
            continue
        grupo = m.groups()
        numero = grupo[-1] if len(grupo) > 1 else grupo[0]
        try:
            n = int(numero)
        except (TypeError, ValueError):
            continue
        if 0 < n <= 999:
            return n
    return None


def es_pelicula_de_serie(nombre):
    """Heuristica: 'Serie S01E02' indica que la carpeta es de serie."""
    return bool(re.search(r"[Ss]\d{1,2}\s?[Ee]\d{1,3}", nombre or ""))


def generar_alias(titulo, ano=None):
    """
    6.4 Genera los candidatos de busqueda a partir del nombre de la carpeta.
        Devuelve una lista sin repetir y sin vacios.
    """
    alias = []
    if not titulo:
        return alias

    def anadir(valor):
        valor = (valor or "").strip()
        if valor and valor not in alias:
            alias.append(valor)

    anadir(titulo)

    sin_acentos = quitar_acentos(titulo)
    anadir(sin_acentos)
    anadir(sin_acentos.lower())

    # Sin articulos iniciales: "El Ultimo Samurai" -> "Ultimo Samurai"
    palabras = sin_acentos.split()
    if palabras and quitar_acentos(palabras[0]).lower() in ARTICULOS:
        anadir(" ".join(palabras[1:]))

    # Con articulo agregado: "Ultimo Samurai" -> "The Ultimo Samurai"
    if palabras and quitar_acentos(palabras[0]).lower() not in ARTICULOS:
        anadir("The " + sin_acentos)
        anadir("El " + sin_acentos)
        anadir("La " + sin_acentos)

    # Con el ano (seccion 6.1: se envia "Matrix" y "Matrix 1999")
    if ano:
        try:
            n = int(ano)
        except (TypeError, ValueError):
            n = None
        if n:
            anadir("%s %d" % (sin_acentos, n))
            anadir("%s (%d)" % (sin_acentos, n))

    return alias


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
        c = re.sub(r"\b%d\b" % int(ano_compara), " ", c).strip(" ()[]-.")
        r = re.sub(r"\b%d\b" % int(ano_compara), " ", r).strip(" ()[]-.")

    c = re.sub(r"\s+", " ", c).strip()
    r = re.sub(r"\s+", " ", r).strip()
    return c, r, (bool(c) and c == r)


def _palabras(texto):
    return set(re.findall(r"\w+", quitar_acentos(texto or "").lower()))


def _entero(valor):
    try:
        return int(valor) if valor not in (None, "") else None
    except (TypeError, ValueError):
        return None


def puntuar(titulo_carpeta, ano_carpeta, temporada_carpeta, resultado):
    """
    6.5 Puntua un resultado devuelto por una API.

        +50  coincide exactamente
        +35  coincide ignorando mayusculas y acentos
        +30  coincide un alias en otro idioma
        +25  el ano coincide
        +15  la temporada pedida existe
        +10  es del tipo pedido
        -40  el ano NO coincide
        -30  diferencia de longitud mayor a 6 caracteres
        -25  no comparte ninguna palabra
    """
    titulo_resultado = (resultado.get("titulo") or "").strip()
    if not titulo_resultado:
        return 0

    puntos = 0

    # Anios primero: se necesitan para comparar bien los titulos.
    ano_resultado = _entero(resultado.get("ano"))
    ano_carpeta = _entero(ano_carpeta)

    # Los titulos se comparan sin el ano: "Matrix (1999)" y "Matrix"
    # son el mismo nombre, y el ano ya se puntua aparte.
    c, r, exacto = _comparar_titulos(titulo_carpeta, ano_carpeta,
                                      titulo_resultado)

    if exacto:
        # El nombre de la carpeta es EXACTAMENTE el del resultado.
        puntos += 50
    elif c == r:
        puntos += 35

    # Alias en otro idioma (seccion 6.4).
    for alias in resultado.get("alias") or []:
        a = quitar_acentos(alias or "").strip().lower()
        if not a:
            continue
        if a == c or a == r:
            puntos += 30
            break

    # Ano.

    if ano_carpeta and ano_resultado:
        if ano_carpeta == ano_resultado:
            puntos += 25
        else:
            puntos -= 40

    # Temporada.
    if temporada_carpeta is not None:
        temporadas = resultado.get("temporadas") or []
        numeros = []
        for t in temporadas:
            try:
                numeros.append(int(t))
            except (TypeError, ValueError):
                continue
        try:
            pedida = int(temporada_carpeta)
        except (TypeError, ValueError):
            pedida = None
        if pedida is not None and pedida in numeros:
            puntos += 15

    # Tipo pedido (+10). Se comparan por familia para que "anime" cuente
    # como "serie" y "novelas" como "serie". Antes esta comparacion no
    # se hacia nunca y el bonus se perdia siempre.
    tipo_pedido = resultado.get("tipo_pedido")
    if tipo_pedido:
        f_real = _familia(resultado.get("tipo"))
        f_pedido = _familia(tipo_pedido)
        if f_real and f_pedido and f_real == f_pedido:
            puntos += 10

    # Longitud muy distinta.
    if abs(len(c) - len(r)) > 6:
        puntos -= 30

    # Ninguna palabra en comun.
    pc = _palabras(c)
    pr = _palabras(r)
    if pc and pr and not pc.intersection(pr):
        puntos -= 25

    return max(0, puntos)


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
    base = re.sub(r"[^a-z0-9\u00c0-\uffff ]+", " ", base)
    return re.sub(r"\s+", " ", base).strip()


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


def elegir_mejor(candidatos, titulo_carpeta, ano_carpeta, temporada_carpeta):
    """
    6.6 Aplica el umbral de 60 puntos y resuelve empates.
        Devuelve (mejor, motivo). mejor es None si no se puede decidir.
        Motivo: 'aceptado', 'empate' o 'bajo_puntaje'.
    """
    puntuados = []
    for c in candidatos or []:
        p = puntuar(titulo_carpeta, ano_carpeta, temporada_carpeta, c)
        c = dict(c)
        c["puntuacion"] = p
        puntuados.append(c)

    puntuados.sort(key=lambda x: x["puntuacion"], reverse=True)

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

        if exactos:
            # Varias fuentes pueden traer el mismo nombre exacto.
            # Si es el mismo contenido, gana la mejor fuente.
            ganador = _desempatar(exactos)
            if ganador is not None:
                ganador["puntuacion"] = max(ganador["puntuacion"],
                                            UMBRAL_ACEPTACION)
                puntuados.sort(key=lambda x: x["puntuacion"], reverse=True)
                return (ganador, "aceptado_exacto", puntuados[:10])
            return (None, "empate", puntuados[:10])

        return (None, "bajo_puntaje", puntuados[:10])

    if len(sobre) >= 2 and sobre[0]["puntuacion"] == sobre[1]["puntuacion"]:
        # Mismo titulo desde varias fuentes: no es ambiguedad.
        ganador = _desempatar([c for c in sobre
                               if c["puntuacion"] == sobre[0]["puntuacion"]])
        if ganador is not None:
            return (ganador, "aceptado", puntuados[:10])
        # Titulos distintos con la misma puntuacion: revision manual.
        return (None, "empate", puntuados[:10])

    return (sobre[0], "aceptado", puntuados[:10])