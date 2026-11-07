"""Show folder to timed drops: score every episode ending, pack ~4 to 5 min drops that end on the
strongest cliffhanger, and write a come-back teaser per drop that quotes a real line (checked in code)."""
import re
from pathlib import Path

from rapidfuzz import fuzz

try:
    from . import llm
    from .parse_scripts import parse
except ImportError:
    import llm
    from parse_scripts import parse

TAIL_S = 20  # seconds of each episode ending that the scorer reads
LO_S, HI_S = 210, 360  # drop length window, 3.5 to 6 min; ~2 to 3 episodes of a 2 min show
CUE = re.compile(r"shock|terrif|horrif|gasp|scream|furious|panic|desperat|fear|stunn|trembl|menac|threat|cry", re.I)
THREAT = re.compile(r"\b(kill|die|dead|death|gallows|burn|poison|execut|guards?|secret|truth|never|blood|hang|"
                    r"arrest|witch|lie|liar|traitor)", re.I)


def load_show(show_dir, skipped=None):
    out = []
    for p in sorted(Path(show_dir).glob("episode-*.txt")):
        e = parse(p)
        blocks = [b for s in e["scenes"] for b in s["blocks"] if b["start"] is not None]
        if not blocks:  # an empty or untimed episode cannot be scheduled; reported, never dropped silently
            if skipped is not None:
                skipped.append(p.name)
            continue
        dur = max(b["end"] or b["start"] for b in blocks)
        talk = [b for b in blocks if b["type"] != "camera"]
        tail = [b for b in talk if b["start"] >= dur - TAIL_S] or talk[-3:]
        out.append({"ep": e["episode"], "seconds": round(dur, 1), "logline": e.get("episode_logline", ""), "tail": tail})
    if not out:
        raise ValueError(f"no parseable episode-*.txt files in {show_dir}")
    return out


def line(b):
    who = b["speaker"] or b["type"].upper()
    return f"{who}{' (' + b['cue'] + ')' if b['cue'] else ''}: {b['text']}"


def rule_score(tail):
    text = " ".join(b["text"] for b in tail)
    last = tail[-1]["text"].strip().strip('"') if tail else ""
    s = min(text.count("?"), 2) * 0.15 + min(text.count("!"), 3) * 0.1
    s += 0.25 if CUE.search(" ".join(b["cue"] or "" for b in tail)) else 0
    s += 0.2 if THREAT.search(text) else 0
    s += 0.15 if any(b["type"] == "sound_fx" for b in tail) else 0
    s += 0.15 if re.search(r"\?|\.\.\.$|!$", last) else 0
    return round(min(s, 1.0), 2)


def llm_scores(eps, batch=10):
    scores = {}
    for i in range(0, len(eps), batch):
        chunk = eps[i:i + batch]
        body = "\n\n".join(f"EPISODE {e['ep']} ENDING:\n" + "\n".join(line(b) for b in e["tail"]) for e in chunk)
        out = llm.complete(
            f"{body}\n\nFor each episode, rate how strongly its ending makes a viewer need the next episode: "
            f"5 = unresolved danger, reveal or question; 1 = calm or resolved. Name the open question in under 12 words. "
            f'Return JSON {{"episodes": [{{"ep": 1, "score": 3, "open_question": "..."}}]}}',
            system="You judge cliffhangers in vertical microdramas. JSON only.", want_json=True, task="cliff")
        for r in out.get("episodes", []):
            if r.get("ep") in {e["ep"] for e in chunk}:
                scores[r["ep"]] = {"score": max(1, min(5, int(r.get("score", 1)))), "open_question": r.get("open_question", "")}
    return scores


def pack(eps):
    """Greedy: from each start, cut where the ending is strongest inside the length window."""
    drops, i = [], 0
    while i < len(eps):
        total, cands = 0, []
        for j in range(i, len(eps)):
            if j > i and not cands and total + eps[j]["seconds"] > HI_S:
                cands.append((eps[j - 1]["combined"], -(j - 1), j - 1))  # cut short before an over-long episode
                break
            total += eps[j]["seconds"]
            if total > HI_S and cands:
                break
            if total >= LO_S or total > HI_S or j == len(eps) - 1:
                cands.append((eps[j]["combined"], -j, j))
            if total >= HI_S:
                break
        end = max(cands)[2]
        drops.append((i, end))
        i = end + 1
    return drops


def grounded(quote, tail):
    q = (quote or "").strip().strip('"').strip()
    return len(q) >= 3 and any(fuzz.partial_ratio(q.lower(), b["text"].strip('"').lower()) >= 85 for b in tail)


def teasers(drops, eps, language, batch=5):
    lang = "Hinglish (Hindi in Roman script mixed with English)" if language == "hinglish" else "English"
    res = {}
    for i in range(0, len(drops), batch):
        chunk = list(enumerate(drops))[i:i + batch]
        body = "\n\n".join(f"DROP {k + 1} ENDING LINES:\n" + "\n".join(line(b) for b in eps[end]["tail"])
                           for k, (_, end) in chunk)
        out = llm.complete(
            f"{body}\n\nFor each drop write a teaser in {lang} that makes the viewer come back for the next drop: "
            f"max 2 short lines, include exactly one line of dialogue copied word for word from its ENDING LINES inside "
            f"double quotes, never say what happens next. "
            f'Return JSON {{"teasers": [{{"drop": 1, "teaser": "...", "quoted_line": "..."}}]}}',
            system="You write come-back teasers for an Indian microdrama app. JSON only.", want_json=True,
            task=f"teaser_{language}")
        asked = {k + 1 for k, _ in chunk}
        for r in out.get("teasers", []):
            if r.get("drop") in asked and r["drop"] not in res:  # ignore invented drops and duplicates
                res[r["drop"]] = r
    return res


def build_schedule(show_dir, language="english", use_llm=True):
    skipped = []
    eps = load_show(show_dir, skipped)
    scores = llm_scores(eps) if use_llm else {}
    for e in eps:
        e["rule"] = rule_score(e["tail"])
        s = scores.get(e["ep"])
        e["llm"] = s["score"] if s else None
        e["open_question"] = s["open_question"] if s else ""
        e["combined"] = round(0.6 * e["llm"] / 5 + 0.4 * e["rule"], 2) if s else e["rule"]
    spans = pack(eps)
    tz = teasers(spans, eps, language) if use_llm else {}
    drops = []
    for k, (a, b) in enumerate(spans):
        t = dict(tz.get(k + 1, {}))
        quote = (t.get("quoted_line") or "").strip().strip('"')
        t["repaired"] = False
        if grounded(quote, eps[b]["tail"]) and fuzz.partial_ratio(quote.lower(), (t.get("teaser") or "").lower()) < 85:
            t["teaser"], t["repaired"] = f'{(t.get("teaser") or "").strip()}\n"{quote}"', True  # code adds the verified quote
        drops.append({"n": k + 1, "episodes": [e["ep"] for e in eps[a:b + 1]], "repaired": t["repaired"],
                      "seconds": round(sum(e["seconds"] for e in eps[a:b + 1]), 1),
                      "cliff_score": eps[b]["combined"], "llm_score": eps[b]["llm"], "rule_score": eps[b]["rule"],
                      "open_question": eps[b]["open_question"], "teaser": t.get("teaser", ""),
                      "quoted_line": t.get("quoted_line", ""),
                      "grounded": grounded(t.get("quoted_line"), eps[b]["tail"]) and
                      fuzz.partial_ratio((t.get("quoted_line") or "").strip('"').lower(), (t.get("teaser") or "").lower()) >= 85})
    return {"show_dir": str(show_dir), "language": language, "episodes": len(eps), "skipped_episodes": skipped,
            "episode_scores": [{k: e[k] for k in ("ep", "seconds", "rule", "llm", "combined", "open_question")} for e in eps],
            "drops": drops}
