# -*- coding: utf-8 -*-
"""Prueba de deteccion de dispositivos: discos y unidades de la PC."""
import sys

sys.path.insert(0, r"C:\QBASWING-COVERS")
import escaneo

print("=" * 74)
print("1) escaneo.detectar_unidades()")
print("=" * 74)
unidades = escaneo.detectar_unidades()
print("%-30s %-12s %-11s %s" % ("RUTA", "TIPO", "SISTEMA", "DESCRIPCION"))
print("-" * 74)
for u in unidades:
    print("%-30s %-12s %-11s %s" % (
        u["ruta"][:30], u["tipo"], u.get("sistema") or "-",
        u["descripcion"]))

print()
print("=" * 74)
print("2) COMPROBACIONES")
print("=" * 74)
fallos = []
print("  %-58s %s" % ("detectar_unidades devuelve algo",
                     "OK" if unidades else "FALLO"))
if not unidades:
    fallos.append("sin unidades")

tipos_de_disco = {"local", "removible", "red", "cd"}
raros = [u.get("tipo") for u in unidades
         if u.get("tipo") not in tipos_de_disco]
print("  %-58s %s" % ("todos los tipos son de disco",
                     "OK" if not raros else "FALLO"))
if raros:
    fallos.append("tipos inesperados: %s" % raros)

print()
print("Unidades totales: %d" % len(unidades))
print("FALLOS: %d" % len(fallos))
if fallos:
    raise SystemExit("FALLOS: " + "; ".join(fallos))
