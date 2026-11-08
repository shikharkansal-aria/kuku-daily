# Kuku Daily

- Prototype (guided demo): https://shikharkansal-aria.github.io/kuku-daily/
- Live lab (runs the real model on your own words or a new show): https://kuku-daily.streamlit.app/
- 30 s trailer: https://shikharkansal-aria.github.io/kuku-daily/trailer.mp4 (also on the prototype page)

Prototype for Kuku's AI Generalist assignment (Problem 3). A new viewer answers a few questions, gets 2 shows that fit them, and watches the story in 3.5 to 6 minute drops that end on a cliffhanger. A timer sits before the next drop, for free users and subscribers alike, so the habit is coming back, not bingeing to a paywall.

## How it works

| Step | File | AI does | Code does |
|---|---|---|---|
| Onboarding | `tools/persona.py` | Reads 5 free-text answers (Hinglish or English) into a profile | Quick-pick mode needs no AI; validates every field, drops unknown tags, dislikes win over likes |
| Matching | `tools/match.py` | Picks 2 of a 6-show shortlist and explains why, in the viewer's language | Shortlists by tags, removes non-family-safe shows for family viewers, rejects any show id the model invents |
| Drops | `tools/drops.py` | Scores each episode's last 20 s as a cliffhanger (1 to 5); writes a come-back teaser | Parses the screenplay, adds rule scores, packs episodes into 3.5 to 6 min drops cut at the strongest ending, checks each teaser quotes a real line from that ending |
| Gates | `tools/gates.py` | Nothing | Free: 1 drop per unlock, waits 24 h, 10 h, 5 h as the streak grows. Subscriber: 2 drops, waits 10 h, 5 h, 2 h. Coming back late drops one level, not to zero |

## Run it

```bash
./setup.sh                          # makes .venv and installs requirements.txt
cp .env.example .env                # add one key; Groq and Gemini free tiers both work
.venv/bin/streamlit run app.py      # the app, with a fictional demo show
.venv/bin/python -m tools.run_batch --show data/sample_show --title "The Lost Haveli (demo)" --out outputs/runs/demo
```

A show is a folder of `episode-001-*.txt` files in the screenplay format of `data/sample_show/`. To run on a new show, point `--show` at its folder, or upload a zip in the app's "For reviewers" box. Each run writes per-persona JSON, the drop schedule in English and Hinglish, and `validation_report.md` with every failure listed.

## Swap the model

All calls go through `tools/llm.py`. Set `LLM_PROVIDER=openai` with `OPENAI_BASE_URL`, `OPENAI_API_KEY` and `LLM_MODEL` for any OpenAI-compatible endpoint, or `LLM_PROVIDER=anthropic` with `ANTHROPIC_API_KEY`. Per run: `--model`, `--base-url`, `--key-env`. In the app: the "For reviewers" box at the bottom, where a typed key stays in that browser session only. Responses are cached in `.cache/llm/`, so re-runs are free.

Tested on Groq `openai/gpt-oss-120b` and Gemini `gemini-3.5-flash`. Compare two runs with `python -m tools.compare_runs RUN_A RUN_B`.

## Tests

```bash
.venv/bin/python -m tools.test_core   # offline, mock model: gates, persona, matching, drops, full batch
.venv/bin/python -m tools.test_app    # Streamlit click-through on the mock model
python3 -I tools/test_parse.py        # screenplay parser
.venv/bin/python -m tools.test_web_gates  # web/gates.js gives the same answers as tools/gates.py (needs node)
```

## Layout

| Path | What |
|---|---|
| `web/` | Static guided prototype on GitHub Pages; `data.js` is built from real pipeline outputs by `python -m tools.export_web` |
| `trailer/` | Remotion source of the 30 s trailer (`web/trailer.mp4`); `cd trailer && npm install && npm run render` re-exports `web/data.js` and renders |
| `app.py` | Streamlit live lab |
| `tools/` | Parser, LLM adapter, persona, matching, drops, gates, batch runner, review mining, tests |
| `data/catalog.json` | 10 public microdrama shows (titles, tags, own-words loglines, source links) |
| `data/sample_show/` | Fictional 6-episode demo show written for this repo |
| `data/test_personas.json` | 10 synthetic viewers, including 2 edge cases |
| `docs/` | Research notes |

Kuku's input pack and the raw outputs on it are confidential and are not in this repository.
