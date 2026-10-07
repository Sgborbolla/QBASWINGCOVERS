t=open("QBASWING_COVERS_ESPECIFICACION.txt",encoding="utf-8").read()
j=t.find("13.2")
if j<0: j=t.find("iniciar.bat")
print(t[j:j+2200])
