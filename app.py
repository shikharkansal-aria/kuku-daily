"""Kuku Daily prototype. Run: streamlit run app.py"""
import re
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

from tools import drops, gates, llm, match, persona as P

st.set_page_config(page_title="Kuku Daily", layout="centered")
st.markdown("<style>.block-container{padding:1rem 1rem 3rem}</style>", unsafe_allow_html=True)
DEMO = Path(__file__).parent / "data" / "sample_show"
S = st.session_state
S.setdefault("persona", None)


def secret(k):
    try:
        return st.secrets.get(k, "")
    except Exception:
        return ""


# ---- sidebar: model settings (applied per call, never stored in env/files) ----
with st.sidebar:
    st.header("Model settings")
    prov = st.selectbox("Provider", ["openai", "anthropic"])
    model = st.text_input("Model", secret("LLM_MODEL"))
    base = st.text_input("Base URL", secret("OPENAI_BASE_URL"))
    key = st.text_input("API key", type="password")
    tier = st.radio("Tier", ["free", "subscriber"], horizontal=True)
    src = st.radio("Show source", ["Demo show", "Upload zip"])
    upload = st.file_uploader("Episodes zip", type="zip") if src == "Upload zip" else None


def cfg():
    k = {"OPENAI_API_KEY": key or secret("OPENAI_API_KEY")} if prov == "openai" else \
        {"ANTHROPIC_API_KEY": key or secret("ANTHROPIC_API_KEY")}
    return llm.use(LLM_PROVIDER=prov if (model or base or key) else "", LLM_MODEL=model, OPENAI_BASE_URL=base, **k)


def unzip(f):
    d = Path(tempfile.mkdtemp(prefix="kd_"))
    with zipfile.ZipFile(f) as z:
        if len(z.infolist()) > 300:
            raise ValueError("Zip has more than 300 files.")
        n = total = 0
        for i in z.infolist():
            base_name = Path(i.filename).name
            if i.is_dir() or not re.fullmatch(r"episode-[\w .-]+\.txt", base_name):
                continue
            with z.open(i) as fh:
                data = fh.read(5_000_001 - total)  # count real bytes, not the sizes the zip claims
            total += len(data)
            if total > 5_000_000:
                raise ValueError("Zip is larger than 5 MB.")
            (d / base_name).write_bytes(data)
            n += 1
    if not n:
        raise ValueError("No episode-*.txt files found in the zip.")
    return str(d)


show_dir, title = str(DEMO), "The Lost Haveli"
if upload:
    try:
        if S.get("up_id") != upload.file_id:
            S.up_dir, S.up_id = unzip(upload), upload.file_id
        show_dir, title = S.up_dir, Path(upload.name).stem
    except Exception as e:
        st.sidebar.error(str(e))

st.title("Kuku Daily")
st.caption("Two shows that fit you. One short drop at a time.")

# ---- step 1: onboarding ----
st.subheader("1. About you")
lang = st.radio("Language", ["Hinglish", "English"], horizontal=True).lower()
if lang not in ("hinglish", "english"):
    lang = "english"
t1, t2 = st.tabs(["Quick pick", "Tell us about you"])
with t1, st.form("quick"):
    who = st.selectbox("Who are you?", ["student", "homemaker", "working professional", "retired"])
    likes = st.multiselect("Likes", P.TAGS)
    dislikes = st.multiselect("Dislikes", P.TAGS)
    slot = st.time_input("Usual free time", value=datetime.strptime("20:00", "%H:%M").time())
    wm = st.radio("Watching", ["alone", "family"], horizontal=True)
    if st.form_submit_button("Continue"):
        S.persona = P.quick(who, likes, dislikes, [slot.strftime("%H:%M")], lang, wm)
        S.pop("state", None)
with t2, st.form("chat"):
    ans = [st.text_input(q, key=f"q{i}") for i, q in enumerate(P.QUESTIONS[lang])]
    if st.form_submit_button("Continue"):
        try:
            with cfg():
                S.persona = P.extract(ans, lang)
            S.pop("state", None)
        except Exception as e:
            st.error(f"Could not read your answers (check Model settings): {str(e)[:150]}")
pers = S.persona
if not pers:
    st.info("Pick a few things above to get your shows.")
    st.stop()
st.success(pers.summary or f"{pers.who}, likes {', '.join(pers.likes) or 'anything'}")


# ---- step 2: shows ----
@st.cache_data(show_spinner="Reading the show...")
def entry(sd, ttl, _cfg_id):
    try:
        with cfg():
            return match.show_entry(sd, ttl)
    except Exception:
        return {"id": "demo", "title": ttl, "platform": "Kuku Daily", "language": ["english"], "tags": [],
                "logline": "", "family_safe": True, "source_url": "local", "has_scripts": True}


st.subheader("2. Your shows")
res = match.pick(pers, match.load_catalog(extra=[entry(show_dir, title, (prov, model, base))]))
for s in res["picks"]:
    with st.container(border=True):
        st.markdown(f"**{s['title']}**  \n{s['platform']}")
        st.caption(" | ".join(s["tags"]))
        st.write(s.get("reason") or s.get("logline", ""))
        if s.get("has_scripts"):
            st.markdown("**Episodes ready**")

# ---- step 3: drops ----
st.subheader("3. Today's drop")


@st.cache_data(show_spinner="Choosing the cliffhangers...")
def schedule(sd, lg, _cfg_id):
    try:
        with cfg():
            return drops.build_schedule(sd, lg), None
    except Exception as e:
        return drops.build_schedule(sd, lg, use_llm=False), str(e)[:150]


sched, err = schedule(show_dir, pers.language, (prov, model, base))
if err:
    st.warning(f"Model unavailable ({err}). Showing rule-based drops without teasers.")
D = sched["drops"]
st.session_state.setdefault("state", {"clock": datetime(2026, 11, 9, 20, 0), "streak": 0, "cur": 0, "unlock": None})
stt = S.state
n = gates.TIERS[tier]["drops_per_unlock"]
fmt = lambda t: t.strftime("%a %d %b, %I:%M %p")  # noqa: E731
now = D[stt["cur"]:stt["cur"] + n]
if not now:
    st.success("You have watched the whole show.")
for d in now:
    with st.container(border=True):
        st.markdown(f"**Drop {d['n']}**: episodes {', '.join(map(str, d['episodes']))}, about {d['seconds'] / 60:.1f} min")
        st.write(d["teaser"] or "Come back for what happens next.")
        if d["open_question"]:
            st.caption(d["open_question"])
if now and stt["unlock"] is None and st.button("I watched it"):
    stt["unlock"] = gates.next_unlock(stt["clock"], tier, stt["streak"])
    st.rerun()
if stt["unlock"]:
    rem = gates.reminder(stt["unlock"], pers.slots)
    with st.container(border=True):
        st.markdown(f"**Locked until {fmt(stt['unlock'])}**")
        st.write(f"We will remind you at {fmt(rem)}.")
if now:
    lvl = gates.level(stt["streak"])
    st.progress(min(stt["streak"] / gates.LEVELS[-1], 1.0), text=f"Streak: {stt['streak']} day(s), wait level {lvl + 1} of 3")


def advance(extra):
    u = stt["unlock"] or gates.next_unlock(stt["clock"], tier, stt["streak"])
    back = gates.reminder(u, pers.slots) + extra
    stt.update(streak=gates.update_streak(stt["streak"], u, back), clock=back, unlock=None, cur=stt["cur"] + n)


c1, c2 = st.columns(2)
if now and c1.button("Simulate: come back at reminder"):
    advance(timedelta())
    st.rerun()
if now and c2.button("Simulate: skip 2 days"):
    advance(timedelta(days=2))
    st.rerun()
st.caption(f"Simulated clock: {fmt(stt['clock'])}")
for d in D[stt["cur"] + n:]:
    st.markdown(f"<div style='opacity:.45'>Drop {d['n']} (locked): episodes {', '.join(map(str, d['episodes']))}</div>",
                unsafe_allow_html=True)
st.divider()
st.caption("Prototype for a Kuku assignment. Demo show is fictional.")
