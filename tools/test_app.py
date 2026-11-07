"""AppTest on the mock provider. Run: .venv/bin/python -m tools.test_app"""
import json
import os
import re
from pathlib import Path

os.environ["LLM_PROVIDER"] = "mock"
from streamlit.testing.v1 import AppTest  # noqa: E402

from . import llm  # noqa: E402

llm.MOCKS.update({
    "show_entry": lambda p: json.dumps({"tags": ["revenge", "family drama"], "logline": "x", "family_safe": True}),
    "match": lambda p: json.dumps({"picks": [{"id": i, "reason": "r"} for i in re.findall(r"id=(\S+)", p)[:2]]}),
    "cliff": lambda p: json.dumps({"episodes": [{"ep": int(e), "score": 4, "open_question": "q"}
                                                for e in re.findall(r"EPISODE (\d+) ENDING", p)]}),
})
for lang in ("english", "hinglish"):
    llm.MOCKS[f"teaser_{lang}"] = lambda p: json.dumps({"teasers": [
        {"drop": int(k), "teaser": f'Kal dekho: "{q}"', "quoted_line": q}
        for k, q in re.findall(r'DROP (\d+) ENDING LINES:\n[^:\n]*: "?([^"\n]+)', p)]})

at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=60).run()
assert not at.exception, at.exception
html = lambda: " ".join(m.value for m in at.markdown)
at.button(key="v_homemaker").click().run()  # one-click demo viewer, no model
assert not at.exception, at.exception
assert "Your viewer profile" in html() and "Homemaker in Kanpur" in html(), "profile card"
at.button(key="next").click().run()
assert not at.exception, at.exception
assert html().count('class="kd-show"') == 2, "2 show cards"
assert html().count("Episodes ready") == 1, "one show has episodes"
at.button(key=next(b.key for b in at.button if b.label == "Start watching")).click().run()
assert not at.exception, at.exception
assert "Drop 1 of 3" in html(), "drop 1 open"
assert "Karan" in html(), "teaser from the demo cache"
at.button(key="watched").click().run()
assert not at.exception, at.exception
assert "unlocks in" in html() and "24:00:00" in html() and "(your slot)" in html(), "lock card"
at.button(key="ff").click().run()
assert not at.exception, at.exception
assert at.session_state.state["streak"] == 1, "streak"
assert "Drop 2 of 3" in html(), "drop 2 open"
print("app self-check: ok")
