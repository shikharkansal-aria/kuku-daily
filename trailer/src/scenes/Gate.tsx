// Beat 5: the gate. Countdown ring, push at her free slot, streak fills, wait ladder steps down.
import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import data from "../data.json";
import { C, F } from "../theme";
import { Arrow, Column, Headline, Kicker, Sub, eIO, inOut, ramp } from "../ui";

export const GATE_LEN = 165;
const RUN_FROM = 10;
const READY = 72;
const NOTIFY = 86;
const s = data.session;

/** Phone clock during the time-lapse: watched time, plus the wait, plus the gap to her reminder slot. */
export const gateClock = (f: number) => {
  const mins = s.watchedHour * 60 + s.waitH * 60 * ramp(f, RUN_FROM, READY, 0, 1, eIO) + (s.reminderHour - s.watchedHour) * 60 * ramp(f, READY, NOTIFY - 4, 0, 1, eIO);
  const h = Math.floor(mins / 60) % 24;
  const m = Math.floor(mins % 60);
  return `${((h + 11) % 12) + 1}:${String(m).padStart(2, "0")}`;
};

const R = 112;
const CIRC = 2 * Math.PI * R;

export const GateScreen: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const left = 1 - ramp(f, RUN_FROM, READY, 0, 1, eIO);
  const ready = f >= READY;
  const arc = ready ? ramp(f, READY, READY + 12) : left;
  const pulse = ready ? 1 + 0.07 * Math.sin(Math.PI * ramp(f, READY, READY + 14, 0, 1, (x) => x)) : 1;
  const secs = Math.round(left * s.waitH * 3600);
  const hms = [Math.floor(secs / 3600), Math.floor((secs % 3600) / 60), secs % 60].map((n) => String(n).padStart(2, "0")).join(":");
  const note = spring({ frame: f - NOTIFY, fps, config: { damping: 15, stiffness: 140 } });
  const btn = spring({ frame: f - (NOTIFY + 18), fps, config: { damping: 16, stiffness: 140 } });
  const label: React.CSSProperties = { fontFamily: F.u, fontWeight: 800, fontSize: 13, letterSpacing: "0.16em", color: C.ink3 };
  return (
    <AbsoluteFill style={{ background: `radial-gradient(420px 420px at 50% 40%, rgba(242, 169, 59, ${0.1 + (ready ? 0.1 : 0)}), transparent 70%), ${C.app}`, opacity: ramp(f, 0, 10) }}>
      <div style={{ position: "absolute", top: 92, left: 0, right: 0, textAlign: "center", opacity: 1 - Math.min(1, Math.max(0, note)) }}>
        <div style={{ fontFamily: F.d, fontSize: 32, color: C.ink }}>{data.show.title}</div>
        <div style={{ ...label, color: C.gold, marginTop: 8 }}>NEXT: DROP {s.nextDrop}</div>
      </div>
      <div style={{ position: "absolute", top: 196, left: 195 - 130, width: 260, height: 260, transform: `scale(${pulse})` }}>
        <svg width="260" height="260" viewBox="0 0 260 260">
          <circle cx="130" cy="130" r={R} fill="none" stroke={C.surface2} strokeWidth="12" />
          <circle
            cx="130" cy="130" r={R} fill="none" stroke={ready ? C.gold2 : C.gold} strokeWidth="12" strokeLinecap="round"
            strokeDasharray={CIRC} strokeDashoffset={CIRC * (1 - arc)} transform="rotate(-90 130 130)"
            style={{ filter: "drop-shadow(0 0 10px rgba(242, 169, 59, .55))" }}
          />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          {ready ? (
            <>
              <div style={{ fontFamily: F.d, fontSize: 56, lineHeight: 1, color: C.gold2 }}>Ready</div>
              <div style={{ ...label, marginTop: 10 }}>DROP {s.nextDrop}</div>
            </>
          ) : (
            <>
              <div style={{ ...label, marginBottom: 8 }}>UNLOCKS IN</div>
              <div style={{ fontFamily: F.u, fontWeight: 800, fontSize: 40, lineHeight: 1, color: C.ink, fontVariantNumeric: "tabular-nums" }}>{hms}</div>
            </>
          )}
        </div>
      </div>
      <div style={{ position: "absolute", top: 490, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 18px", borderRadius: 999, background: C.surface, fontFamily: F.u, fontWeight: 700, fontSize: 17, color: C.ink2 }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={C.gold} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z" /><path d="M10 20.5a2 2 0 0 0 4 0" />
          </svg>
          Reminder at {s.reminder}, her free slot
        </div>
      </div>
      <div
        style={{
          position: "absolute", top: 560, left: 40, right: 40, height: 60, borderRadius: 30, background: C.gold, color: C.goldInk,
          display: "flex", alignItems: "center", justifyContent: "center", fontFamily: F.u, fontWeight: 800, fontSize: 20,
          opacity: f < NOTIFY + 18 ? 0 : Math.min(1, btn * 1.5), transform: `translateY(${(1 - btn) * 20}px)`,
        }}
      >
        Watch Drop {s.nextDrop}
      </div>

      <div
        style={{
          position: "absolute", top: 54, left: 10, right: 10, padding: "14px 16px", borderRadius: 24, background: "rgba(58, 39, 61, .97)",
          boxShadow: "0 24px 50px -16px rgba(0, 0, 0, .85), inset 0 0 0 1px rgba(247, 236, 223, .1)", display: "flex", gap: 12, zIndex: 40,
          opacity: f < NOTIFY ? 0 : 1, transform: `translateY(${(1 - note) * -150}px)`,
        }}
      >
        <div style={{ width: 42, height: 42, borderRadius: 11, background: C.gold, flex: "none", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: F.d, fontSize: 24, color: C.goldInk }}>D</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontFamily: F.u, fontWeight: 700, fontSize: 12, letterSpacing: "0.06em", color: C.ink3 }}>
            <span>KUKU DAILY</span>
            <span style={{ letterSpacing: 0 }}>now</span>
          </div>
          <div style={{ marginTop: 3, fontFamily: F.u, fontWeight: 800, fontSize: 16, lineHeight: 1.3, color: C.ink }}>
            {data.show.title}: Drop {s.nextDrop} khul gaya
          </div>
          <div style={{ marginTop: 2, fontFamily: F.u, fontWeight: 600, fontSize: 15, lineHeight: 1.35, color: C.ink2 }}>{data.drop.teaser[0]}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const SEG_FROM = 64;
const SEG_EVERY = 11;
const segAt = (i: number) => SEG_FROM + i * SEG_EVERY;

export const GateText: React.FC = () => {
  const f = useCurrentFrame();
  const end = GATE_LEN + 2;
  const max = data.gates.levels[data.gates.levels.length - 1];
  const streak = Array.from({ length: max }, (_, i) => i).filter((i) => f >= segAt(i) + 4).length;
  const active = data.gates.levels.reduce((a, lv, i) => (streak >= lv ? i : a), 0);
  const rows: [string, number[]][] = [["Free", data.gates.free], ["Subscriber", data.gates.subscriber]];
  const cell: React.CSSProperties = { width: 128, textAlign: "center" };
  return (
    <Column>
      <div style={inOut(f, 4, end)}>
        <Kicker>3 · The gate</Kicker>
      </div>
      <div style={{ position: "relative", height: 166, marginTop: 26 }}>
        <div style={{ position: "absolute", inset: 0, ...inOut(f, 8, NOTIFY + 8) }}>
          <Headline size={78}>Tomorrow, the phone buzzes at her free slot.</Headline>
        </div>
        <div style={{ position: "absolute", inset: 0, ...inOut(f, NOTIFY + 6, end) }}>
          <Headline size={78}>
            Even subscribers wait. <span style={{ color: C.gold2 }}>Nobody binges.</span>
          </Headline>
        </div>
      </div>
      <div style={{ position: "relative", height: 46, marginTop: 18 }}>
        <Sub style={{ position: "absolute", inset: 0, ...inOut(f, 14, NOTIFY + 8) }}>
          Drop {s.nextDrop} unlocks after {s.waitH} h. The nudge lands at {s.reminder}.
        </Sub>
        <Sub style={{ position: "absolute", inset: 0, ...inOut(f, NOTIFY + 10, end) }}>Come back daily, wait less.</Sub>
      </div>

      <div style={{ marginTop: 46, ...inOut(f, 44, end) }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <Kicker style={{ color: C.ink2, fontSize: 17, width: 150 }}>Streak</Kicker>
          <div style={{ display: "flex", gap: 8 }}>
            {Array.from({ length: max }, (_, i) => (
              <div key={i} style={{ width: 62, height: 14, borderRadius: 7, background: C.surface2, overflow: "hidden" }}>
                <div style={{ height: "100%", background: C.gold, transformOrigin: "0 50%", transform: `scaleX(${ramp(f, segAt(i), segAt(i) + 8)})` }} />
              </div>
            ))}
          </div>
          <div style={{ fontFamily: F.u, fontWeight: 800, fontSize: 22, color: C.gold2, fontVariantNumeric: "tabular-nums", width: 90 }}>{streak} days</div>
        </div>
        <div style={{ marginTop: 26, display: "flex", alignItems: "center", gap: 18, fontFamily: F.u, fontWeight: 700, fontSize: 17, color: C.ink3, letterSpacing: "0.04em" }}>
          <div style={{ width: 150 }} />
          {data.gates.levels.map((lv, i) => (
            <React.Fragment key={lv}>
              {i > 0 && <div style={{ width: 26 }} />}
              <div style={{ ...cell, color: i === active ? C.gold2 : C.ink3 }}>Streak {lv}{i > 0 ? "+" : ""}</div>
            </React.Fragment>
          ))}
        </div>
        {rows.map(([name, waits]) => (
          <div key={name} style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 18 }}>
            <div style={{ width: 150, fontFamily: F.u, fontWeight: 700, fontSize: 24, color: C.ink2 }}>{name}</div>
            {waits.map((h, i) => (
              <React.Fragment key={i}>
                {i > 0 && <Arrow color={i <= active ? C.gold : "rgba(174, 152, 162, .5)"} />}
                <div
                  style={{
                    ...cell, padding: "6px 0", borderRadius: 16, fontFamily: F.d, fontSize: 44, lineHeight: 1.1,
                    color: i === active ? C.gold2 : "rgba(247, 236, 223, .38)", background: i === active ? C.goldSoft : "transparent",
                    boxShadow: i === active ? "inset 0 0 0 1.5px rgba(242, 169, 59, .4)" : "none",
                  }}
                >
                  {h} h
                </div>
              </React.Fragment>
            ))}
          </div>
        ))}
      </div>
    </Column>
  );
};
