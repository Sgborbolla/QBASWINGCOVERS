import re
t=open("QBASWING_COVERS_ESPECIFICACION.txt",encoding="utf-8").read()
print("=== Menciones nuevas ===")
for pat in ["MTP","celular","telefono","teléfono","movil","móvil","portatil","portátil","Android","dispositivo","extraible","extraíble","externo","usb","USB","escaner"]:
    n=len(re.findall(pat,t))
    if n: print("  %-14s -> %d" % (pat,n))
print("=== Secciones (numeradas) ===")
for m in re.finditer(r"^(\d{1,2})\.\s+([A-Z][A-Z \-]{4,60})\s*$", t, re.M):
    print("  %s. %s" % (m.group(1), m.group(2).strip()))
