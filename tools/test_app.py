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
at.multiselect[0].set_value(["revenge"])
next(b for b in at.button if b.label == "Continue").click()
at.run()
assert not at.exception, at.exception
assert any("Episodes ready" in m.value for m in at.markdown), "show cards"
assert sum("Episodes ready" in m.value for m in at.markdown) == 1
assert any(m.value.startswith("**Drop 1**") for m in at.markdown), "drop"
next(b for b in at.button if b.label == "I watched it").click()
at.run()
assert any("Locked until" in m.value for m in at.markdown), "lock card"
next(b for b in at.button if b.label == "Simulate: come back at reminder").click()
at.run()
assert not at.exception, at.exception
assert at.session_state.state["streak"] == 1, "streak"
print("app self-check: ok")
