// Timer gates, a line-for-line port of tools/gates.py. tools/test_web_gates.py checks both give identical output.
// Times are naive wall-clock values (like the Python datetimes) stored in UTC fields; format them with timeZone "UTC".
(function (root) {
  const G = (root.KD || {}).gates;  // one source of truth: data.js, exported from tools/gates.py
  if (!G) throw new Error("load data.js before gates.js");
  const H = 3600e3;
  const SLOT = /^([01]\d|2[0-3]):[0-5]\d$/;

  const at = (y, mo, d, h = 0, mi = 0) => new Date(Date.UTC(y, mo - 1, d, h, mi));
  const iso = (t) => t.toISOString().slice(0, 16);  // "2026-11-09T20:00", same as Python isoformat(timespec="minutes")
  const addH = (t, h) => new Date(t.getTime() + h * H);

  function level(streak) {
    let best = 0;
    G.levels.forEach((need, i) => { if (Math.max(0, streak) >= need) best = i; });
    return best;
  }

  const waitH = (tier, streak) => G.tiers[tier].waits_h[level(streak)];
  const nextUnlock = (watchedAt, tier, streak) => addH(watchedAt, waitH(tier, streak));

  function reminder(unlockAt, slots) {
    const ok = (slots || []).filter((s) => SLOT.test(s));
    let best = null;
    for (const day of [0, 1]) {
      for (const s of ok.length ? ok : ["20:00"]) {
        const [h, m] = s.split(":").map(Number);
        const t = addH(unlockAt, 24 * day);
        t.setUTCHours(h, m, 0, 0);
        if (t >= unlockAt && (!best || t < best)) best = t;
      }
    }
    return best;
  }

  function updateStreak(streak, unlockAt, cameBackAt) {
    if (cameBackAt <= addH(unlockAt, G.grace_h)) return streak + 1;
    return G.levels[Math.max(level(streak) - 1, 0)];
  }

  function simulate(tier, slots, totalDrops, days = 10, start = at(2026, 11, 9, 20, 0), skipDays = []) {
    let t = start, streak = 0, opened = 0;
    const rows = [];
    for (let day = 0; day < days; day++) {
      if (opened >= totalDrops) break;
      opened = Math.min(totalDrops, opened + G.tiers[tier].drops_per_unlock);
      const unlock = nextUnlock(t, tier, streak);
      const remind = reminder(unlock, slots);
      rows.push({ session: day + 1, watched_at: iso(t), streak, drops_open: opened, wait_h: waitH(tier, streak),
                  next_unlock: iso(unlock), reminder: iso(remind) });
      const back = skipDays.includes(day + 1) ? addH(remind, 48) : remind;
      streak = updateStreak(streak, unlock, back);
      t = back;
    }
    return rows;
  }

  const api = { level, waitH, nextUnlock, reminder, updateStreak, simulate, at, iso, addH, config: G };
  root.KDGates = api;
  if (typeof module !== "undefined") module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
