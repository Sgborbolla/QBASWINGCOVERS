# -*- coding: utf-8 -*-
"""Lista de todas las clases que usa el HTML, para no perder ningun estilo."""
import collections
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import servidor  # noqa

crudo = io.open(os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "servidor.py"), encoding="utf-8").read()

vistos = collections.Counter()
for m in re.finditer(r'class=\\?"([^"\\]+)\\?"', crudo):
    for c in m.group(1).split():
        vistos[c] += 1

# Las que se escriben con %s o con + dentro del HTML de Python.
for m in re.finditer(r'class="([^"]*)"', crudo):
    for c in m.group(1).split():
        if c and "%" not in c and "{" not in c:
            vistos[c] += 1

css = servidor.CSS + servidor.CSS_PORTADA + servidor.fondo.CSS
en_css = set(re.findall(r'\.([a-zA-Z][\w-]*)', css))

usadas = sorted(c for c in vistos if "%" not in c and "{" not in c)
print("clases en el HTML: %d   clases en el CSS: %d" % (len(usadas), len(en_css)))
print()
print("SIN ESTILO:", ", ".join(c for c in usadas if c not in en_css) or "ninguna")
print()
for c in usadas:
    print("%-26s %s" % (c, "ok" if c in en_css else "<<< SIN ESTILO"))