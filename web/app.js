// Kuku Daily prototype: one state machine drives autoplay and manual mode.
// All times come from KDGates (naive wall-clock stored in UTC fields), never hardcoded.
(() => {
  "use strict";
  const KD = window.KD, G = window.KDGates;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const RM = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const EASE = "cubic-bezier(.16,1,.3,1)", EASE_IN = "cubic-bezier(.55,0,.75,.2)", EASE_IO = "cubic-bezier(.65,0,.35,1)";
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const unq = (s) => String(s).replace(/^"+|"+$/g, "");
  const WATCHED = G.at(2026, 11, 9, 20, 0);

  // ---------- Icons (authored inline SVG, one stroke weight) ----------
  const I = {
    play: '<path d="M8 5.5v13l10.5-6.5z" fill="currentColor" stroke="none"/>',
    pause: '<path d="M8.5 5.5v13M15.5 5.5v13"/>',
    skip: '<path d="M6 6v12l8.5-6z" fill="currentColor" stroke="none"/><path d="M18 6v12"/>',
    back: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    next: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    flame: '<path d="M12 3c1 3.5 5 5.6 5 10.2a5 5 0 0 1-10 0c0-2.3 1-3.8 2.3-4.8.2 1.7.9 2.7 1.9 3.2C11 9.2 10.6 6 12 3z"/>',
    lock: '<rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/>',
    unlock: '<rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8 10.5V8a4 4 0 0 1 7.7-1.6"/>',
    shield: '<path d="M12 3l7 3v5.5c0 4.3-3 7.9-7 9.5-4-1.6-7-5.2-7-9.5V6z"/><path d="M9 12l2.2 2.2L15.5 10"/>',
    shieldx: '<path d="M12 3l7 3v5.5c0 4.3-3 7.9-7 9.5-4-1.6-7-5.2-7-9.5V6z"/><path d="M9.5 9.5l5 5M14.5 9.5l-5 5"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    bell: '<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 1.5h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
    clock: '<circle cx="12" cy="12" r="8.5"/><path class="hh" d="M12 12V8.2"/><path class="mh" d="M12 12h4.2"/>',
    speaker: '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11"/>',
    spark: '<path d="M12 3.5l1.8 5.2 5.2 1.8-5.2 1.8L12 17.5l-1.8-5.2L5 10.5l5.2-1.8z"/><path d="M18.5 16.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>',
    wave: '<path d="M3 12h2M7 8v8M11 5v14M15 9v6M19 11v2"/>',
    fwd: '<path d="M4 6.5v11l7-5.5zM12.5 6.5v11l7-5.5z" fill="currentColor" stroke="none"/>',
    replay: '<path d="M4.5 12a7.5 7.5 0 1 0 2.2-5.3"/><path d="M4.5 4.5v4h4"/>',
    layers: '<path d="M12 4l8.5 4.5L12 13 3.5 8.5z"/><path d="M3.5 12.5L12 17l8.5-4.5M3.5 16.5L12 21l8.5-4.5"/>',
  };
  const ico = (n, c = "") => `<svg class="i ${c}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${I[n]}</svg>`;

  // ---------- Copy inside the phone (viewer language) ----------
  const WD = { english: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], hinglish: ["Ravivaar", "Somvaar", "Mangalvaar", "Budhvaar", "Guruvaar", "Shukravaar", "Shanivaar"] };
  const WDS = { english: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], hinglish: ["Ravi", "Som", "Mangal", "Budh", "Guru", "Shukra", "Shani"] };
  const T = {
    hinglish: {
      tagline: "Roz ek drop. Aapke time pe.", start: "Shuru karein",
      hello: "Namaste! 5 chhote sawaal, phir aapke liye 2 shows.", type: "Yahan likhiye", pick: "Jawab chuniye", sample: "Sample viewer ka jawab",
      reading: "Aapke jawab padh rahe hain", about: "Aapke baare mein", fSlots: "Free time", fLikes: "Pasand", fDis: "Nahi dekhna", fWith: "Kiske saath", fMin: "Roz ka time",
      min: (m) => `${m} min roz`, with: { family: "Family ke saath", partner: "Partner ke saath", alone: "Akele", friends: "Doston ke saath" },
      tier: { tier1: "Bada shehar", tier2: "Tier 2 shehar", tier3: "Chhota shehar" },
      shield: "Sirf family-safe shows", shieldS: "Family ke saath dekhti hain",
      all: (n) => `${n} shows mein se`, out: (n) => `${n} shows hataaye: family-safe nahi`, forYou: "Aapke liye 2 shows",
      watch: "Dekhna shuru karein", noScript: "Is demo mein iski script nahi hai",
      drop: (d, m) => `Drop ${d.n}: episode ${d.episodes.join(" aur ")}, ${m} min`, epN: (n) => `Episode ${n}`,
      cliff: "Cliffhanger score", model: "Model", rules: "Rules", tbc: "To be continued", tbcS: "Agla drop kal",
      teaser: "Agli baar", found: (e) => `Yeh line episode ${e} ke end mein hai`, listen: "Suniye",
      next: (l) => `Agla: Drop ${l}`, unlocks: (w) => `${w} khulega`, ready: "Taiyaar", remind: "Yaad dilayenge", opened: (l) => `Drop ${l} khul gaya`,
      play: "Abhi dekhein", ladder: "Roz aaoge, kam intezaar", rung: (a, b) => `Streak ${a}${b == null ? "+" : ` se ${b}`}`, hrs: (h) => `${h} ghante`,
      perUnlock: (n) => (n > 1 ? `Har unlock pe ${n} drops` : "Har unlock pe 1 drop"), now: "abhi", done: "Saare drops khul gaye", days: "din",
    },
    english: {
      tagline: "One drop a day. At your hour.", start: "Start",
      hello: "Hi! Five quick questions, then two shows picked for you.", type: "Type here", pick: "Pick an answer", sample: "Sample viewer's answer",
      reading: "Reading your answers", about: "About you", fSlots: "Free at", fLikes: "Likes", fDis: "Never", fWith: "Watches", fMin: "Daily time",
      min: (m) => `${m} min a day`, with: { family: "With family", partner: "With partner", alone: "Alone", friends: "With friends" },
      tier: { tier1: "Metro", tier2: "Tier 2 city", tier3: "Small town" },
      shield: "Only family-safe shows", shieldS: "Watches with family",
      all: (n) => `From ${n} shows`, out: (n) => `${n} shows removed: not family-safe`, forYou: "Two shows for you",
      watch: "Start watching", noScript: "No scripts for this one in the demo",
      drop: (d, m) => `Drop ${d.n}: episodes ${d.episodes.join(" and ")}, ${m} min`, epN: (n) => `Episode ${n}`,
      cliff: "Cliffhanger score", model: "Model", rules: "Rules", tbc: "To be continued", tbcS: "Next drop soon",
      teaser: "Next time", found: (e) => `Line found in episode ${e}'s ending`, listen: "Listen",
      next: (l) => `Next: Drop ${l}`, unlocks: (w) => `Unlocks ${w.replace(/^(Today|Tomorrow)/, (m) => m.toLowerCase())}`, ready: "Ready", remind: "Reminder", opened: (l) => `Drop ${l} is open`,
      play: "Watch now", ladder: "Come back daily, wait less", rung: (a, b) => `Streak ${a}${b == null ? "+" : ` to ${b}`}`, hrs: (h) => `${h} h`,
      perUnlock: (n) => (n > 1 ? `${n} drops per unlock` : "1 drop per unlock"), now: "now", done: "All drops are open", days: "days",
    },
  };
  // Who the two sample viewers are (from their own first answers in KD.viewers).
  const WHO = {
    hinglish: { long: "a 42 year old homemaker in Kanpur", short: "Homemaker, 42, Kanpur", she: "she", her: "her", lang: "Hinglish" },
    english: { long: "a 63 year old retired teacher in Lucknow", short: "Retired teacher, 63, Lucknow", she: "he", her: "his", lang: "English" },
  };
  // Quick-pick chips for manual mode; the sample viewer's real answer is always first.
  const ALT = {
    hinglish: [["Student hoon", "Job karti hoon"], ["Subah 8 baje", "Raat 9 baje"], ["Romance", "Thriller"], ["Kuch nahi", "Horror nahi"], ["Akele", "Partner ke saath"]],
    english: [["Student", "Working, 28"], ["8 am", "9 pm"], ["Romance", "Thrillers"], ["Nothing", "No horror"], ["Alone", "With family"]],
  };

  // ---------- State ----------
  const S = { lang: "hinglish", tier: "free", mode: "idle", beat: 0, done: false, paused: false, token: 0, elapsed: 0,
    streak: 0, watched: WATCHED, now: WATCHED, opened: 1, deviated: false, busy: false, held: [], jsonOpen: !matchMedia("(max-width: 899px)").matches };
  const V = () => KD.viewers[S.lang];
  const P = () => V().persona;
  const L = () => T[S.lang];
  const DROPS = () => KD.drops[S.lang].drops;
  const W = () => WHO[S.lang];

  // ---------- Time and motion helpers (pause-aware, cancellable) ----------
  class Cancel extends Error {}
  const live = (tk) => { if (tk !== S.token) throw new Cancel(); };
  function wait(ms) {
    const tk = S.token;
    return new Promise((res, rej) => {
      let left = ms, last = performance.now();
      const tick = (now) => {
        if (tk !== S.token) return rej(new Cancel());
        if (!S.paused) left -= now - last;
        last = now;
        if (left <= 0) res(); else requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }
  function tween(ms, fn, ease = (p) => 1 - Math.pow(1 - p, 3), free = false) {
    const tk = S.token;
    return new Promise((res, rej) => {
      let t = 0, last = performance.now();
      const tick = (now) => {
        if (!free && tk !== S.token) return rej(new Cancel());
        if (free || !S.paused) t += now - last;
        last = now;
        const p = RM || ms <= 0 ? 1 : Math.min(1, t / ms);
        fn(ease(p));
        if (p >= 1) res(); else requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }
  const sine = (p) => -(Math.cos(Math.PI * p) - 1) / 2;
  function fx(el, kf, o = {}) {
    if (!el || !el.animate) return null;
    const a = el.animate(kf, { duration: RM ? 0 : (o.d ?? 420), delay: RM ? 0 : (o.delay ?? 0), easing: o.e ?? EASE, fill: o.fill ?? "both", iterations: o.it ?? 1 });
    if (S.paused) { a.pause(); S.held.push(a); }
    return a;
  }
  async function anim(el, kf, o) {
    const tk = S.token, a = fx(el, kf, o);
    if (a) await a.finished.catch(() => {});
    live(tk);
  }
  const quiet = (p) => p && p.catch((e) => { if (!(e instanceof Cancel)) console.error(e); });
  async function typeText(el, text, cps = 40) {
    if (RM) { el.textContent = text; return; }
    const per = Math.max(1, Math.round(cps / 30));
    for (let i = per; i < text.length + per; i += per) { el.textContent = text.slice(0, i); await wait(33); }
  }
  async function reveal(el) {
    const sc = el && el.closest(".scene");
    if (!sc) return;
    const s = sc.getBoundingClientRect(), r = el.getBoundingClientRect(), z = s.height / sc.offsetHeight || 1;
    const pb = parseFloat($("#screen").style.getPropertyValue("--pb")) || 0;
    const low = s.bottom - (pb + 14) * z, high = s.top + 10 * z;
    const dy = r.bottom > low ? (r.bottom - low) / z : r.top < high ? (r.top - high) / z : 0;
    if (Math.abs(dy) < 2) return;
    sc.scrollBy({ top: dy, behavior: RM ? "auto" : "smooth" });
    await wait(RM ? 0 : 420);
  }
  async function tap(el) {
    if (!el) return wait(0);
    await reveal(el);
    const r = document.createElement("span");
    r.className = "ripple";
    r.style.left = "50%"; r.style.top = "50%";
    el.append(r);
    fx(r, [{ transform: "scale(0)", opacity: .35 }, { transform: "scale(4)", opacity: 0 }], { d: 600, fill: "none" });
    fx(el, [{ transform: "scale(1)" }, { transform: "scale(.95)" }, { transform: "scale(1)" }], { d: 320, e: EASE_IO, fill: "none" });
    setTimeout(() => r.remove(), 700);
    return wait(380);
  }

  // ---------- Time labels ----------
  const dayN = (d) => Math.floor(d.getTime() / 864e5);
  const h12 = (d) => { const m = d.getUTCMinutes(); return `${d.getUTCHours() % 12 || 12}${m ? ":" + String(m).padStart(2, "0") : ""}`; };
  const ampm = (d) => (d.getUTCHours() < 12 ? "am" : "pm");
  function when(d, ref = S.now, lang = S.lang) {
    const diff = dayN(d) - dayN(ref), h = d.getUTCHours();
    if (lang === "hinglish") {
      const day = diff === 0 ? "Aaj" : diff === 1 ? "Kal" : diff === 2 ? "Parson" : WD.hinglish[d.getUTCDay()];
      const part = h < 4 ? "raat" : h < 12 ? "subah" : h < 16 ? "dopahar" : h < 19 ? "shaam" : "raat";
      return `${day} ${part} ${h12(d)} baje`;
    }
    const day = diff === 0 ? "Today" : diff === 1 ? "Tomorrow" : WD.english[d.getUTCDay()];
    return `${day}, ${h12(d)} ${ampm(d)}`;
  }
  const lowerDay = (s) => s.replace(/^(Today|Tomorrow|Aaj|Kal|Parson)/, (m) => m.toLowerCase());
  const at = (d, ref = S.now) => lowerDay(when(d, ref, "english")).replace(", ", " at ");
  const clockFull = (d) => `${WDS[S.lang][d.getUTCDay()]} ${d.toLocaleDateString("en-GB", { timeZone: "UTC", day: "numeric", month: "short" })}, ${d.toLocaleTimeString("en-US", { timeZone: "UTC", hour: "numeric", minute: "2-digit" }).toLowerCase()}`;
  const slotLabel = (s) => when(G.at(2026, 11, 9, +s.slice(0, 2), +s.slice(3)), G.at(2026, 11, 9)).replace(/^(Aaj |Today, )/, "");

  // ---------- Posters: authored typographic art, no images ----------
  const PAL = [["#7b1e2e", "#f2a93b"], ["#1e3d3a", "#e8c07a"], ["#8a3b12", "#f6d7a7"], ["#14324f", "#f2a93b"], ["#5c1a3a", "#f4b6c2"], ["#2e3b1f", "#d9c36a"], ["#b23a2b", "#fbe3c4"], ["#3b2416", "#e9a15b"]];
  const MOTIF = [
    (f) => `<path d="M18 140V76a32 32 0 0 1 64 0v64" fill="${f}"/><path d="M31 140V80a19 19 0 0 1 38 0v60" fill="rgba(0,0,0,.42)"/><circle cx="50" cy="40" r="3" fill="${f}"/>`,
    (f) => `<circle cx="50" cy="58" r="27" fill="${f}"/><path d="M0 92h100M0 100h100M0 108h100" stroke="${f}" stroke-width="2.4" opacity=".55"/>`,
    (f) => `<path d="M-10 118L66-10h20L10 118zM24 150L104 22v22L44 150z" fill="${f}" opacity=".85"/>`,
    (f) => [0, 1, 2].map((r) => [0, 1, 2].map((c) => `<path d="M${14 + c * 26} ${58 + r * 30}v-12a9 9 0 0 1 18 0v12z" fill="${f}" opacity="${0.35 + 0.2 * ((r + c) % 3)}"/>`).join("")).join(""),
    (f, b) => `<circle cx="54" cy="54" r="28" fill="${f}"/><circle cx="66" cy="46" r="25" fill="${b}"/>`,
    (f) => `<path d="M0 140L50 60l50 80z" fill="${f}" opacity=".8"/><path d="M20 140L60 80l40 60z" fill="rgba(0,0,0,.3)"/>`,
  ];
  const hash = (s) => { let h = 7; for (const c of s) h = (h * 31 + c.charCodeAt(0)) | 0; return Math.abs(h); };
  const art = (id, seed = id) => {
    const h = hash(seed), [b, f] = PAL[h % PAL.length], m = id === KD.show.id ? 0 : (h >> 3) % MOTIF.length;
    return { b, f, svg: `<svg viewBox="0 0 100 140" preserveAspectRatio="xMidYMid slice" aria-hidden="true">${MOTIF[m](f, b)}</svg>` };
  };
  function poster(s) {
    const a = art(s.id);
    return `<div class="poster" style="--pbg:${a.b};--pfg:${a.f}">${a.svg}<span class="p-pl">${esc(s.platform.replace(" (fictional)", ""))}</span><span class="p-t">${esc(s.title)}</span></div>`;
  }

  // ---------- Hero wall: 30 tiles collapse into the 2 picks ----------
  const PICK_AT = [14, 15];
  function buildWall() {
    const picks = V().match.picks;
    let html = "";
    for (let i = 0; i < 30; i++) {
      const k = PICK_AT.indexOf(i), a = k >= 0 ? art(picks[k].id) : art("tile", "t" + i * 7);
      html += `<div class="tile${k >= 0 ? " is-pick" : ""}" style="--pbg:${a.b};--pfg:${a.f}">${a.svg}<i></i><i></i></div>`;
    }
    $(".tiles").innerHTML = html;
    $(".duo").innerHTML = picks.map(() => '<div class="duo-card"></div>').join("") + '<p class="duo-for"></p>';
    fillDuo();
  }
  function fillDuo() {
    $$(".duo-card").forEach((c, k) => { c.innerHTML = poster(V().match.picks[k]); });
    $(".duo-for").textContent = `Picked for: ${W().short}`;
  }
  async function playWall() {
    const sleep = (ms) => new Promise((r) => setTimeout(r, RM ? 0 : ms));
    const tiles = $$(".tile"), picks = $$(".tile.is-pick"), wall = $(".tiles").getBoundingClientRect();
    tiles.forEach((t, i) => t.animate([{ opacity: 0, transform: "translateY(10px) scale(.96)" }, { opacity: 1, transform: "none" }], { duration: RM ? 0 : 520, delay: RM ? 0 : i * 14, easing: EASE, fill: "backwards" }));
    await sleep(1900);
    const cx = wall.left + wall.width / 2, cy = wall.top + wall.height / 2;
    tiles.filter((t) => !t.classList.contains("is-pick")).forEach((t) => {
      const r = t.getBoundingClientRect(), dx = (cx - r.left - r.width / 2) * .4, dy = (cy - r.top - r.height / 2) * .4;
      t.animate([{ opacity: 1, transform: "none", filter: "blur(0)" }, { opacity: 0, transform: `translate(${dx}px,${dy}px) scale(.55)`, filter: "blur(3px)" }],
        { duration: RM ? 0 : 620, delay: RM ? 0 : Math.max(0, 260 - Math.hypot(dx, dy) * .8), easing: EASE_IN, fill: "forwards" });
    });
    const duo = $(".duo"); duo.classList.add("on");
    $$(".duo-card").forEach((c, k) => {
      const from = picks[k].getBoundingClientRect(), to = c.getBoundingClientRect();
      c.animate([{ transform: `translate(${from.left - to.left}px,${from.top - to.top}px) scale(${from.width / to.width})` },
        { transform: `rotate(${k ? 3 : -3}deg)` }], { duration: RM ? 0 : 1000, delay: RM ? 0 : 280, easing: EASE, fill: "both" });
    });
    picks.forEach((p) => p.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 1, delay: RM ? 0 : 280, fill: "forwards" }));
    $(".duo-for").animate([{ opacity: 0, transform: "translateY(6px)" }, { opacity: 1, transform: "none" }], { duration: RM ? 0 : 500, delay: RM ? 0 : 1100, easing: EASE, fill: "both" });
    const n = $(".wall-n"), l = $(".wall-l");
    await sleep(300);
    tween(900, (p) => { n.textContent = Math.round(30 - 28 * p); }, undefined, true);
    l.textContent = "shows after five questions";
  }

  // ---------- Phone chrome ----------
  function setClock(d) { S.now = d; $("#sb-time").textContent = d.toLocaleTimeString("en-GB", { timeZone: "UTC", hour: "numeric", minute: "2-digit", hour12: true }).replace(/\s?[ap]m$/i, ""); const c = $(".ck-t"); if (c) c.textContent = clockFull(d); }
  function setStreak(n, animate) {
    const el = $("#streak"), b = el.querySelector("b"), old = +b.textContent;
    el.setAttribute("aria-label", `Streak: ${n} ${n === 1 ? "day" : "days"}`);
    el.classList.toggle("lit", n > 0);
    b.textContent = n;
    if (animate && n !== old) {
      const up = n > old;
      fx(b, [{ transform: `translateY(${up ? 10 : -10}px)`, opacity: 0 }, { transform: "none", opacity: 1 }], { d: 420, fill: "none" });
      fx(el.querySelector("svg"), up ? [{ transform: "scale(1)" }, { transform: "scale(1.5) rotate(-8deg)" }, { transform: "scale(1)" }] : [{ opacity: 1 }, { opacity: .3 }, { opacity: 1 }], { d: 620, e: EASE_IO, fill: "none" });
      fx(el, up ? [{ boxShadow: "0 0 0 0 rgba(242,169,59,.6)" }, { boxShadow: "0 0 0 12px rgba(242,169,59,0)" }] : [{ transform: "translateX(0)" }, { transform: "translateX(-4px)" }, { transform: "translateX(4px)" }, { transform: "none" }], { d: 620, fill: "none" });
    }
  }
  function scene(cls, html) {
    const host = $("#scenes");
    $$(".scene", host).forEach((old) => {
      if (old.dataset.leaving) return;
      old.dataset.leaving = "1";
      const a = fx(old, [{ opacity: 1, transform: "none" }, { opacity: 0, transform: "scale(.985)" }], { d: 240, e: EASE_IN, fill: "forwards" });
      if (a) a.finished.then(() => old.remove(), () => old.remove()); else old.remove();
    });
    const el = document.createElement("div");
    el.className = "scene " + cls;
    el.innerHTML = html;
    host.append(el);
    fx(el, [{ opacity: 0, transform: "translateY(14px)" }, { opacity: 1, transform: "none" }], { d: 560, delay: 140, fill: "backwards" });
    return el;
  }
  function notify(title, body) {
    const n = $("#notif");
    n.innerHTML = `<span class="n-ic">${ico("flame")}</span><span class="n-b"><span class="n-top"><span>Kuku Daily</span><span>${L().now}</span></span><span class="n-t" style="display:block">${esc(title)}</span><span class="n-x" style="display:block">${esc(body)}</span></span>`;
    n.classList.add("on");
    return anim(n, [{ transform: "translateY(-150%)" }, { transform: "translateY(6px)", offset: .7 }, { transform: "none" }], { d: 620 });
  }
  function hideNotif(animate) {
    const n = $("#notif");
    if (!n.classList.contains("on")) return;
    n.getAnimations().forEach((a) => a.cancel());
    if (!animate) { n.classList.remove("on"); return; }
    const a = fx(n, [{ transform: "none", opacity: 1 }, { transform: "translateY(-150%)", opacity: .6 }], { d: 380, e: EASE_IN, fill: "forwards" });
    if (a) a.finished.then(() => { n.classList.remove("on"); a.cancel(); }, () => {});
  }

  // ---------- Captions, rail and progress ----------
  const BEATS = [
    { title: "Start here", est: 1 },
    { title: "Five questions in chat", est: 13000 },
    { title: "The AI reads you", est: 9000 },
    { title: "Two shows, not thirty", est: 10500 },
    { title: "Today's drop", est: 21000 },
    { title: "The gate", est: 21000 },
  ];
  function cap(title, text) {
    const h = $("#cap-h"), t = $("#cap-t");
    h.textContent = title; t.innerHTML = text;
    fx($(".cap"), [{ opacity: .2, transform: "translateY(6px)" }, { opacity: 1, transform: "none" }], { d: 420, fill: "none" });
  }
  function renderRail() {
    $("#steps").innerHTML = BEATS.slice(1).map((b, i) => {
      const n = i + 1, cur = n === S.beat, done = n < S.beat || (cur && S.done);
      return `<li><button type="button" data-beat="${n}" class="${done ? "done" : ""}"${cur ? ' aria-current="step"' : ""}><span class="n">${n}</span>${b.title}</button></li>`;
    }).join("");
    $("#mode-note").textContent = S.mode === "auto" ? "Autoplay, about 75 seconds" : S.mode === "manual" ? "Manual: Next moves on" : "";
    const nav = $("#nav"), btsBtn = `<button type="button" class="btn sm bts-open" aria-controls="bts" aria-expanded="false">${ico("layers")}Behind the scenes</button>`;
    if (S.mode === "auto") {
      nav.innerHTML = `<button type="button" class="btn sm primary" data-act="pause" id="pause" aria-pressed="${S.paused}">${S.paused ? ico("play") + "Resume" : ico("pause") + "Pause"}</button><button type="button" class="btn sm" data-act="skip" id="skip">${ico("skip")}Skip</button>${btsBtn}`;
    } else if (S.mode === "ended") {
      nav.innerHTML = `<button type="button" class="btn sm primary" data-act="auto">${ico("replay")}Replay</button><button type="button" class="btn sm" data-act="manual">Try it yourself</button>${btsBtn}`;
    } else if (S.mode === "manual") {
      const nx = S.beat < 5 ? `<span>Next<span class="nx-t">: ${BEATS[S.beat + 1].title}</span></span>` : "<span>How it works</span>";
      nav.innerHTML = `${S.beat > 1 ? `<button type="button" class="btn sm" data-act="prev" id="back" aria-label="Back">${ico("back")}</button>` : ""}<button type="button" class="btn sm primary${S.done ? " nudge" : ""}" data-act="next" id="next">${nx}${ico("next")}</button>${btsBtn}`;
    } else {
      nav.innerHTML = `<button type="button" class="btn sm primary" data-act="auto">${ico("play")}Play the first 3 days</button><button type="button" class="btn sm" data-act="manual">Try it yourself</button>${btsBtn}`;
    }
  }
  let lastT = 0;
  function loop(now) {
    const dt = lastT ? Math.min(100, now - lastT) : 0;
    lastT = now;
    if (S.beat && !S.paused && !S.done) S.elapsed += dt;
    $$(".prog i").forEach((el, i) => {
      const n = i + 1, f = n < S.beat ? 1 : n > S.beat ? 0 : S.done ? 1 : Math.min(.96, S.elapsed / BEATS[n].est);
      el.style.transform = `scaleX(${f})`;
    });
    requestAnimationFrame(loop);
  }

  // ---------- Behind the scenes ----------
  function hl(obj) {
    return JSON.stringify(obj, null, 2).replace(/("(?:\\.|[^"\\])*")(\s*:)?|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|\b(true|false|null)\b/g,
      (m, str, colon, num, lit) => (str ? `<span class="${colon ? "k" : "s"}">${esc(str)}</span>${colon || ""}` : num ? `<span class="n">${num}</span>` : `<span class="b">${lit}</span>`));
  }
  const gcalc = () => {
    const unlock = G.nextUnlock(S.watched, S.tier, S.streak);
    return { unlock, remind: G.reminder(unlock, P().slots), wait: G.waitH(S.tier, S.streak), level: G.level(S.streak) };
  };
  function btsData() {
    const p = P(), v = V(), lang = S.lang, d = DROPS()[0];
    switch (S.beat) {
      case 1: return { ai: "Nothing yet. The five questions are fixed text in the viewer's language.",
        code: "Sends the questions and stores the answers word for word. No forms or dropdowns: the viewer can type anything.",
        label: `questions.${lang} + viewers.${lang}.input`, json: { questions: KD.questions[lang], ...v.input } };
      case 2: return { ai: `One Groq call reads the five answers and returns ${Object.keys(p).length} profile fields, with a one-line summary in ${W().lang}.`,
        code: `Checks slots are real <code>HH:MM</code> times; <code>watch_with: "${esc(p.watch_with)}"</code> sets the family-safe rule <b>${p.watch_with === "family" ? "on" : "off"}</b>, and the model cannot change it.`,
        label: `viewers.${lang}.persona`, json: p };
      case 3: {
        const all = [KD.show, ...KD.catalog], out = all.filter((s) => !s.family_safe);
        return { ai: "Picks two shows from the list it is given and writes one reason for each, in the viewer's language.",
          code: p.watch_with === "family" ? `Family-safe rule on: removes <span class="tip" title="${out.map((s) => esc(s.title)).join(", ")}">${out.length} shows</span>, so picks come from the other ${all.length - out.length}; only scripted shows start drops.`
            : `No family filter (<code>watch_with: "${esc(p.watch_with)}"</code>), so all ${all.length} shows stay in; only scripted shows start drops.`,
          label: `viewers.${lang}.match`, json: v.match };
      }
      case 4: {
        const sc = KD.drops[lang].episode_scores.filter((e) => d.episodes.includes(e.ep)), last = sc[sc.length - 1], ep = foundIn(d);
        return { ai: `Rated each ending 1 to 5 (episode ${last.ep}: ${last.llm}), named the open question and wrote the teaser.`,
          code: `Rule score ${last.rule}, combined <b>0.6 x ${last.llm}/5 + 0.4 x ${last.rule} = ${last.combined}</b>; quote found in episode ${ep}, <code>repaired: ${d.repaired}</code>.`,
          label: `drops.${lang}.drops[0] + episode_scores + episodes[${d.episodes[d.episodes.length - 1] - 1}].tail`,
          json: { drop: d, episode_scores: sc, ending: KD.episodes[d.episodes[d.episodes.length - 1] - 1].tail } };
      }
      case 5: {
        const g = gcalc(), cfg = G.config;
        return { ai: "Nothing: waits, reminders and streaks are code; <code>gates.js</code> ports <code>tools/gates.py</code> and a test checks they match.",
          code: `<code>${S.tier}</code> at streak ${S.streak}: <b>${g.wait} h</b> wait, reminder at the next free slot, streak +1 if back within ${cfg.grace_h} h.`,
          label: "gates + KDGates.simulate(...)", sim: G.simulate(S.tier, p.slots, DROPS().length, 3),
          json: { gates: KD.gates, now: { tier: S.tier, streak: S.streak, watched_at: G.iso(S.watched), next_unlock: G.iso(g.unlock), reminder: G.iso(g.remind) } } };
      }
      default: return { ai: "Two jobs: read the viewer and the scripts.", code: "Everything predictable: family-safe filter, drop sizes, quote checks, timers, streaks.", label: "show", json: KD.show };
    }
  }
  function renderBTS() {
    const x = btsData();
    $("#bts-beat").textContent = S.beat ? `Step ${S.beat}: ${BEATS[S.beat].title}` : "Step by step";
    const sim = x.sim ? `<details open><summary>First 3 days <code>KDGates.simulate</code></summary><table class="sim"><thead><tr><th>Day</th><th>Watched</th><th>Streak</th><th>Wait</th><th>Reminder</th></tr></thead><tbody>${x.sim.map((r) => `<tr><td>${r.session}</td><td>${r.watched_at.slice(5).replace("T", " ")}</td><td>${r.streak}</td><td>${r.wait_h} h</td><td>${r.reminder.slice(5).replace("T", " ")}</td></tr>`).join("")}</tbody></table></details>` : "";
    $("#bts-body").innerHTML = `<section class="bt ai"><h3>What the AI did</h3><p>${x.ai}</p></section><section class="bt cd"><h3>What code did</h3><p>${x.code}</p></section>${sim}<details class="raw"${S.jsonOpen ? " open" : ""}><summary>Raw output <code>${esc(x.label)}</code></summary><pre><code>${hl(x.json)}</code></pre></details>`;
    $("#bts-body .raw").addEventListener("toggle", (e) => { S.jsonOpen = e.target.open; });
  }

  // ---------- Beat runner (shared by autoplay and manual) ----------
  async function go(n) {
    S.token++;
    const tk = S.token;
    if (S.paused) setPaused(false);
    S.beat = n; S.elapsed = 0; S.done = false; S.busy = false;
    if (window.speechSynthesis) speechSynthesis.cancel();
    hideNotif(false);
    $("#screen").classList.toggle("cine", n === 4);
    renderRail(); renderBTS();
    try {
      await RUN[n]();
      live(tk);
      S.done = true; renderRail();
      if (S.mode === "auto") {
        await wait(1100);
        if (n < 5) go(n + 1); else endAuto();
      }
    } catch (e) { if (!(e instanceof Cancel)) console.error(e); }
  }
  function startAuto() {
    S.mode = "auto"; S.tier = "free";
    $("#demo").scrollIntoView({ behavior: RM ? "auto" : "smooth" });
    go(1);
  }
  function startManual(n = 1) {
    S.mode = "manual";
    if (n === 1) $("#demo").scrollIntoView({ behavior: RM ? "auto" : "smooth" });
    go(n);
  }
  function takeOver() { if (S.mode === "auto") { S.token++; S.mode = "manual"; S.done = true; if (S.paused) setPaused(false); renderRail(); } }
  function endAuto() {
    S.mode = "ended"; renderRail();
    cap("That was the loop", `Five questions, two shows, a 4 minute drop and a reminder at ${W().her} hour; <b>switch language</b> to meet the other viewer.`);
  }
  function setPaused(p) {
    S.paused = p;
    if (p) {
      S.held = document.getAnimations().filter((a) => a.playState === "running");
      S.held.forEach((a) => a.pause());
      if (window.speechSynthesis) speechSynthesis.pause();
    } else {
      S.held.forEach((a) => { if (a.playState === "paused") a.play(); });
      S.held = [];
      if (window.speechSynthesis) speechSynthesis.resume();
    }
    if (S.mode === "auto") renderRail();
  }

  // ---------- Beat 0: splash ----------
  function splash() {
    $("#screen").classList.remove("cine");
    const picks = V().match.picks;
    const el = scene("s-splash", `<p class="splash-mark">Kuku <span>Daily</span></p><p class="splash-t">${L().tagline}</p><div class="splash-art">${picks.map((p) => `<div>${poster(p)}</div>`).join("")}</div><button type="button" class="pbtn" data-act="manual">${L().start}${ico("next")}</button>`);
    cap(BEATS[0].title, "Watch one viewer's first 3 days in <b>75 seconds</b>, or step through yourself.");
    return el;
  }

  // ---------- Beat 1: onboarding chat ----------
  async function beatChat() {
    setStreak(0, false); setClock(WATCHED); S.deviated = false;
    const qs = KD.questions[S.lang], ans = V().input.answers, auto = S.mode === "auto";
    cap(BEATS[1].title, `Meet <b>${W().long}</b>: ${auto ? `five free-text questions in ${W().lang}, while Kuku TV asks only the language.` : `tap a chip to answer; the first is ${W().her} real one.`}`);
    const el = scene("s-chat", `<div class="chat" role="log" aria-label="Onboarding chat"></div>${auto ? `<div class="composer" aria-hidden="true"><span class="field"><span class="typed"></span><span class="ph">${L().type}</span><span class="caret"></span></span><span class="send">${ico("next")}</span></div>` : ""}<div class="chips" role="group" aria-label="${L().pick}"></div>`);
    const log = $(".chat", el);
    await bot(log, L().hello, true);
    for (let i = 0; i < qs.length; i++) {
      await bot(log, qs[i]);
      let text = ans[i];
      if (auto) {
        const typed = $(".typed", el);
        await wait(150);
        await typeText(typed, text, 60);
        await wait(120);
        await tap($(".send", el));
        typed.textContent = "";
      } else {
        text = await choose(el, i);
        if (text !== ans[i]) S.deviated = true;
      }
      bubble(log, "me", esc(text));
      await wait(auto ? 300 : 250);
    }
  }
  function bubble(log, who, html) {
    const b = document.createElement("div");
    b.className = "bub " + who;
    b.innerHTML = html;
    log.append(b);
    fx(b, [{ opacity: 0, transform: `translate(${who === "me" ? 12 : -12}px, 10px) scale(.96)` }, { opacity: 1, transform: "none" }], { d: 420, fill: "none" });
    log.scrollTop = log.scrollHeight;
    return b;
  }
  async function bot(log, text, first) {
    if (first) { bubble(log, "bot first", esc(text)); await wait(500); return; }
    const b = bubble(log, "bot", '<span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>');
    await wait(S.mode === "auto" ? 520 : 450);
    b.textContent = text;
    log.scrollTop = log.scrollHeight;
    await wait(150);
  }
  function choose(el, i) {
    const box = $(".chips", el), ans = V().input.answers[i], opts = [ans, ...ALT[S.lang][i]];
    box.innerHTML = opts.map((o, k) => `<button type="button" class="chip${k ? "" : " sample"}" data-k="${k}">${k ? "" : `<span class="tag">${L().sample}</span>`}${esc(o)}</button>`).join("");
    $$(".chip", box).forEach((c, k) => fx(c, [{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: "none" }], { d: 360, delay: k * 50, fill: "backwards" }));
    $(".chat", el).scrollTop = 1e6;
    return new Promise((res) => {
      const h = (e) => {
        const c = e.target.closest(".chip");
        if (!c) return;
        box.removeEventListener("click", h);
        box.innerHTML = "";
        res(opts[+c.dataset.k]);
      };
      box.addEventListener("click", h);
    });
  }

  // ---------- Beat 2: the AI reads you ----------
  async function beatProfile() {
    const p = P(), l = L(), fam = p.watch_with === "family";
    cap(BEATS[2].title, S.deviated ? "You changed some answers, but this is <b>the real model output</b> for the sample ones; the live lab runs yours." : `<b>One model call</b> turns five answers into a profile: when ${W().she} is free, what ${W().she} likes, who ${W().she} watches with.`);
    const pills = (a) => a.map((x) => `<span class="pill">${esc(x)}</span>`).join("");
    const age = p.age_band.replace("-", " to ");
    const el = scene("s-prof", `
      <div class="reading">${ico("spark")}<span>${l.reading}</span><span class="bar"><i></i></span></div>
      <article class="idcard" aria-label="${l.about}">
        <header><p class="id-k">${l.about}</p><h3>${esc(p.who)}</h3><p class="id-meta">${esc(age)} · ${esc(l.tier[p.city_tier] || p.city_tier)}</p></header>
        <dl>
          <div class="row"><dt>${l.fSlots}</dt><dd>${pills(p.slots.map(slotLabel))}</dd></div>
          <div class="row"><dt>${l.fLikes}</dt><dd>${pills(p.likes)}</dd></div>
          ${p.dislikes.length ? `<div class="row"><dt>${l.fDis}</dt><dd>${pills(p.dislikes)}</dd></div>` : ""}
          <div class="row"><dt>${l.fWith}</dt><dd>${pills([l.with[p.watch_with] || p.watch_with])}</dd></div>
          <div class="row"><dt>${l.fMin}</dt><dd>${pills([l.min(p.minutes_per_day)])}</dd></div>
        </dl>
        <p class="summary" lang="${S.lang === "english" ? "en" : "hi-Latn"}"></p>
      </article>
      ${fam ? `<div class="shield" role="note">${ico("shield")}<span>${l.shield}<small>${l.shieldS}</small></span></div>` : ""}`);
    const card = $(".idcard", el), rows = [$("header", card), ...$$(".row", card)], shield = $(".shield", el);
    [card, ...rows].forEach((r) => { r.style.opacity = 0; });
    if (shield) shield.style.opacity = 0;
    fx($(".reading .bar i", el), [{ transform: "translateX(-100%)" }, { transform: "translateX(250%)" }], { d: 900, it: 2, e: EASE_IO, fill: "none" });
    await wait(1200);
    await anim($(".reading", el), [{ opacity: 1 }, { opacity: .45 }], { d: 300, fill: "forwards" });
    card.style.opacity = "";
    fx(card, [{ opacity: 0, transform: "translateY(16px) scale(.97)" }, { opacity: 1, transform: "none" }], { d: 520 });
    for (const r of rows) {
      r.style.opacity = "";
      fx(r, [{ opacity: 0, transform: "translateX(-26px)", filter: "blur(6px)" }, { opacity: 1, transform: "none", filter: "blur(0)" }], { d: 520 });
      await wait(220);
    }
    await wait(150);
    await typeText($(".summary", el), p.summary, 90);
    if (shield) {
      await wait(300);
      shield.style.opacity = "";
      await reveal(shield);
      await anim(shield, [{ opacity: 0, transform: "scale(1.5) rotate(-6deg)" }, { opacity: 1, transform: "scale(.96) rotate(-2deg)", offset: .7 }, { opacity: 1, transform: "rotate(-2deg)" }], { d: 560, e: EASE_IO });
      cap(BEATS[2].title, `${W().she[0].toUpperCase() + W().she.slice(1)} watches with family, so <b>code</b> turns on a family-safe rule the model cannot turn off.`);
    }
    await wait(1700);
  }

  // ---------- Beat 3: two shows ----------
  async function beatShows() {
    const l = L(), picks = V().match.picks, fam = P().watch_with === "family", all = [KD.show, ...KD.catalog], auto = S.mode === "auto";
    const ids = picks.map((p) => p.id), outN = all.filter((s) => !s.family_safe).length;
    cap(BEATS[3].title, `<b>${all.length} shows</b> in the demo catalog: ${KD.catalog.length} public ones and one fictional demo show with scripts.`);
    const el = scene("s-shows", `<p class="sh-h">${l.all(all.length)}</p><p class="sh-s" aria-live="polite"></p>
      <div class="minis">${all.map((s) => `<div class="mini" data-id="${s.id}" data-safe="${s.family_safe}">${poster(s)}<span class="no">${ico("shieldx")}</span></div>`).join("")}</div>
      <div class="picks" hidden>${picks.map((p) => `<article class="pick" data-id="${p.id}">${poster(p)}<div><h4>${esc(p.title)}</h4><p class="pick-pl">${esc(p.platform)}</p><p class="tags">${p.tags.slice(0, 3).map((t) => `<span>${esc(t)}</span>`).join("")}</p><p class="reason"></p>${p.has_scripts ? `<button type="button" class="pbtn" data-act="watch">${ico("play")}${l.watch}</button>` : `<p class="na">${l.noScript}</p>`}</div></article>`).join("")}</div>`);
    const minis = $$(".mini", el);
    minis.forEach((m, i) => fx(m, [{ opacity: 0, transform: "translateY(12px) scale(.94)" }, { opacity: 1, transform: "none" }], { d: 460, delay: i * 35, fill: "backwards" }));
    await wait(1100);
    if (fam) {
      $(".sh-s", el).textContent = l.out(outN);
      minis.filter((m) => m.dataset.safe === "false").forEach((m) => { m.classList.add("out"); fx(m, [{ opacity: 1, filter: "grayscale(0)" }, { opacity: .35, filter: "grayscale(1)" }], { d: 500, fill: "forwards" }); });
      cap(BEATS[3].title, `<b>Code</b> removes the ${outN} shows not marked family-safe, so the model cannot pick them.`);
      await wait(1700);
    }
    minis.forEach((m) => { if (ids.includes(m.dataset.id)) fx(m.querySelector(".poster"), [{ boxShadow: "0 0 0 0 rgba(242,169,59,0)" }, { boxShadow: "0 0 0 3px rgba(242,169,59,1)" }], { d: 400, fill: "forwards" }); });
    await wait(500);
    const outs = minis.filter((m) => !ids.includes(m.dataset.id));
    outs.forEach((m, i) => fx(m, [{ opacity: getComputedStyle(m).opacity, transform: "none" }, { opacity: 0, transform: "scale(.82)" }], { d: 420, delay: i * 25, e: EASE_IN, fill: "forwards" }));
    await wait(700);
    $(".sh-h", el).textContent = l.forYou; $(".sh-s", el).textContent = "";
    await anim($(".minis", el), [{ opacity: 1 }, { opacity: 0, transform: "scale(.96)" }], { d: 220, e: EASE_IN, fill: "forwards" });
    $(".minis", el).hidden = true;
    const box = $(".picks", el); box.hidden = false;
    const cards = $$(".pick", box);
    cards.forEach((c, i) => fx(c, [{ opacity: 0, transform: "translateY(24px) scale(.96)" }, { opacity: 1, transform: "none" }], { d: 600, delay: i * 160, fill: "backwards" }));
    cap(BEATS[3].title, `The model picks two with reasons in ${W().lang}; only <b>The Lost Haveli</b> has scripts here, so start there.`);
    await wait(500);
    await Promise.all(cards.map((c, i) => typeText($(".reason", c), picks[i].reason, 90)));
    if (auto) {
      await wait(1500);
      await tap($('[data-act="watch"]', el));
    } else await wait(300);
  }

  // ---------- Beat 4: today's drop, cinematic script player ----------
  const HAVELI = `<svg viewBox="0 0 390 844" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <defs><radialGradient id="lamp" cx="50%" cy="46%" r="40%"><stop offset="0" stop-color="#f2a93b" stop-opacity=".75"/><stop offset=".45" stop-color="#b8541f" stop-opacity=".28"/><stop offset="1" stop-color="#170d18" stop-opacity="0"/></radialGradient>
    <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b0e16"/><stop offset="1" stop-color="#0a0508"/></linearGradient>
    <filter id="soft"><feGaussianBlur stdDeviation="14"/></filter></defs>
    <rect width="390" height="844" fill="url(#wall)"/>
    <ellipse cx="195" cy="390" rx="210" ry="260" fill="url(#lamp)"/>
    <path d="M120 640V330a75 75 0 0 1 150 0v310z" fill="#2a120f" opacity=".9"/>
    <path d="M136 640V336a59 59 0 0 1 118 0v304z" fill="#f2a93b" opacity=".22" filter="url(#soft)"/>
    <path d="M150 640V350a45 45 0 0 1 90 0v290z" fill="#0b0507"/>
    <path d="M168 640v-120h54v120z" fill="#f6c27a" opacity=".1"/>
    <g fill="#0d0609"><rect x="40" y="250" width="34" height="420"/><rect x="316" y="250" width="34" height="420"/><rect x="30" y="236" width="54" height="16"/><rect x="306" y="236" width="54" height="16"/></g>
    <g fill="#f2a93b" opacity=".18">${[0, 1, 2, 3, 4].map((i) => `<circle cx="${133 + i * 31}" cy="268" r="3"/>`).join("")}</g>
    <path d="M195 120v120" stroke="#3a2416" stroke-width="2"/><circle cx="195" cy="250" r="9" fill="#ffc56a"/><circle cx="195" cy="250" r="40" fill="#f2a93b" opacity=".2" filter="url(#soft)"/>
    <ellipse cx="195" cy="660" rx="200" ry="40" fill="#f2a93b" opacity=".08" filter="url(#soft)"/>
    <rect y="640" width="390" height="204" fill="#070406"/>
  </svg>`;
  const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
  function foundIn(d) {
    for (const e of d.episodes) if (KD.episodes[e - 1].tail.some((t) => t.text.includes(d.quoted_line))) return e;
    return d.episodes[d.episodes.length - 1];
  }
  function voice() {
    if (!window.speechSynthesis) return null;
    const vs = speechSynthesis.getVoices();
    return S.lang === "hinglish" ? vs.find((v) => /^hi[-_]IN/i.test(v.lang)) : vs.find((v) => /^en[-_]IN/i.test(v.lang)) || vs.find((v) => /^en/i.test(v.lang));
  }
  async function beatDrop() {
    const l = L(), d = DROPS()[0], lastN = d.episodes[d.episodes.length - 1], ep = KD.episodes[lastN - 1], mins = Math.round(d.seconds / 60), epF = foundIn(d);
    const firstLen = KD.episodes[d.episodes[0] - 1].seconds;
    cap(BEATS[4].title, `<b>Drop 1</b> packs episodes ${d.episodes.join(" and ")} into about ${mins} minutes and stops on a cliffhanger.`);
    const [tl1, tl2] = d.teaser.split("\n");
    const q = esc(tl2 || ""), ql = esc(d.quoted_line), qHtml = q.includes(ql) ? q.replace(ql, `<mark>${ql}</mark>`) : q;
    const el = scene("s-drop", `
      <div class="film">
        <div class="bg">${HAVELI}</div><div class="grain"></div><div class="vig"></div><div class="flash"></div>
        <div class="tcard"><p class="tc-show">${esc(KD.show.title)}</p><p class="tc-drop">${esc(l.drop(d, mins))}</p>
          <div class="eps">${d.episodes.map((e) => `<span style="flex:${KD.episodes[e - 1].seconds}"><i></i></span>`).join("")}</div>
          <div class="eps-l">${d.episodes.map((e) => `<span>${l.epN(e)}</span>`).join("")}</div></div>
        <div class="hud"><span class="live">${esc(l.epN(lastN))}</span><span class="tc">0:00 / ${mmss(ep.seconds)}</span></div>
        <div class="subs"></div>
        <div class="meter" role="group" aria-label="${l.cliff}"><div class="m-top"><span>${l.cliff}</span><b class="m-v">0.00</b></div><div class="m-bar"><i></i></div>
          <div class="m-rows"><span class="ai">${l.model}<b>${d.llm_score}/5</b></span><span class="cd">${l.rules}<b>${d.rule_score.toFixed(2)}</b></span></div></div>
        <p class="tbc">${l.tbc}<small>${l.tbcS}</small></p>
      </div>
      <article class="teaser" aria-label="${l.teaser}">
        <p class="t-k">${l.teaser}</p><p class="t-1">${esc(tl1)}</p><blockquote class="t-q">${qHtml}</blockquote>
        <div class="t-row"><span class="badge">${ico("check")}${esc(l.found(epF))}</span><button type="button" class="pbtn listen" data-act="listen" hidden>${ico("speaker")}${l.listen}</button></div>
      </article>`);
    const tcEl = $(".tc", el), eps = $$(".eps i", el), subs = $(".subs", el);
    fx($(".tc-show", el), [{ opacity: 0, transform: "translateY(18px)", filter: "blur(8px)" }, { opacity: 1, transform: "none", filter: "blur(0)" }], { d: 900, delay: 200 });
    fx($(".tc-drop", el), [{ opacity: 0 }, { opacity: 1 }], { d: 600, delay: 600 });
    await wait(1400);
    // Play through: episode 1 completes, episode 2 scrubs to the scored ending.
    const endAt = ep.tail[0].start / ep.seconds;
    await tween(1100, (p) => {
      const t = p * (firstLen + ep.tail[0].start);
      eps[0].style.transform = `scaleX(${Math.min(1, t / firstLen)})`;
      if (eps[1]) eps[1].style.transform = `scaleX(${Math.max(0, Math.min(endAt, (t - firstLen) / ep.seconds))})`;
    }, sine);
    cap(BEATS[4].title, `Jump to the ending: <b>the last 20 seconds</b> of episode ${lastN}, the exact lines the model scored.`);
    await anim($(".tcard", el), [{ opacity: 1 }, { opacity: 0, transform: "translateY(-10px)" }], { d: 360, e: EASE_IN, fill: "forwards" });
    fx($(".hud", el), [{ opacity: 0 }, { opacity: 1 }], { d: 400, fill: "forwards" });
    for (const ln of ep.tail) {
      const dur = Math.min(2800, Math.max(1700, (ln.end - ln.start) * 340));
      const prev = subs.firstElementChild;
      if (prev) { await anim(prev, [{ opacity: 1 }, { opacity: 0, transform: "translateY(-6px)" }], { d: 220, e: EASE_IN, fill: "forwards" }); prev.remove(); }
      const s = document.createElement("div");
      s.className = "sub";
      s.innerHTML = ln.type === "dialogue" ? `<p class="sub-who">${esc(ln.speaker || "")}${ln.cue ? `<span>${esc(ln.cue)}</span>` : ""}</p><p class="sub-line"></p>`
        : ln.type === "sound_fx" ? `<p class="sub-fx">${ico("wave")}<span class="sub-line-fx"></span></p>` : `<p class="sub-act"><span class="sub-tag">ACTION</span><span class="sub-line-a"></span></p>`;
      subs.append(s);
      fx(s, [{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: "none" }], { d: 300 });
      quiet(tween(dur, (p) => { tcEl.textContent = `${mmss(ln.start + (ln.end - ln.start) * p)} / ${mmss(ep.seconds)}`; }, (p) => p));
      if (ln.type === "sound_fx") fx($(".vig", el), [{ opacity: 1 }, { opacity: .55 }, { opacity: 1 }, { opacity: .6 }, { opacity: 1 }], { d: 1400, e: EASE_IO, fill: "none" });
      const target = s.querySelector(".sub-line, .sub-line-fx, .sub-line-a");
      await Promise.all([typeText(target, unq(ln.text), 36), wait(dur)]);
    }
    // Cliffhanger meter
    const meter = $(".meter", el);
    await anim(meter, [{ opacity: 0, transform: "translateY(-12px)" }, { opacity: 1, transform: "none" }], { d: 480 });
    fx($(".m-bar i", el), [{ transform: "scaleX(0)" }, { transform: `scaleX(${d.cliff_score})` }], { d: 1400 });
    await tween(1400, (p) => { $(".m-v", el).textContent = (d.cliff_score * p).toFixed(2); });
    cap(BEATS[4].title, `<b>Cliffhanger score ${d.cliff_score}</b>: model ${d.llm_score} of 5, script rules ${d.rule_score.toFixed(2)}, and code cuts drops where it runs high.`);
    await wait(1900);
    // Freeze frame
    const film = $(".film", el), bg = $(".bg", el);
    bg.getAnimations().forEach((a) => a.pause());
    fx($(".flash", el), [{ opacity: 0 }, { opacity: .35 }, { opacity: 0 }], { d: 420, e: EASE_IO, fill: "none" });
    fx(bg, [{ filter: "saturate(1) brightness(1)" }, { filter: "saturate(0) contrast(1.15) brightness(.85)" }], { d: 600, fill: "forwards" });
    fx(subs, [{ opacity: 1 }, { opacity: .25 }], { d: 500, fill: "forwards" });
    fx(meter, [{ opacity: 1 }, { opacity: 0 }], { d: 400, fill: "forwards" });
    await anim($(".tbc", el), [{ opacity: 0, transform: "scale(1.12)", filter: "blur(8px)" }, { opacity: 1, transform: "none", filter: "blur(0)" }], { d: 800, delay: 150 });
    film.dataset.frozen = "1";
    await wait(1000);
    // Teaser with the grounded quote
    const teaser = $(".teaser", el);
    await anim(teaser, [{ transform: "translateY(105%)" }, { transform: "none" }], { d: 650 });
    fx($(".t-q mark", el), [{ textDecorationColor: "rgba(242,169,59,0)" }, { textDecorationColor: "rgba(242,169,59,1)" }], { d: 700, delay: 300 });
    fx($(".badge", el), [{ opacity: 0, transform: "scale(.8)" }, { opacity: 1, transform: "none" }], { d: 420, delay: 500 });
    syncListen();
    cap(BEATS[4].title, `The model's teaser quotes one line, and <b>code</b> found it in episode ${epF}'s ending; this one ${d.repaired ? "needed a repair" : "passed as written"}.`);
    await wait(2600);
  }
  function syncListen() {
    const b = $('[data-act="listen"]');
    if (b) b.hidden = !voice();
  }
  function listen() {
    const d = DROPS()[0], v = voice();
    if (!v) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(d.teaser.split("\n").map(unq).join(". "));
    u.voice = v; u.lang = v.lang; u.rate = .95;
    speechSynthesis.speak(u);
  }

  // ---------- Beat 5: the gate ----------
  function nextDrops() {
    const total = DROPS().length, per = G.config.tiers[S.tier].drops_per_unlock, out = [];
    for (let k = S.opened + 1; k <= Math.min(total, S.opened + per); k++) out.push(k);
    return out;
  }
  const joinN = (a) => a.join(S.lang === "hinglish" ? " aur " : " and ");
  function gateHTML() {
    const l = L(), cfg = G.config;
    const rungs = cfg.levels.map((from, i) => `<li class="rung" data-l="${i}"><span class="rung-b" style="--h:${40 + i * 30}%">${l.hrs(cfg.tiers[S.tier].waits_h[i])}</span><span class="rung-l">${l.rung(from, cfg.levels[i + 1] != null ? cfg.levels[i + 1] - 1 : null)}</span></li>`).join("");
    return `<div class="simclock">${ico("clock")}<span class="ck-t">${clockFull(S.now)}</span></div>
      <article class="lock" aria-live="polite">
        <div class="ring"><svg viewBox="0 0 120 120" aria-hidden="true"><circle class="r-bg" cx="60" cy="60" r="52"/><circle class="r-fg" cx="60" cy="60" r="52" stroke-dasharray="326.73" stroke-dashoffset="0"/></svg><span class="ring-c"><span class="ring-ic">${ico("lock")}</span><span class="ring-t"></span></span></div>
        <div><p class="lock-k">${esc(KD.show.title)}</p><h3 class="lock-h"></h3><p class="lock-w"></p></div>
        <p class="remind">${ico("bell")}<span>${l.remind}: <b class="rm-t"></b></span></p>
      </article>
      <section class="ladder"><h4>${l.ladder}</h4><p class="tierline"></p><ol class="rungs">${rungs}</ol></section>
      <div class="demo" role="group" aria-label="Demo controls">
        <p class="demo-h">DEMO CONTROLS</p>
        <button type="button" class="dbtn main" data-act="ff">${ico("fwd")}Fast-forward to my reminder</button>
        <div class="demo-row"><button type="button" class="dbtn" data-act="s7">${ico("flame")}Give me a 7-day streak</button><button type="button" class="dbtn" data-act="skip2">Skip 2 days</button></div>
        <div class="seg tier" role="group" aria-label="Plan"><button type="button" data-tier="free" aria-pressed="${S.tier === "free"}">Free</button><button type="button" data-tier="subscriber" aria-pressed="${S.tier === "subscriber"}">Subscriber</button></div>
      </div>`;
  }
  function paintRing(frac, label, icon) {
    const fg = $(".r-fg"), t = $(".ring-t"), ic = $(".ring-ic");
    if (!fg) return;
    fg.setAttribute("stroke-dashoffset", (326.73 * (1 - Math.max(0, Math.min(1, frac)))).toFixed(2));
    t.textContent = label;
    if (icon && ic.dataset.i !== icon) { ic.dataset.i = icon; ic.innerHTML = ico(icon); }
  }
  const left = (ms) => { const m = Math.max(0, Math.round(ms / 6e4)); return `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, "0")}m`; };
  function renderGate(animateRing) {
    const l = L(), g = gcalc(), nx = nextDrops(), cfg = G.config;
    const h = $(".lock-h");
    if (!h) return;
    if (!nx.length) { h.textContent = l.done; $(".lock-w").textContent = ""; }
    else { h.textContent = l.next(joinN(nx)); $(".lock-w").textContent = l.unlocks(when(g.unlock)); }
    $(".rm-t").textContent = when(g.remind);
    $(".tierline").textContent = `${S.tier === "free" ? "Free" : "Subscriber"}: ${l.perUnlock(cfg.tiers[S.tier].drops_per_unlock)}`;
    $$(".rung").forEach((r, i) => { r.classList.toggle("on", i === g.level); r.querySelector(".rung-b").textContent = l.hrs(cfg.tiers[S.tier].waits_h[i]); });
    $$(".tier button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.tier === S.tier)));
    const ffb = $('[data-act="ff"]');
    if (ffb) ffb.disabled = S.busy || !nx.length;
    $$('.demo [data-act="s7"], .demo [data-act="skip2"], .tier button').forEach((b) => { b.disabled = S.busy; });
    const total = g.wait * 3600e3, rem = g.unlock - S.now;
    if (animateRing) quiet(tween(800, (p) => paintRing(p * rem / total, left(rem * p), "lock")));
    else paintRing(rem / total, rem > 0 ? left(rem) : l.ready, rem > 0 ? "lock" : "unlock");
    setClock(S.now);
    renderBTS();
  }
  async function beatGate() {
    S.streak = 0; S.watched = WATCHED; S.now = WATCHED; S.opened = 1;
    setStreak(0, false);
    const el = scene("s-gate", gateHTML());
    renderGate(true);
    const g = gcalc();
    cap(BEATS[5].title, `<b>Drop 2</b> unlocks after ${g.wait} hours, ${at(g.unlock)}, with a reminder at ${W().her} next free slot, ${at(g.remind)}.`);
    $$(".lock, .ladder, .demo", el).forEach((c, i) => fx(c, [{ opacity: 0, transform: "translateY(16px)" }, { opacity: 1, transform: "none" }], { d: 560, delay: 150 + i * 110, fill: "backwards" }));
    await wait(2800);
    if (S.mode !== "auto") return;
    await tap($('[data-act="ff"]')); await ff();
    await wait(1000);
    await tap($('[data-act="s7"]')); await streak7();
    await wait(2500);
    await tap($('[data-act="skip2"]')); await skip2();
    await wait(2700);
    await tap($('.tier [data-tier="subscriber"]')); await setTier("subscriber");
    await wait(2400);
  }
  function busy(b) { S.busy = b; renderGate(false); }
  async function ff() {
    if (!nextDrops().length) return;
    const l = L(), g = gcalc(), from = S.now, total = g.wait * 3600e3, nx = nextDrops();
    busy(true);
    cap("Fast-forward", `<b>Drop ${joinN(nx)}</b> opens ${at(g.unlock, from)}; ${W().her} phone buzzes ${at(g.remind, from)} with ${S.lang === "hinglish" ? "the teaser's first line" : "the open question"}.`);
    const hands = $$(".simclock .hh, .simclock .mh");
    hands.forEach((h, i) => fx(h, [{ transform: "rotate(0)" }, { transform: "rotate(360deg)" }], { d: i ? 500 : 1500, it: Infinity, e: "linear", fill: "none" }));
    let unlocked = false;
    await tween(2000, (p) => {
      const t = new Date(from.getTime() + (g.remind - from) * p);
      setClock(t);
      const rem = g.unlock - t;
      if (rem > 0) paintRing(rem / total, left(rem), "lock");
      else {
        paintRing(0, l.ready, "unlock");
        if (!unlocked) { unlocked = true; $(".lock-w").textContent = l.ready; fx($(".ring"), [{ transform: "scale(1)" }, { transform: "scale(1.1)" }, { transform: "scale(1)" }], { d: 500, fill: "none" }); }
      }
    }, sine);
    hands.forEach((h) => h.getAnimations().forEach((a) => a.cancel()));
    const prev = DROPS()[S.opened - 1];
    await notify(`${KD.show.title}: ${l.opened(joinN(nx))}`, S.lang === "hinglish" ? prev.teaser.split("\n")[0] : prev.open_question);
    await wait(1200);
    await tap($("#notif"));
    hideNotif(true);
    const ns = G.updateStreak(S.streak, g.unlock, g.remind);
    S.opened = nx[nx.length - 1]; S.watched = g.remind; S.streak = ns;
    $(".lock-h").textContent = l.opened(joinN(nx));
    $(".lock-w").innerHTML = `<span class="pbtn" aria-hidden="true">${ico("play")}${l.play}</span>`;
    fx($(".lock"), [{ transform: "scale(.97)" }, { transform: "none" }], { d: 500, fill: "none" });
    setStreak(ns, true);
    cap("Back on time", `${W().she[0].toUpperCase() + W().she.slice(1)} came back within ${G.config.grace_h} hours of the unlock: streak <b>0 to ${ns}</b>, and day 2 starts with drop ${joinN(nx)}.`);
    await wait(900);
    S.busy = false;
    renderGate(true);
  }
  async function streak7() {
    busy(true);
    const before = gcalc().wait;
    S.streak = 7; S.now = S.watched;
    setStreak(7, true);
    renderGate(true);
    const g = gcalc();
    fx($(".rung.on .rung-b"), [{ transform: "scaleY(.6)", transformOrigin: "50% 100%" }, { transform: "none", transformOrigin: "50% 100%" }], { d: 600, fill: "none" });
    cap("A 7-day streak", `Seven straight days cut ${W().her} wait from ${before} to <b>${g.wait} hours</b>; the next drop is ready ${at(g.unlock)}.`);
    await wait(400);
    S.busy = false; renderGate(false);
  }
  async function skip2() {
    busy(true);
    const g = gcalc(), back = G.addH(g.remind, 48), from = S.streak, ns = G.updateStreak(S.streak, g.unlock, back);
    await tween(1500, (p) => setClock(new Date(S.now.getTime() + (back - S.now) * p)), sine);
    S.watched = back; S.now = back; S.streak = ns;
    setStreak(ns, true);
    renderGate(true);
    cap("Skip 2 days", G.level(from) > 0
      ? `Two missed days drop the streak one level, <b>${from} to ${ns}</b>${ns > 0 ? ", not to zero" : ""}, and the wait returns to ${G.waitH(S.tier, ns)} hours.`
      : `Two missed days at streak ${from} leave it at <b>${ns}</b>, already the bottom rung, so try a 7-day streak first.`);
    await wait(400);
    S.busy = false; renderGate(false);
  }
  async function setTier(t) {
    S.tier = t;
    renderGate(true);
    $$(".rung-b").forEach((b, i) => fx(b, [{ opacity: .3, transform: "translateY(6px)" }, { opacity: 1, transform: "none" }], { d: 420, delay: i * 70, fill: "none" }));
    const w = G.config.tiers[t];
    cap(t === "subscriber" ? "Subscriber" : "Free", t === "subscriber"
      ? `Subscribers get <b>${w.drops_per_unlock} drops per unlock</b> and waits of ${w.waits_h.join(", ")} hours; free viewers get every drop, slower.`
      : `Free viewers get <b>${w.drops_per_unlock} drop per unlock</b> and wait ${w.waits_h.join(", ")} hours as the streak grows.`);
    await wait(0);
  }

  const RUN = [async () => { splash(); }, beatChat, beatProfile, beatShows, beatDrop, beatGate];

  // ---------- Results ----------
  function buildLedger() {
    const r = KD.results;
    const rows = [  // [value, suffix, label, note, tooltip]
      [r.drops, "", `<b>drops</b> from ${r.episodes} episodes`],
      [r.drops_in_range, ` of ${r.drops}`, `run <b>4 to 6 minutes</b>`, "", "Drops that land between 4 and 6 minutes."],
      [r.teasers_grounded, ` of ${r.drops}`, `teasers <b>quote a real line</b>`, `${r.teasers_repaired} repaired`, `Every teaser quotes a real line from the episode. Code repaired ${r.teasers_repaired} of them.`],
      [r.within_one_point, ` of ${r.episodes}`, `within <b>1 point</b> of Gemini`, `Spearman ${r.spearman}`, "Endings scored within 1 point by a second model (Gemini)."],
      [r.cents_per_show, " US cents", `<b>per 50-episode show</b>, both languages`, "", "Both languages, at Groq's list price."],
      [r.usd_per_million_viewers, "/month", `<b>model calls</b>, 1M new viewers`, "", "About $800 a month in model calls at 1 million new viewers a month."],
    ];
    $("#ledger").innerHTML = rows.map(([v, suf, txt, note, tip], i) => `<li${tip ? ` title="${tip}"` : ""}><span class="v">${i === 5 ? "$" : ""}<span data-to="${v}">${v}</span><small>${suf}</small></span><p>${txt}${note ? `<small class="note">${note}</small>` : ""}</p></li>`).join("");
    const io = new IntersectionObserver((es) => es.forEach((e) => {
      if (!e.isIntersecting) return;
      io.disconnect();
      $$("#ledger [data-to]").forEach((n) => { const to = +n.dataset.to; tween(1300, (p) => { n.textContent = Math.round(to * p); }, undefined, true); });
    }), { threshold: .35 });
    io.observe($("#ledger"));
    const pio = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("run"); pio.disconnect(); } }), { threshold: .3 });
    pio.observe($("#pipe"));
  }

  // ---------- Events ----------
  function setLang(lang) {
    if (lang === S.lang) return;
    S.lang = lang;
    $$(".lang button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
    fillDuo();
    if (S.mode === "ended") S.mode = "manual";
    go(S.beat);
  }
  function openBTS(open) {
    const b = $("#bts");
    b.classList.toggle("open", open);
    $$(".bts-open").forEach((x) => x.setAttribute("aria-expanded", String(open)));
    if (open) $(".bts-close").focus({ preventScroll: true });
  }
  function act(fn) { quiet(fn()); }
  document.addEventListener("click", (e) => {
    const t = e.target.closest("button, [data-act]");
    if (!t) return;
    if (t.dataset.start) return t.dataset.start === "auto" ? startAuto() : startManual();
    if (t.dataset.lang) return setLang(t.dataset.lang);
    if (t.dataset.beat) { takeOver(); S.mode = "manual"; return go(+t.dataset.beat); }
    if (t.dataset.tier) { if (S.busy || t.dataset.tier === S.tier) return; takeOver(); return act(() => setTier(t.dataset.tier)); }
    if (t.classList.contains("bts-open")) return openBTS(true);
    if (t.classList.contains("bts-close")) return openBTS(false);
    switch (t.dataset.act) {
      case "auto": return startAuto();
      case "manual": return startManual();
      case "pause": return setPaused(!S.paused);
      case "skip": return S.beat < 5 ? go(S.beat + 1) : (S.token++, endAuto());
      case "next": return S.beat < 5 ? go(S.beat + 1) : $("#how").scrollIntoView({ behavior: RM ? "auto" : "smooth" });
      case "prev": return go(Math.max(1, S.beat - 1));
      case "watch": if (S.mode !== "auto") go(4); return;
      case "listen": return listen();
      case "ff": if (!S.busy) { takeOver(); act(ff); } return;
      case "s7": if (!S.busy) { takeOver(); act(streak7); } return;
      case "skip2": if (!S.busy) { takeOver(); act(skip2); } return;
    }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && $("#bts").classList.contains("open")) openBTS(false); });

  function fit() {
    const mobile = innerWidth < 900;
    document.documentElement.style.setProperty("--z", mobile ? 1 : Math.max(.6, Math.min(1, (innerHeight - 60 - 56) / 868)).toFixed(3));
    // Pad the phone scenes by the live caption-sheet height and keep their bottom anchored when it changes.
    const scr = $("#screen"), old = parseFloat(scr.style.getPropertyValue("--pb")) || 0, pb = mobile ? $("#rail").offsetHeight : 0;
    scr.style.setProperty("--pb", pb + "px");
    if (pb !== old) $$(".scene").forEach((s) => { if (s.scrollHeight > s.clientHeight) s.scrollTop += pb - old; });
  }
  new ResizeObserver(fit).observe($("#rail"));
  addEventListener("resize", fit);
  if (window.speechSynthesis) speechSynthesis.addEventListener?.("voiceschanged", syncListen);

  // ---------- Boot ----------
  $("#price-pct").textContent = KD.results.price_share_pct;
  buildWall(); buildLedger(); fit();
  RUN[0](); renderRail(); renderBTS();
  requestAnimationFrame(loop);
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => playWall());
})();
