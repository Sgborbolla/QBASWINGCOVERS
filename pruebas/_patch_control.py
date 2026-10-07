# -*- coding: utf-8 -*-
"""
escaneo.py - control del escaneo: pausar, seguir, detener y cancelar.

Se agrega al final del modulo. Define:
  class Detenido(Exception)      se lanza para salir del recorrido
  class Control                  los botones del escaneo
"""
import io
import re

RUTA = r"C:\QBASWING-COVERS\escaneo.py"
texto = io.open(RUTA, encoding="utf-8").read()

if "class Control(object)" in texto:
    print("ya estaba aplicado")
    raise SystemExit(0)

# import del threading, necesario para los eventos
if "\nimport threading\n" not in texto:
    texto = texto.replace("import json\n", "import json\nimport threading\n", 1)

CONTROL = '''

# --------------------------------------------------------------------------
# 5.9 Controles del escaneo:  pausar / seguir / detener / cancelar
# --------------------------------------------------------------------------

class Detenido(Exception):
    """Se lanza para salir del recorrido cuando el usuario detiene o cancela."""


class Control(object):
    """
    Los botones del escaneo.

    es_seguro()          -> True mientras se puede seguir escaneando
    esperar()            -> si esta en pausa, espera a que le digan "seguir"
    estado()             -> "corriendo" | "pausado" | "detenido" | "cancelado"
    pausar() / seguir() / detener() / cancelar()
    """

    def __init__(self):
        self._pausa = threading.Event()      # puesto = hay que esperar
        self._parar = threading.Event()
        self._cancelar = threading.Event()

    # ---------------------------------------------------------- botones
    def pausar(self):
        self._pausa.set()

    def seguir(self):
        self._pausa.clear()
        self._parar.clear()

    def detener(self):
        """Se detiene el escaneo pero se guarda lo que ya se encontro."""
        self._parar.set()
        self._pausa.clear()

    def cancelar(self):
        """Se abandona el escaneo y se cierra la pantalla."""
        self._cancelar.set()
        self._parar.set()
        self._pausa.clear()

    # ---------------------------------------------------------- consultas
    def estado(self):
        if self._cancelar.is_set():
            return "cancelado"
        if self._parar.is_set():
            return "detenido"
        if self._pausa.is_set():
            return "pausado"
        return "corriendo"

    def es_pausado(self):
        return self._pausa.is_set()

    def terminado(self):
        return self._parar.is_set() or self._cancelar.is_set()

    def es_seguro(self):
        """False si el usuario detuvo o cancelo."""
        return not self.terminado()

    # ---------------------------------------------------------- espera
    def esperar(self, timeout_max=86400):
        """
        Si esta en pausa, espera a que el usuario pulse "seguir".
        Devuelve False si mientras tanto se detiene o se cancela.
        """
        if not self._pausa.is_set():
            return self.es_seguro()
        if self._pausa.wait(timeout_max):
            return self.es_seguro()
        return self.es_seguro()

    def punto_control(self):
        """
        Se llama antes de cada carpeta.
        Lanza Detenido si el usuario detuvo o cancelo.
        """
        if not self.es_seguro():
            raise Detenido(self.estado())
        if not self.espera():
            raise Detenido(self.estado())
'''

texto = texto.rstrip("\n") + "\n" + CONTROL
io.open(RUTA, "w", encoding="utf-8", newline="\n").write(texto)

import ast
ast.parse(io.open(RUTA, encoding="utf-8").read())
print("escaneo.py: controles del escaneo agregados, sintaxis OK")