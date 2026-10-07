import re, io
t = io.open("i18n.py", encoding="utf-8").read()
claves = re.findall(r'"([a-zA-Z0-9_]+)"\s*:\s*\{\s*"es"', t)
print("Total de claves:", len(claves))
print()
print(", ".join(sorted(claves)))
