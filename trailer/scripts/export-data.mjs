// Reads ../web/data.js (window.KD, the real pipeline outputs) and writes src/data.json.
// Every word the trailer shows comes from here; the only change is typographic:
// non-breaking hyphens (U+2011) become plain hyphens so the web fonts can draw them.
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const src = path.resolve(here, "../../web/data.js");
const out = path.resolve(here, "../src/data.json");

const ctx = { window: {} };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(src, "utf8"), ctx);
const KD = ctx.window.KD;
if (!KD) throw new Error("web/data.js did not set window.KD");

const clean = (s) => String(s).replace(/\u2011/g, "-");
const LANG = "hinglish";
const viewer = KD.viewers[LANG];
const drop = KD.drops[LANG].drops[0];
const lastEp = drop.episodes[drop.episodes.length - 1];
const tail = KD.episodes.find((e) => e.ep === lastEp).tail;
const foundIn = KD.episodes.find((e) => e.tail.some((l) => l.text.includes(drop.quoted_line)));
const firstSession = viewer.gate_sim[0];
const fmtHM = (hm) => {
  const [h, m] = hm.split(":").map(Number);
  return `${((h + 11) % 12) + 1}${m ? `:${String(m).padStart(2, "0")}` : ""} ${h < 12 ? "am" : "pm"}`;
};
const fmtTime = (iso) => fmtHM(iso.slice(11, 16));

const data = {
  show: { title: KD.show.title },
  firstScreen: KD.results.first_screen_shows,
  picks: viewer.match.picks.map((p) => ({
    title: p.title,
    platform: p.platform,
    tags: p.tags.slice(0, 2),
    familySafe: p.family_safe,
    reason: clean(p.reason),
  })),
  // The app shows the bracketed hint as a placeholder, so the chat bubble keeps the question only.
  questions: KD.questions[LANG].map((q) => clean(q.replace(/\s*\(.*\)\s*$/, ""))),
  answers: viewer.input.answers.map(clean),
  persona: {
    who: viewer.persona.who,
    slots: viewer.persona.slots.map(fmtHM),
    likes: viewer.persona.likes,
    watchWith: viewer.persona.watch_with,
  },
  drop: {
    n: drop.n,
    episodes: drop.episodes,
    minutes: Math.round(drop.seconds / 60),
    cliff: drop.cliff_score,
    llm: drop.llm_score,
    rule: drop.rule_score,
    teaser: drop.teaser.split("\n").map((l) => l.replace(/^"|"$/g, "")),
    quoted: drop.quoted_line,
    grounded: drop.grounded,
    foundInEpisode: foundIn ? foundIn.ep : null,
  },
  tail: tail.map((l) => ({ type: l.type, speaker: l.speaker, cue: l.cue, start: l.start, end: l.end, text: l.text.replace(/^"|"$/g, "") })),
  tailEpisode: lastEp,
  tailEpisodeSeconds: KD.episodes.find((e) => e.ep === lastEp).seconds,
  gates: {
    levels: KD.gates.levels,
    free: KD.gates.tiers.free.waits_h,
    subscriber: KD.gates.tiers.subscriber.waits_h,
  },
  session: {
    watched: fmtTime(firstSession.watched_at),
    watchedHour: Number(firstSession.watched_at.slice(11, 13)),
    reminderHour: Number(firstSession.reminder.slice(11, 13)),
    waitH: firstSession.wait_h,
    reminder: fmtTime(firstSession.reminder),
    nextDrop: firstSession.drops_open + 1,
  },
};

fs.writeFileSync(out, JSON.stringify(data, null, 2) + "\n");
console.log(`wrote ${path.relative(process.cwd(), out)}`);
