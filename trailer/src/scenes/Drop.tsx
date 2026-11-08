// Beat 4: the drop player. Real last lines as subtitles, real cliffhanger score, freeze, grounded teaser.
import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import data from "../data.json";
import { C, F } from "../theme";
import { Check, Column, Grain, Haveli, Headline, Kicker, Sub, eIO, inOut, ramp } from "../ui";

export const DROP_LEN = 210;
const SUB_FROM = 10;
const SUB_TO = 116;
const FREEZE = 120;
const TEASER = 132;
const d = data.drop;

// Real tail timings, compressed into SUB_FROM..SUB_TO.
const t0 = data.tail[0].start;
const t1 = data.tail[data.tail.length - 1].end;
const toFrame = (t: number) => SUB_FROM + ((t - t0) / (t1 - t0)) * (SUB_TO - SUB_FROM);
const episodeTime = (f: number) => t0 + ramp(f, SUB_FROM, SUB_TO, 0, 1, (x) => x) * (t1 - t0);
const mmss = (t: number) => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, "0")}`;

const Subtitle: React.FC<{ f: number }> = ({ f }) => {
  const idx = data.tail.findIndex((l) => f >= toFrame(l.start) && f < toFrame(l.end));
  const j = idx >= 0 ? idx : f >= SUB_TO ? data.tail.length - 1 : -1;
  if (j < 0) return null;
  const l = data.tail[j];
  const a = ramp(f, toFrame(l.start), toFrame(l.start) + 5);
  const out = ramp(f, TEASER - 6, TEASER + 2, 1, 0, eIO);
  const fx = l.type !== "dialogue";
  return (
    <div style={{ position: "absolute", left: 24, right: 24, bottom: 74, opacity: a * out, textShadow: "0 2px 14px rgba(0, 0, 0, .95)" }}>
      {!fx && (
        <div style={{ fontFamily: F.u, fontWeight: 800, fontSize: 13, letterSpacing: "0.12em", color: C.gold }}>
          {l.speaker}
          <span style={{ marginLeft: 8, color: C.ink3, fontWeight: 650, letterSpacing: "0.02em" }}>{l.cue}</span>
        </div>
      )}
      <div style={{ marginTop: 6, fontFamily: F.u, fontWeight: fx ? 600 : 700, fontSize: fx ? 20 : 25, lineHeight: 1.3, color: fx ? C.gold2 : "#fff7ec" }}>
        {fx ? `[ ${l.text} ]` : l.text}
      </div>
    </div>
  );
};

export const DropScreen: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = ramp(f, 0, FREEZE, 0, 1, (x) => x);
  const frozen = ramp(f, FREEZE, FREEZE + 10);
  const flash = f >= FREEZE ? ramp(f, FREEZE, FREEZE + 9, 0.45, 0, eIO) : 0;
  const t = episodeTime(Math.min(f, FREEZE));
  const teaser = spring({ frame: f - TEASER, fps, config: { damping: 18, stiffness: 120 } });
  const underline = ramp(f, TEASER + 14, TEASER + 30, 0, 1, eIO);
  const check = spring({ frame: f - (TEASER + 26), fps, config: { damping: 12, stiffness: 160 } });
  return (
    <AbsoluteFill style={{ background: "#070407", opacity: ramp(f, 0, 10) }}>
      <AbsoluteFill style={{ filter: `grayscale(${0.6 * frozen}) brightness(${1 - 0.3 * frozen})` }}>
        <div style={{ position: "absolute", inset: "-4%", transform: `scale(${1 + 0.13 * zoom}) translateY(${-1.5 * zoom}%)`, transformOrigin: "50% 40%" }}>
          <Haveli />
        </div>
        <Grain opacity={0.16} every={2} until={FREEZE} />
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, transparent 35%, rgba(0, 0, 0, .78) 100%)" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "#fff7ec", opacity: flash }} />

      <div style={{ position: "absolute", top: 62, left: 22, right: 22, display: "flex", justifyContent: "space-between", fontFamily: F.u, fontWeight: 800, fontSize: 13, letterSpacing: "0.06em", color: "rgba(247, 236, 223, .8)", fontVariantNumeric: "tabular-nums" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 7 }}>
          <span style={{ width: 8, height: 8, borderRadius: 4, background: f < FREEZE ? C.red : C.ink3 }} />
          DROP {d.n} · EP {data.tailEpisode}
        </span>
        <span>{mmss(t)}</span>
      </div>
      <div style={{ position: "absolute", top: 88, left: 22, right: 22, display: "flex", gap: 5 }}>
        {d.episodes.map((ep) => (
          <div key={ep} style={{ flex: 1, height: 4, borderRadius: 2, background: "rgba(247, 236, 223, .2)", overflow: "hidden" }}>
            <div style={{ height: "100%", background: C.gold, transformOrigin: "0 50%", transform: `scaleX(${ep < data.tailEpisode ? 1 : t / data.tailEpisodeSeconds})` }} />
          </div>
        ))}
      </div>
      <div style={{ position: "absolute", top: 112, left: 22, fontFamily: F.d, fontSize: 30, color: C.ink, opacity: ramp(f, 4, 18) * (1 - frozen), textShadow: "0 2px 18px rgba(0, 0, 0, .8)" }}>
        {data.show.title}
      </div>

      <Subtitle f={f} />

      <div style={{ position: "absolute", top: 128, left: 0, right: 0, textAlign: "center", fontFamily: F.u, fontWeight: 800, fontSize: 15, letterSpacing: "0.34em", color: C.ink, textShadow: "0 2px 16px rgba(0, 0, 0, .9)", opacity: ramp(f, FREEZE + 4, FREEZE + 16) }}>
        TO BE CONTINUED
      </div>

      <div
        style={{
          position: "absolute", left: 18, right: 18, bottom: 40, padding: "22px 22px 20px", borderRadius: 26, background: "rgba(24, 13, 25, .92)",
          boxShadow: `inset 0 0 0 1px ${C.line2}, 0 30px 60px -20px rgba(0, 0, 0, .9)`,
          opacity: f < TEASER ? 0 : Math.min(1, teaser * 1.5), transform: `translateY(${(1 - teaser) * 60}px)`,
        }}
      >
        <div style={{ fontFamily: F.u, fontWeight: 800, fontSize: 13, letterSpacing: "0.16em", color: C.gold }}>AGLI BAAR · DROP {d.n + 1}</div>
        <div style={{ marginTop: 12, fontFamily: F.d, fontSize: 29, lineHeight: 1.15, color: C.ink }}>{d.teaser[0]}</div>
        <div style={{ marginTop: 12, fontFamily: F.u, fontWeight: 700, fontSize: 22, lineHeight: 1.4, color: "#fff7ec" }}>
          <span
            style={{
              paddingBottom: 5, backgroundImage: `linear-gradient(${C.gold}, ${C.gold})`, backgroundRepeat: "no-repeat", backgroundPosition: "0 100%",
              backgroundSize: `${underline * 100}% 3px`, boxDecorationBreak: "clone", WebkitBoxDecorationBreak: "clone",
            }}
          >
            “{d.teaser[1]}”
          </span>
        </div>
        {d.grounded && (
          <div
            style={{
              marginTop: 18, display: "flex", alignItems: "center", gap: 10, fontFamily: F.u, fontWeight: 700, fontSize: 17, color: C.ok,
              opacity: f < TEASER + 26 ? 0 : Math.min(1, check * 1.5), transform: `scale(${0.85 + 0.15 * check})`, transformOrigin: "0% 50%",
            }}
          >
            <Check size={22} />
            Line found in episode {d.foundInEpisode}'s ending
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

const Pill: React.FC<{ children: React.ReactNode; at: number; f: number }> = ({ children, at, f }) => (
  <div
    style={{
      padding: "9px 18px", borderRadius: 999, background: C.surface2, boxShadow: `inset 0 0 0 1.5px ${C.line2}`, fontFamily: F.u, fontWeight: 700,
      fontSize: 24, color: C.ink, fontVariantNumeric: "tabular-nums", ...inOut(f, at, Infinity, 14),
    }}
  >
    {children}
  </div>
);

export const DropText: React.FC = () => {
  const f = useCurrentFrame();
  const score = d.cliff * ramp(f, 28, 104, 0, 1, eIO);
  const end = DROP_LEN + 4;
  return (
    <Column>
      <div style={inOut(f, 4, end)}>
        <Kicker>2 · The drop</Kicker>
      </div>
      <div style={{ position: "relative", height: 166, marginTop: 26 }}>
        <div style={{ position: "absolute", inset: 0, ...inOut(f, 8, TEASER - 6) }}>
          <Headline size={78}>One drop a day, cut on a cliffhanger.</Headline>
        </div>
        <div style={{ position: "absolute", inset: 0, ...inOut(f, TEASER - 8, end) }}>
          <Headline size={78}>Then a teaser that quotes the episode.</Headline>
        </div>
      </div>
      <div style={{ position: "relative", height: 46, marginTop: 18 }}>
        <Sub style={{ position: "absolute", inset: 0, ...inOut(f, 14, TEASER - 6) }}>
          Drop {d.n}: episodes {d.episodes.join(" and ")}, about {d.minutes} minutes.
        </Sub>
        <Sub style={{ position: "absolute", inset: 0, ...inOut(f, TEASER - 4, end) }}>The quoted line is checked against the episode.</Sub>
      </div>
      <div style={{ marginTop: 52, ...inOut(f, 22, end) }}>
        <Kicker style={{ color: C.ink2, fontSize: 18 }}>Cliffhanger score</Kicker>
        <div style={{ display: "flex", alignItems: "center", gap: 28, marginTop: 10 }}>
          <div style={{ width: 250, fontFamily: F.d, fontSize: 128, lineHeight: 1, color: C.gold2, fontVariantNumeric: "tabular-nums" }}>{score.toFixed(2)}</div>
          <div style={{ display: "flex", gap: 12 }}>
            <Pill at={50} f={f}>Model {d.llm}/5</Pill>
            <Pill at={60} f={f}>Rules {d.rule.toFixed(2)}</Pill>
          </div>
        </div>
        <div style={{ marginTop: 18, width: 640, height: 14, borderRadius: 7, background: C.surface2, overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${score * 100}%`, borderRadius: 7, background: `linear-gradient(90deg, ${C.gold}, ${C.gold2})`, boxShadow: "0 0 24px rgba(242, 169, 59, .6)" }} />
        </div>
      </div>
    </Column>
  );
};
