import re
t=open("QBASWING_COVERS_ESPECIFICACION.txt",encoding="utf-8").read()
for m in re.finditer(r"(extern|removible|extraible|extraíble|USB|unidad de red|todas las unidades|medios)", t, re.I):
    ini=max(0,m.start()-200); fin=min(len(t),m.end()+260)
    print("...", t[ini:fin].replace("\n"," | "), "...")
    print("="*70)
