import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { C, F } from "./theme";

export const eOut = Easing.bezier(0.16, 1, 0.3, 1);
export const eIO = Easing.bezier(0.65, 0, 0.35, 1);

export const ramp = (f: number, a: number, b: number, from = 0, to = 1, easing: (t: number) => number = eOut) =>
  interpolate(f, [a, b], [from, to], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing });

/** Fade and rise in at `start`; fade and lift out ending at `end` (local frames). */
export const inOut = (f: number, start: number, end = Infinity, dist = 28): React.CSSProperties => {
  const a = ramp(f, start, start + 20);
  const b = end === Infinity ? 1 : ramp(f, end - 12, end, 1, 0, eIO);
  return { opacity: a * b, transform: `translateY(${(1 - a) * dist - (1 - b) * 14}px)` };
};

const rand = (seed: number) => {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
};
export { rand };

const GRAIN =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 .95 0 0 0 0 .88 0 0 0 .6 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E";

/** Film grain: one static noise tile, jumped to a new offset every `every` frames. */
export const Grain: React.FC<{ opacity?: number; every?: number; until?: number }> = ({ opacity = 0.06, every = 3, until = Infinity }) => {
  const f = useCurrentFrame();
  const step = Math.floor(Math.min(f, until) / every);
  return (
    <AbsoluteFill
      style={{
        backgroundImage: `url("${GRAIN}")`,
        backgroundPosition: `${Math.round(rand(step) * 180)}px ${Math.round(rand(step + 0.5) * 180)}px`,
        opacity,
        mixBlendMode: "overlay",
        pointerEvents: "none",
      }}
    />
  );
};

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.55 }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 46%, transparent 52%, rgba(0, 0, 0, ${strength}) 100%)`, pointerEvents: "none" }} />
);

/** Plum night with a slow marigold lamp glow, as in web/style.css body. */
export const Backdrop: React.FC = () => {
  const f = useCurrentFrame();
  const x = 8 + Math.sin(f / 70) * 3;
  const y = -6 + Math.cos(f / 90) * 3;
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(1500px 960px at ${x}% ${y}%, rgba(242, 169, 59, .13), transparent 62%), radial-gradient(1100px 800px at 100% 42%, rgba(236, 106, 82, .07), transparent 60%), ${C.bg}`,
      }}
    />
  );
};

export const Kicker: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ fontFamily: F.u, fontWeight: 800, fontSize: 20, lineHeight: 1, letterSpacing: "0.2em", textTransform: "uppercase", color: C.gold, ...style }}>
    {children}
  </div>
);

export const Headline: React.FC<{ children: React.ReactNode; size?: number; style?: React.CSSProperties }> = ({ children, size = 80, style }) => (
  <div style={{ fontFamily: F.d, fontSize: size, lineHeight: 1.04, letterSpacing: "-0.015em", color: C.ink, textWrap: "balance", ...style } as React.CSSProperties}>
    {children}
  </div>
);

export const Sub: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ fontFamily: F.u, fontWeight: 600, fontSize: 30, lineHeight: 1.4, color: C.ink2, ...style }}>{children}</div>
);

export const Gold: React.FC<{ children: React.ReactNode }> = ({ children }) => <span style={{ color: C.gold2 }}>{children}</span>;

export const Check: React.FC<{ size?: number; color?: string }> = ({ size = 22, color = C.ok }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{ flex: "none" }}>
    <circle cx="12" cy="12" r="11" fill={color} />
    <path d="M7 12.4l3.2 3.2L17.2 8.6" fill="none" stroke={C.app} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Arrow: React.FC<{ color?: string }> = ({ color = C.ink3 }) => (
  <svg width="26" height="14" viewBox="0 0 26 14" style={{ flex: "none" }}>
    <path d="M1 7h22M17 1.5L23 7l-6 5.5" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const StatusBar: React.FC<{ time: string }> = ({ time }) => (
  <div
    style={{
      position: "absolute", top: 0, left: 0, right: 0, height: 52, padding: "0 30px 0 38px", display: "flex", alignItems: "center",
      justifyContent: "space-between", zIndex: 25, fontFamily: F.u, fontWeight: 700, fontSize: 16, color: C.ink, fontVariantNumeric: "tabular-nums",
    }}
  >
    <span>{time}</span>
    <span style={{ display: "flex", gap: 6, alignItems: "center" }}>
      <svg width="18" height="12" viewBox="0 0 18 12" fill={C.ink}>
        <rect x="0" y="8" width="3" height="4" rx="1" /><rect x="5" y="5.5" width="3" height="6.5" rx="1" /><rect x="10" y="3" width="3" height="9" rx="1" /><rect x="15" y="0" width="3" height="12" rx="1" />
      </svg>
      <svg width="26" height="12" viewBox="0 0 26 12">
        <rect x=".5" y=".5" width="22" height="11" rx="3" fill="none" stroke={C.ink} opacity=".5" /><rect x="2" y="2" width="16" height="8" rx="1.5" fill={C.ink} /><rect x="24" y="4" width="1.6" height="4" rx=".8" fill={C.ink} opacity=".5" />
      </svg>
    </span>
  </div>
);

/** 390 x 844 phone, same shell as the prototype's .phone/.screen. */
export const Phone: React.FC<{ children: React.ReactNode; time: string; style?: React.CSSProperties }> = ({ children, time, style }) => (
  <div
    style={{
      position: "absolute", width: 414, height: 868, padding: 12, borderRadius: 60, background: "#0b060b",
      boxShadow: "inset 0 0 0 1.5px #3b2a3d, 0 0 0 1px #050205, 0 60px 110px -30px rgba(0, 0, 0, .9), 0 30px 90px -30px rgba(242, 169, 59, .3)",
      ...style,
    }}
  >
    <div style={{ position: "relative", width: 390, height: 844, borderRadius: 48, overflow: "hidden", background: C.app, isolation: "isolate" }}>
      {children}
      <StatusBar time={time} />
      <div style={{ position: "absolute", top: 11, left: 136, width: 118, height: 34, borderRadius: 20, background: "#000", zIndex: 30 }} />
    </div>
  </div>
);

/** The prototype's drop-player backdrop (web/app.js HAVELI), drawn as JSX. */
export const Haveli: React.FC = () => (
  <svg viewBox="0 0 390 844" preserveAspectRatio="xMidYMid slice" width="100%" height="100%" style={{ display: "block" }}>
    <defs>
      <radialGradient id="lamp" cx="50%" cy="46%" r="40%">
        <stop offset="0" stopColor="#f2a93b" stopOpacity=".75" />
        <stop offset=".45" stopColor="#b8541f" stopOpacity=".28" />
        <stop offset="1" stopColor="#170d18" stopOpacity="0" />
      </radialGradient>
      <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#1b0e16" />
        <stop offset="1" stopColor="#0a0508" />
      </linearGradient>
      <filter id="soft"><feGaussianBlur stdDeviation="14" /></filter>
    </defs>
    <rect width="390" height="844" fill="url(#wall)" />
    <ellipse cx="195" cy="390" rx="210" ry="260" fill="url(#lamp)" />
    <path d="M120 640V330a75 75 0 0 1 150 0v310z" fill="#2a120f" opacity=".9" />
    <path d="M136 640V336a59 59 0 0 1 118 0v304z" fill="#f2a93b" opacity=".22" filter="url(#soft)" />
    <path d="M150 640V350a45 45 0 0 1 90 0v290z" fill="#0b0507" />
    <path d="M168 640v-120h54v120z" fill="#f6c27a" opacity=".1" />
    <g fill="#0d0609">
      <rect x="40" y="250" width="34" height="420" /><rect x="316" y="250" width="34" height="420" />
      <rect x="30" y="236" width="54" height="16" /><rect x="306" y="236" width="54" height="16" />
    </g>
    <g fill="#f2a93b" opacity=".18">
      {[0, 1, 2, 3, 4].map((i) => <circle key={i} cx={133 + i * 31} cy="268" r="3" />)}
    </g>
    <path d="M195 120v120" stroke="#3a2416" strokeWidth="2" />
    <circle cx="195" cy="250" r="9" fill="#ffc56a" />
    <circle cx="195" cy="250" r="40" fill="#f2a93b" opacity=".2" filter="url(#soft)" />
    <ellipse cx="195" cy="660" rx="200" ry="40" fill="#f2a93b" opacity=".08" filter="url(#soft)" />
    <rect y="640" width="390" height="204" fill="#070406" />
  </svg>
);

/** Left text column shared by the phone scenes. */
export const Column: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ position: "absolute", left: 150, top: 0, bottom: 0, width: 800, display: "flex", flexDirection: "column", justifyContent: "center", ...style }}>
    {children}
  </div>
);
