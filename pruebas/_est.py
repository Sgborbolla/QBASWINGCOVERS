import io
t = io.open("servidor.py", encoding="utf-8").read().splitlines()
i = next(k for k,l in enumerate(t) if l.startswith("def _estado_de_carpeta"))
print("\n".join("%d: %s" % (k+1, t[k]) for k in range(i, min(i+30, len(t)))))
