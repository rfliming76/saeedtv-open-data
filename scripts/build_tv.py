"""Free-to-air TV streams by language, from the iptv-org open lists, checked to play in a web page.

Writes data/tv/index.json (counts per language), data/tv/<lang>.json (one list per language) and data/tv/iptv.json
(every channel once, with its country and categories, for the Saeed TV «قنوات IPTV» page).
A stream is kept only when it is https, its channel is not adult, closed or on the iptv-org blocklist,
it needs no special user agent or referrer, and its playlist answers from a browser page on another site
(status 200, an #EXTM3U playlist and a CORS header): those are the streams a browser can actually play.
Streams iptv-org labels "Geo-blocked" are left out of the language lists and kept in iptv.json with a mark (flag 1), so the
page can say so instead of showing them as working. Flag 2 = not on air all day ("Not 24/7").
A thin run (under 300 playable streams) writes nothing, so the published lists never go empty.
"""
import concurrent.futures as cf
import json
import os
import sys
import time
import urllib.request

API = "https://iptv-org.github.io/api/"
ORIGIN = "https://saeedtv.pages.dev"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "tv")
MIN_TOTAL = 300

# ISO 639-3 (iptv-org) to the ISO 639-1 codes Saeed TV uses; languages without a two-letter code keep their three letters.
L3 = {"ara": "ar", "eng": "en", "fra": "fr", "deu": "de", "spa": "es", "por": "pt", "ita": "it", "rus": "ru", "ukr": "uk",
      "pol": "pl", "tur": "tr", "fas": "fa", "urd": "ur", "hin": "hi", "ben": "bn", "tam": "ta", "tel": "te", "mal": "ml",
      "kan": "kn", "mar": "mr", "guj": "gu", "pan": "pa", "zho": "zh", "jpn": "ja", "kor": "ko", "vie": "vi", "tha": "th",
      "ind": "id", "msa": "ms", "fil": "tl", "tgl": "tl", "nld": "nl", "swe": "sv", "nor": "no", "dan": "da", "fin": "fi",
      "isl": "is", "ces": "cs", "slk": "sk", "hun": "hu", "ron": "ro", "bul": "bg", "srp": "sr", "hrv": "hr", "bos": "bs",
      "slv": "sl", "mkd": "mk", "sqi": "sq", "ell": "el", "heb": "he", "kur": "ku", "aze": "az", "kaz": "kk", "uzb": "uz",
      "kat": "ka", "hye": "hy", "lit": "lt", "lav": "lv", "est": "et", "bel": "be", "cat": "ca", "eus": "eu", "glg": "gl",
      "som": "so", "amh": "am", "swa": "sw", "hau": "ha", "yor": "yo", "ibo": "ig", "zul": "zu", "afr": "af", "pus": "ps",
      "nep": "ne", "sin": "si", "khm": "km", "lao": "lo", "mya": "my", "mon": "mn", "tat": "tt", "kir": "ky", "tgk": "tg",
      "tuk": "tk", "gle": "ga", "cym": "cy", "mlt": "mt", "ltz": "lb", "fao": "fo", "yue": "zh", "cmn": "zh"}


def get(name, tries=3):
    local = os.environ.get("IPTV_API_DIR")  # local test runs: read already downloaded API files from this folder
    if local:
        path = os.path.join(local, name)
        if not os.path.exists(path):
            raise SystemExit("missing " + path)
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    for i in range(tries):
        try:
            req = urllib.request.Request(API + name, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 - one retry policy for every network error
            print("retry", name, e, file=sys.stderr)
            time.sleep(5 * (i + 1))
    raise SystemExit("could not read " + name)


def playable(url):
    """True when a browser page on another site could load this playlist."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Origin": ORIGIN, "Referer": ORIGIN + "/"})
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status != 200:
                return False
            acao = (r.headers.get("Access-Control-Allow-Origin") or "").strip()
            if acao not in ("*", ORIGIN):
                return False
            return r.read(2048).lstrip(b"\xef\xbb\xbf \r\n\t").startswith(b"#EXTM3U")
    except Exception:  # noqa: BLE001 - any failure means the page could not play it
        return False


def main():
    streams, channels, feeds = get("streams.json"), get("channels.json"), get("feeds.json")
    try:
        blocked = {b.get("channel") for b in get("blocklist.json")}
    except SystemExit:
        blocked = set()
    try:
        logos = {}
        for x in get("logos.json"):
            logos.setdefault(x.get("channel"), x.get("url"))
    except SystemExit:
        logos = {}
    ch = {c["id"]: c for c in channels}
    fl = {}
    for f in feeds:
        fl.setdefault(f["channel"], []).append(f)

    cand = []
    for s in streams:
        cid, url = s.get("channel"), s.get("url") or ""
        c = ch.get(cid)
        if not c or not url.startswith("https://") or s.get("user_agent") or s.get("referrer"):
            continue
        if c.get("is_nsfw") or c.get("closed") or cid in blocked:
            continue
        labels = [str(x).lower() for x in (s.get("labels") or [])]
        geo = any("geo" in x for x in labels)
        fs = fl.get(cid, [])
        feed = next((f for f in fs if f.get("id") == s.get("feed")), None) or next((f for f in fs if f.get("is_main")), None)
        langs = (feed or {}).get("languages") or sorted({l for f in fs for l in (f.get("languages") or [])})
        langs = sorted({L3.get(l, l) for l in langs})
        cand.append({"id": cid, "n": s.get("title") or c.get("name"), "u": url, "c": c.get("country") or "",
                     "cat": c.get("categories") or [], "q": s.get("quality") or "", "lg": langs,
                     "logo": logos.get(cid) or "", "p": 0 if any("24/7" in x for x in labels) else 1, "g": geo})
    print("candidates", len(cand), file=sys.stderr)

    ok = []
    with cf.ThreadPoolExecutor(64) as ex:
        for x, good in zip(cand, ex.map(lambda x: playable(x["u"]), cand)):
            if good:
                ok.append(x)
    print("playable", len(ok), file=sys.stderr)
    if len(ok) < MIN_TOTAL:
        raise SystemExit("only %d playable streams: keeping the published lists" % len(ok))

    # One stream per channel and language: the best quality first.
    qn = lambda q: int("".join(ch for ch in q if ch.isdigit()) or 0)
    by = {}
    for x in sorted(ok, key=lambda x: -qn(x["q"])):
        if x["g"]:
            continue
        for l in x["lg"]:
            by.setdefault(l, {}).setdefault(x["id"], x)
    built = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        if old.endswith(".json"):
            os.remove(os.path.join(OUT, old))
    counts = {}
    for l, m in by.items():
        rows = sorted(m.values(), key=lambda x: (x["p"], x["n"].lower()))
        counts[l] = len(rows)
        with open(os.path.join(OUT, l + ".json"), "w", encoding="utf-8") as f:
            json.dump({"built": built, "lang": l, "source": "iptv-org (CC0 / Unlicense)",
                       "channels": [[x["n"], x["u"], x["c"], x["cat"], x["q"], x["logo"], x["id"]] for x in rows]},
                      f, ensure_ascii=False, separators=(",", ":"))
    # Every channel once: a stream without the geo mark first, then the best quality.
    one = {}
    for x in sorted(ok, key=lambda x: (x["g"], -qn(x["q"]))):
        one.setdefault(x["id"], x)
    rows = sorted(one.values(), key=lambda x: (x["c"], x["n"].lower()))
    with open(os.path.join(OUT, "iptv.json"), "w", encoding="utf-8") as f:
        json.dump({"built": built, "source": "iptv-org (CC0 / Unlicense)", "checked_from": ORIGIN,
                   "fields": ["name", "url", "country", "categories", "quality", "logo", "id", "languages", "flags"],
                   "flags": {"1": "geo-blocked outside its country (iptv-org label)", "2": "not 24/7"},
                   "channels": [[x["n"], x["u"], x["c"], x["cat"], x["q"], x["logo"], x["id"], x["lg"],
                                 (1 if x["g"] else 0) | (2 if x["p"] == 0 else 0)] for x in rows]},
                  f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"built": built, "source": "https://github.com/iptv-org/iptv", "checked_from": ORIGIN,
                   "count": len({x["id"] for x in ok if not x["g"]}), "iptv": len(one), "geo_marked": sum(1 for x in one.values() if x["g"]),
                   "languages": dict(sorted(counts.items(), key=lambda kv: -kv[1]))},
                  f, ensure_ascii=False, indent=1)
    print("languages", len(counts), "pl", counts.get("pl"), "ar", counts.get("ar"), file=sys.stderr)


if __name__ == "__main__":
    main()
