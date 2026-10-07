import re
t = open("QBASWING_COVERS_ESPECIFICACION.txt", encoding="utf-8").read()
for pat in ["F2", "atajo", "tecla", "Escape", "ESC", "barra espaciadora"]:
    for m in re.finditer(pat, t, re.IGNORECASE):
        ini = max(0, m.start()-90); fin = min(len(t), m.end()+90)
        print("[%s] ...%s..." % (pat, t[ini:fin].replace("\n"," | ")))
    print("-"*60)
