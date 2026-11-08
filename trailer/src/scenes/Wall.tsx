// Beats 1 and 2: a wall of 30 abstract posters collapses into the viewer's 2 real picks.
import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import data from "../data.json";
import { C, F } from "../theme";
import { Gold, Headline, Kicker, Sub, eIO, inOut, ramp, rand } from "../ui";

const COLS = 6;
const ROWS = 5;
const TW = 124;
const TH = 176;
const GAP = 16;
const GX = 990; // grid origin on screen
const GY = 68;
const PICKS = [13, 16]; // tile indices that become the two cards
const CW = 452;
const CH = 548;
const CARD_X = [870 - GX, 1352 - GX]; // card positions in grid space
const CARD_Y = (1080 - CH) / 2 - GY;
const COLLAPSE = 122;

const PAL: [string, string][] = [
  ["#5b2a4a", "#e0784a"], ["#2d1e4f", "#c2577a"], ["#3a2a1a", "#f2a93b"], ["#1f3a4a", "#93bedd"],
  ["#4a1e2a", "#ec6a52"], ["#24402f", "#86cfa0"], ["#3b2340", "#ffc56a"], ["#402018", "#d98c5f"],
];

const Poster: React.FC<{ i: number }> = ({ i }) => {
  const [a, b] = PAL[Math.floor(rand(i * 3.1) * PAL.length)];
  const hx = 20 + rand(i + 0.3) * 60;
  const two = rand(i + 0.7) > 0.55;
  return (
    <AbsoluteFill style={{ background: `radial-gradient(120% 70% at ${hx}% 18%, ${b} 0%, ${a} 55%, #120a13 100%)` }}>
      <svg viewBox="0 0 124 176" preserveAspectRatio="xMidYMax meet" width="100%" height="100%" style={{ position: "absolute", inset: 0 }}>
        <g fill="rgba(10, 4, 10, .55)">
          <circle cx={two ? 44 : 62} cy={two ? 88 : 80} r={two ? 17 : 21} />
          <path d={two ? "M12 176c0-34 14-56 32-56s32 22 32 56z" : "M18 176c0-40 18-66 44-66s44 26 44 66z"} />
          {two && (
            <>
              <circle cx="86" cy="96" r="15" />
              <path d="M58 176c0-30 12-50 28-50s28 20 28 50z" />
            </>
          )}
        </g>
      </svg>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, transparent 50%, rgba(10, 4, 10, .85) 100%)" }} />
    </AbsoluteFill>
  );
};

const PosterBars: React.FC<{ i: number; opacity: number }> = ({ i, opacity }) => (
  <div style={{ position: "absolute", left: 12, right: 12, bottom: 14, opacity }}>
    <div style={{ height: 8, width: `${55 + rand(i + 0.9) * 35}%`, borderRadius: 4, background: "rgba(247, 236, 223, .62)" }} />
    <div style={{ height: 6, width: `${30 + rand(i + 1.3) * 30}%`, borderRadius: 3, background: "rgba(247, 236, 223, .3)", marginTop: 7 }} />
  </div>
);

const Card: React.FC<{ k: number; f: number }> = ({ k, f }) => {
  const p = data.picks[k];
  const body = ramp(f, COLLAPSE + 30 + k * 5, COLLAPSE + 50 + k * 5);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 286, padding: "0 28px", opacity: body, transform: `translateY(${(1 - body) * 18}px)` }}>
      <div style={{ fontFamily: F.u, fontWeight: 800, fontSize: 16, letterSpacing: "0.12em", textTransform: "uppercase", color: C.ink3 }}>{p.platform}</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 12 }}>
        {p.tags.map((t) => (
          <span key={t} style={{ fontFamily: F.u, fontWeight: 700, fontSize: 17, padding: "5px 13px", borderRadius: 999, background: C.surface2, color: C.ink2 }}>{t}</span>
        ))}
        {p.familySafe && (
          <span style={{ fontFamily: F.u, fontWeight: 700, fontSize: 17, padding: "5px 13px", borderRadius: 999, background: C.goldSoft, color: C.gold2 }}>family-safe</span>
        )}
      </div>
      <div style={{ marginTop: 20, paddingLeft: 16, borderLeft: `3px solid ${C.gold}`, fontFamily: F.u, fontWeight: 600, fontSize: 23, lineHeight: 1.42, color: C.ink }}>
        {p.reason}
      </div>
    </div>
  );
};

export const Wall: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = spring({ frame: f - COLLAPSE, fps, config: { damping: 200 }, durationInFrames: 40 });
  const drift = ramp(f, 0, COLLAPSE, 0, -26, (t) => t);
  const tilt = 1 - k;

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute", left: GX, top: GY, width: COLS * (TW + GAP) - GAP, height: ROWS * (TH + GAP) - GAP,
          transform: `perspective(2200px) rotateY(${-15 * tilt}deg) rotateX(${5 * tilt}deg)`, transformOrigin: "0% 50%",
        }}
      >
        {Array.from({ length: COLS * ROWS }, (_, i) => {
          const c = i % COLS;
          const r = Math.floor(i / COLS);
          const x = c * (TW + GAP);
          const y = r * (TH + GAP);
          const pick = PICKS.indexOf(i);
          const enter = spring({ frame: f - ((r + c) * 2.4 + rand(i) * 5), fps, config: { damping: 15, stiffness: 120, mass: 0.8 } });
          if (pick < 0) {
            const d = Math.hypot(c - 2.5, r - 2) * 2.2;
            const out = ramp(f, COLLAPSE + d, COLLAPSE + d + 18, 0, 1, eIO);
            if (out >= 1) return null;
            const tx = (2.5 * (TW + GAP) - x) * out * 0.3;
            const ty = (2 * (TH + GAP) - y) * out * 0.3;
            return (
              <div
                key={i}
                style={{
                  position: "absolute", left: x, top: y + drift, width: TW, height: TH, borderRadius: 14, overflow: "hidden",
                  boxShadow: "0 14px 30px -14px rgba(0, 0, 0, .8), inset 0 0 0 1px rgba(247, 236, 223, .08)",
                  opacity: Math.min(1, enter * 1.4) * (1 - out),
                  transform: `translate(${tx}px, ${ty + (1 - enter) * 40}px) scale(${(0.9 + 0.1 * enter) * (1 - 0.35 * out)})`,
                }}
              >
                <Poster i={i} />
                <PosterBars i={i} opacity={1} />
              </div>
            );
          }
          const m = spring({ frame: f - COLLAPSE - 4, fps, config: { damping: 200 }, durationInFrames: 36 });
          const L = interpolate(m, [0, 1], [x, CARD_X[pick]]);
          const T = interpolate(m, [0, 1], [y + drift, CARD_Y]);
          const W = interpolate(m, [0, 1], [TW, CW]);
          const H = interpolate(m, [0, 1], [TH, CH]);
          const ph = interpolate(m, [0, 1], [TH, 266]);
          const title = ramp(f, COLLAPSE + 22 + pick * 5, COLLAPSE + 40 + pick * 5);
          return (
            <div
              key={i}
              style={{
                position: "absolute", left: L, top: T, width: W, height: H, borderRadius: interpolate(m, [0, 1], [14, 26]), overflow: "hidden",
                background: C.surface, zIndex: 5,
                boxShadow: `0 40px 80px -30px rgba(0, 0, 0, .9), 0 0 0 ${1 + m}px rgba(242, 169, 59, ${0.08 + 0.3 * m})`,
                opacity: Math.min(1, enter * 1.4), transform: `translateY(${(1 - enter) * 40}px)`,
              }}
            >
              <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: ph, overflow: "hidden" }}>
                <Poster i={i} />
                <PosterBars i={i} opacity={1 - ramp(f, COLLAPSE, COLLAPSE + 12)} />
                <div
                  style={{
                    position: "absolute", left: 28, right: 28, bottom: 22, opacity: title, transform: `translateY(${(1 - title) * 16}px)`,
                    fontFamily: F.d, fontSize: 46, lineHeight: 1.02, color: C.ink, textShadow: "0 4px 24px rgba(0, 0, 0, .6)",
                  }}
                >
                  {data.picks[pick].title}
                </div>
              </div>
              <Card k={pick} f={f} />
            </div>
          );
        })}
      </div>

      <div style={{ position: "absolute", left: 150, top: 0, bottom: 0, width: 690, display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <div style={{ position: "relative", height: 420 }}>
          <div style={{ position: "absolute", inset: 0, ...inOut(f, 6, COLLAPSE + 4) }}>
            <Kicker>A new viewer opens the app</Kicker>
            <Headline size={84} style={{ marginTop: 28 }}>
              Kuku TV shows a new viewer about <Gold>30</Gold> shows.
            </Headline>
            <Sub style={{ marginTop: 26 }}>{data.firstScreen} on the very first screen.</Sub>
          </div>
          <div style={{ position: "absolute", inset: 0, ...inOut(f, COLLAPSE + 2) }}>
            <Kicker>Kuku Daily</Kicker>
            <Headline size={84} style={{ marginTop: 28 }}>
              Kuku Daily shows <Gold>two</Gold>.
            </Headline>
            <Sub style={{ marginTop: 26 }}>Picked from her own words, each with a reason in Hinglish.</Sub>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
