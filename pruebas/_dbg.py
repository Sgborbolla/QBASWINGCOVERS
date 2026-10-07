import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
import posters as p

nombres = ["Matrix (1999) 1080p x264 Blu-Ray", "El Senor de los Anillos (2001)",
           "One Piece T20", "Breaking Bad S01", "La Casa de Papel T3 720p HDTV",
           "Cien anos de soledad", "The Walking Dead (2010) WEB-DL"]
for n in nombres:
    print(repr(n), "->", repr(p.limpiar_nombre(n)), "| anio", p.extraer_anio(n), "| temp", p.extraer_temporada(n))

r = {"titulo":"Matrix","ano":1999,"tipo":"pelicula","tipo_pedido":"pelicula","temporadas":[],"alias":[]}
print("titulo='Matrix', ano=1999 ->", p.puntuar("Matrix", 1999, None, r))
print("titulo='Matrix (1999)', ano=1999 ->", p.puntuar("Matrix (1999)", 1999, None, r))
