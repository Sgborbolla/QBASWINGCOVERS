import re, io
t = io.open("i18n.py", encoding="utf-8").read()
es = re.findall(r'"([a-z0-9_]+)"\s*:\s*"', t)
print("Claves en i18n.py:", len(set(es)))
# Mostrar las que habian fewer (busca relacionadas con unidades)
cands = sorted(set(k for k in es if any(x in k for x in ("uni","disco","disposit","ext","usb","extra"))))
print("Relacionadas:", cands)
