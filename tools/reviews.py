"""Pull newest Play Store reviews, tag themes by keyword, write CSV + summary JSON. No LLM.
Usage: python -m tools.reviews --app com.vlv.aravali.reels --n 300 --lang en --country in --out outputs/evidence/
"""
import argparse, csv, json, os, re
from collections import Counter
from google_play_scraper import reviews, Sort

# Transparent keyword lists (lowercase, matched at word start, case-insensitive). Edit here.
THEMES = {
    "paywall_price": ["paisa", "paise", "mehenga", "mahenga", "expensive", "recharge", "subscription", "subscribe",
                      "coins", "coin", "pay ", "paid", "payment", "premium", "price", "pricey", "costly", "money",
                      "unlock", "refund", "charged", "rupees", "₹", "lock", "free episode", "membership",
                      "plan", "paywall", "autopay", "deduct"],
    "too_many_or_wrong_fit": ["too many shows", "too many stories", "too many series", "too many similar", "so many shows", "so many stories",
                              "same type", "no variety", "variety", "wrong recommend",
                              "recommendation", "irrelevant", "can't find", "cannot find", "search",
                              "dubbed", "not interesting", "my taste", "choice", "category", "genre",
                              "only romance", "only hindi", "options"],
    "repetitive_or_burnout": ["bore", "boring", "repetitive", "same story", "same stories",
                              "same thing", "same type", "same plot", "all same", "copy", "timepass", "stretch", "dragged", "too long", "unnecessary",
                              "one story",
                              "ek jaisi", "ek hi", "wahi", "fir se"],
    "ads": ["ads", "ad", "advert", "vigyapan"],
    "app_bugs": ["bug", "crash", "glitch", "hang", "lag", "buffer", "not working", "doesn't work", "does not work",
                 "not loading", "won't load", "error", "slow", "freeze", "stuck", "black screen", "login", "otp",
                 "chalta nahi", "nahi chal"],
    "positive_story": ["good story", "great story", "nice story", "best story", "love the story", "love the shows",
                       "interesting", "excellent", "amazing", "awesome", "superb", "entertaining", "addictive",
                       "binge", "bingeing", "well made", "fresh", "kahani", "mast", "badhiya", "good shows",
                       "nice shows", "good content", "quality", "climax", "twist"],
}

def tags(text):
    t = (text or "").lower()  # match at word start, any ending (so "bore" hits "boredom")
    def hit(k, w):
        w = w.strip()
        neg = r"(?<!not )(?<!no )" if k == "positive_story" else ""
        return re.search(r"(?<!\w)" + neg + re.escape(w) + (r"(?!\w)" if len(w) <= 3 else ""), t)
    return [k for k, kws in THEMES.items() if any(hit(k, w) for w in kws)]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--app", required=True); p.add_argument("--n", type=int, default=300)
    p.add_argument("--lang", default="en"); p.add_argument("--country", default="in")
    p.add_argument("--out", default="outputs/evidence/"); p.add_argument("--suffix", default="")
    a = p.parse_args()
    raw, _ = reviews(a.app, lang=a.lang, country=a.country, sort=Sort.NEWEST, count=a.n)
    rows = [{"date": r["at"].strftime("%Y-%m-%d"), "score": r["score"], "thumbs_up": r["thumbsUpCount"],
             "text": re.sub(r"\s+", " ", r["content"] or "").strip(),
             "themes": ";".join(tags(r["content"]))} for r in raw]
    if not rows: raise SystemExit(f"no reviews returned: {a}")
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.join(a.out, f"reviews_{a.app}{a.suffix or ('_' + a.lang if a.lang != 'en' else '')}")
    with open(stem + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    n = len(rows); tc = Counter(t for r in rows for t in r["themes"].split(";") if t)
    stars = Counter(r["score"] for r in rows)
    by_star = {s: {t: sum(1 for r in rows if r["score"] == s and t in r["themes"].split(";")) for t in THEMES}
               for s in sorted(stars)}
    summ = {"app": a.app, "lang": a.lang, "country": a.country, "n": n,
            "date_range": [min(r["date"] for r in rows), max(r["date"] for r in rows)],
            "untagged": sum(1 for r in rows if not r["themes"]),
            "themes": {t: {"count": tc[t], "pct": round(100 * tc[t] / n, 1)} for t in THEMES},
            "stars": {str(s): {"count": c, "pct": round(100 * c / n, 1)} for s, c in sorted(stars.items())},
            "theme_by_star": {str(s): v for s, v in by_star.items()}}
    json.dump(summ, open(stem + "_summary.json", "w", encoding="utf-8"), indent=2)
    print(stem, n, {t: summ["themes"][t]["pct"] for t in THEMES})

if __name__ == "__main__":
    main()
