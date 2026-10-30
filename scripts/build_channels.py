"""Official YouTube channels of broadcasters and news media, from Wikidata (CC0), grouped by language and country.

No keys, no accounts: only the public Wikidata SPARQL endpoint. Output: data/youtube-channels.json
  {"built": ISO time, "source": "wikidata", "count": n, "channels": [[channelId, name, [lang...], [country...], kind], ...]}
Languages are ISO 639-1. A channel with no stated language takes the official languages of its country.
"""
import json, os, sys, time, urllib.parse, urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
AGENT = "SaeedTV-open-data/1.0 (https://github.com/rfliming76/saeedtv-open-data)"
# One query per class: a single query over all of them times out on the public endpoint.
KINDS = {
    "tv_channel": "Q2001305",
    "tv_station": "Q1616075",
    "broadcaster": "Q15265344",
    "news_agency": "Q192283",
    "newspaper": "Q11032",
    "radio_station": "Q14350",
}


def sparql(query, tries=4):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:  # 429/504 from the shared endpoint: wait and retry
            print("retry", attempt + 1, e, file=sys.stderr)
            time.sleep(15 * (attempt + 1))
    raise RuntimeError("wikidata query failed")


def value(b, key):
    return b[key]["value"] if key in b else None


def country_languages():
    rows = sparql("""SELECT ?cc ?lang WHERE { ?c wdt:P297 ?cc; wdt:P37 ?l. ?l wdt:P218 ?lang }""")
    out = {}
    for b in rows:
        out.setdefault(value(b, "cc"), set()).add(value(b, "lang"))
    return out


def channels_of(kind, qid):
    rows = sparql(f"""SELECT ?item ?yt ?name ?lang ?cc WHERE {{
  ?item wdt:P2397 ?yt; wdt:P31/wdt:P279* wd:{qid} .
  FILTER NOT EXISTS {{ ?item wdt:P576 ?ended }}
  OPTIONAL {{ ?item wdt:P407 ?l. ?l wdt:P218 ?lang }}
  OPTIONAL {{ ?item wdt:P17 ?c. ?c wdt:P297 ?cc }}
  OPTIONAL {{ ?item rdfs:label ?name FILTER(LANG(?name) IN ("en","ar")) }}
}}""")
    print(kind, len(rows), file=sys.stderr)
    return rows


def build():
    by_country = country_languages()
    found = {}
    for kind, qid in KINDS.items():
        for b in channels_of(kind, qid):
            cid = value(b, "yt")
            if not cid or not cid.startswith("UC") or len(cid) != 24:
                continue
            row = found.setdefault(cid, {"name": "", "lang": set(), "cc": set(), "kind": kind})
            name = value(b, "name")
            if name and (not row["name"] or b["name"].get("xml:lang") == "en"):
                row["name"] = name
            if value(b, "lang"):
                row["lang"].add(value(b, "lang"))
            if value(b, "cc"):
                row["cc"].add(value(b, "cc"))
        time.sleep(2)
    out = []
    for cid, row in sorted(found.items()):
        # Country fallback only where the country has one or two official languages: the United States lists Samoan
        # and Chamorro for its territories, which would mislabel every American channel.
        fallback = set()
        for c in row["cc"]:
            official = by_country.get(c, set())
            if 0 < len(official) <= 2:
                fallback |= official
        lang = row["lang"] or fallback
        out.append([cid, row["name"], sorted(lang), sorted(row["cc"]), row["kind"]])
    return out


def main():
    rows = build()
    if len(rows) < 500:  # a broken endpoint answer must not replace good data
        sys.exit(f"only {len(rows)} channels; keeping the previous file")
    langs = {}
    for r in rows:
        for l in r[2] or ["?"]:
            langs[l] = langs.get(l, 0) + 1
    os.makedirs("data", exist_ok=True)
    doc = {"built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": "wikidata", "license": "CC0-1.0",
           "count": len(rows), "languages": dict(sorted(langs.items(), key=lambda x: -x[1])), "channels": rows}
    with open("data/youtube-channels.json", "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    print(len(rows), "channels;", list(doc["languages"].items())[:20])


if __name__ == "__main__":
    main()
