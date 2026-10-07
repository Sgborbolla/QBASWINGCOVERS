import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

import i18n, escaneo, fuentes, posters, servidor
print("imports OK")

# Novelas significa telenovelas: solo consultas de television, no de libros.
assert fuentes.TIPOS_APIS["novelas"] == ["tmdb_tv", "tvmaze"]
assert "openlibrary" not in fuentes.TIPOS_APIS["otros"]
assert "googlebooks" not in fuentes.TIPOS_APIS["otros"]

# i18n
assert i18n.t("btn_aceptar", "en") == "Accept", "i18n en"
assert i18n.t("btn_aceptar", "es") == "Aceptar", "i18n es"
assert i18n.t("clave_inexistente", "en") == "clave_inexistente", "fallback"

# posters
assert posters.limpiar_nombre("Matrix (1999) 1080p x264 Blu-Ray") == "Matrix (1999)", posters.limpiar_nombre("Matrix (1999) 1080p x264 Blu-Ray")
assert posters.extraer_anio("Matrix (1999)") == 1999
assert posters.extraer_temporada("One Piece T20") == 20
assert posters.extraer_temporada("Serie Season 3") == 3
assert posters.quitar_acentos("ÁRVOLZ Nuñez") == "ARVOLZ Nunez"
r = {"titulo":"Matrix","ano":1999,"tipo":"pelicula","tipo_pedido":"pelicula","temporadas":[],"alias":[]}
p = posters.puntuar("Matrix (1999)", 1999, None, r)
assert p >= 60, p
mejor, motivo, _ = posters.elegir_mejor([r], "Matrix (1999)", 1999, None)
assert motivo == "aceptado", (mejor, motivo)
empate = [dict(r), dict(r)]
m2, mo2, _ = posters.elegir_mejor(empate, "Matrix (1999)", 1999, None)
assert mo2 == "empate", (m2, mo2)
print("posters OK  (puntaje Matrix =", p, ")")

# escaneo
u = escaneo.detectar_unidades()
assert u, "sin unidades"
assert all("ruta" in x for x in u), "campo ruta falta"
print("escaneo OK  (", len(u), "unidades )")

# servidor
for nombre in ("ServidorGaleria", "Manejador", "E", "escribir_inventario", "ventana_galeria"):
    assert hasattr(servidor, nombre), nombre
servidor.escribir_historia_archivo()
print("servidor OK")
print("ACERCA_DE_NOSOTROS.txt existe:", servidor.HISTORIA.exists())
