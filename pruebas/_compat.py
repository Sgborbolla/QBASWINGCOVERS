import re, glob, io
patrones = {
 "removeprefix/removesuffix (3.9)": r"\.(removeprefix|removesuffix)\(",
 "functools.cache (3.9)": r"functools\.cache",
 "dict union | (3.9)": r"\w\s*\|\s*\{",
 "list/dict/tuple[...] anotacion (3.9)": r":\s*(list|dict|tuple|set)\[",
 "union X | Y anotacion (3.10)": r"->\s*\w+\s*\|\s*\w+",
 "match (3.10)": r"^\s*match\s+.*:\s*$",
 "zoneinfo (3.9)": r"\bzoneinfo\b",
 "math.lcm (3.9)": r"math\.lcm",
 "graphlib (3.9)": r"\bgraphlib\b",
 "anext (3.10)": r"\banext\(",
 "tomllib (3.11)": r"\btomllib\b",
 "ExceptionGroup (3.11)": r"ExceptionGroup",
 "walrus := (3.8 ok)": r":=",
 "f-string = (3.8 ok)": r"f['\"].*\{\w+=\}",
}
archivos = [f for f in glob.glob("*.py") if not f.startswith("_")]
for nombre, pat in patrones.items():
    hits = []
    for a in archivos:
        t = io.open(a, encoding="utf-8").read()
        for m in re.finditer(pat, t, re.M):
            linea = t[:m.start()].count("\n")+1
            hits.append("%s:%d" % (a, linea))
    if hits:
        print("%-38s %s" % (nombre, ", ".join(hits[:8])))
print("--- fin de revision ---")
