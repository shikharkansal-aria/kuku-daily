// Beat 3: onboarding chat on the phone; profile chips fly out beside it.
import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import data from "../data.json";
import { C, F } from "../theme";
import { Check, Column, Headline, Kicker, inOut, ramp } from "../ui";

const qStart = (i: number) => 16 + i * 26;
const TYPE = 7; // frames between question and first typed character
const CPS = 3; // characters per frame
const answerDone = (i: number) => qStart(i) + TYPE + Math.ceil(data.answers[i].length / CPS);

export const ONBOARD_LEN = 165;

export const ChatScreen: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const done = data.answers.filter((_, i) => f >= answerDone(i)).length;
  return (
    <AbsoluteFill style={{ background: `radial-gradient(520px 420px at 50% -12%, rgba(242, 169, 59, .14), transparent 70%), ${C.app}`, opacity: ramp(f, 0, 10) }}>
      <div style={{ position: "absolute", top: 62, left: 22, right: 22 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
          <div style={{ fontFamily: F.d, fontSize: 27, color: C.ink }}>
            Kuku <span style={{ color: C.gold }}>Daily</span>
          </div>
          <div style={{ fontFamily: F.u, fontWeight: 800, fontSize: 14, color: C.ink3, fontVariantNumeric: "tabular-nums" }}>{done} / 5</div>
        </div>
        <div style={{ display: "flex", gap: 5, marginTop: 12 }}>
          {data.answers.map((_, i) => (
            <div key={i} style={{ flex: 1, height: 4, borderRadius: 2, background: "rgba(247, 236, 223, .16)", overflow: "hidden" }}>
              <div style={{ height: "100%", background: C.gold, transformOrigin: "0 50%", transform: `scaleX(${ramp(f, answerDone(i) - 2, answerDone(i) + 6)})` }} />
            </div>
          ))}
        </div>
      </div>

      <div style={{ position: "absolute", top: 136, left: 16, right: 16, display: "flex", flexDirection: "column", gap: 8 }}>
        {data.questions.map((q, i) => {
          const qs = qStart(i);
          if (f < qs) return null;
          const s = spring({ frame: f - qs, fps, config: { damping: 14, stiffness: 170 } });
          const typed = f >= qs + TYPE ? Math.min(data.answers[i].length, (f - qs - TYPE + 1) * CPS) : 0;
          const typing = typed < data.answers[i].length;
          return (
            <React.Fragment key={i}>
              <div
                style={{
                  alignSelf: "flex-start", maxWidth: 300, marginTop: i ? 8 : 0, padding: "10px 15px", borderRadius: "18px 18px 18px 6px",
                  background: C.surface, color: C.ink, fontFamily: F.u, fontWeight: 600, fontSize: 17, lineHeight: 1.35,
                  opacity: Math.min(1, s * 1.5), transform: `translateY(${(1 - s) * 12}px) scale(${0.86 + 0.14 * s})`, transformOrigin: "0% 100%",
                }}
              >
                {q}
              </div>
              {typed > 0 && (
                <div
                  style={{
                    alignSelf: "flex-end", maxWidth: 292, padding: "10px 15px", borderRadius: "18px 18px 6px 18px",
                    background: C.gold, color: C.goldInk, fontFamily: F.u, fontWeight: 700, fontSize: 17, lineHeight: 1.35,
                  }}
                >
                  {data.answers[i].slice(0, typed)}
                  {typing && <span style={{ display: "inline-block", width: 2, height: 18, marginLeft: 2, verticalAlign: -3, background: C.goldInk }} />}
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const CHIPS = [
  cap(data.persona.who),
  `Free at ${data.persona.slots.join(" and ")}`,
  cap(data.persona.likes.join(", ")),
  `Family-safe, watches with ${data.persona.watchWith}`,
];

export const OnboardText: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const out = ramp(f, ONBOARD_LEN - 8, ONBOARD_LEN + 4, 1, 0);
  return (
    <Column>
      <div style={inOut(f, 4, ONBOARD_LEN + 4)}>
        <Kicker>1 · Onboarding</Kicker>
        <Headline size={78} style={{ marginTop: 26 }}>
          Five questions. She answers in her own words.
        </Headline>
      </div>
      <div style={{ marginTop: 60, opacity: out }}>
        <Kicker style={{ color: C.ink3, fontSize: 17, opacity: ramp(f, answerDone(0) - 8, answerDone(0) + 4) }}>Her profile</Kicker>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 14, marginTop: 20, width: 760 }}>
          {CHIPS.map((c, i) => {
            const s = spring({ frame: f - answerDone(i), fps, config: { damping: 13, stiffness: 110 } });
            const safe = i === 3;
            return (
              <div
                key={c}
                style={{
                  display: "flex", alignItems: "center", gap: 12, padding: "13px 24px 13px 18px", borderRadius: 999,
                  background: safe ? C.goldSoft : C.surface2, boxShadow: `inset 0 0 0 1.5px ${safe ? "rgba(242, 169, 59, .45)" : C.line2}`,
                  color: safe ? C.gold2 : C.ink, fontFamily: F.u, fontWeight: 700, fontSize: 28, lineHeight: 1.2,
                  opacity: f < answerDone(i) ? 0 : Math.min(1, s * 2),
                  transform: `translate(${(1 - s) * 680}px, ${(1 - s) * (i * 40 - 60)}px) scale(${0.6 + 0.4 * s})`,
                }}
              >
                {safe ? <Check size={26} color={C.gold} /> : <span style={{ width: 12, height: 12, borderRadius: 6, background: C.gold, flex: "none" }} />}
                {c}
              </div>
            );
          })}
        </div>
      </div>
    </Column>
  );
};
