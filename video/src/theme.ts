import {loadFont as loadInter} from "@remotion/google-fonts/Inter";
import {loadFont as loadMono} from "@remotion/google-fonts/JetBrainsMono";

const {fontFamily: interFamily} = loadInter("normal", {weights: ["400", "600", "700", "800"], subsets: ["latin"]});
const {fontFamily: monoFamily} = loadMono("normal", {weights: ["400", "700"], subsets: ["latin"]});

export const colors = {
  bg: "#0f141c",
  bgCard: "#141b26",
  bgCardAlt: "#111823",
  cyan: "#38bdf8",
  cyanDim: "rgba(56, 189, 248, 0.35)",
  emerald: "#34d399",
  emeraldDim: "rgba(52, 211, 153, 0.35)",
  rose: "#f87171",
  roseDim: "rgba(248, 113, 113, 0.35)",
  textPrimary: "#e2e8f0",
  textMuted: "#8291a6",
  border: "rgba(148, 163, 184, 0.16)",
};

export const fonts = {
  sans: interFamily,
  mono: monoFamily,
};

export const FPS = 60;

export const SCENE_FRAMES = {
  problem: 15 * FPS,
  architecture: 20 * FPS,
  demo: 30 * FPS,
  benchmarks: 13 * FPS,
  outro: 7 * FPS,
};

export const TOTAL_FRAMES = Object.values(SCENE_FRAMES).reduce((a, b) => a + b, 0);
