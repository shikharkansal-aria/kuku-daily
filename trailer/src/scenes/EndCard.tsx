// Beat 6: end card.
import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, F } from "../theme";
import { inOut, ramp } from "../ui";

export const EndCard: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const word = (d: number) => {
    const s = spring({ frame: f - d, fps, config: { damping: 16, stiffness: 110 } });
    return { display: "inline-block", opacity: Math.min(1, s * 1.4), transform: `translateY(${(1 - s) * 60}px)` };
  };
  const glow = ramp(f, 0, 40);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", textAlign: "center" }}>
      <AbsoluteFill style={{ background: `radial-gradient(900px 520px at 50% 40%, rgba(242, 169, 59, ${0.16 * glow}), transparent 70%)` }} />
      <div style={{ position: "relative", marginTop: -40 }}>
        <div style={{ fontFamily: F.d, fontSize: 176, lineHeight: 1, letterSpacing: "-0.02em", color: C.ink }}>
          <span style={word(6)}>Kuku</span> <span style={{ ...word(12), color: C.gold }}>Daily</span>
        </div>
        <div style={{ marginTop: 34, fontFamily: F.d, fontSize: 54, lineHeight: 1.15, color: C.ink, ...inOut(f, 26) }}>Two shows, not thirty.</div>
        <div style={{ marginTop: 4, fontFamily: F.d, fontSize: 54, lineHeight: 1.15, color: C.ink2, ...inOut(f, 36) }}>Then the story brings you back.</div>
        <div style={{ marginTop: 46, display: "flex", justifyContent: "center", ...inOut(f, 50) }}>
          <div style={{ padding: "14px 30px", borderRadius: 999, boxShadow: `inset 0 0 0 1.5px rgba(242, 169, 59, .5)`, background: C.goldSoft, fontFamily: F.u, fontWeight: 700, fontSize: 32, color: C.gold2 }}>
            shikharkansal-aria.github.io/kuku-daily
          </div>
        </div>
        <div style={{ marginTop: 40, fontFamily: F.u, fontWeight: 600, fontSize: 21, color: C.ink3, ...inOut(f, 62) }}>
          Concept prototype by Shikhar Kansal. Not an official Kuku product.
        </div>
      </div>
    </AbsoluteFill>
  );
};
