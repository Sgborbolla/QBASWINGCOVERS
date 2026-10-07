import re
t=open("QBASWING_COVERS_ESPECIFICACION.txt",encoding="utf-8").read()
for pat in ["9ebfa9", "api_key", "API KEY", "clave", "TMDB", "themoviedb", "api.themoviedb"]:
    n=len(re.findall(re.escape(pat), t, re.I))
    print("%-16s -> %d" % (pat, n))
print("="*60)
for m in re.finditer(r".{0,120}(api_key|clave de api|themoviedb).{0,160}", t, re.I):
    print("...", m.group(0).replace("\n"," | "), "...")
    print("-"*50)
