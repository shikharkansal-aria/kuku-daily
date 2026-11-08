import { loadFont as loadRozha } from "@remotion/google-fonts/RozhaOne";
import { loadFont as loadManrope } from "@remotion/google-fonts/Manrope";

const rozha = loadRozha("normal", { weights: ["400"], subsets: ["latin"] });
const manrope = loadManrope("normal", { weights: ["500", "600", "700", "800"], subsets: ["latin"] });

// Same tokens as web/style.css so the trailer reads as the same product.
export const C = {
  bg: "#170d18",
  bg2: "#1f1321",
  app: "#120a13",
  surface: "#2a1b2d",
  surface2: "#362339",
  line: "rgba(247, 236, 223, .12)",
  line2: "rgba(247, 236, 223, .22)",
  ink: "#f7ecdf",
  ink2: "#d9c7bc",
  ink3: "#ae98a2",
  gold: "#f2a93b",
  gold2: "#ffc56a",
  goldInk: "#211204",
  goldSoft: "rgba(242, 169, 59, .14)",
  ok: "#86cfa0",
  red: "#ec6a52",
};

export const F = {
  d: `"${rozha.fontFamily}", Georgia, serif`,
  u: `"${manrope.fontFamily}", system-ui, sans-serif`,
};
