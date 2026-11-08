import React from "react";
import { AbsoluteFill, Sequence, spring, useCurrentFrame, useVideoConfig } from "remotion";
import data from "./data.json";
import { ChatScreen, ONBOARD_LEN, OnboardText } from "./scenes/Onboard";
import { DROP_LEN, DropScreen, DropText } from "./scenes/Drop";
import { GATE_LEN, GateScreen, GateText, gateClock } from "./scenes/Gate";
import { EndCard } from "./scenes/EndCard";
import { Wall } from "./scenes/Wall";
import { Backdrop, Grain, Phone, Vignette, eIO, ramp } from "./ui";

export const DURATION = 900; // 30 s at 30 fps

const ONBOARD = 240;
const DROP = ONBOARD + ONBOARD_LEN; // 405
const GATE = DROP + DROP_LEN; // 615
const END = GATE + GATE_LEN; // 780

const PhoneStage: React.FC = () => {
  const f = useCurrentFrame(); // 0 = ONBOARD
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 17, stiffness: 80 } });
  const out = ramp(f, END - ONBOARD - 2, END - ONBOARD + 16, 0, 1, eIO);
  const gate = f - (GATE - ONBOARD);
  const time = gate >= 0 ? gateClock(gate) : `${((data.session.watchedHour + 11) % 12) + 1}:00`;
  return (
    <Phone
      time={time}
      style={{
        left: 1395 - 207, top: 540 - 434, opacity: ramp(f, 0, 12) * (1 - out),
        transform: `translateY(${(1 - s) * 320 + out * 160}px) rotate(${(1 - s) * -5}deg) scale(${1.1 - out * 0.06})`,
      }}
    >
      <Sequence durationInFrames={ONBOARD_LEN + 12}>
        <ChatScreen />
      </Sequence>
      <Sequence from={DROP - ONBOARD} durationInFrames={DROP_LEN + 12}>
        <DropScreen />
      </Sequence>
      <Sequence from={GATE - ONBOARD}>
        <GateScreen />
      </Sequence>
    </Phone>
  );
};

export const Trailer: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: "#170d18" }}>
      <Backdrop />
      <Sequence durationInFrames={ONBOARD + 6}>
        <AbsoluteFill style={{ opacity: ramp(f, ONBOARD - 14, ONBOARD + 2, 1, 0, eIO) }}>
          <Wall />
        </AbsoluteFill>
      </Sequence>
      <Sequence from={ONBOARD} durationInFrames={ONBOARD_LEN + 6}>
        <OnboardText />
      </Sequence>
      <Sequence from={DROP} durationInFrames={DROP_LEN + 6}>
        <DropText />
      </Sequence>
      <Sequence from={GATE} durationInFrames={GATE_LEN + 6}>
        <GateText />
      </Sequence>
      <Sequence from={ONBOARD} durationInFrames={END - ONBOARD + 20}>
        <PhoneStage />
      </Sequence>
      <Sequence from={END}>
        <EndCard />
      </Sequence>
      <Grain opacity={0.07} />
      <Vignette />
    </AbsoluteFill>
  );
};
