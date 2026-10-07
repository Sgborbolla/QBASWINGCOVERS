# -*- coding: utf-8 -*-
"""Prueba de deteccion de dispositivos: discos + telefonos MTP."""
import sys

sys.path.insert(0, r"C:\QBASWING-COVERS")
import escaneo
import mtp

print("=" * 74)
print("1) DISPOSITIVOS MTP (telefonos/tablets)")
print("=" * 74)
nombres = mtp.dispositivos()
print("   encontrados:", nombres if nombres else "(ninguno conectado)")
print("   hay_soporte:", mtp.hay_soporte())

print()
print("=" * 74)
print("2) escaneo.detectar_unidades()")
print("=" * 74)
unidades = escaneo.detectar_unidades()
print("%-30s %-12s %-11s %s" % ("RUTA", "TIPO", "SISTEMA", "DESCRIPCION"))
print("-" * 74)
for u in unidades:
    marca = ""
    if escaneo.es_mtp(u["ruta"]):
        marca = "   <-- MTP"
    if nombres and u["ruta"].startswith("mtp://"):
        marca = "   <-- MTP COINCIDE CON DISPOSITIVO REAL"
    print("%-30s %-12s %-11s %s%s" % (
        u["ruta"][:30], u["tipo"], u.get("sistema") or "-",
        u["descripcion"], marca))

print()
print("=" * 74)
print("3) COMPROBACIONES")
print("=" * 74)
fallos = []
print("  %-58s %s" % ("detectar_unidades devuelve algo",
                     "OK" if unidades else "FALLO"))
if not unidades:
    fallos.append("sin unidades")

tiene_portatil = any(u["tipo"] == "portatil" for u in unidades)
print("  %-58s %s" % ("el tipo 'portatil' esta definido",
                     "OK" if tiene_portatil or not nombres else "FALLO"))
if nombres and not tiene_portatil:
    fallos.append("hay telefonos pero no salen como unidad")

for u in unidades:
    if escaneo.es_mtp(u["ruta"]):
        d, partes = mtp.partir(u["ruta"])
        print("  %-58s %s" % ("el telefono %r se parte bien" % d,
                              "OK" if d else "FALLO"))
        if not d:
            fallos.append("partir() fallo")

print()
print("Unidades totales: %d   Portatiles: %d"
      % (len(unidades), sum(1 for u in unidades if u["tipo"] == "portatil")))
print("FALLOS: %d" % len(fallos))