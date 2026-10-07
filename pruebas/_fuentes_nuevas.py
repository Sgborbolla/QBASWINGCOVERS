# -*- coding: utf-8 -*-
import json, urllib.request
UA = {"User-Agent": "QBASWING-Covers/1.0 (local)"}
def pedir(nombre, url, headers=None):
    h = dict(UA)
    if headers: h.update(headers)
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=25)
        j = json.loads(r.read().decode("utf-8","replace"))
        print("%-22s OK   %s" % (nombre, str(j)[:90].replace("\n"," ")))
        return j
    except Exception as e:
        print("%-22s FALLO %s" % (nombre, e))
        return None

j = pedir("Jikan (anime)", "https://api.jikan.moe/v4/anime?q=naruto&limit=2")
if j and j.get("data"):
    print("      poster ->", j["data"][0]["images"]["jpg"]["large_image_url"])

pedir("MangaDex (manga)", "https://api.mangadex.org/manga?limit=2&title=berserk")
mb = pedir("MusicBrainz (musica)", "https://musicbrainz.org/ws/2/release/?query=release:%22Abbey%20Road%22&fmt=json&limit=2",
           {"User-Agent": "QBASWING-Covers/1.0 (local)"})
if mb and mb.get("releases"):
    rid = mb["releases"][0]["id"]
    print("      release ->", rid)
    pedir("CoverArtArchive", "https://coverartarchive.org/release/%s" % rid)
pedir("Internet Archive", "https://archive.org/advancedsearch.php?q=title:%22godfather%22+AND+mediatype:movies&fl[]=identifier&rows=2&output=json")
