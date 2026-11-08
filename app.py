"""Kuku Daily live lab: runs the real model on your own words or on a new show. Run: streamlit run app.py"""
import html
import json
import re
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

from tools import drops, gates, llm, match, persona as P

st.set_page_config(page_title="Kuku Daily · Live lab", page_icon=":material/live_tv:", layout="centered", initial_sidebar_state="collapsed")
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
STEPS = ["Who is watching?", "Your 2 shows", "Today's drop", "Come back later"]
FLOW = ["Who is watching", "2 shows for you", "Today's drop", "Come back later"]
LEDE = {
    1: "Answer five short questions and the model writes your viewer profile. In a hurry? Fill in a sample viewer's answers, "
       "or pick a demo viewer (no model call).",
    3: "Each drop runs 3.5 to 6 minutes and stops on the episode ending the model rated hardest to walk away from.",
    4: "The next drop is locked. Free viewers wait 24 hours at first and less as their streak grows. Subscribers get 2 drops "
       "and shorter waits, but nobody can binge the whole show.",
}
HOW = {
    1: ("Only in \"Your own words\": a model turns 5 short answers into a profile (who, free time, likes, dislikes, who you watch with).",
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
POSTERS = ["linear-gradient(160deg,#6a2c55,#1d0f1e 58%,#7a4217)", "linear-gradient(200deg,#2d3d63,#160d1b 58%,#66283a)",
           "linear-gradient(150deg,#77521a,#1f1020 55%,#45204f)", "linear-gradient(190deg,#215049,#150c17 58%,#653f1e)"]
GRAIN = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E"
         "%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E"
         "%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Rozha+One&family=Manrope:wght@400..800&display=swap');
@property --p{syntax:'<number>';inherits:false;initial-value:0}
:root{--bg:#170d18;--sf:#2a1b2d;--sf2:#362339;--line:rgba(247,236,223,.12);--line2:rgba(247,236,223,.22);--ink:#f7ecdf;
 --ink2:#d9c7bc;--ink3:#b49fa9;--gold:#f2a93b;--gold2:#ffc56a;--gink:#211204;--gsoft:rgba(242,169,59,.14);--ok:#86cfa0;
 --fd:"Rozha One",Georgia,serif;--eo:cubic-bezier(.16,1,.3,1)}
.stApp{background:radial-gradient(900px 600px at 8% -6%,rgba(242,169,59,.11),transparent 62%),
 radial-gradient(700px 500px at 100% 40%,rgba(236,106,82,.05),transparent 60%),var(--bg)}
.stApp::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:99;opacity:.045;mix-blend-mode:overlay;background-image:GRAIN}
header[data-testid="stHeader"]{background:transparent}
.block-container{padding:.8rem 1rem 3rem;max-width:820px}
[data-testid="stHeaderActionElements"]{display:none}
::selection{background:var(--gold);color:var(--gink)}
button[data-testid^="stBaseButton"]{min-height:44px;transition:transform .25s var(--eo),box-shadow .25s,border-color .25s}
button[data-testid^="stBaseButton-primary"]:not(:disabled),button[data-testid^="stBaseButton-primary"]:not(:disabled) p{color:var(--gink)!important;font-weight:700}
button[data-testid^="stBaseButton-primary"]:not(:disabled):hover{transform:translateY(-1px);box-shadow:0 10px 26px -10px rgba(242,169,59,.75)}
button[data-testid^="stBaseButton-secondary"]:hover{border-color:var(--gold)}
@keyframes kd-rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes kd-fade{from{opacity:0}}
@keyframes kd-pulse{0%{box-shadow:0 0 0 0 rgba(134,207,160,.55)}100%{box-shadow:0 0 0 9px rgba(134,207,160,0)}}
@keyframes kd-fill{from{width:var(--from)}to{width:var(--to)}}
@keyframes kd-pop{0%{transform:scale(.55)}70%{transform:scale(1.08)}100%{transform:scale(1)}}
@keyframes kd-zoom{from{transform:scale(1)}to{transform:scale(1.14) translate(-2%,2%)}}
@keyframes kd-grow{from{width:0}}
@keyframes kd-ring{from{--p:0}}
@keyframes kd-drop{from{opacity:0;transform:translateY(-18px) scale(.96)}}
@keyframes kd-out{to{opacity:.32;filter:grayscale(1)}}
@keyframes kd-strike{to{opacity:.3;text-decoration:line-through;filter:grayscale(1)}}
@keyframes kd-glow{to{background:var(--gold);border-color:var(--gold);color:var(--gink);box-shadow:0 0 0 5px var(--gsoft)}}
@keyframes kd-ping{0%{transform:scale(1);opacity:.7}100%{transform:scale(1.6);opacity:0}}

.kd-top{display:flex;align-items:center;gap:.7rem;flex-wrap:wrap;padding:.2rem 0 1.6rem}
.kd-brand{font-family:var(--fd);font-size:1.55rem;line-height:1}
.kd-brand span{color:var(--gold)}
.kd-live{display:inline-flex;align-items:center;gap:.45rem;padding:.22rem .65rem;border-radius:999px;border:1px solid rgba(134,207,160,.45);
 color:var(--ok);font-size:.7rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}
.kd-live i{width:7px;height:7px;border-radius:50%;background:var(--ok);animation:kd-pulse 1.8s ease-out infinite}
.kd-top nav{margin-left:auto;display:flex;gap:1.1rem;font-size:.92rem}
.kd-top nav a{color:var(--ink2)!important;text-decoration:none}
.kd-top nav a:hover{color:var(--gold2)!important}
.kd-eye{color:var(--gold);font-size:.74rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase;margin:0 0 .5rem}
.kd-h1{font-family:var(--fd);font-size:clamp(2.1rem,6vw,3rem);line-height:1.04;margin:0 0 .9rem;animation:kd-rise .8s var(--eo) both}
.kd-h1 em{font-style:normal;color:var(--gold)}
.kd-lede{color:var(--ink2);font-size:1.02rem;line-height:1.62;max-width:64ch;margin:0;animation:kd-rise .8s .08s var(--eo) both}
.kd-lede a{color:var(--gold2)!important}
.kd-facts{display:flex;flex-wrap:wrap;gap:.45rem;margin:1.1rem 0 0;animation:kd-rise .8s .16s var(--eo) both}
.kd-fact{font-size:.8rem;color:var(--ink2);padding:.32rem .75rem;border:1px solid var(--line);border-radius:999px;background:rgba(42,27,45,.65)}
.kd-fact b{color:var(--ink);font-weight:700}

.kd-steps{list-style:none;display:grid;grid-template-columns:repeat(4,1fr);margin:2.2rem 0 1.4rem!important;padding:0!important;position:relative}
.kd-steps::before,.kd-steps::after{content:"";position:absolute;top:16px;left:12.5%;height:2px;border-radius:2px}
.kd-steps::before{right:12.5%;background:var(--line2)}
.kd-steps::after{width:var(--to);background:linear-gradient(90deg,var(--gold),var(--gold2));animation:kd-fill 1s var(--eo) both}
.kd-steps li{list-style:none;text-align:center;font-size:.78rem;color:var(--ink3);position:relative;z-index:1;margin:0!important;padding:0 .15rem!important;line-height:1.3}
.kd-steps li b{display:grid;place-items:center;width:34px;height:34px;margin:0 auto .5rem;border-radius:50%;background:var(--sf);
 border:1px solid var(--line2);color:var(--ink2);font-size:.85rem}
.kd-steps li.done{color:var(--ink2)}
.kd-steps li.done b{background:#3b2a24;border-color:var(--gold);color:var(--gold2)}
.kd-steps li.on{color:var(--ink);font-weight:700}
.kd-steps li.on b{background:var(--gold);border-color:var(--gold);color:var(--gink);box-shadow:0 0 0 6px var(--gsoft);animation:kd-pop .6s .35s var(--eo) both}
.kd-h2{font-family:var(--fd);font-size:clamp(1.8rem,4.8vw,2.35rem);line-height:1.08;margin:0 0 .45rem;animation:kd-rise .7s var(--eo) both}
.kd-p{color:var(--ink2);line-height:1.6;margin:0 0 .4rem;animation:kd-rise .7s .06s var(--eo) both}

.kd-card,div[class*="st-key-card_"]{background:linear-gradient(180deg,rgba(54,35,57,.6),rgba(38,24,41,.9));border:1px solid var(--line);
 border-radius:18px;padding:1.1rem 1.1rem 1.3rem;box-shadow:0 22px 44px -26px rgba(0,0,0,.8);animation:kd-rise .7s var(--eo) both}
div[class*="st-key-card_ready"]{border-color:rgba(242,169,59,.55);box-shadow:0 22px 50px -26px rgba(242,169,59,.35)}
.st-key-card_demo{background:transparent!important;border-style:dashed!important;box-shadow:none!important}
.kd-label{color:var(--ink3);font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;margin:0 0 .35rem}
.kd-name{font-family:var(--fd);font-size:1.6rem;line-height:1.1}
.kd-mut{color:var(--ink3);font-size:.88rem;line-height:1.5}
.kd-meta{display:flex;flex-wrap:wrap;gap:.35rem .9rem;color:var(--ink2);font-size:.88rem;margin:.35rem 0 .7rem}
.kd-row{margin:.3rem 0;font-size:.9rem;color:var(--ink2)}
.kd-row b{display:inline-block;min-width:4.2rem;color:var(--ink3);font-size:.72rem;letter-spacing:.08em;text-transform:uppercase}
.kd-chip{display:inline-block;padding:.14rem .62rem;margin:.15rem .25rem .15rem 0;border-radius:999px;background:#3a2740;
 border:1px solid var(--line);font-size:.8rem;color:var(--ink)}
.kd-chip.no{text-decoration:line-through;color:var(--ink3)}
.kd-src{display:inline-flex;align-items:center;gap:.4rem;margin-top:.8rem;font-size:.8rem;font-weight:700;color:var(--ok)}
.kd-src.off{color:var(--ink3);font-weight:600}
.kd-shield{display:inline-block;margin-top:.5rem;padding:.2rem .6rem;border-radius:8px;border:1px solid rgba(134,207,160,.4);color:var(--ok);font-size:.8rem;font-weight:700}
.kd-sum{margin-top:.7rem;padding-left:.8rem;border-left:2px solid var(--gold);color:var(--ink2);font-size:.92rem;line-height:1.5}

[data-testid="stRadioGroup"]{gap:.45rem!important;flex-wrap:wrap}
[data-testid="stRadioOption"]{border:1px solid var(--line2);border-radius:999px;padding:.35rem .95rem .35rem .65rem!important;background:var(--sf);
 margin:0!important;min-height:42px;transition:border-color .25s,background .25s}
[data-testid="stRadioOption"][data-selected="true"]{border-color:var(--gold);background:var(--gsoft)}
.stTabs [data-baseweb="tab-list"]{gap:.2rem;border-bottom:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{min-height:46px;padding:0 .85rem;font-weight:600}
.stTabs [data-baseweb="tab"][aria-selected="true"] p{color:var(--gold2)}
.stTabs [data-baseweb="tab-highlight"]{background:var(--gold)}
.st-key-words_box [data-testid="stWidgetLabel"]{background:var(--sf2);border:1px solid var(--line);border-radius:16px 16px 16px 4px;
 padding:.55rem .85rem;width:fit-content;max-width:90%;margin-bottom:.5rem}
.st-key-words_box [data-testid="stWidgetLabel"] p{font-size:.95rem;color:var(--ink)}
.st-key-words_box [data-testid="stTextInput"]{animation:kd-rise .6s var(--eo) both}
.st-key-words_box [data-testid="stTextInputRootElement"]{border-radius:16px 16px 4px 16px!important;margin-left:auto!important;width:min(88%,30rem)!important}

.kd-who{display:flex;align-items:center;gap:.7rem;margin-bottom:.55rem}
.kd-ava{flex:none;width:44px;height:44px;border-radius:50%;display:grid;place-items:center;font-family:var(--fd);font-size:1.3rem;
 color:var(--gink);background:var(--av)}
.kd-who b{display:block;font-size:1rem;line-height:1.2}
.kd-who small{color:var(--ink3);font-size:.8rem}

.kd-pool{display:flex;flex-wrap:wrap;gap:.35rem;margin:.2rem 0 1.2rem}
.kd-pool span{padding:.3rem .7rem;border-radius:999px;border:1px solid var(--line2);background:var(--sf);font-size:.8rem;color:var(--ink2)}
.kd-pool .unsafe{animation:kd-strike .6s calc(.3s + var(--d)) var(--eo) forwards}
.kd-pool .low{animation:kd-out .6s calc(.9s + var(--d)) var(--eo) forwards}
.kd-pool .short{animation:kd-out .6s calc(1.7s + var(--d)) var(--eo) forwards}
.kd-pool .pick{animation:kd-glow .7s 2.3s var(--eo) forwards;font-weight:700}
.kd-key{display:flex;flex-wrap:wrap;gap:.3rem 1rem;font-size:.76rem;color:var(--ink3);margin:-.6rem 0 1.2rem}
.kd-poster{position:relative;height:156px;border-radius:14px;overflow:hidden;display:flex;flex-direction:column;justify-content:flex-end;
 padding:.85rem .95rem;margin-bottom:.75rem;background:var(--pg)}
.kd-poster::after{content:"";position:absolute;inset:0;background:linear-gradient(transparent 35%,rgba(10,5,10,.75))}
.kd-poster::before,.kd-screen::before{content:"";position:absolute;inset:0;z-index:1;background-image:GRAIN;opacity:.13;mix-blend-mode:overlay;pointer-events:none}
.kd-poster>*{position:relative;z-index:1}
.kd-poster small{font-size:.7rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:rgba(247,236,223,.85)}
.kd-poster h3{font-family:var(--fd);font-weight:400;font-size:1.55rem;line-height:1.05;margin:.15rem 0 0;padding:0;color:#fff;text-shadow:0 2px 14px rgba(0,0,0,.55)}
.kd-badge{display:inline-block;padding:.16rem .6rem;border-radius:6px;font-size:.74rem;font-weight:800;background:var(--gold);color:var(--gink)}
.kd-badge.off{background:transparent;border:1px solid var(--line2);color:var(--ink3);font-weight:600}
.kd-why{margin:.65rem 0 0;line-height:1.5;color:var(--ink)}
.kd-why::before{content:"\\201C";font-family:var(--fd);color:var(--gold);font-size:1.4rem;line-height:0;vertical-align:-.35rem;margin-right:.15rem}

.st-key-card_phone{max-width:390px;margin:0 auto;border-radius:36px!important;border:2px solid #4d3652!important;
 background:#120a13!important;padding:.75rem .8rem 1.2rem!important;box-shadow:0 40px 80px -40px rgba(242,169,59,.35),0 30px 60px -30px #000!important}
.st-key-card_phone::before{content:"";display:block;width:84px;height:6px;border-radius:6px;background:#3b2a3e;margin:.1rem auto .2rem}
.kd-ph-top{display:flex;justify-content:space-between;align-items:baseline;gap:.5rem;font-size:.8rem;color:var(--ink3);margin:0 .2rem .55rem}
.kd-ph-top b{color:var(--gold2);white-space:nowrap}
.kd-screen{height:236px;border-radius:20px;position:relative;overflow:hidden;padding:1rem;display:flex;flex-direction:column;justify-content:flex-end}
.kd-screen .bg{position:absolute;inset:-12%;background:radial-gradient(55% 45% at 30% 28%,rgba(242,169,59,.38),transparent 70%),
 linear-gradient(160deg,#52285c,#1a0f1c 55%,#753a19);animation:kd-zoom 16s ease-in-out infinite alternate}
.kd-screen::after{content:"";position:absolute;inset:0;background:linear-gradient(transparent 40%,rgba(8,4,8,.78))}
.kd-screen>*:not(.bg){position:relative;z-index:1}
.kd-play{position:absolute!important;top:40%;left:50%;width:62px;height:62px;margin:-31px 0 0 -31px;border-radius:50%;
 background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.3);backdrop-filter:blur(6px)}
.kd-play::before{content:"";position:absolute;inset:-1px;border-radius:50%;border:1px solid rgba(255,255,255,.5);animation:kd-ping 2.2s ease-out infinite}
.kd-play::after{content:"";position:absolute;left:25px;top:19px;border-left:18px solid #fff;border-top:12px solid transparent;border-bottom:12px solid transparent}
.kd-screen b{font-family:var(--fd);font-weight:400;font-size:1.35rem;line-height:1.1}
.kd-screen span{color:rgba(247,236,223,.8);font-size:.85rem}
.kd-meter{margin:1rem .15rem .9rem}
.kd-meter .top{display:flex;justify-content:space-between;align-items:baseline}
.kd-meter .top b{font-size:1.3rem;color:var(--gold2);font-variant-numeric:tabular-nums}
.kd-bar{height:8px;border-radius:8px;background:rgba(247,236,223,.1);overflow:hidden;margin:.3rem 0 .35rem}
.kd-bar i{display:block;height:100%;width:var(--v);border-radius:8px;background:linear-gradient(90deg,#ec6a52,var(--gold),var(--gold2));
 animation:kd-grow 1.5s .35s var(--eo) both}
.kd-quote{margin:.3rem .15rem .55rem;padding:.8rem .95rem;border-radius:4px 16px 16px 16px;background:var(--gsoft);border:1px solid rgba(242,169,59,.32);
 line-height:1.58;font-size:1rem;animation:kd-rise .7s .9s var(--eo) both}
.kd-quote mark{background:none;color:var(--gold2);text-decoration:underline;text-decoration-color:rgba(255,197,106,.55);
 text-decoration-thickness:2px;text-underline-offset:.24em}
.kd-check{display:flex;align-items:center;gap:.4rem;margin:0 .15rem .3rem;font-size:.82rem;font-weight:700;color:var(--ok);animation:kd-fade .6s 1.3s both}
.kd-check.off{color:var(--ink3);font-weight:600}
.kd-open{margin:0 .15rem .5rem;color:var(--ink3);font-size:.86rem;line-height:1.45}

.kd-lock{text-align:center;padding:.3rem 0 .2rem}
.kd-ring{width:212px;height:212px;margin:.2rem auto 1rem;border-radius:50%;display:grid;place-items:center;position:relative;
 background:conic-gradient(var(--gold) calc(var(--p) * 1%),rgba(247,236,223,.08) 0);animation:kd-ring 1.6s .2s var(--eo) both}
.kd-ring::before{content:"";position:absolute;inset:9px;border-radius:50%;background:radial-gradient(circle at 50% 30%,#2a1b2d,#170d18)}
.kd-ring>div{position:relative}
.kd-big{font-size:2.5rem;font-weight:800;color:var(--ink);font-variant-numeric:tabular-nums;line-height:1.05;margin:.2rem 0;letter-spacing:-.02em}
.kd-pad{width:22px;height:16px;background:var(--gold);border-radius:4px;margin:12px auto 4px;position:relative}
.kd-pad::before{content:"";position:absolute;box-sizing:border-box;width:14px;height:12px;border:3px solid var(--gold);border-bottom:none;
 border-radius:8px 8px 0 0;left:4px;top:-11px}
.kd-push{display:flex;gap:.75rem;align-items:flex-start;text-align:left;max-width:370px;margin:1.1rem auto .2rem;padding:.75rem .9rem;
 border-radius:18px;background:rgba(247,236,223,.08);border:1px solid var(--line2);backdrop-filter:blur(8px);animation:kd-drop .8s 1.2s var(--eo) both}
.kd-push .ic{flex:none;width:36px;height:36px;border-radius:10px;background:var(--gold);color:var(--gink);display:grid;place-items:center;
 font-family:var(--fd);font-size:1.15rem}
.kd-push div{font-size:.9rem;line-height:1.4}
.kd-push small{display:block;color:var(--ink3);font-size:.76rem;margin-bottom:.1rem}
.kd-seg{display:flex;gap:5px;margin:.5rem 0}
.kd-seg span{flex:1;height:12px;border-radius:4px;background:#3a2a3d}
.kd-seg span.f{background:linear-gradient(180deg,var(--gold2),var(--gold));box-shadow:0 0 12px -2px rgba(242,169,59,.7);animation:kd-pop .5s var(--eo) both}
.kd-ladder{display:flex;gap:.45rem;margin:.45rem 0}
.kd-ladder div{flex:1;text-align:center;border:1px solid var(--line);border-radius:14px;padding:.6rem .25rem;color:var(--ink3);font-size:.78rem;
 transition:background .3s}
.kd-ladder b{display:block;font-size:1.45rem;color:var(--ink2);font-variant-numeric:tabular-nums}
.kd-ladder .on{border-color:var(--gold);background:var(--gsoft);color:var(--ink);animation:kd-pop .6s .3s var(--eo) both}
.kd-ladder .on b{color:var(--gold2)}
.kd-tl{border-left:2px solid var(--line2);margin:.5rem 0 1.2rem .45rem;padding-left:1.1rem}
.kd-tl div{position:relative;padding:.5rem 0;display:flex;flex-wrap:wrap;justify-content:space-between;gap:.15rem 1rem;color:var(--ink2);
 font-size:.9rem;animation:kd-rise .6s calc(var(--d) + .2s) var(--eo) both}
.kd-tl div::before{content:"";position:absolute;left:calc(-1.1rem - 7px);top:.85rem;width:12px;height:12px;border-radius:50%;
 background:var(--bg);border:2px solid var(--gold)}
.kd-tl span{white-space:nowrap}
.kd-tl span:last-child{color:var(--ink3)}

[data-testid="stExpander"] details{border:1px solid var(--line);border-radius:14px;background:rgba(42,27,45,.45)}
[data-testid="stExpander"] summary{min-height:48px}
.kd-foot{margin-top:2.2rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--ink3);font-size:.8rem;line-height:1.55}
.kd-foot a{color:var(--ink2)!important}
@media (max-width:520px){.kd-steps li{font-size:.7rem}.kd-top nav{margin-left:0;width:100%}.kd-ring{width:188px;height:188px}.kd-big{font-size:2.15rem}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-delay:0ms!important;
 animation-iteration-count:1!important;transition:none!important}}
</style>""".replace("GRAIN", GRAIN), unsafe_allow_html=True)


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


def head(n, lede):
    html_block(f'<p class="kd-eye">Step {n} of 4</p><div class="kd-h2" role="heading" aria-level="2">{STEPS[n - 1]}</div>'
               f'<p class="kd-p">{lede}</p>')


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
MODEL = cfg_id()[1]
frm, S.shown_step = S.get("shown_step", S.step), S.step  # the progress line grows from the step you came from


def step_li(i, t):
    cls, cur = ("on", ' aria-current="step"') if i == S.step else ("done" if i < S.step else "", "")
    return f'<li class="{cls}"{cur}><b>{i}</b>{t}</li>'


html_block(
    f'<div class="kd-top"><div class="kd-brand">Kuku <span>Daily</span></div><span class="kd-live"><i></i>Live lab</span>'
    f'<nav><a href="{PROTOTYPE_URL}" target="_blank">Guided demo ↗</a>'
    f'<a href="{PROTOTYPE_URL}trailer.mp4" target="_blank">Trailer ↗</a><a href="{REPO}" target="_blank">Code ↗</a></nav></div>'
    '<p class="kd-eye">The real model, running now</p>'
    '<div class="kd-h1" role="heading" aria-level="1">Two shows, not thirty.<br><em>Then the story brings you back.</em></div>'
    '<p class="kd-lede">Kuku TV shows a new viewer about 30 shows and asks them to pay (Rs 199 to 1,499, auto-renew) before any story '
    'hooks them. Kuku Daily picks 2 that fit you, tells the story in 5 minute drops that end on a cliffhanger, and unlocks the next '
    f'one at your free time, like a TV serial. The <a href="{PROTOTYPE_URL}" target="_blank">guided demo</a> replays saved outputs; '
    'this lab runs the model on your own words or on a new show.</p>'
    '<div class="kd-facts">'
    + (f'<span class="kd-fact"><b>Model</b> {e(MODEL)}</span>' if MODEL else
       '<span class="kd-fact"><b>No model key here</b> demo viewers and saved drops still work</span>')
    + '<span class="kd-fact"><b>Catalog</b> 10 public microdramas + 1 demo show</span>'
      '<span class="kd-fact"><b>Demo show</b> fictional</span></div>'
    f'<ol class="kd-steps" style="--from:{(frm - 1) * 25}%;--to:{(S.step - 1) * 25}%" aria-label="Progress">'
    + "".join(step_li(i + 1, t) for i, t in enumerate(FLOW)) + '</ol>')


# ---- step 1: who are you ----
def set_lang():
    S.lang = S.lang_w
    if S.persona:
        S.persona = S.persona.model_copy(update={"language": S.lang.lower()})


def set_viewer(k):
    spec = VIEWERS[k][1]
    S.persona, S.viewer, S.lang = P.quick(**spec), k, spec["language"].title()


def sample_answers(lang):
    """Real answers from the saved demo-show run (data/demo_cache/viewers), one viewer per language."""
    for f in sorted((CACHE / "viewers").glob("*.json")):
        v = json.loads(f.read_text())
        if v["input"]["language"] == lang:
            return v["input"]["answers"]
    return []


def fill_sample(lang):
    for i, a in enumerate(sample_answers(lang)):
        S[f"q{i}_{lang}"] = a


def avatar(name):
    return POSTERS[sum(map(ord, name)) % len(POSTERS)]


def profile_card(p):
    who = {"family": "with family", "partner": "with a partner", "alone": "alone"}.get(p.watch_with)
    live = S.get("viewer") == "words"  # only the model sets minutes_per_day; quick profiles keep the default
    meta = "".join(f"<span>{e(x)}</span>" for x in [p.language.title(), who and f"Watches {who}",
                                                    f"Free at {slot_text(p.slots)}", live and f"{p.minutes_per_day} min a day"] if x)
    src = ('<div class="kd-src">● Read by the model from your answers</div>' if live else
           '<div class="kd-src off">Set by you. No model call.</div>')
    extra = f'<div class="kd-sum">{e(p.summary)}</div>' if live and p.summary else ""
    shield = '<div class="kd-shield">Family-safe shows only</div>' if p.watch_with == "family" else ""
    html_block(f'<div class="kd-card" style="margin-top:1rem"><div class="kd-label">Your viewer profile</div>'
               f'<div class="kd-name">{e(p.who[:1].upper() + p.who[1:])}</div><div class="kd-meta">{meta}</div>'
               f'<div class="kd-row"><b>Likes</b>{chips(p.likes) or "anything"}</div>'
               f'<div class="kd-row"><b>Avoids</b>{chips(p.dislikes, "no") or "nothing set"}</div>{shield}{extra}{src}</div>')


def step1():
    head(1, LEDE[1])
    S.lang_w = S.lang
    st.radio("Language for your shows and teasers", ["Hinglish", "English"], key="lang_w", horizontal=True, on_change=set_lang)
    lang = S.lang.lower()
    t1, t2, t3 = st.tabs(["Your words · live AI", "Demo viewers", "Build your own"])
    with t1:
        st.button("Fill in a sample viewer's answers", key="fill", on_click=fill_sample, args=(lang,), icon=":material/edit_note:")
        with st.container(key="words_box"), st.form("words", border=False):
            ans = [st.text_input(q, key=f"q{i}_{lang}", placeholder="Apne shabdon mein likhiye" if lang == "hinglish" else "In a few words")
                   for i, q in enumerate(P.QUESTIONS[lang])]
            if st.form_submit_button("Read my answers", type="primary"):
                try:
                    with st.spinner("The model is reading your answers..."), cfg():
                        S.persona, S.viewer = P.extract(ans, lang), "words"
                    st.rerun()
                except Exception as ex:
                    st.error(f"Could not read your answers ({str(ex)[:120]}). Pick a demo viewer or use Build your own: neither needs a model.")
    with t2:
        for col, (k, (name, spec)) in zip(st.columns(3), VIEWERS.items()):
            role, city = name.split(", ")
            with col, st.container(key=f"card_viewer_{k}"):
                html_block(f'<div class="kd-who"><span class="kd-ava" style="--av:{avatar(name)}">{role[0]}</span>'
                           f'<div><b>{e(role)}</b><small>{e(city)} · {spec["language"].title()}</small></div></div>'
                           f'<div class="kd-mut">{"With family" if spec["watch_with"] == "family" else "Alone"} · free at '
                           f'{slot_text(spec["slots"])}<br>Likes {e(", ".join(spec["likes"]))}'
                           + (f'<br>Avoids {e(", ".join(spec.get("dislikes", [])))}' if spec.get("dislikes") else "") + '</div>')
                chosen = S.get("viewer") == k
                st.button("Chosen" if chosen else "Choose", key=f"v_{k}", type="primary" if chosen else "secondary", width="stretch",
                          on_click=set_viewer, args=(k,), icon=":material/check:" if chosen else None)
    with t3, st.form("own"):
        who = st.selectbox("I am a", ["student", "homemaker", "working professional", "retired"])
        likes = st.multiselect("I like", P.TAGS, placeholder="Pick a few")
        dislikes = st.multiselect("Never show me", P.TAGS, placeholder="Optional")
        slot = st.time_input("I am usually free at", value=datetime.strptime("20:00", "%H:%M").time())
        wm = st.radio("I watch", ["alone", "family"], horizontal=True, format_func=lambda x: "with family" if x == "family" else x)
        if st.form_submit_button("Use this profile", type="primary"):
            S.persona, S.viewer = P.quick(who, likes or [], dislikes or [], [slot.strftime("%H:%M")], lang, wm), "own"
            st.rerun()
    S.bts = S.persona.model_dump() if S.persona else None
    if S.persona:
        profile_card(S.persona)


# ---- step 2: your 2 shows ----
def pick(pers, entry):
    with st.spinner("The model is picking 2 shows for you..."), cfg():
        return match.pick(pers, match.load_catalog(extra=[entry]))


def show_html(s, hinglish):
    why = s.get("reason") or s.get("logline", "")
    if hinglish and why.startswith("Matches what you like: "):  # the code fallback speaks English; keep the viewer's language
        why = "Aapki pasand se match: " + why.split(": ", 1)[1]
    badge = '<span class="kd-badge">Episodes ready</span>' if s.get("has_scripts") else \
        '<span class="kd-badge off">No episodes in this demo</span>'
    return (f'<div class="kd-show"><div class="kd-poster" style="--pg:{avatar(s["title"])}"><small>{e(s["platform"])}</small>'
            f'<h3>{e(s["title"])}</h3></div>{badge}<div style="margin-top:.55rem">{chips(s["tags"])}</div>'
            f'<p class="kd-why">{e(why)}</p></div>')


def funnel(pers, entry, picks):
    """The same filter and shortlist match.pick runs, drawn as chips that drop out stage by stage."""
    pool = match.load_catalog(extra=[entry])
    safe = [s for s in pool if s.get("family_safe", True)] if pers.watch_with == "family" else pool
    short = {s["id"] for s in sorted(safe or pool, key=lambda s: match.score(pers, s), reverse=True)[:6]}
    chosen, safe_ids = {s["id"] for s in picks}, {s["id"] for s in safe or pool}
    kind = lambda s: "pick" if s["id"] in chosen else "short" if s["id"] in short else "low" if s["id"] in safe_ids else "unsafe"
    order = sorted(pool, key=lambda s: s["id"] not in chosen)[::-1]  # picks last, so they light up at the end of the row
    return (f'<div class="kd-label">From {len(pool)} shows to 2</div><div class="kd-pool">'
            + "".join(f'<span class="{kind(s)}" style="--d:{i * 70}ms">{e(s["title"])}</span>' for i, s in enumerate(order))
            + '</div><div class="kd-key"><span>Struck: not family-safe</span><span>Dimmed first: weak tag match</span>'
              '<span>Dimmed next: shortlist the model passed over</span><span>Gold: the model\'s 2 picks</span></div>')


def start():
    S.state, S.step = new_state(), 3
    S.pop("flash", None)


def step2():
    pers, entry = S.persona, show_entry()
    res = once("picks", (pers.model_dump_json(), entry["id"], cfg_id()), lambda: pick(pers, entry))
    by = {"llm": "The model chose these 2 and wrote each reason.",
          "llm+fallback": "The model chose one; the tag score filled the other.",
          "fallback": "The model was unavailable, so the tag score chose."}.get(res["source"], "")
    head(2, f"Picked for {e(pers.who)}. {by} Only {e(TITLE)} has episodes in this prototype.")
    html_block(funnel(pers, entry, res["picks"]))
    S.bts = res
    for i, (col, s) in enumerate(zip(st.columns(2), res["picks"])):
        with col, st.container(key=f"card_{'ready' if s.get('has_scripts') else 'show'}{i}"):
            html_block(show_html(s, pers.language == "hinglish"))
            if s.get("has_scripts"):
                st.button("Start watching", type="primary", key=f"start{i}", width="stretch", on_click=start, icon=":material/play_arrow:")
    if not any(s.get("has_scripts") for s in res["picks"]):
        st.info(f"Neither pick has episodes here: this prototype only has scripts for {TITLE}. Watch it to see how drops work.")
        st.button(f"Watch {TITLE} instead", type="primary", key="start_demo", on_click=start)


# ---- step 3: today's drop ----
def ep_text(eps):
    return f"Episode {eps[0]}" if len(eps) == 1 else f"Episodes {', '.join(map(str, eps[:-1]))} and {eps[-1]}"


def teaser_html(t):
    """Underline the quoted line inside the teaser: that is the part code checked against the episode."""
    m = re.search(r'"[^"]*"?', t)
    out = e(t) if not m else e(t[:m.start()]) + f"<mark>{e(m.group())}</mark>" + e(t[m.end():])
    return out.replace("\n", "<br>")


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


def meter(d):
    parts = [f"model {d['llm_score']}/5" if d.get("llm_score") is not None else "",
             f"rules {d['rule_score']:.2f}" if d.get("rule_score") is not None else ""]
    v = d.get("cliff_score") or 0
    return (f'<div class="kd-meter"><div class="top"><span class="kd-label">Cliffhanger pull</span><b>{v:.2f}</b></div>'
            f'<div class="kd-bar"><i style="--v:{v * 100:.0f}%"></i></div>'
            f'<div class="kd-mut">{" · ".join(p for p in parts if p)}</div></div>')


def step3():
    sched, err = schedule()
    D, stt = sched["drops"], S.state
    head(3, LEDE[3])
    if S.get("flash"):
        kind, msg = S.pop("flash")
        (st.warning if kind == "late" else st.success)(msg)
    if err:
        st.warning(f"The model did not answer ({err}). These drops are cut by rules only, without teasers.")
    now = D[stt["cur"]:stt["cur"] + gates.TIERS[S.tier]["drops_per_unlock"]]
    S.bts = now
    if not now:
        finished()
        return
    nums = " and ".join(str(d["n"]) for d in now)
    last = now[-1]
    check = ('<div class="kd-check">✓ The quoted line is in the episode</div>' if last.get("grounded") else
             '<div class="kd-check off">Teaser not checked against the episode</div>') if last["teaser"] else ""
    with st.container(key="card_phone"):
        html_block(f'<div class="kd-ph-top"><span>{e(TITLE)}</span><b>Drop{"s" if len(now) > 1 else ""} {nums} of {len(D)}</b></div>'
                   f'<div class="kd-screen"><div class="bg"></div><div class="kd-play"></div>'
                   f'<b>{ep_text([x for d in now for x in d["episodes"]])}</b>'
                   f'<span>About {round(sum(d["seconds"] for d in now) / 60)} min</span></div>{meter(last)}'
                   f'<div class="kd-label" style="margin:0 .15rem">It ends on this teaser</div>'
                   f'<div class="kd-quote">{teaser_html(last["teaser"] or "Come back for what happens next.")}</div>{check}'
                   + (f'<div class="kd-open">Left open: {e(last["open_question"])}</div>' if last["open_question"] else ""))
        st.button("Mark as watched", type="primary", key="watched", width="stretch", on_click=watched, args=(len(now),),
                  icon=":material/check_circle:")
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
            + "".join(f'<span class="{"f" if i < streak else ""}" style="animation-delay:{i * 60}ms"></span>' for i in range(7))
            + f'</div><div class="kd-mut">{nxt}</div>'
            '<div class="kd-label" style="margin-top:1rem">Wait before your next drop</div><div class="kd-ladder">'
            + "".join(f'<div class="{"on" if i == lvl else ""}"><b>{w} h</b>{names[i]}</div>' for i, w in enumerate(waits)) +
            '</div><div class="kd-mut">Come back more than a day late and you drop one level, not to zero.</div>')


def step4():
    head(4, LEDE[4])
    S.tier_w = S.tier
    st.radio("Your plan", ["free", "subscriber"], key="tier_w", horizontal=True, on_change=set_tier,
             format_func={"free": "Free · 1 drop per unlock", "subscriber": "Subscriber · 2 drops, shorter waits"}.get)
    sched, _ = schedule()
    D, stt = sched["drops"], S.state
    nxt = stt["cur"] + stt["watched"]
    if nxt >= len(D):
        finished()
        return
    u = gates.next_unlock(stt["clock"], S.tier, stt["streak"])
    r = gates.reminder(u, S.persona.slots)
    left = int((u - stt["clock"]).total_seconds() // 60)
    S.bts = {"plan": S.tier, "streak": stt["streak"], "now": stt["clock"].isoformat(), "next_unlock": u.isoformat(),
             "reminder": r.isoformat(), "waits_h": gates.TIERS[S.tier]["waits_h"]}
    line = (D[nxt - 1]["teaser"] or D[nxt - 1]["open_question"] or "Your next drop is ready.").split("\n")[0] if nxt else ""
    with st.container(key="card_lock"):
        html_block(f'<div class="kd-lock"><div class="kd-ring" style="--p:{min(100, left / 14.4):.0f}"><div><div class="kd-pad"></div>'
                   f'<div class="kd-mut">Drop {nxt + 1} of {len(D)} unlocks in</div>'
                   f'<div class="kd-big">{left // 60:02d}:{left % 60:02d}:00</div></div></div>'
                   f'<div class="kd-mut">Opens {day(u)}, {hm(u)}</div><div><b>We will remind you at {hm(r)} on {day(r)} (your slot).</b></div>'
                   f'<div class="kd-push"><span class="ic">K</span><div><small>Kuku Daily · {hm(r)}</small>{e(line)}</div></div></div>')
    with st.container(key="card_streak"):
        html_block(ladder_html(stt["streak"]))
    with st.container(key="card_demo"):
        html_block('<div class="kd-label">Demo controls</div><div class="kd-mut">Nobody waits a day in a demo, so these move a '
                   f'pretend clock. It is now {day(stt["clock"])}, {hm(stt["clock"])}.</div>')
        with st.container(horizontal=True):
            st.button("Fast-forward to my reminder", type="primary", key="ff", on_click=advance, args=(0,), icon=":material/fast_forward:")
            st.button("Skip 2 days", key="skip", on_click=advance, args=(2,))
            st.button("Give me a 7-day streak", key="s7", on_click=streak7)
        st.caption("Fast-forward: you open the app when reminded, so the streak grows and the next drop opens. "
                   "Skip 2 days: you come back late, so the streak falls one level.")
    rows = upcoming(D, stt)
    html_block('<div class="kd-label" style="margin-top:1.2rem">Coming up, if you come back at every reminder</div><div class="kd-tl">' + "".join(
        f'<div style="--d:{i * 80}ms"><span>Drop {d["n"]} · {ep_text(d["episodes"])}</span><span>Locked until {day(t)}, {hm(t)}</span></div>'
        for i, (d, t) in enumerate(rows)) + '</div>')


# ---- the stepper ----
[step1, step2, step3, step4][S.step - 1]()
with st.container(horizontal=True, horizontal_alignment="distribute", key="nav"):
    if S.step > 1:
        st.button("Back", key="back", on_click=go, args=(S.step - 1,), icon=":material/arrow_back:")
    if S.step == 1:
        st.button("Next: see my 2 shows", type="primary", key="next", disabled=not S.persona, on_click=go, args=(2,),
                  icon=":material/arrow_forward:", icon_position="right")
with st.expander("Behind the scenes: what the AI did, what code did, raw output"):
    ai, code = HOW[S.step]
    st.markdown(f"**What the AI does:** {ai}\n\n**What plain code does:** {code}")
    if S.get("bts") is not None:
        st.caption("Raw output for this step")
        st.json(S.bts, expanded=1)

# ---- for reviewers: own show, own model ----
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
html_block(f'<div class="kd-foot">Concept prototype by Shikhar Kansal for Kuku\'s AI Generalist assignment. Not an official Kuku product. '
           f'The demo show is fictional. <a href="{REPO}" target="_blank">Code, README and tests</a></div>')
