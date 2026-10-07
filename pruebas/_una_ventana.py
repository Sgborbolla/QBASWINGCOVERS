# -*- coding: utf-8 -*-
"""
Las pantallas se sustituyen: la siguiente cierra la anterior.

Seccion 0.2 de la especificacion: "Cada pantalla es una ventana del
navegador. Cuando aparece la siguiente, la anterior se cierra sola."

  - La navegacion usa location.replace() en vez de location.href, para
    que el boton "atras" del navegador no acumule pantallas viejas.
  - El programa abre el navegador en la pestana actual (new=1), no en
    una nueva, para no apilar ventanas cada vez que arranca.
"""
import ast
import io

hechos = []

# ------------------------------------------------------ 1) servidor.py
RUTA = r"C:\QBASWING-COVERS\servidor.py"
t = io.open(RUTA, encoding="utf-8").read()

VIEJO_IR = "function ir(url){window.location.href=url;}"
NUEVO_IR = ("/* 0.2 La pantalla siguiente sustituye a esta: no se apilan. */\n"
            "function ir(url){window.location.replace(url);}")
if VIEJO_IR in t:
    t = t.replace(VIEJO_IR, NUEVO_IR, 1)
    hechos.append("ir() usa location.replace()")
else:
    raise SystemExit("no se encontro ir()")

# Los avances automaticos de las pantallas de escaneo y busqueda.
for viejo, nuevo, nombre in (
    ("window.location.href='/paso4';",
     "window.location.replace('/paso4');", "escaneo -> paso4"),
    ("window.location.href='/galeria';",
     "window.location.replace('/galeria');", "busqueda -> galeria"),
    ("window.location.href = seguir ? '/paso4' : '/paso4';",
     "window.location.replace('/paso4');", "escaneo (reanudar)"),
):
    if viejo in t:
        t = t.replace(viejo, nuevo)
        hechos.append("avance sin apilar: %s" % nombre)

# La descarga tambien sustituye, no abre otra ventana.
t = t.replace("if(d && d.ok){ window.location.href = d.url; }",
              "if(d && d.ok){ window.location.replace(d.url); }", 1)

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(t)
ast.parse(io.open(RUTA, encoding="utf-8").read())

# ---------------------------------------------- 2) qbaswing_covers.py
RUTA2 = r"C:\QBASWING-COVERS\qbaswing_covers.py"
q = io.open(RUTA2, encoding="utf-8").read()
VIEJO = "webbrowser.open(url, new=2, autoraise=True)"
NUEVO = ("# new=1: reutiliza la pestana actual. Con new=2 se apilaba una\n"
         "            # ventana nueva cada vez que arrancaba el programa.\n"
         "            webbrowser.open(url, new=1, autoraise=True)")
if VIEJO in q:
    q = q.replace(VIEJO, NUEVO, 1)
    hechos.append("el navegador se abre en la pestana actual")
else:
    raise SystemExit("no se encontro webbrowser.open")

io.open(RUTA2, "w", encoding="utf-8", newline="\n").write(q)
ast.parse(io.open(RUTA2, encoding="utf-8").read())

print("Ventanas que se sustituyen:")
for h in hechos:
    print("   -", h)
print("sintaxis OK")