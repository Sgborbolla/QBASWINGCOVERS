import re
t=open("QBASWING_COVERS_ESPECIFICACION.txt",encoding="utf-8").read()
for pat in ["celular","telefono","teléfono","movil","móvil","MTP","portatil","portátil","smartphone","Android","iPhone"]:
    n=len(re.findall(pat,t,re.I))
    if n: print("%-12s -> %d" % (pat,n))
print("(si no aparece ninguna linea, la especificacion no menciona telefonos)")
