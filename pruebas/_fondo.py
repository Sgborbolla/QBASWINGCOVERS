# -*- coding: utf-8 -*-
"""
El fondo de portada entra en todas las pantallas.

  - servidor.py usa fondo.CSS y mete fondo.html() en cada pagina.
  - La portada inicial no lo lleva: esa ya tiene su propio collage.
  - El pie de pagina lleva el aviso de TMDB, que es donde salen los
    Posters reales.
  - Se tapa el error de conexion anulada que salia en la consola cuando
    el navegador se iba a otra pantalla a media descarga.
"""
import ast
import io

RUTA = r"C:\QBASWING-COVERS\servidor.py"
t = io.open(RUTA, encoding="utf-8").read()
hechos = []


def cambiar(viejo, nuevo, nombre, veces=1):
    global t
    if viejo not in t:
        raise SystemExit("NO SE ENCONTRO: %s" % nombre)
    t = t.replace(viejo, nuevo, veces)
    hechos.append(nombre)


# ------------------------------------------------------- 1) el import
cambiar("import iconos\n", "import iconos\nimport fondo\n", "el modulo fondo")

# ------------------------------------------------------- 2) los estilos
cambiar('.oculto{display:none}\n"""',
        '.oculto{display:none}\n""" + fondo.CSS',
        "los estilos del fondo")

# ------------------------------------------------------- 3) el fondo en pagina
cambiar(
    'def pagina(lang, titulo, cuerpo, actual="", extra_barra="", head_extra=""):\n'
    '    return (',
    'def pagina(lang, titulo, cuerpo, actual="", extra_barra="", head_extra="",\n'
    '            con_fondo=True):\n'
    '    """\n'
    '    Una sola pagina para todas las ventanas. El fondo de portada se\n'
    '    pone en todas menos en la inicial, que ya tiene el suyo propio.\n'
    '    """\n'
    '    decorado = fondo.html(lang) if con_fondo else ""\n'
    '    return (',
    "pagina() acepta el fondo")

cambiar(
    '        % (lang, esc("%s \xb7 QBASWING COVERS" % titulo), CSS, head_extra,\n'
    '           barra_superior(lang, titulo, actual, extra_barra),\n'
    '           \'<div class="envoltura">\', cuerpo, "</div>", pie(lang) + script_ir(lang),\n'
    '           esc(t("msg_cerrando", lang)))',
    '        % (lang, esc("%s \xb7 QBASWING COVERS" % titulo), CSS, head_extra,\n'
    '           barra_superior(lang, titulo, actual, extra_barra), decorado,\n'
    '           \'<div class="envoltura">\', cuerpo, "</div>", pie(lang) + script_ir(lang),\n'
    '           esc(t("msg_cerrando", lang)))',
    "el fondo se dibuja detras del contenido")

# La portada inicial se queda con su collage propio.
cambiar('''    return pagina(lang, t("titulo_bienvenida", lang), cuerpo, "/",
                  head_extra="<style>%s</style>%s%s" % (CSS_PORTADA, JS_PORTADA, TILT))''',
        '''    return pagina(lang, t("titulo_bienvenida", lang), cuerpo, "/",
                  head_extra="<style>%s</style>%s%s" % (CSS_PORTADA, JS_PORTADA, TILT),
                  con_fondo=False)''',
        "la portada inicial sin fondo duplicado")

# ------------------------------------------------------- 4) aviso de TMDB
cambiar(
    '''def pie(lang):
    """0.4 Pie de pagina fijo en la esquina inferior izquierda."""
    derechos = t("pie_derechos", lang)
    return ('<div class="pie">QBASWING COVERS &middot; Powered by QBASwing Designer'
            '<br>%s</div>' % esc(derechos))''',
    '''def pie(lang):
    """0.4 Pie de pagina fijo en la esquina inferior izquierda."""
    derechos = t("pie_derechos", lang)
    # Aviso obligatorio de TMDB: en el fondo hay Posters suyos.
    aviso = ('<br>%s' % esc(t("aviso_tmdb", lang))) if E else ""
    return ('<div class="pie">QBASWING COVERS &middot; Powered by QBASwing Designer'
            '<br>%s%s</div>' % (esc(derechos), aviso))''',
    "el aviso de TMDB en el pie")

# ------------------------------- 5) la conexion anulada no rompe la consola
cambiar(
    '''        try:
            self.wfile.write(cuerpo)
        except (BrokenPipeError, ConnectionResetError):
            pass''',
    '''        try:
            self.wfile.write(cuerpo)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError,
                ConnectionError, OSError):
            # El navegador se fue a otra pantalla a media respuesta. Es
            # normal: 0.2 dice que la siguiente sustituye a la anterior.
            pass''',
    "sin tracebacks de conexion anulada")

cambiar(
    '''        self.end_headers()
        try:
            self.wfile.write(cuerpo)''',
    '''        try:
            self.end_headers()
            self.wfile.write(cuerpo)''',
    "los encabezados tambien toleran la ida del navegador")

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(t)
ast.parse(io.open(RUTA, encoding="utf-8").read())

# ------------------------------------------------------- 6) el aviso, en i18n
RUTA_I = r"C:\QBASWING-COVERS\i18n.py"
i = io.open(RUTA_I, encoding="utf-8").read()
if "aviso_tmdb" not in i:
    anadir = '''    "aviso_tmdb": {"es": "Posters: TMDB y AniList. Este producto usa la API de TMDB pero no esta avalado ni certificado por TMDB.", "en": "Covers: TMDB and AniList. This product uses the TMDB API but is not endorsed or certified by TMDB."},
'''
    i = i.replace("}\n\ndef t(clave", anadir + "}\n\ndef t(clave", 1)
    io.open(RUTA_I, "w", encoding="utf-8", newline="\n").write(i)
    ast.parse(io.open(RUTA_I, encoding="utf-8").read())
    hechos.append("la clave aviso_tmdb")

print("Fondo en todas las pantallas:")
for h in hechos:
    print("   -", h)
print("sintaxis OK")