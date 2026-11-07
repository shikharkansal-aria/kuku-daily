"""Raw outputs: personas -> show picks -> timed drops -> gate simulation -> validation report.

python -m tools.run_batch --show input/scripts --title "Show name" --personas data/test_personas.json --out outputs/runs/NAME
"""
import argparse
import json
import statistics
import time
from datetime import datetime
from pathlib import Path

from . import gates, llm
from .drops import build_schedule
from .match import load_catalog, pick, show_entry
from .persona import extract, quick


def run(show, personas, out, title=None, catalog=None):
    out = Path(out)
    (out / "personas").mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    entry = show_entry(show, title)
    cat = load_catalog(catalog, extra=[entry])
    sched = {lang: build_schedule(show, lang) for lang in ("english", "hinglish")}
    for lang, s in sched.items():
        (out / f"drops_{lang}.json").write_text(json.dumps(s, indent=2, ensure_ascii=False))
    (out / "show_entry.json").write_text(json.dumps(entry, indent=2))
    rows = []
    for p in json.loads(Path(personas).read_text(encoding="utf-8")):
        try:
            persona = quick(**p["quick"]) if "quick" in p else extract(p["answers"], p["language"])
        except Exception as e:  # recorded, never hidden
            rows.append({"id": p["id"], "error": f"persona: {str(e)[:200]}"})
            continue
        m = pick(persona, cat)
        drops = sched[persona.language]["drops"]
        sim = gates.simulate(p.get("tier", "free"), persona.slots, len(drops), days=14, skip_days=(4,))
        rec = {"input": p, "persona": persona.model_dump(), "match": m,
               "gets_input_show": any(x["id"] == entry["id"] for x in m["picks"]), "gate_sim": sim}
        (out / "personas" / f"{p['id']}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False))
        rows.append({"id": p["id"], "persona": persona, "match": m, "gets": rec["gets_input_show"],
                     "tier": p.get("tier", "free"), "sim": sim})
    meta = {"when": datetime.now().isoformat(timespec="seconds"), "llm": llm.settings(), "calls": dict(llm.CALLS),
            "seconds": round(time.time() - t0, 1), "show": str(show), "personas": str(personas)}
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2))
    (out / "validation_report.md").write_text(report(rows, sched, entry, meta))
    return out


def report(rows, sched, entry, meta):
    L = ["# Validation report", f"Run {meta['when']} | provider {meta['llm']} | LLM calls {meta['calls']} | {meta['seconds']} s", ""]
    d = sched["english"]["drops"]
    secs = [x["seconds"] for x in d]
    inwin = sum(240 <= s <= 360 for s in secs)
    strong = sum(x["cliff_score"] >= 0.6 for x in d)
    L += ["## Drops (Kuku show)", f"- {len(d)} drops from {sched['english']['episodes']} episodes; length min {min(secs)} s, "
          f"median {statistics.median(secs)} s, max {max(secs)} s; {inwin}/{len(d)} within 4 to 6 min",
          f"- {strong}/{len(d)} drops end on a strong cliffhanger (combined score 0.6+)"]
    for lang, s in sched.items():
        bad = [x["n"] for x in s["drops"] if not x["grounded"]]
        fixed = [x["n"] for x in s["drops"] if x.get("repaired")]
        L.append(f"- {lang} teasers grounded in a real ending line: {len(s['drops']) - len(bad)}/{len(s['drops'])}"
                 + (f"; NOT grounded: drops {bad}" if bad else "")
                 + (f"; quote added by code (model left it out): drops {fixed}" if fixed else ""))
    if sched["english"].get("skipped_episodes"):
        L.append(f"- episode files skipped (empty or untimed): {sched['english']['skipped_episodes']}")
    unscored = [e["ep"] for e in sched["english"]["episode_scores"] if e["llm"] is None]
    L.append(f"- episodes the LLM failed to score (rule score used): {unscored or 'none'}")
    L += ["", "## Personas and picks",
          "| persona | tier | who | lang | likes | dislikes | picks (source) | gets Kuku show | problems |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if "error" in r:
            L.append(f"| {r['id']} | | | | | | | | {r['error']} |")
            continue
        p, m = r["persona"], r["match"]
        probs = []
        for s in m["picks"]:
            if set(s["tags"]) & set(p.dislikes):
                probs.append(f"{s['id']} has a disliked tag")
            if p.watch_with == "family" and not s.get("family_safe", True):
                probs.append(f"{s['id']} not family safe")
        if not p.likes:
            probs.append("no likes extracted")
        if m["error"]:
            probs.append("LLM error, fallback used")
        L.append(f"| {r['id']} | {r['tier']} | {p.who} | {p.language} | {', '.join(p.likes)} | {', '.join(p.dislikes)} | "
                 f"{'; '.join(s['title'] for s in m['picks'])} ({m['source']}) | {'yes' if r['gets'] else 'no'} | {'; '.join(probs) or 'none'} |")
    L += ["", "## Gate simulation (first persona of each tier, viewer skips day 4)"]
    for tier in ("free", "subscriber"):
        r = next((r for r in rows if r.get("tier") == tier and "sim" in r), None)
        if r:
            L.append(f"- {tier}: waits by session {[x['wait_h'] for x in r['sim']]} h; drops open {[x['drops_open'] for x in r['sim']]}")
    L += ["", f"Kuku show catalog entry: tags {entry['tags']}, family_safe {entry['family_safe']}"]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", required=True)
    ap.add_argument("--title")
    ap.add_argument("--personas", default="data/test_personas.json")
    ap.add_argument("--catalog")
    ap.add_argument("--out", default=f"outputs/runs/{datetime.now():%Y%m%d-%H%M}")
    ap.add_argument("--model", help="override LLM_MODEL")
    ap.add_argument("--base-url", help="override OPENAI_BASE_URL")
    ap.add_argument("--key-env", help="name of the env var holding the API key, e.g. ALT_OPENAI_API_KEY")
    a = ap.parse_args()
    import os
    with llm.use(LLM_MODEL=a.model, OPENAI_BASE_URL=a.base_url, OPENAI_API_KEY=os.getenv(a.key_env or "", "")):
        print("wrote", run(a.show, a.personas, a.out, a.title, a.catalog))
