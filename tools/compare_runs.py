"""Agreement between two runs of the same inputs on different models (a cheap quality check).

python -m tools.compare_runs outputs/runs/A outputs/runs/B > compare.md
"""
import json
import statistics
import sys
from pathlib import Path


def load(d):
    d = Path(d)
    drops = json.loads((d / "drops_english.json").read_text())
    picks = {p.stem: {x["id"] for x in json.loads(p.read_text())["match"]["picks"]} for p in (d / "personas").glob("*.json")}
    model = json.loads((d / "run_meta.json").read_text())["llm"].get("LLM_MODEL", "?")
    return drops, picks, model


def compare(a, b):
    (da, pa, ma), (db, pb, mb) = load(a), load(b)
    sa = {e["ep"]: e["llm"] for e in da["episode_scores"] if e["llm"]}
    sb = {e["ep"]: e["llm"] for e in db["episode_scores"] if e["llm"]}
    eps = sorted(set(sa) & set(sb))
    x, y = [sa[e] for e in eps], [sb[e] for e in eps]
    rho = statistics.correlation(x, y, method="ranked") if len(eps) > 2 and len(set(x)) > 1 and len(set(y)) > 1 else float("nan")
    within1 = sum(abs(i - j) <= 1 for i, j in zip(x, y))
    cuts_a = {d["episodes"][-1] for d in da["drops"]}
    cuts_b = {d["episodes"][-1] for d in db["drops"]}
    shared = sorted(set(pa) & set(pb))
    overlap = [len(pa[p] & pb[p]) for p in shared]
    L = [f"# Model agreement: {ma} vs {mb}", "",
         f"- Cliffhanger scores (1 to 5) on {len(eps)} episode endings: Spearman {rho:.2f}; "
         f"within 1 point on {within1}/{len(eps)}; exact match on {sum(i == j for i, j in zip(x, y))}/{len(eps)}",
         f"- Drop cut points: {len(cuts_a & cuts_b)} shared of {len(cuts_a)} ({ma}) and {len(cuts_b)} ({mb})",
         f"- Show picks per persona (2 each): both same {overlap.count(2)}, one same {overlap.count(1)}, "
         f"none same {overlap.count(0)} (of {len(shared)})",
         "", "| episode | " + ma + " | " + mb + " |", "|---|---|---|"]
    L += [f"| {e} | {sa[e]} | {sb[e]} |" for e in eps if abs(sa[e] - sb[e]) >= 2]
    return "\n".join(L) + "\n\n(Table lists only episodes where the models differ by 2 or more points.)\n"


if __name__ == "__main__":
    print(compare(sys.argv[1], sys.argv[2]))
