# -*- coding: utf-8 -*-
"""
Prueba del fondo de las pantallas.

El fondo se dibuja con Posters generados por el propio programa, para no
meter imagenes ajenas dentro del .exe. Ademas se mueve y cada pantalla
tiene un reparto distinto.

Aqui se comprueba todo eso.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fondo

fallos = []


def comprobar(condicion, aviso):
    if not condicion:
        fallos.append(aviso)


h = fondo.html("es")
mural = fondo._mural("ventana_discos")
tira = fondo._tira("ventana_discos")
lienzos = len(mural) + len(tira)

print("Fondo del programa")
print("   tamano del HTML      %6d caracteres" % len(h))
print("   carteles             %6d  (mural %d + bordes %d)" % (lienzos, len(mural), len(tira)))
print("   tipos usados       %s" % ", ".join(sorted(set(
    re.findall(r'data-tipo="(\w+)"', h)))))
print("   scripts y css        %s / %s" % ("<script>" in h, "fondo{" in fondo.CSS))

# --- lo que el usuario pidio: muchos carteles por toda la pantalla -------
comprobar(lienzos >= 45, "solo hay %d carteles: se pidieron muchos mas" % lienzos)
comprobar(len(mural) >= 35, "el mural de fondo tiene solo %d carteles" % len(mural))
comprobar(len(tira) >= 12, "la tira de los bordes tiene solo %d carteles" % len(tira))

# El mural tiene que repartirse por TODA la pantalla, no solo por un trozo.
izq = [p[0] for p in mural]
der = [p[0] + p[2] for p in mural]
altos = [p[1] for p in mural]
print("   mural                de %.0f%% a %.0f%% de ancho, de %.0f%% a %.0f%% de alto"
      % (min(der), max(der), min(altos), max(altos)))
comprobar(min(izq) < 0 and max(der) > 100,
          "el mural no llega a los bordes de la pantalla")
comprobar(max(altos) > 60, "el mural no cubre toda la altura de la pantalla")

# --- los ocho tipos de contenido audiovisual pasan siempre --------------
for tipo in fondo.CICLO:
    comprobar('data-tipo="%s"' % tipo in h, "el tipo %s no sale en el fondo" % tipo)
    comprobar('f-rotulo">%s<' % fondo.titulo(tipo, "es") in h,
              "el tipo %s va sin rotulo" % tipo)

# --- los degradados no pueden repetir nombre (SVG invalido) --------------
ids = re.findall(r'<linearGradient id="(g\d+)"', h)
repetidos = [i for i in set(ids) if ids.count(i) > 1]
print("   degradados           %6d  repetidos: %s" % (len(ids), repetidos or "ninguno"))
comprobar(not repetidos, "se repiten los degradados: %s" % repetidos)

# --- cada cartel dibuja con un <symbol> que existe de verdad -------------
simbolos = set(re.findall(r'<symbol id="(fa-\w+)"', h))
usos = set(re.findall(r'<use href="#(fa-\w+)"', h))
print("   simbolos / usos      %6d / %d" % (len(simbolos), len(usos)))
comprobar(len(simbolos) == len(fondo.CICLO),
          "hay %d simbolos y deberian ser %d" % (len(simbolos), len(fondo.CICLO)))
comprobar(usos <= simbolos, "hay carteles que usan un simbolo inexistente: %s"
          % sorted(usos - simbolos))
comprobar(h.count('xlink:href="#fa-') == h.count('<use href="#fa-'),
          "faltan los xlink:href para los navegadores viejos")

# El dibujo de un tipo tiene que llevar su color y su icono.
a = fondo._simbolo("anime")
comprobar(fondo.COLORES["anime"][0] in a and fondo.COLORES["anime"][1] in a,
          "el dibujo de anime no lleva sus colores")
comprobar("linearGradient" in a and "<symbol" in a and a.count("</symbol>") == 1,
          "el dibujo de anime no esta bien cerrado")

# --- nada de imagenes ajenas dentro del programa ------------------------
comprobar("<img" not in h, "hay imagenes incrustadas en el fondo")
comprobar("http" not in h.split("<script>")[0],
          "el fondo descarga algo de internet antes de verse")

# --- se mueve ------------------------------------------------------------
comprobar("animation:deriva" in fondo.CSS, "los carteles no se mueven solos")
comprobar("@keyframes deriva" in fondo.CSS, "falta el movimiento de los carteles")
comprobar("animation:muralPaseo" in fondo.CSS, "la pared de fondo no se desliza")
comprobar("mousemove" in h, "no hay parallax con el raton")
comprobar("prefers-reduced-motion" in fondo.CSS and "prefers-reduced-motion" in h,
          "no se respeta quien tiene el movimiento reducido activado")
duraciones = set(re.findall(r'--t:(\d+)s', h))
print("   tiempos de carton    %6s" % ", ".join(sorted(duraciones, key=int)) + " s")
comprobar(len(duraciones) >= 4, "todos los carteles se mueven igual de tiempo")

# --- cada pantalla con su propio reparto --------------------------------
repartos = {}
for pantalla in ("ventana_discos", "ventana_escaneo", "ventana_galeria",
                 "ventana_acerca", "ventana_portada"):
    pagina = fondo.html("es", pantalla)
    reparto = tuple(re.findall(r'class="f-lienzo f-\w+" style="([^"]*)"', pagina))
    comprobar(reparto not in repartos,
              "la pantalla %s sale con el mismo reparto que %s"
              % (pantalla, repartos.get(reparto, "otra")))
    reparto, repartos[reparto] = reparto, pantalla
    comprobar(pagina.count('data-semilla="%s"' % pantalla) == 1,
              "la pantalla %s no lleva su semilla" % pantalla)
print("   repartos distintos   %6d de %d pantallas"
      % (len(repartos), 5))

# Sin semilla debe salir el reparto de siempre, sin romperse.
comprobar(fondo.html("es", "") == fondo.html("es", ""),
          "el fondo sin semilla no es estable")

# --- los dos idiomas ----------------------------------------------------
en = fondo.html("en", "ventana_galeria")
comprobar('<span class="f-rotulo">Movies</span>' in en, "en ingles falta Movies")
comprobar('<span class="f-rotulo">Classics</span>' in en, "en ingles falta Classics")
comprobar("Pel&iacute;culas" not in en, "en ingles quedan rotulos en espanol")
comprobar(fondo.html("es", "ventana_galeria").count('data-semilla="ventana_galeria"') == 1,
          "el fondo se rompe al cambiar de idioma")

print()
if fallos:
    print("FALLOS:")
    for f in fallos:
        print("   -", f)
    sys.exit(1)
print("El fondo se dibuja, se mueve y es distinto en cada pantalla.")