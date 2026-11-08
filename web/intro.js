// First-visit intro: 4 story cards (problem, why it hurts, the fix, how to use the page).
// Shows once per browser (localStorage), always with ?intro=1, and again from the "Intro" nav button.
(() => {
  "use strict";
  const dlg = document.getElementById("intro");
  if (!dlg || !dlg.showModal) return;
  const KEY = "kd-intro-seen", DUR = 5500, root = document.documentElement;
  const RM = matchMedia("(prefers-reduced-motion: reduce)").matches, HOVER = matchMedia("(hover: hover)");
  const cards = [...dlg.querySelectorAll(".ib-card")], bars = [...dlg.querySelectorAll(".ib-bars i")], N = cards.length;
  const box = dlg.querySelector(".ib-cards"), count = dlg.querySelector(".ib-n"), pauseBtn = dlg.querySelector(".ib-pause");
  const prevBtn = dlg.querySelector(".ib-prev"), nextBtn = dlg.querySelector(".ib-next"), hero = document.querySelector(".hero .btn.primary");
  let idx = 0, t = 0, last = 0, raf = 0, userPaused = false, hover = false, kbFocus = false, opener = null;

  // Facts come from the same data as the hero.
  const pct = window.KD && KD.results ? KD.results.price_share_pct : 20;
  dlg.querySelectorAll(".ib-pct").forEach((n) => { n.textContent = pct; });
  dlg.style.setProperty("--pct", pct + "%");
  if (RM) pauseBtn.hidden = true;  // nothing auto-advances under reduced motion

  // Card 1 visual: a wall of 30 abstract poster tiles in the hero palette.
  const PAL = [["#7b1e2e", "#f2a93b"], ["#1e3d3a", "#e8c07a"], ["#8a3b12", "#f6d7a7"], ["#14324f", "#f2a93b"], ["#5c1a3a", "#f4b6c2"], ["#2e3b1f", "#d9c36a"], ["#b23a2b", "#fbe3c4"], ["#3b2416", "#e9a15b"]];
  dlg.querySelector(".iv-wall").innerHTML = Array.from({ length: 30 }, (_, i) => {
    const [b, f] = PAL[(i * 5 + (i >> 2)) % PAL.length];
    return `<span class="iv-tile s${i % 4}" style="--pbg:${b};--pfg:${f};--d:${(i * 22) % 400 + i * 6}ms"><i></i><i></i></span>`;
  }).join("");

  const paused = () => RM || userPaused || hover || kbFocus || document.hidden;
  function paint() {
    bars.forEach((b, i) => { b.style.transform = `scaleX(${i < idx ? 1 : i > idx ? 0 : RM ? 1 : Math.min(1, t / DUR)})`; });
  }
  function go(i, auto) {
    idx = Math.max(0, Math.min(N - 1, i)); t = 0;
    cards.forEach((c, k) => { const on = k === idx; c.classList.toggle("on", on); c.inert = !on; });
    count.textContent = `${idx + 1} of ${N}`;
    prevBtn.disabled = idx === 0; nextBtn.disabled = idx === N - 1;
    box.setAttribute("aria-live", auto ? "off" : "polite");
    paint();
  }
  function tick(now) {
    const dt = Math.min(100, now - last); last = now;
    if (!paused() && t < DUR) {
      t += dt;
      if (t >= DUR) { if (idx < N - 1) go(idx + 1, true); else t = DUR; }
    }
    paint();
    raf = requestAnimationFrame(tick);
  }
  function setUserPaused(p) {
    userPaused = p;
    pauseBtn.setAttribute("aria-pressed", String(p));
    pauseBtn.setAttribute("aria-label", p ? "Play the intro" : "Pause the intro");
  }

  function open() {
    if (dlg.open) return;
    const a = document.activeElement;
    opener = a && a.classList.contains("intro-open") ? a : hero;
    const p = document.getElementById("pause");
    if (p && p.getAttribute("aria-pressed") === "false") p.click();  // pause the autoplay demo behind the intro
    try { localStorage.setItem(KEY, "1"); } catch (e) { /* storage blocked: intro still works */ }
    hover = kbFocus = false; setUserPaused(false);
    dlg.showModal(); root.classList.add("intro-lock");
    dlg.focus();
    go(0); last = performance.now();
    cancelAnimationFrame(raf); raf = requestAnimationFrame(tick);
  }
  function cleanup() {
    cancelAnimationFrame(raf);
    root.classList.remove("intro-lock");
    if (opener) { opener.focus({ preventScroll: true }); opener = null; }
  }
  function close() { if (!dlg.open) return; dlg.close(); cleanup(); }
  dlg.addEventListener("close", () => { if (opener) cleanup(); });
  dlg.addEventListener("cancel", (e) => { e.preventDefault(); close(); });  // Esc

  // Runs before app.js's document handler, so data-start buttons close the intro first, then start the demo.
  dlg.addEventListener("click", (e) => {
    const b = e.target.closest("button, a");
    if (b) {
      if (b.classList.contains("ib-skip")) close();
      else if (b === pauseBtn) setUserPaused(!userPaused);
      else if (b === prevBtn) go(idx - 1);
      else if (b === nextBtn) go(idx + 1);
      else if (b.dataset.start) close();
      else if (b.classList.contains("ib-trailer")) { close(); document.getElementById("trailer-open").click(); }
      return;
    }
    const r = dlg.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) return;  // backdrop
    go(e.clientX - r.left < r.width / 2 ? idx - 1 : idx + 1);
  });
  dlg.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") { e.preventDefault(); go(idx + 1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); go(idx - 1); }
    else if (e.key === "Tab") {  // keep Tab inside the intro
      const f = [...dlg.querySelectorAll("button:not([disabled])")].filter((x) => !x.closest("[inert]") && x.offsetParent);
      if (!f.length) return;
      const i = f.indexOf(document.activeElement);
      if (e.shiftKey && i <= 0) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && (i === -1 || i === f.length - 1)) { e.preventDefault(); f[0].focus(); }
    }
  });
  dlg.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse" && HOVER.matches) hover = true; });
  dlg.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") hover = false; });
  dlg.addEventListener("focusin", (e) => { kbFocus = e.target !== dlg && e.target.matches(":focus-visible"); });
  dlg.addEventListener("focusout", () => { kbFocus = false; });
  document.addEventListener("visibilitychange", () => { last = performance.now(); });

  document.querySelectorAll(".intro-open").forEach((b) => b.addEventListener("click", open));

  let seen = false;
  try { seen = localStorage.getItem(KEY) === "1"; } catch (e) { /* treat as first visit */ }
  if (new URLSearchParams(location.search).get("intro") === "1" || !seen) open();
})();
