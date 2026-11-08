"""Kuku Daily prototype. Run: streamlit run app.py"""
import html
import json
import re
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

from tools import drops, gates, llm, match, persona as P

st.set_page_config(page_title="Kuku Daily", layout="centered", initial_sidebar_state="collapsed")
ROOT = Path(__file__).parent
DEMO = ROOT / "data" / "sample_show"
CACHE = ROOT / "data" / "demo_cache"  # drops and tags for the fictional demo show, made ahead so the demo needs no key
REPO = "https://github.com/shikharkansal-aria/kuku-daily"
PROTOTYPE_URL = "https://shikharkansal-aria.github.io/kuku-daily/"  # the static guided demo in web/, on GitHub Pages
S = st.session_state
for k, v in {"step": 1, "persona": None, "lang": "Hinglish", "tier": "free"}.items():
    S.setdefault(k, v)
e = html.escape  # every model or user string goes through this before it enters HTML

VIEWERS = {  # one-click demo viewers: persona.quick, no model call
    "homemaker": ("Homemaker, Kanpur", {"who": "homemaker in Kanpur", "likes": ["family drama", "betrayal", "revenge"],
                                         "slots": ["14:00"], "language": "hinglish", "watch_with": "family"}),
    "student": ("College student, Indore", {"who": "college student in Indore", "likes": ["thriller", "revenge", "mystery", "betrayal"],
                                            "slots": ["23:00"], "language": "hinglish", "watch_with": "alone"}),
    "banker": ("Banker, Pune", {"who": "banker in Pune", "likes": ["romance", "hidden identity", "marriage"], "dislikes": ["mafia/crime"],
                                "slots": ["08:30", "22:00"], "language": "english", "watch_with": "alone"}),
}
STEPS = ["Who are you?", "Your 2 shows", "Today's drop", "Come back later"]
FLOW = ["Tell us who you are", "Get 2 shows that fit", "Watch a 5 min drop", "Come back for the next"]
HOW = {
    1: ("Only in \"In your own words\": a model turns 5 short answers into a profile (who, free time, likes, dislikes, who you watch with).",
        "Demo viewers and Build your own use no AI. Code checks every field, drops unknown tags, and dislikes always win over likes."),
    2: ("Picks 2 shows from a 6-show shortlist and writes the reason in your language.",
        "Shortlists 10 public microdramas by your tags, removes shows that are not family-safe when you watch with family, "
        "and rejects any show the model makes up. If the model fails, the tag score picks."),
    3: ("Rated how hard each episode's last 20 seconds pulls you into the next one (1 to 5) and wrote the come-back teaser.",
        "Parses the scripts, packs episodes into 3.5 to 6 minute drops cut at the strongest ending, and checks the teaser quotes a "
        "real line from that ending. The demo show's drops were made ahead with Groq gpt-oss-120b, so this page needs no key."),
    4: ("Nothing. Waits are plain rules that Kuku can tune.",
        "Free: 1 drop per unlock, wait 24 h, then 10 h at a 3-day streak, 5 h at 7 days. Subscriber: 2 drops, wait 10, 5, then 2 h. "
        "Coming back within a day of the unlock grows the streak; later drops one level, not to zero. The reminder uses your time slot."),
}

st.markdown("""<style>
:root{--acc:#F2B544;--card:#221F2B;--line:#3A3446;--mut:#ABA4B6;--txt:#EEE9E2}
.block-container{padding:1.6rem 1rem 4rem;max-width:780px}
[data-testid="stHeaderActionElements"]{display:none}
button[data-testid^="stBaseButton-primary"]:not(:disabled),button[data-testid^="stBaseButton-primary"]:not(:disabled) p{color:#1B1408 !important;font-weight:700}
.kd-title{font-size:2.2rem;font-weight:800;margin:0;line-height:1.1;letter-spacing:-.5px}
.kd-title span{color:var(--acc)}
.kd-pf{margin:.5rem 0 0;line-height:1.5}
.kd-pf b{color:var(--acc)}
.kd-small,.kd-mut{color:var(--mut);font-size:.85rem;line-height:1.45}
.kd-small{margin:.45rem 0 0}
.kd-flow{display:grid;grid-template-columns:repeat(4,1fr);gap:.4rem;margin:1.1rem 0 .4rem}
.kd-flow div{border:1px solid var(--line);border-radius:10px;padding:.5rem;font-size:.8rem;color:var(--mut);line-height:1.25;background:var(--card)}
.kd-flow i{font-style:normal;display:flex;width:1.4rem;height:1.4rem;border-radius:50%;align-items:center;justify-content:center;
 background:#353041;color:var(--txt);font-size:.75rem;font-weight:700;margin-bottom:.3rem}
.kd-flow .on{border-color:var(--acc);color:var(--txt)}
.kd-flow .on i{background:var(--acc);color:#1B1408}
.kd-step{color:var(--acc);font-size:.8rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-top:.8rem}
.kd-h{font-size:1.6rem;font-weight:700;margin:.1rem 0 .3rem}
.kd-label{color:var(--mut);font-size:.75rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin:.2rem 0 .3rem}
.kd-name{font-size:1.2rem;font-weight:700}
.kd-chip{display:inline-block;padding:.12rem .6rem;margin:.15rem .3rem .15rem 0;border-radius:999px;background:#302B3B;
 border:1px solid var(--line);font-size:.8rem}
.kd-chip.no{text-decoration:line-through;color:var(--mut)}
.kd-badge{display:inline-block;padding:.15rem .55rem;border-radius:6px;font-size:.75rem;font-weight:700;background:var(--acc);color:#1B1408}
.kd-badge.off{background:transparent;border:1px solid var(--line);color:var(--mut);font-weight:500}
.kd-show h3{font-size:1.25rem;margin:.35rem 0 .4rem;padding:0}
.kd-why{margin:.6rem 0 0;line-height:1.45}
div[class*="st-key-card_"]{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:1rem 1rem 1.4rem}
div[class*="st-key-card_ready"]{border-color:var(--acc)}
div[class*="st-key-card_viewer"]{padding:.8rem .8rem 1.2rem}
@media (min-width:640px){div[class*="st-key-card_viewer"]{min-height:10.5rem}}
.st-key-card_demo{background:transparent !important;border-style:dashed !important}
.st-key-card_phone{max-width:380px;margin:0 auto;border-radius:30px !important;border:2px solid #4A4356 !important;background:#1A1720 !important}
.kd-ph-top{display:flex;justify-content:space-between;font-size:.8rem;color:var(--mut);margin-bottom:.5rem}
.kd-ph-top b{color:var(--acc)}
.kd-screen{height:210px;border-radius:16px;position:relative;padding:.9rem;display:flex;flex-direction:column;justify-content:flex-end;
 background:linear-gradient(160deg,#47305A 0%,#211C2B 55%,#5A3520 100%)}
.kd-play{position:absolute;top:38%;left:50%;transform:translate(-50%,-50%);width:58px;height:58px;border-radius:50%;background:rgba(255,255,255,.16)}
.kd-play:after{content:"";position:absolute;left:23px;top:17px;border-left:18px solid #fff;border-top:12px solid transparent;border-bottom:12px solid transparent}
.kd-screen b{font-size:1.1rem}
.kd-quote{border-left:3px solid var(--acc);padding:.55rem .8rem;margin:.3rem 0 .4rem;background:rgba(242,181,68,.08);
 border-radius:0 8px 8px 0;font-style:italic;line-height:1.5}
.kd-lock{text-align:center}
.kd-pad{width:24px;height:17px;background:var(--acc);border-radius:4px;margin:16px auto 6px;position:relative}
.kd-pad:before{content:"";position:absolute;box-sizing:border-box;width:16px;height:13px;border:3px solid var(--acc);border-bottom:none;border-radius:8px 8px 0 0;left:4px;top:-12px}
.kd-big{font-size:3.2rem;font-weight:800;color:var(--acc);font-variant-numeric:tabular-nums;line-height:1.1;margin:.15rem 0}
.kd-seg{display:flex;gap:4px;margin:.45rem 0}
.kd-seg span{flex:1;height:10px;border-radius:3px;background:#363141}
.kd-seg span.f{background:var(--acc)}
.kd-ladder{display:flex;gap:.4rem;margin:.4rem 0}
.kd-ladder div{flex:1;text-align:center;border:1px solid var(--line);border-radius:12px;padding:.5rem .25rem;color:var(--mut);font-size:.78rem}
.kd-ladder b{display:block;font-size:1.35rem;color:var(--txt)}
.kd-ladder .on{border-color:var(--acc);background:rgba(242,181,68,.12);color:var(--txt)}
.kd-ladder .on b{color:var(--acc)}
.kd-locked span{white-space:nowrap}
.kd-locked{display:flex;flex-wrap:wrap;justify-content:space-between;column-gap:1rem;padding:.55rem .8rem;border:1px dashed var(--line);border-radius:10px;
 margin:.35rem 0;color:var(--mut);font-size:.88rem}
</style>""", unsafe_allow_html=True)


def secret(k):
    try:
        return st.secrets.get(k, "")
    except Exception:
        return ""


def cfg_id():
    """Model settings from the reviewer panel (no key: this is used as a cache key)."""
    return S.get("m_prov", "openai"), S.get("m_model", secret("LLM_MODEL")), S.get("m_base", secret("OPENAI_BASE_URL"))


def cfg():
    prov, model, base = cfg_id()
    key = S.get("m_key", "")
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


def active_show():
    up = S.get("zip")
    S.up_err = ""
    if up:
        try:
            if S.get("up_id") != up.file_id:
                S.up_dir, S.up_id = unzip(up), up.file_id
            return S.up_dir, Path(up.name).stem, False
        except Exception as ex:
            S.up_err = str(ex)
    return str(DEMO), "The Lost Haveli (demo)", True


def once(name, key, fn):
    """Compute once per session for this key, so reruns never repeat a model call."""
    if S.get(name + "_key") != key:
        S[name], S[name + "_key"] = fn(), key
    return S[name]


def hm(t):
    return t.strftime("%I:%M %p").lstrip("0")


def day(t):
    return f"{t:%a} {t.day} {t:%b}"


def slot_text(slots):
    return " and ".join(hm(datetime.strptime(s, "%H:%M")) for s in slots)


def chips(tags, cls=""):
    return "".join(f'<span class="kd-chip {cls}">{e(t)}</span>' for t in tags)


def html_block(s):
    st.markdown(s, unsafe_allow_html=True)


def go(step):
    S.step = step


def new_state():
    h, m = map(int, S.persona.slots[0].split(":"))  # the viewer starts at their own slot, like a TV serial
    return {"clock": datetime(2026, 11, 9, h, m), "streak": 0, "cur": 0, "watched": 0}


# ---- data for the active show (demo cache, or an uploaded zip through the model) ----
SHOW_DIR, TITLE, IS_DEMO = active_show()
if S.get("show_dir") != SHOW_DIR:  # a new upload restarts the flow from the show picks
    S.show_dir = SHOW_DIR
    S.step = min(S.step, 2)


def show_entry():
    if IS_DEMO and (CACHE / "show_entry.json").exists():
        return {**json.loads((CACHE / "show_entry.json").read_text()), "platform": "Demo show (fictional)"}

    def build():
        try:
            with st.spinner("Reading your show to tag its genre and check it is family-safe. About 10 seconds."), cfg():
                return {**match.show_entry(SHOW_DIR, TITLE), "platform": "Your upload"}
        except Exception:
            return {"id": "upload", "title": TITLE, "platform": "Your upload", "language": ["english"], "tags": [],
                    "logline": "", "family_safe": True, "source_url": "local", "has_scripts": True}
    return once("entry", (SHOW_DIR, cfg_id()), build)


def schedule():
    lang = S.persona.language
    f = CACHE / f"drops_{lang}.json"
    if IS_DEMO and f.exists():
        return json.loads(f.read_text()), None

    def build():
        try:
            with st.spinner("Reading each episode's ending and finding the cliffhangers. First run takes about a minute."), cfg():
                return drops.build_schedule(SHOW_DIR, lang), None
        except Exception as ex:
            return drops.build_schedule(SHOW_DIR, lang, use_llm=False), str(ex)[:150]
    return once("sched", (SHOW_DIR, lang, cfg_id()), build)


if S.step >= 2 and not S.persona:
    S.step = 1
if S.step >= 3 and "state" not in S:
    S.step = 2

# ---- header: what this is, always visible ----
html_block(
    '<div class="kd-title">Kuku <span>Daily</span></div>'
    '<p class="kd-pf"><b>Problem:</b> Kuku TV shows a new viewer about 30 shows and asks them to pay (Rs 199 to 1,499, auto-renew) '
    'before any story hooks them.<br><b>Fix:</b> answer a few questions, get 2 shows that fit you, and watch the story in 5 minute '
    'drops that end on a cliffhanger. The next drop unlocks at your time slot, like a TV serial.</p>'
    '<p class="kd-small">Prototype for Kuku\'s AI Generalist assignment. The demo show is fictional.</p>'
    f'<p class="kd-pf"><b>This is the live lab:</b> it runs the real model on your own words or on a new show. '
    f'For the guided product demo, open <a href="{PROTOTYPE_URL}" target="_blank">the Kuku Daily prototype</a>.</p>'
    '<div class="kd-flow">' + "".join(f'<div class="{"on" if i + 1 == S.step else ""}"><i>{i + 1}</i>{t}</div>'
                                      for i, t in enumerate(FLOW)) + '</div>'
    f'<div class="kd-step">Step {S.step} of 4</div><div class="kd-h">{STEPS[S.step - 1]}</div>')


# ---- step 1: who are you ----
def set_lang():
    S.lang = S.lang_w
    if S.persona:
        S.persona = S.persona.model_copy(update={"language": S.lang.lower()})


def set_viewer(k):
    spec = VIEWERS[k][1]
    S.persona, S.viewer, S.lang = P.quick(**spec), k, spec["language"].title()


def profile_card(p):
    who = {"family": "with family", "partner": "with a partner", "alone": "alone"}.get(p.watch_with)
    meta = " · ".join(x for x in [p.language.title(), who, f"usually free at {slot_text(p.slots)}"] if x)
    extra = f'<div class="kd-mut" style="margin-top:.4rem">{e(p.summary)}</div>' if S.get("viewer") == "words" and p.summary else ""
    with st.container(key="card_profile"):
        html_block(f'<div class="kd-label">Your viewer profile</div><div class="kd-name">{e(p.who[:1].upper() + p.who[1:])}</div>'
                   f'<div class="kd-mut">{e(meta)}</div><div style="margin-top:.5rem">Likes: {chips(p.likes) or "anything"}</div>'
                   f'<div>Avoids: {chips(p.dislikes, "no") or "nothing set"}</div>{extra}')


def step1():
    st.markdown("Pick a demo viewer to see the app in one click, or describe yourself.")
    S.lang_w = S.lang
    st.radio("Language for your shows and teasers", ["Hinglish", "English"], key="lang_w", horizontal=True, on_change=set_lang)
    lang = S.lang.lower()
    t1, t2, t3 = st.tabs(["Demo viewers", "Build your own", "In your own words"])
    with t1:
        for col, (k, (name, spec)) in zip(st.columns(3), VIEWERS.items()):
            with col, st.container(key=f"card_viewer_{k}"):
                st.button(name, key=f"v_{k}", type="primary" if S.get("viewer") == k else "secondary", width="stretch",
                          on_click=set_viewer, args=(k,))
                html_block(f'<div class="kd-mut">{spec["language"].title()} · {"with family" if spec["watch_with"] == "family" else "alone"}'
                           f' · {slot_text(spec["slots"])}<br>Likes {e(", ".join(spec["likes"]))}'
                           + (f'<br>Avoids {e(", ".join(spec.get("dislikes", [])))}' if spec.get("dislikes") else "") + '</div>')
    with t2, st.form("own"):
        who = st.selectbox("I am a", ["student", "homemaker", "working professional", "retired"])
        likes = st.multiselect("I like", P.TAGS, placeholder="Pick a few")
        dislikes = st.multiselect("Never show me", P.TAGS, placeholder="Optional")
        slot = st.time_input("I am usually free at", value=datetime.strptime("20:00", "%H:%M").time())
        wm = st.radio("I watch", ["alone", "family"], horizontal=True, format_func=lambda x: "with family" if x == "family" else x)
        if st.form_submit_button("Use this profile", type="primary"):
            S.persona, S.viewer = P.quick(who, likes or [], dislikes or [], [slot.strftime("%H:%M")], lang, wm), "own"
            st.rerun()
    with t3, st.form("words"):
        st.caption("A model reads your answers. Needs a model key (set below for reviewers, or on the hosted demo).")
        ans = [st.text_input(q, key=f"q{i}_{lang}") for i, q in enumerate(P.QUESTIONS[lang])]
        if st.form_submit_button("Read my answers", type="primary"):
            try:
                with st.spinner("Reading your answers..."), cfg():
                    S.persona, S.viewer = P.extract(ans, lang), "words"
                st.rerun()
            except Exception as ex:
                st.error(f"Could not read your answers ({str(ex)[:120]}). Pick a demo viewer or use Build your own: neither needs a model.")
    if S.persona:
        profile_card(S.persona)


# ---- step 2: your 2 shows ----
def pick(pers, entry):
    with st.spinner("Picking 2 shows for you from 10..."), cfg():
        return match.pick(pers, match.load_catalog(extra=[entry]))


def show_html(s, hinglish):
    why = s.get("reason") or s.get("logline", "")
    if hinglish and why.startswith("Matches what you like: "):  # the code fallback speaks English; keep the viewer's language
        why = "Aapki pasand se match: " + why.split(": ", 1)[1]
    badge = '<span class="kd-badge">Episodes ready</span>' if s.get("has_scripts") else \
        '<span class="kd-badge off">No episodes in this demo</span>'
    return (f'<div class="kd-show"><div class="kd-label">{e(s["platform"])}</div><h3>{e(s["title"])}</h3>{badge}'
            f'<div style="margin-top:.5rem">{chips(s["tags"])}</div><p class="kd-why">{e(why)}</p></div>')


def start():
    S.state, S.step = new_state(), 3
    S.pop("flash", None)


def step2():
    pers, entry = S.persona, show_entry()
    res = once("picks", (pers.model_dump_json(), entry["id"], cfg_id()), lambda: pick(pers, entry))
    st.markdown(f"Picked for **{e(pers.who)}** from 10 public microdramas. Only one show has episodes in this prototype.")
    for i, (col, s) in enumerate(zip(st.columns(2), res["picks"])):
        with col, st.container(key=f"card_{'ready' if s.get('has_scripts') else 'show'}{i}"):
            html_block(show_html(s, pers.language == "hinglish"))
            if s.get("has_scripts"):
                st.button("Start watching", type="primary", key=f"start{i}", width="stretch", on_click=start)
    if not any(s.get("has_scripts") for s in res["picks"]):
        st.info(f"Neither pick has episodes here: this prototype only has scripts for {TITLE}. Watch it to see how drops work.")
        st.button(f"Watch {TITLE} instead", type="primary", key="start_demo", on_click=start)


# ---- step 3: today's drop ----
def ep_text(eps):
    return f"Episode {eps[0]}" if len(eps) == 1 else f"Episodes {', '.join(map(str, eps[:-1]))} and {eps[-1]}"


def watched(k):
    S.state["watched"], S.step = k, 4


def restart():
    for k in ("persona", "viewer", "state", "picks_key"):
        S.pop(k, None)
    S.step = 1


def finished():
    with st.container(key="card_done"):
        html_block(f'<div class="kd-name">That was the last drop of {e(TITLE)}.</div>'
                   '<div class="kd-mut">In the full app, your second show would start here on the same daily slot.</div>')
        st.button("Start over with another viewer", key="restart", on_click=restart)


def step3():
    sched, err = schedule()
    D, stt = sched["drops"], S.state
    if S.get("flash"):
        kind, msg = S.pop("flash")
        (st.warning if kind == "late" else st.success)(msg)
    if err:
        st.warning(f"The model did not answer ({err}). These drops are cut by rules only, without teasers.")
    now = D[stt["cur"]:stt["cur"] + gates.TIERS[S.tier]["drops_per_unlock"]]
    if not now:
        finished()
        return
    nums = " and ".join(str(d["n"]) for d in now)
    last = now[-1]
    teaser = e(last["teaser"] or "Come back for what happens next.").replace("\n", "<br>")
    with st.container(key="card_phone"):
        html_block(f'<div class="kd-ph-top"><span>{e(TITLE)}</span><b>Drop{"s" if len(now) > 1 else ""} {nums} of {len(D)}</b></div>'
                   f'<div class="kd-screen"><div class="kd-play"></div><b>{ep_text([x for d in now for x in d["episodes"]])}</b>'
                   f'<span class="kd-mut">About {round(sum(d["seconds"] for d in now) / 60)} min</span></div>'
                   f'<div class="kd-label" style="margin-top:.9rem">It ends on this teaser</div><div class="kd-quote">{teaser}</div>'
                   + (f'<div class="kd-mut" style="margin-bottom:.4rem">Left open: {e(last["open_question"])}</div>' if last["open_question"] else ""))
        st.button("Mark as watched", type="primary", key="watched", width="stretch", on_click=watched, args=(len(now),))
    st.caption(f"{S.tier.title()} plan: {len(now)} drop{'s' if len(now) > 1 else ''} per unlock. You can switch plans on the next step.")


# ---- step 4: come back later ----
def set_tier():
    S.tier = S.tier_w


def advance(days):
    stt = S.state
    u = gates.next_unlock(stt["clock"], S.tier, stt["streak"])
    back = gates.reminder(u, S.persona.slots) + timedelta(days=days)
    old, new = stt["streak"], gates.update_streak(stt["streak"], u, back)
    stt.update(streak=new, clock=back, cur=stt["cur"] + stt["watched"], watched=0)
    if not days:
        S.flash = ("ok", f"You came back at your reminder ({day(back)}, {hm(back)}). Streak {old} to {new}. The next drop is open.")
    elif new < old and gates.level(old):
        S.flash = ("late", f"You came back {days} days late, so your streak fell one level: {old} to {new}, not to zero.")
    else:
        S.flash = ("late", f"You came back {days} days late. Streak {old} to {new}: you were already on the lowest wait level. "
                           "Next time, press \"Give me a 7-day streak\" on step 4 first to see it fall one level, from 7 to 3.")
    S.step = 3


def streak7():
    S.state["streak"] = 7


def upcoming(D, stt):
    rows, t, streak, i = [], stt["clock"], stt["streak"], stt["cur"] + stt["watched"]
    n = gates.TIERS[S.tier]["drops_per_unlock"]
    while i < len(D):  # assumes the viewer comes back at every reminder
        u = gates.next_unlock(t, S.tier, streak)
        rows += [(d, u) for d in D[i:i + n]]
        t, streak, i = gates.reminder(u, S.persona.slots), streak + 1, i + n
    return rows


def ladder_html(streak):
    lvl, waits = gates.level(streak), gates.TIERS[S.tier]["waits_h"]
    nxt = (f"{gates.LEVELS[lvl + 1] - streak} more on-time day{'s' if gates.LEVELS[lvl + 1] - streak > 1 else ''} "
           f"and your wait drops to {waits[lvl + 1]} h.") if lvl < 2 else "You have the shortest wait."
    names = ["streak 0 to 2", "streak 3 to 6", "streak 7+"]
    return (f'<div class="kd-label">Your streak: {streak} day{"" if streak == 1 else "s"}</div><div class="kd-seg">'
            + "".join(f'<span class="{"f" if i < streak else ""}"></span>' for i in range(7)) + f'</div><div class="kd-mut">{nxt}</div>'
            '<div class="kd-label" style="margin-top:.9rem">Wait before your next drop</div><div class="kd-ladder">'
            + "".join(f'<div class="{"on" if i == lvl else ""}"><b>{w} h</b>{names[i]}</div>' for i, w in enumerate(waits)) +
            '</div><div class="kd-mut">Come back more than a day late and you drop one level, not to zero.</div>')


def step4():
    S.tier_w = S.tier
    st.radio("Your plan", ["free", "subscriber"], key="tier_w", horizontal=True, on_change=set_tier, format_func=str.title,
             captions=["1 drop per unlock", "2 drops per unlock, shorter waits"])
    sched, _ = schedule()
    D, stt = sched["drops"], S.state
    nxt = stt["cur"] + stt["watched"]
    if nxt >= len(D):
        finished()
        return
    u = gates.next_unlock(stt["clock"], S.tier, stt["streak"])
    r = gates.reminder(u, S.persona.slots)
    left = int((u - stt["clock"]).total_seconds() // 60)
    with st.container(key="card_lock"):
        html_block(f'<div class="kd-lock"><div class="kd-pad"></div><div class="kd-mut">Drop {nxt + 1} of {len(D)} unlocks in</div>'
                   f'<div class="kd-big">{left // 60:02d}:{left % 60:02d}:00</div><div>Opens {day(u)}, {hm(u)}</div>'
                   f'<div style="margin-top:.6rem"><b>We will remind you at {hm(r)} on {day(r)} (your slot).</b></div></div>')
    with st.container(key="card_streak"):
        html_block(ladder_html(stt["streak"]))
    with st.container(key="card_demo"):
        html_block('<div class="kd-label">Demo controls</div><div class="kd-mut">Nobody waits a day in a demo, so these move a '
                   f'pretend clock. It is now {day(stt["clock"])}, {hm(stt["clock"])}.</div>')
        with st.container(horizontal=True):
            st.button("Fast-forward to my reminder", type="primary", key="ff", on_click=advance, args=(0,))
            st.button("Skip 2 days", key="skip", on_click=advance, args=(2,))
            st.button("Give me a 7-day streak", key="s7", on_click=streak7)
        st.caption("Fast-forward: you open the app when reminded, so the streak grows and the next drop opens. "
                   "Skip 2 days: you come back late, so the streak falls one level.")
    rows = upcoming(D, stt)
    html_block('<div class="kd-label" style="margin-top:.6rem">Coming up</div>' + "".join(
        f'<div class="kd-locked"><span>Drop {d["n"]} · {ep_text(d["episodes"])}</span><span>Locked until {day(t)}, {hm(t)}</span></div>'
        for d, t in rows))


# ---- the stepper ----
[step1, step2, step3, step4][S.step - 1]()
with st.container(horizontal=True, horizontal_alignment="distribute", key="nav"):
    if S.step > 1:
        st.button("Back", key="back", on_click=go, args=(S.step - 1,))
    if S.step == 1:
        st.button("Next: see my 2 shows", type="primary", key="next", disabled=not S.persona, on_click=go, args=(2,))
with st.expander("How this works"):
    ai, code = HOW[S.step]
    st.markdown(f"**What the AI does:** {ai}\n\n**What plain code does:** {code}")

# ---- for reviewers: own show, own model ----
st.divider()
with st.expander("For reviewers: run on your own show or swap the model"):
    st.markdown("Upload a zip of `episode-*.txt` files in the screenplay format of `data/sample_show/` "
                "(up to 300 files, 5 MB). Your show replaces the demo show from step 2 on.")
    st.file_uploader("Episodes zip", type="zip", key="zip")
    if S.up_err:
        st.error(S.up_err)
    elif not IS_DEMO:
        st.success(f"Using your show: {TITLE}.")
    st.selectbox("Provider", ["openai", "anthropic"], key="m_prov", help="openai means any OpenAI-compatible API: Groq, Gemini, OpenAI, Ollama.")
    st.text_input("Model", secret("LLM_MODEL"), key="m_model")
    st.text_input("Base URL", secret("OPENAI_BASE_URL"), key="m_base")
    st.text_input("API key", type="password", key="m_key", help="Used for this browser session only. Never saved.")
    st.markdown(f"Code, README and tests: [{REPO}]({REPO})")
