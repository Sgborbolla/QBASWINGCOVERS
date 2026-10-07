# -*- coding: utf-8 -*-
"""Ejecuta _PS_LISTAR crudo para ver por que devuelve vacio."""
import json
import sys

sys.path.insert(0, r"C:\QBASWING-COVERS")
import mtp

nombres = mtp.dispositivos()
disp = nombres[0]
print("QB_DEVICE =", repr(disp))
print("QB_PARTES =", repr(json.dumps([], ensure_ascii=False)))
print()

salida = mtp._power_shell(
    mtp._PS_LISTAR,
    {"QB_DEVICE": disp, "QB_PARTES": json.dumps([], ensure_ascii=False)},
    timeout=90)
print("--- salida cruda de _PS_LISTAR ---")
print(repr(salida))
print()
print("--- texto legible ---")
print(salida or "(vacia)")

print()
print("--- con QB_PARTES ausente ---")
salida2 = mtp._power_shell(mtp._PS_LISTAR, {"QB_DEVICE": disp}, timeout=90)
print(salida2 or "(vacia)")

print()
print("--- listar_subcarpetas() ---")
raiz = mtp.unir(disp, [])
print("raiz:", raiz)
print("resultado:", mtp.listar_subcarpetas(raiz))