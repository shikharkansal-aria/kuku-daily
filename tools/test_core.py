"""Offline checks on the mock provider (no key, no Kuku data). Run: .venv/bin/python -m tools.test_core"""
import json
import os
import re
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

os.environ["LLM_PROVIDER"] = "mock"
from . import drops, gates, llm, match, persona, run_batch  # noqa: E402

llm.MOCKS.update({
    "persona": lambda p: json.dumps({"who": "homemaker", "slots": ["14:00", "9pm"], "likes": ["family drama", "zombies"],
                                     "dislikes": ["fantasy"], "watch_with": "family", "minutes_per_day": 20, "summary": "x"}),
    "show_entry": lambda p: json.dumps({"tags": ["revenge", "romance", "nonsense"], "logline": "x", "family_safe": False}),
    "match": lambda p: json.dumps({"picks": [{"id": i, "reason": "r"} for i in re.findall(r"id=(\S+)", p)[:1]] + [{"id": "ghost", "reason": "r"}]}),
    "cliff": lambda p: json.dumps({"episodes": [{"ep": int(e), "score": int(e) % 5 + 1, "open_question": "q"}
                                                for e in re.findall(r"EPISODE (\d+) ENDING", p)]}),
})
for lang in ("english", "hinglish"):
    llm.MOCKS[f"teaser_{lang}"] = lambda p: json.dumps({"teasers": [
        {"drop": int(k), "teaser": f'Kal dekho: "{q}"', "quoted_line": q}
        for k, q in re.findall(r'DROP (\d+) ENDING LINES:\n[^:\n]*: "?([^"\n]+)', p)]
        + [{"drop": 99, "teaser": 'invented "nope"', "quoted_line": "nope"}]})  # a drop it was not shown

EP = """EPISODE NUMBER: Episode {n}
EPISODE LOGLINE: Test episode {n}.
CONTINUITY NOTES: none

SCENE 01
Scene heading: INT. HOUSE - DAY
Scene start: 00:00.00
Scene end: 02:00.00

**ACTION:**
Start: (00:05.00) | End: (00:08.00)
She opens the door.

**ANNA (Terrified):**
Start: (01:45.00) | End: (02:00.00)
"Who is standing behind you?"
"""

# gates: waits shrink with streak, never zero; lateness drops one level
assert [gates.TIERS["free"]["waits_h"][gates.level(s)] for s in (0, 2, 3, 6, 7, 30)] == [24, 24, 10, 10, 5, 5]
assert min(gates.TIERS["subscriber"]["waits_h"]) > 0
t = datetime(2026, 11, 9, 20, 0)
assert gates.reminder(t + timedelta(hours=10), ["20:00"]) == datetime(2026, 11, 10, 20, 0)
assert gates.reminder(datetime(2026, 11, 10, 6, 0), ["08:30", "22:00"]) == datetime(2026, 11, 10, 8, 30)
assert gates.update_streak(8, t, t + timedelta(hours=3)) == 9
assert gates.update_streak(8, t, t + timedelta(hours=30)) == 3
sim = gates.simulate("free", ["20:00"], total_drops=5)
assert len(sim) == 5 and sim[-1]["drops_open"] == 5

# persona: model junk is coerced, contradictions resolved toward dislikes
q = persona.Persona.model_validate({"minutes_per_day": "unknown", "watch_with": "with saas", "likes": ["revenge", "romance"], "dislikes": ["revenge"]})
assert q.minutes_per_day == 15 and q.watch_with == "unknown" and q.likes == ["romance"]
# persona: unknown tags and bad slots are dropped by validation
p = persona.extract(["a"] * 5, "hinglish")
assert p.likes == ["family drama"] and p.slots == ["14:00"] and p.language == "hinglish"

with tempfile.TemporaryDirectory() as d:
    show = Path(d) / "show"
    show.mkdir()
    for n in range(1, 7):
        (show / f"episode-{n:03d}-Episode {n}.txt").write_text(EP.format(n=n))
    s = drops.build_schedule(show, "english")
    eps = [e for x in s["drops"] for e in x["episodes"]]
    assert eps == list(range(1, 7)), eps  # every episode once, in order
    assert all(x["grounded"] for x in s["drops"]), s["drops"]
    assert all(drops.LO_S <= x["seconds"] <= drops.HI_S for x in s["drops"][:-1])
    entry = match.show_entry(show, "Test Show")
    assert entry["tags"] == ["revenge", "romance"]
    cat = match.load_catalog(extra=[entry])
    m = match.pick(p, cat)
    assert len(m["picks"]) == 2 and m["source"] == "llm+fallback"  # ghost id rejected, fallback filled
    out = run_batch.run(show, Path(__file__).resolve().parent.parent / "data" / "test_personas.json", Path(d) / "run", "Test Show")
    rep = (out / "validation_report.md").read_text()
    assert "grounded" in rep and len(list((out / "personas").glob("*.json"))) == 10
print("core self-check: ok")
