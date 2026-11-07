"""Self-check for parse_scripts.py on a synthetic episode. Run: python3 -I tools/test_parse.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_scripts import parse  # noqa: E402

SAMPLE = """EPISODE NUMBER: Episode 7
EPISODE LOGLINE: A test logline.
CONTINUITY NOTES: Test notes.

--- SCRIPT START ---

SCENE 01
Scene heading: INT. HALL - NIGHT
Scene start: 00:00.00
Scene end: 01:05.50

Actions and dialogue:

**ACTION:**
Start: (00:01.00) | End: (00:02.50)
She raises her hand.

**ANNA (O.S.) (Cold, Furious):**
Start: (00:02.50) | End: (00:04.00)
"Get out."

**CAMERA:**
Start: (00:04.00) | End: (01:05.50)
Slow push in. --- SCRIPT END ---
"""

with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "episode-007-Episode 1.txt"
    p.write_text(SAMPLE)
    ep = parse(p)

assert ep["episode"] == 7 and ep["episode_logline"] == "A test logline."
s = ep["scenes"][0]
assert s["scene_start"] == 0.0 and s["scene_end"] == 65.5
a, d, c = s["blocks"]
assert a["type"] == "action" and a["start"] == 1.0 and a["text"] == "She raises her hand."
assert d["speaker"] == "ANNA" and d["delivery"] == ["O.S."] and d["cue"] == "Cold, Furious"
assert c["type"] == "camera" and c["text"] == "Slow push in."
print("parse_scripts self-check: ok")
