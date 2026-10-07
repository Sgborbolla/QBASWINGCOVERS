# -*- coding: utf-8 -*-
"""Prueba MTP real contra el telefono conectado."""
import sys
import time

sys.path.insert(0, r"C:\QBASWING-COVERS")
import escaneo
import mtp

print("=" * 74)
print("1) DISPOSITIVOS")
print("=" * 74)
nombres = mtp.dispositivos()
print("   ", nombres)
raiz = mtp.unir(nombres[0], [])
print("    raiz:", raiz, "-> es_mtp:", escaneo.es_mtp(raiz))

print()
print("=" * 74)
print("2) CARPETAS EN LA RAIZ DEL TELEFONO")
print("=" * 74)
t0 = time.time()
subs = mtp.listar_subcarpetas(raiz)
print("    %d carpetas en %.1f s" % (len(subs), time.time() - t0))
for s in subs[:15]:
    print("     -", s["nombre"], "->", s["ruta"])
if len(subs) > 15:
    print("     ... y %d mas" % (len(subs) - 15))

print()
print("=" * 74)
print("3) BAJAR UN NIVEL")
print("=" * 74)
if subs:
    hijo = subs[0]["ruta"]
    t0 = time.time()
    nietos = mtp.listar_subcarpetas(hijo)
    print("    '%s' -> %d subcarpetas en %.1f s"
          % (subs[0]["nombre"], len(nietos), time.time() - t0))
    for n in nietos[:10]:
        print("     -", n["nombre"])
    nietos_todos = nietos + subs[1:]
else:
    nietos_todos = []

print()
print("=" * 74)
print("4) ESCANEO MTP (limite corto: 90 s)")
print("=" * 74)
vistos = [0]


def progreso(ruta):
    vistos[0] += 1
    if vistos[0] % 40 == 0:
        print("    ... %d carpetas revisadas" % vistos[0])


t0 = time.time()
res = escaneo.escanear_unidad(raiz, progreso=progreso)
print("    Duration: %.1f s" % (time.time() - t0))
print("    candidatas con video: %d" % len(res))
for r in res[:20]:
    print("     - %-40s videos=%s ya_tiene=%s"
          % (r["nombre"][:40], r["videos"], r["ya_tiene"]))
if len(res) > 20:
    print("     ... y %d mas" % (len(res) - 20))

print()
print("=" * 74)
print("5) ESTADO DE UNA CARPETA")
print("=" * 74)
objetivo = res[0]["ruta"] if res else (nietos_todos[0]["ruta"] if nietos_todos else raiz)
print("    consultando:", objetivo)
t0 = time.time()
est = mtp.estado_carpeta(objetivo)
print("    estado: %s  (%.1f s)" % (est, time.time() - t0))