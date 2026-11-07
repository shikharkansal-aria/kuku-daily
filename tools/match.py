"""Persona to 2 shows: code shortlists by tags, the LLM picks and explains, code checks the picks."""
import json
import re
from pathlib import Path

from rapidfuzz import fuzz

try:
    from . import llm
    from .parse_scripts import parse
    from .persona import TAGS
except ImportError:
    import llm
    from parse_scripts import parse
    from persona import TAGS

ROOT = Path(__file__).resolve().parent.parent


def load_catalog(path=None, extra=()):
    return json.loads(Path(path or ROOT / "data" / "catalog.json").read_text()) + list(extra)


def show_entry(show_dir, title=None):
    """Catalog entry for a show we have scripts for, built from loglines spread across the whole show."""
    files = sorted(Path(show_dir).glob("episode-*.txt"))
    step = max(1, len(files) // 10)  # about 10 loglines from start to end, not just the opening
    eps = [parse(p) for p in files[::step]]
    loglines = "\n".join(f"Ep {e['episode']}: {e.get('episode_logline', '')}" for e in eps)
    data = llm.complete(
        f"{loglines}\n\nReturn JSON: tags (3 to 5, only from {TAGS}; cover the genre, the setting and the core trope), logline (one sentence, max 25 words), "
        f"family_safe (false if any episode has torture, graphic violence or sexual content; true only if fine "
        f"to watch with parents and kids).",
        system="You tag microdramas for a catalog. JSON only.", want_json=True, task="show_entry")
    title = title or Path(show_dir).name
    return {"id": re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-"), "title": title,
            "platform": "Kuku TV (input pack)", "language": ["english"],
            "tags": [t for t in data.get("tags", []) if t in TAGS], "logline": data.get("logline", ""),
            "family_safe": bool(data.get("family_safe", False)), "source_url": "local", "has_scripts": True}


def _hits(wanted, tags):
    return sum(1 for w in wanted if any(fuzz.token_set_ratio(w, t) >= 85 for t in tags))


def score(persona, show):
    s = 2 * _hits(persona.likes, show["tags"]) - 3 * _hits(persona.dislikes, show["tags"])
    if persona.language == "hinglish" and "hindi" in show.get("language", []):
        s += 1
    if persona.watch_with == "family" and not show.get("family_safe", True):
        s -= 3
    return s


def pick(persona, catalog, n=2, k=6):
    if persona.watch_with == "family":  # safety is a hard rule in code, not a hint to the model
        catalog = [s for s in catalog if s.get("family_safe", True)] or catalog
    short = sorted(catalog, key=lambda s: score(persona, s), reverse=True)[:k]
    by_id = {s["id"]: s for s in short}
    lang = "Hinglish" if persona.language == "hinglish" else "English"
    items = "\n".join(f"- id={s['id']} | {s['title']} ({s['platform']}) | tags: {', '.join(s['tags'])} | {s['logline']}"
                      for s in short)
    prompt = (f"Viewer: {persona.model_dump_json()}\n\nShows:\n{items}\n\n"
              f"Pick the {n} shows this viewer is most likely to finish. Never pick a show with a tag they dislike. "
              f'Return JSON {{"picks": [{{"id": "...", "reason": "one line in {lang}, spoken to the viewer"}}]}}')
    error = None
    try:
        out = llm.complete(prompt, system="You recommend microdramas. JSON only.", want_json=True, task="match")
        picks = [p for p in out.get("picks", []) if p.get("id") in by_id][:n]
    except Exception as e:  # keep the app usable when the model fails; the report counts these
        picks, error = [], str(e)[:200]
    source = "llm"
    if len(picks) < n:  # shortcut: tag-score fallback, fine for a catalog of about 10 shows
        have = {p["id"] for p in picks}
        for s in short:
            if len(picks) < n and s["id"] not in have:
                liked = ", ".join(sorted(set(persona.likes) & set(s["tags"]))) or "a popular pick"
                picks.append({"id": s["id"], "reason": f"Matches what you like: {liked}"})
        source = "llm+fallback" if have else "fallback"
    return {"source": source, "error": error,
            "picks": [{**by_id[p["id"]], "reason": p.get("reason", "")} for p in picks]}
