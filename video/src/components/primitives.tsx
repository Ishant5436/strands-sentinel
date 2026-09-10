import React from "react";
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {Highlight, themes} from "prism-react-renderer";
import {colors, fonts} from "../theme";

export const SceneBg: React.FC<{children: React.ReactNode}> = ({children}) => (
  <AbsoluteFill style={{backgroundColor: colors.bg, fontFamily: fonts.sans}}>
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 20% 15%, rgba(56,189,248,0.10), transparent 45%), " +
          "radial-gradient(circle at 85% 80%, rgba(52,211,153,0.08), transparent 45%)",
      }}
    />
    {children}
  </AbsoluteFill>
);

export const springIn = (frame: number, fps: number, delay = 0) =>
  spring({frame: frame - delay, fps, config: {damping: 200, stiffness: 120, mass: 0.6}});

export const GlassCard: React.FC<{
  children: React.ReactNode;
  glow?: string;
  style?: React.CSSProperties;
}> = ({children, glow = colors.cyanDim, style}) => (
  <div
    style={{
      background: "rgba(20, 27, 38, 0.72)",
      border: `1px solid ${colors.border}`,
      borderRadius: 20,
      boxShadow: `0 0 60px ${glow}, inset 0 1px 0 rgba(255,255,255,0.04)`,
      backdropFilter: "blur(6px)",
      padding: 32,
      ...style,
    }}
  >
    {children}
  </div>
);

export const Pill: React.FC<{text: string; tone?: "cyan" | "emerald" | "rose"; delay?: number}> = ({
  text,
  tone = "cyan",
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = springIn(frame, fps, delay);
  const toneColor = tone === "cyan" ? colors.cyan : tone === "emerald" ? colors.emerald : colors.rose;
  return (
    <span
      style={{
        display: "inline-block",
        padding: "10px 22px",
        borderRadius: 999,
        border: `1px solid ${toneColor}`,
        color: toneColor,
        fontSize: 22,
        fontWeight: 600,
        opacity: p,
        transform: `translateY(${interpolate(p, [0, 1], [16, 0])}px)`,
        background: `${toneColor}14`,
      }}
    >
      {text}
    </span>
  );
};

export const KineticCaption: React.FC<{text: string; startFrame?: number; fontSize?: number}> = ({
  text,
  startFrame = 0,
  fontSize = 40,
}) => {
  const frame = useCurrentFrame() - startFrame;
  const {fps} = useVideoConfig();
  const words = text.split(" ");
  assertWordCount(words);
  return (
    <div style={{fontSize, fontWeight: 700, color: colors.textPrimary, lineHeight: 1.3, textAlign: "center"}}>
      {words.map((word, i) => {
        const wordDelay = i * 2.4;
        const p = springIn(frame, fps, wordDelay);
        return (
          <span
            key={`${word}-${i}`}
            style={{
              display: "inline-block",
              opacity: interpolate(p, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(p, [0, 1], [22, 0])}px)`,
              marginRight: 14,
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};

function assertWordCount(words: string[]): void {
  if (words.length === 0) {
    throw new Error("KineticCaption requires non-empty text");
  }
  if (words.some((w) => w.length === 0)) {
    throw new Error("KineticCaption received an empty word token");
  }
}

export const CountUpNumber: React.FC<{value: string; startFrame?: number; fontSize?: number; color?: string}> = ({
  value,
  startFrame = 0,
  fontSize = 72,
  color = colors.cyan,
}) => {
  const frame = useCurrentFrame() - startFrame;
  const {fps} = useVideoConfig();
  const p = springIn(frame, fps, 0);
  const numericMatch = value.match(/[\d.]+/);
  const targetNumber = numericMatch ? Number.parseFloat(numericMatch[0]) : null;
  const display =
    targetNumber === null
      ? value
      : value.replace(numericMatch![0], formatCounted(targetNumber, p, numericMatch![0]));
  return (
    <div
      style={{
        fontFamily: fonts.mono,
        fontSize,
        fontWeight: 700,
        color,
        opacity: interpolate(p, [0, 0.3], [0, 1], {extrapolateRight: "clamp"}),
      }}
    >
      {display}
    </div>
  );
};

function formatCounted(target: number, progress: number, original: string): string {
  const current = target * Math.min(1, Math.max(0, progress));
  const decimals = original.includes(".") ? original.split(".")[1].length : 0;
  return current.toFixed(decimals);
}

export const CodeBlock: React.FC<{code: string; language?: string; fontSize?: number}> = ({
  code,
  language = "python",
  fontSize = 26,
}) => (
  <Highlight theme={themes.nightOwl} code={code} language={language}>
    {({tokens, getLineProps, getTokenProps}) => (
      <pre
        style={{
          fontFamily: fonts.mono,
          fontSize,
          lineHeight: 1.6,
          margin: 0,
          background: "transparent",
        }}
      >
        {tokens.map((line, i) => (
          // eslint-disable-next-line react/jsx-key
          <div {...getLineProps({line})} key={`line-${i}`}>
            {line.map((token, key) => (
              // eslint-disable-next-line react/jsx-key
              <span {...getTokenProps({token})} key={`token-${key}`} />
            ))}
          </div>
        ))}
      </pre>
    )}
  </Highlight>
);
