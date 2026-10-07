import urllib.request, urllib.error, json
b="https://www.googleapis.com/books/v1/volumes?q=harry+potter&maxResults=3"
try:
    urllib.request.urlopen(urllib.request.Request(b, headers={"User-Agent":"Mozilla/5.0"}),timeout=25)
except urllib.error.HTTPError as e:
    print("codigo:", e.code)
    print("motivo:", e.reason)
    print("cuerpo:")
    print(e.read().decode("utf-8","replace")[:1200])
