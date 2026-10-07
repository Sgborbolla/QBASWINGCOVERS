import json, urllib.request
def t(desc, url, ua):
    try:
        req=urllib.request.Request(url, headers={"User-Agent":ua})
        r=urllib.request.urlopen(req,timeout=25)
        j=json.loads(r.read().decode("utf-8","replace"))
        print("%-30s OK items=%d" % (desc, len(j.get("items") or [])))
    except Exception as e:
        print("%-30s FALLO %s" % (desc, e))
b="https://www.googleapis.com/books/v1/volumes?q=harry+potter&maxResults=3"
t("Books sin UA", b, "Python-urllib/3.13")
t("Books UA navegador", b, "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
t("Books UA QBASwing", b, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QBASWINGCovers/1.0")
t("Books + country=US", b+"&country=US", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
