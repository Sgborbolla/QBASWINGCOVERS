# -*- coding: utf-8 -*-
"""
QBASWING COVERS - Iconos.

Dibujos en SVG, sin archivos externos, nitidos a cualquier tamano.
La carpeta usa el mismo diseno que el Explorador de Windows en vista
de iconos grandes: un folder color manila con la cara de enfrente mas clara.
"""

# Todos los dibujos usan este lienzo.
VIEW = "0 0 96 84"


def _envoltura(dibujo, extra=""):
    return ('<svg viewBox="%s" class="icono-svg" aria-hidden="true" %s>%s</svg>'
            % (VIEW, extra, dibujo))


# --------------------------------------------------------------------------
# Carpeta  (igual que el Explorador de Windows en vista grande)
# --------------------------------------------------------------------------

CARPETA = (
    # parte de atras (mas oscura)
    '<path d="M9 24a6 6 0 0 1 6-6h20.5a6 6 0 0 1 4.6 2.2l6.2 7H81a6 6 0 0 1 6 6v27.4a6 6 0 0 1-6 6H15a6 6 0 0 1-6-6z"'
    ' fill="#D89429"/>'
    # cara de enfrente (mas clara)
    '<path d="M9 36.5h78V57.6a6 6 0 0 1-6 6H15a6 6 0 0 1-6-6z"'
    ' fill="#F3C063"/>'
    '<path d="M9 36.5h78v4.2H9z" fill="#FBD999"/>'
    '<path d="M9 36.5h78V26a6 6 0 0 0-6-6H81a6 6 0 0 0-6 6z" fill="#E8A63C"/>'
)


def carpeta(extra=""):
    return _envoltura(CARPETA, extra)


# --------------------------------------------------------------------------
# Carpetas con video, segun el tipo
# --------------------------------------------------------------------------

def _base_tipo(relleno, dibujo, extra=""):
    return _envoltura(
        '<rect x="6" y="10" width="84" height="64" rx="8" fill="#F7F9FC"'
        ' stroke="#C8D6EA" stroke-width="2"/>'
        '<rect x="6" y="10" width="84" height="16" rx="8" fill="%s"/>'
        '<rect x="6" y="18" width="84" height="8" fill="%s"/>'
        '%s' % (relleno, relleno, dibujo), extra)


def pelicula(extra=""):
    d = ('<path d="M26 38h44v26H26z" fill="#2E6FD8" opacity=".14"/>'
         '<path d="M31 44l10 7-10 7z" fill="#2E6FD8"/>'
         '<path d="M65 44v14l10-7z" fill="#2E6FD8"/>'
         '<rect x="26" y="38" width="44" height="26" rx="4" fill="none"'
         ' stroke="#2E6FD8" stroke-width="3"/>')
    return _base_tipo("#5B9BEB", d, extra)


def serie(extra=""):
    d = ('<rect x="24" y="36" width="48" height="30" rx="4" fill="#2E6FD8"'
         ' opacity=".14"/>'
         '<rect x="24" y="36" width="48" height="30" rx="4" fill="none"'
         ' stroke="#2E6FD8" stroke-width="3"/>'
         '<path d="M34 42v18M48 42v18M62 42v18" stroke="#2E6FD8"'
         ' stroke-width="3" stroke-linecap="round"/>'
         '<path d="M62 66l16-8M40 66l-16-8" stroke="#7FB3F0"'
         ' stroke-width="3" stroke-linecap="round"/>')
    return _base_tipo("#7FB3F0", d, extra)


def anime(extra=""):
    d = ('<path d="M48 33l4.6 9.4 10.4 1.5-7.5 7.3 1.8 10.3-9.3-4.9-9.3 4.9'
         ' 1.8-10.3-7.5-7.3 10.4-1.5z" fill="#2E6FD8" opacity=".18"/>'
         '<path d="M48 34l4.4 8.9 9.8 1.4-7.1 6.9 1.7 9.7-8.8-4.6-8.8 4.6'
         ' 1.7-9.7-7.1-6.9 9.8-1.4z" fill="none" stroke="#2E6FD8"'
         ' stroke-width="3" stroke-linejoin="round"/>')
    return _base_tipo("#5B9BEB", d, extra)


def novela(extra=""):
    d = ('<path d="M28 36h16a5 5 0 0 1 4 2 5 5 0 0 1 4-2h16v28H52a5 5 0 0 0-4 2'
         ' 5 5 0 0 0-4-2H28z" fill="#2E6FD8" opacity=".16"/>'
         '<path d="M28 36h16a5 5 0 0 1 4 2 5 5 0 0 1 4-2h16v28H52a5 5 0 0 0-4 2'
         ' 5 5 0 0 0-4-2H28z" fill="none" stroke="#2E6FD8" stroke-width="3"'
         ' stroke-linejoin="round"/>'
         '<path d="M48 38v28" stroke="#7FB3F0" stroke-width="3"/>')
    return _base_tipo("#7FB3F0", d, extra)


def documental(extra=""):
    d = ('<rect x="22" y="40" width="34" height="26" rx="4" fill="#2E6FD8"'
         ' opacity=".16"/>'
         '<rect x="22" y="40" width="34" height="26" rx="4" fill="none"'
         ' stroke="#2E6FD8" stroke-width="3"/>'
         '<circle cx="39" cy="53" r="7" fill="none" stroke="#2E6FD8"'
         ' stroke-width="3"/>'
         '<path d="M56 48l16-8v30l-16-8z" fill="#2E6FD8" opacity=".2"/>'
         '<path d="M56 48l16-8v30l-16-8z" fill="none" stroke="#2E6FD8"'
         ' stroke-width="3" stroke-linejoin="round"/>')
    return _base_tipo("#5B9BEB", d, extra)


def otro(extra=""):
    d = ('<circle cx="48" cy="51" r="13" fill="#2E6FD8" opacity=".16"/>'
         '<circle cx="48" cy="51" r="13" fill="none" stroke="#2E6FD8"'
         ' stroke-width="3"/>'
         '<circle cx="48" cy="51" r="4" fill="#2E6FD8"/>')
    return _base_tipo("#9AA0A8", d, extra)


TIPOS = {
    "pelicula": pelicula,
    "serie": serie,
    "anime": anime,
    "novela": novela,
    "documental": documental,
    "otro": otro,
    "libro": novela,
    "musica": otro,
}


def por_tipo(tipo, extra=""):
    return TIPOS.get((tipo or "").lower(), otro)(extra)


# --------------------------------------------------------------------------
# Dispositivos
# --------------------------------------------------------------------------

def _disco(cuerpo, extra=""):
    return _envoltura(
        '<rect x="10" y="20" width="76" height="48" rx="8" fill="#F7F9FC"'
        ' stroke="#9AA0A8" stroke-width="2.5"/>%s' % cuerpo, extra)


def disco_local(extra=""):
    return _disco(
        '<rect x="16" y="26" width="64" height="30" rx="4" fill="#DCEBFF"/>'
        '<circle cx="72" cy="59" r="3" fill="#5B9BEB"/>'
        '<rect x="52" y="57" width="14" height="4" rx="2" fill="#7FB3F0"/>', extra)


def disco_extraible(extra=""):
    return _disco(
        '<rect x="16" y="26" width="64" height="30" rx="4" fill="#DCEBFF"/>'
        '<path d="M40 56h22l-3.5-7h-15z" fill="#5B9BEB"/>'
        '<path d="M24 33h30v14H24z" fill="#9AA0A8"/>'
        '<rect x="24" y="33" width="10" height="14" fill="#DCEBFF"/>'
        '<rect x="34" y="33" width="10" height="14" fill="#DCEBFF"/>', extra)


def disco_red(extra=""):
    return _disco(
        '<rect x="16" y="26" width="64" height="30" rx="4" fill="#DCEBFF"/>'
        '<rect x="46" y="31" width="24" height="20" rx="3" fill="#5B9BEB"/>'
        '<path d="M58 36v-4M46 51l-5 5M70 51l5 5" stroke="#5B9BEB"'
        ' stroke-width="3" stroke-linecap="round"/>'
        '<circle cx="58" cy="41" r="2.5" fill="#DCEBFF"/>', extra)


def disco_cd(extra=""):
    return _envoltura(
        '<circle cx="48" cy="42" r="24" fill="#DCEBFF" stroke="#9AA0A8"'
        ' stroke-width="2.5"/>'
        '<circle cx="48" cy="42" r="7" fill="#F7F9FC" stroke="#9AA0A8"'
        ' stroke-width="2.5"/>'
        '<path d="M48 18a24 24 0 0 1 20 11.5L48 42z" fill="#5B9BEB"'
        ' opacity=".45"/>', extra)


def telefono(extra=""):
    return _envoltura(
        '<rect x="30" y="8" width="36" height="68" rx="8" fill="#F7F9FC"'
        ' stroke="#2E6FD8" stroke-width="3"/>'
        '<rect x="35" y="18" width="26" height="42" rx="2" fill="#DCEBFF"/>'
        '<circle cx="48" cy="67" r="4" fill="#5B9BEB"/>'
        '<rect x="43" y="12" width="10" height="3" rx="1.5" fill="#9AA0A8"/>'
        '<path d="M40 36l6 6-6 6M56 36l-6 6 6 6" stroke="#2E6FD8"'
        ' stroke-width="2.5" fill="none" stroke-linecap="round"'
        ' stroke-linejoin="round"/>', extra)


def tablet(extra=""):
    return _envoltura(
        '<rect x="24" y="10" width="48" height="64" rx="7" fill="#F7F9FC"'
        ' stroke="#2E6FD8" stroke-width="3"/>'
        '<rect x="29" y="19" width="38" height="44" rx="2" fill="#DCEBFF"/>'
        '<circle cx="48" cy="68" r="3" fill="#5B9BEB"/>', extra)


DISPOSITIVOS = {
    "local": disco_local,
    "removible": disco_extraible,
    "red": disco_red,
    "cd": disco_cd,
    "portatil": telefono,
}


def por_dispositivo(tipo, extra=""):
    fn = DISPOSITIVOS.get((tipo or "").lower())
    if fn:
        return fn(extra)
    return disco_local(extra)


def telefono_o_tablet(extra=""):
    return telefono(extra)


# --------------------------------------------------------------------------
# Ayudas
# --------------------------------------------------------------------------

def pelicula_o_carpeta(tipo, con_video=True, extra=""):
    """Elige el dibujo de una carpeta segun lo que contenga."""
    if con_video:
        return por_tipo(tipo, extra)
    return carpeta(extra)


# --------------------------------------------------------------------------
# Los tres iconos del pie, los mismos del QBASwing Marketplace
# --------------------------------------------------------------------------

def estrella(extra=""):
    """Estrella dorada de la marca, delante del nombre en el pie."""
    dibujo = ('<path d="M48 6l11.9 26.2L88 35.2 67.3 54.8 73.3 82 48 68.9'
              ' 22.7 82l6-27.2L8 35.2l28.1-3z" fill="#FCD116"/>')
    return _envoltura(dibujo, extra)


def verificado(extra=""):
    """Marca de verificado, delante de la linea de patrocinio."""
    dibujo = ('<circle cx="48" cy="44" r="33" fill="#FCD116"/>'
              '<path d="M32 44.5l11 11.5 21.5-23" fill="none" stroke="#213145"'
              ' stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
    return _envoltura(dibujo, extra)


def paleta(extra=""):
    """Paleta de pintor, delante de la linea de disenio."""
    dibujo = ('<circle cx="48" cy="45" r="33" fill="#FCD116"/>'
              '<circle cx="34" cy="35" r="6.4" fill="#213145"/>'
              '<circle cx="52" cy="29" r="6.4" fill="#213145"/>'
              '<circle cx="67" cy="41" r="6.4" fill="#213145"/>'
              '<circle cx="38" cy="59" r="6.4" fill="#213145"/>')
    return _envoltura(dibujo, extra)