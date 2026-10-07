import io, re
t = io.open("i18n.py", encoding="utf-8").read()
for k in ["disco_externo","disco_extraible","msg_galeria_unidades","titulo_galeria_unidades","msg_carpeta_sin_escanear","msg_carpeta","msg_unidad","msg_bienvenida","btn_unidades"]:
    m = re.search(r'"%s"\s*:\s*\{(.*?)\},?\s*\n' % re.escape(k), t, re.S)
    print("%-26s %s" % (k, " ".join(m.group(1).split()) if m else "NO ENCONTRADA"))
