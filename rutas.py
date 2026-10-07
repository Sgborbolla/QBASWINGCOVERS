# -*- coding: utf-8 -*-
"""
QBASWING COVERS - Rutas de trabajo.

Cuando el programa corre como .py, todo vive junto a los archivos fuente.
Cuando corre empaquetado como .exe, los datos (config.json, cache, log,
inventario.csv, base de datos) viven junto al .exe, y los recursos
empaquetados (logo) se leen desde la carpeta temporal del ejecutable.
"""

import sys
from pathlib import Path


def base_dir():
    """Carpeta donde se guardan los datos del programa."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def recurso(nombre):
    """Ruta de un archivo empaquetado dentro del .exe, si existe."""
    if hasattr(sys, "_MEIPASS"):
        empaquetado = Path(sys._MEIPASS) / nombre
        if empaquetado.exists():
            return empaquetado
    return base_dir() / nombre
