import sys
sys.path.insert(0,".")
import fuentes as F
# La clave TMDB vive solo en config.json (local, no se versiona).
from qbaswing_covers import cargar_config
cfg = cargar_config()
def probar(nombre, fn):
    try:
        r=fn()
        if r:
            p=r[0].get("poster_url")
            print("%-24s %2d resultados | 1er poster: %s" % (nombre, len(r), (p[:70] if p else "SIN POSTER")))
        else:
            print("%-24s SIN RESPUESTA" % nombre)
    except Exception as e:
        print("%-24s ERROR %s" % (nombre, e))
probar("TMDB pelicula", lambda: F.tmdb_pelicula(cfg,"The Matrix",1999))
probar("TMDB serie",    lambda: F.tmdb_serie(cfg,"Breaking Bad",2008))
probar("TVmaze",        lambda: F.tvmaze("Breaking Bad"))
probar("AniList",       lambda: F.anilist("Naruto"))
probar("OpenLibrary",   lambda: F.openlibrary("Harry Potter"))
probar("GoogleBooks",   lambda: F.googlebooks("Harry Potter"))
