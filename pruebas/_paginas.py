# -*- coding: utf-8 -*-
"""
Toda pagina debe salir montada. Se llaman las ventanas de verdad y se
comprueba que el HTML tiene la forma esperada, sin que falte ningun
hueco en el % de los textos.

Con esto no vuelve a pasar lo de "not all arguments converted during
string formatting": eso parte la pagina en blanco.

Aqui tambien se comprueba que todas las pantallas usan la pantalla
entera, que llevan la marca de agua y los Posters de fondo.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import servidor
import i18n

# Sin servidor arrancado no hay estado: se crea uno de mentira.
if servidor.E is None:
    servidor.E = servidor.Estado({"tmdb_api_key": ""})

fallos = []


def revisar(nombre, html):
    if not isinstance(html, str) or len(html) < 200:
        fallos.append("%s: salio vacio o muy corto (%s)" % (nombre, len(html or "")))
        return
    if "%s" in html or "%d" in html:
        fallos.append("%s: quedaron huecos de formato sin rellenar" % nombre)
    if not html.startswith("<!DOCTYPE html>"):
        fallos.append("%s: no empieza por DOCTYPE" % nombre)
    if "<body>" not in html or "</html>" not in html:
        fallos.append("%s: el body esta mal cerrado" % nombre)
    if '</script>' not in html:
        fallos.append("%s: el script quedo sin cerrar" % nombre)

    # Todas las pantallas: marca de agua, Posters de fondo y ancho completo.
    if 'class="marca-agua"' not in html:
        fallos.append("%s: falta la marca de agua" % nombre)
    n = html.count('class="f-lienzo')
    if n < 45:
        fallos.append("%s: solo %d carteles de fondo (se pidieron muchos mas)"
                      % (nombre, n))

    # El pie tiene que ser el del QBASwing Marketplace: franja de la
    # bandera, nombre con el degradado y creditos, en TODAS las pantallas.
    pie = re.search(r'<footer class="pie">.*?</footer>', html, re.S)
    if not pie:
        fallos.append("%s: falta el pie de marca" % nombre)
    else:
        if 'class="pie-bandera"' not in pie.group(0):
            fallos.append("%s: el pie no lleva la franja de la bandera" % nombre)
        if 'class="texto-bandera"' not in pie.group(0):
            fallos.append("%s: el pie no lleva el nombre con degradado" % nombre)
        if "QBASwing Designer" not in pie.group(0):
            fallos.append("%s: el pie no dice quien lo hace" % nombre)
        if "TMDB" in html and "TMDB" not in pie.group(0):
            fallos.append("%s: el pie pierde el aviso de TMDB" % nombre)

    # Nada de estrechar el programa a una columna en medio de la pantalla.
    if re.search(r"\.ancho\{[^}]*max-width:\s*9\d\dpx", servidor.CSS):
        fallos.append("el .ancho vuelve a capar la pagina a una columna estre��a")
    if "width:100%" not in servidor.CSS or "max-width:none" not in servidor.CSS:
        fallos.append("el .ancho no se estira a todo el ancho del navegador")

    # Los textos pequenos tienen que ser legibles sobre el fondo oscuro.
    if "--tenue:#8d94a3" not in servidor.CSS:
        fallos.append("el color de los textos pequeños sigue siendo demasiado oscuro")
    if "antialiased" not in servidor.CSS:
        fallos.append("falta el suavizado de letra para los textos pequeños")

    # El pie va al final de la pagina, a todo el ancho y por encima de los
    # Posters de fondo, igual que el del QBASwing Marketplace.
    if not re.search(r'\.pie\s*\{[^}]*width:\s*100%', servidor.CSS):
        fallos.append("el pie no ocupa todo el ancho")
    if not re.search(r'\.pie-bandera', servidor.CSS):
        fallos.append("falta la franja de la bandera en el CSS del pie")
    if not re.search(r'\.texto-bandera', servidor.CSS):
        fallos.append("falta el degradado de la bandera del nombre")
    if re.search(r'\.pie\s*\{[^}]*position:\s*fixed', servidor.CSS):
        fallos.append("el pie vuelve a estar fijo: ahora va al final de la pagina")

    print("   %-22s %6d car.  fondo=%2d  ancho=%s"
          % (nombre, len(html), n,
             "todo" if "max-width:none" in servidor.CSS else "?"))


print("Paginas:")

revisar("portada", servidor.ventana_portada("es"))
revisar("portada EN", servidor.ventana_portada("en"))
revisar("discos", servidor.ventana_discos("es", servidor.E.unidades or []))
revisar("escaneo", servidor.ventana_escaneo("es", []))
revisar("pregunta", servidor.ventana_pregunta("es", False))
revisar("buscando", servidor.ventana_buscando("es"))
revisar("galeria", servidor.ventana_galeria("es", None))
revisar("galeria EN", servidor.ventana_galeria("en", None))
revisar("resumen", servidor.ventana_resumen("es", {
    "descargados": 2, "ya_tenian": 1, "sin_coincidencia": 0, "fallos": 0}))
revisar("acerca", servidor.ventana_acerca("es", "/"))
revisar("descargando", servidor.ventana_descargando("es"))
revisar("inventario", servidor.ventana_inventario("es"))

# El aviso de TMDB tiene que estar en el pie de las pantallas con fondo.
h = servidor.ventana_galeria("es", None)
if "TMDB" not in h:
    fallos.append("el aviso de TMDB no sale en el pie")

# La opcion de pantalla completa se quito a peticion del usuario:
# el programa ya abre en ventana a todo el ancho, asi que no debe
# quedar ni el boton ni la funcion que lo movia.
if "pantallaCompleta()" in h:
    fallos.append("sigue el boton de pantalla completa")
if "requestFullscreen" in h:
    fallos.append("sigue la llamada a pantalla completa")
if 'class="pantalla"' in h:
    fallos.append("sigue la clase .pantalla en la barra")
for clave in ("btn_pantalla", "btn_pantalla_ayuda"):
    if clave in i18n.I18N:
        fallos.append("sigue la clave %s en i18n" % clave)

# Y el fondo no puede traer ninguna imagen incrustada (nada de derechos).
if "<img" in servidor.fondo.html("es"):
    fallos.append("el fondo trae imagenes incrustadas")
if len(servidor.fondo.html("es")) > 120000:
    fallos.append("el fondo se ha puesto demasiado pesado")

print()
if fallos:
    print("FALLOS:")
    for f in fallos:
        print("   -", f)
    sys.exit(1)
print("Todas las paginas montan bien, a pantalla completa y con fondo.")