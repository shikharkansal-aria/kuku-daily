import React from "react";
import { Composition } from "remotion";
import { Trailer, DURATION } from "./Trailer";

export const RemotionRoot: React.FC = () => (
  <Composition id="Trailer" component={Trailer} durationInFrames={DURATION} fps={30} width={1920} height={1080} />
);
