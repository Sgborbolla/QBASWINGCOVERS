t=open("QBASWING_COVERS_ESPECIFICACION.txt",encoding="utf-8").read()
i=t.find("i18n.py")
# Mostrar la seccion alrededor de la definicion de i18n
import re
for m in re.finditer(r"i18n", t):
    pass
# Imprimir desde "10." o "IDIOMA" hacia adelante
j=t.find("IDIOMA")
print(t[j:j+2500] if j>=0 else "sin seccion IDIOMA")
