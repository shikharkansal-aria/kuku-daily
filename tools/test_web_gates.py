"""Parity check: web/gates.js must give the same answers as tools/gates.py. Needs node on PATH.
Usage: python -m tools.test_web_gates
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

from tools import gates

JS = Path(__file__).resolve().parent.parent / "web" / "gates.js"
FMT = "%Y-%m-%dT%H:%M"

SIMS = [(tier, slots, total, days, skip)
        for tier in ("free", "subscriber")
        for slots in (["20:00"], ["14:00", "22:00"], ["10:00"], [], ["25:99", "bad"], ["23:59", "00:00"])
        for total, days, skip in ((3, 10, []), (21, 14, [4]), (21, 21, [2, 9]), (50, 30, []))]
UNLOCKS = ["2026-11-10T20:00", "2026-11-10T23:30", "2026-12-31T22:01", "2027-02-28T00:00"]
SLOTS = [["20:00"], ["14:00", "22:00"], ["00:00"], [], ["9:00", "07:30"]]
STREAKS = [(s, u, back) for s in (-1, 0, 2, 3, 6, 7, 12)
           for u, back in (("2026-11-10T20:00", "2026-11-11T20:00"), ("2026-11-10T20:00", "2026-11-11T20:01"))]


def python_side():
    p = lambda s: datetime.strptime(s, FMT)
    return {
        "sim": [gates.simulate(t, sl, tot, days, skip_days=tuple(sk)) for t, sl, tot, days, sk in SIMS],
        "rem": [gates.reminder(p(u), sl).strftime(FMT) for u in UNLOCKS for sl in SLOTS],
        "streak": [gates.update_streak(s, p(u), p(b)) for s, u, b in STREAKS],
        "level": [gates.level(s) for s in range(-2, 12)],
    }


NODE = """
const c = JSON.parse(process.argv[2]); globalThis.KD = { gates: c.CFG }; const G = require(process.argv[1]);
const p = (s) => new Date(s + ":00Z");
console.log(JSON.stringify({
  sim: c.SIMS.map(([t, sl, tot, days, sk]) => G.simulate(t, sl, tot, days, undefined, sk)),
  rem: c.UNLOCKS.flatMap((u) => c.SLOTS.map((sl) => G.iso(G.reminder(p(u), sl)))),
  streak: c.STREAKS.map(([s, u, b]) => G.updateStreak(s, p(u), p(b))),
  level: Array.from({ length: 14 }, (_, i) => G.level(i - 2)),
}));
"""


def main():
    cfg = {"tiers": gates.TIERS, "levels": gates.LEVELS, "grace_h": gates.GRACE_H}  # same shape export_web writes
    cases = json.dumps({"SIMS": SIMS, "UNLOCKS": UNLOCKS, "SLOTS": SLOTS, "STREAKS": STREAKS, "CFG": cfg})
    out = subprocess.run(["node", "-e", NODE, str(JS), cases], capture_output=True, text=True, check=True).stdout
    js, py = json.loads(out), python_side()
    for key, want in py.items():
        assert js[key] == want, f"{key} differs:\npy {want}\njs {js[key]}"
    n = sum(len(v) for v in py.values())
    print(f"gates parity ok: {n} cases ({len(SIMS)} simulations)")


if __name__ == "__main__":
    main()
