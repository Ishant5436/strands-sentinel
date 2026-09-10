import React from "react";
import {interpolate, useCurrentFrame, useVideoConfig} from "remotion";
import {SceneBg, GlassCard, KineticCaption, CodeBlock, springIn} from "../components/primitives";
import {colors} from "../theme";
import {linterNoise, dangerousCodeBefore} from "../data";

const TOAST_POSITIONS = [
  {top: "12%", left: "8%"},
  {top: "22%", left: "62%"},
  {top: "48%", left: "4%"},
  {top: "58%", left: "68%"},
  {top: "76%", left: "30%"},
];

const Toast: React.FC<{text: string; index: number; localFrame: number; fps: number}> = ({
  text,
  index,
  localFrame,
  fps,
}) => {
  const delay = index * 6;
  const p = springIn(localFrame, fps, delay);
  const fadeOut = interpolate(localFrame, [270, 320], [1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const pos = TOAST_POSITIONS[index % TOAST_POSITIONS.length];
  return (
    <div
      style={{
        position: "absolute",
        ...pos,
        opacity: p * fadeOut,
        transform: `scale(${interpolate(p, [0, 1], [0.7, 1])}) rotate(${index % 2 === 0 ? -2 : 2}deg)`,
        background: "rgba(30,20,22,0.92)",
        border: `1px solid ${colors.roseDim}`,
        borderRadius: 10,
        padding: "10px 16px",
        color: "#fca5a5",
        fontSize: 18,
        maxWidth: 280,
        boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
      }}
    >
      {text}
    </div>
  );
};

export const Scene1Problem: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const codeRevealChars = Math.floor(interpolate(frame, [0, 150], [0, 260], {extrapolateRight: "clamp"}));
  const noiseWindowStart = 180;
  const showNoise = frame >= noiseWindowStart && frame < 620;
  const dangerP = springIn(frame, fps, 500);
  const captionStart = 720;

  return (
    <SceneBg>
      <div
        style={{
          position: "absolute",
          top: 90,
          left: "50%",
          transform: "translateX(-50%)",
          width: 980,
        }}
      >
        <GlassCard glow={dangerP > 0.4 ? colors.roseDim : colors.cyanDim}>
          <div style={{color: colors.textMuted, fontSize: 18, marginBottom: 12}}>quant_engine.py</div>
          {frame < 480 ? (
            <div style={{minHeight: 220}}>
              <TypedCode text={"# calculating position sizing...\n# risk engine v3"} charsRevealed={codeRevealChars} />
            </div>
          ) : (
            <CodeBlock code={dangerousCodeBefore} fontSize={26} />
          )}
        </GlassCard>
      </div>

      {showNoise &&
        linterNoise.map((text, i) => (
          <Toast key={text} text={text} index={i} localFrame={frame - noiseWindowStart} fps={fps} />
        ))}

      {frame >= captionStart && (
        <div style={{position: "absolute", bottom: 90, left: 0, right: 0, padding: "0 140px"}}>
          <KineticCaption
            text="Traditional linters flood you with noise. Mission-critical bugs still slip through."
            startFrame={captionStart}
            fontSize={38}
          />
        </div>
      )}
    </SceneBg>
  );
};

const TypedCode: React.FC<{text: string; charsRevealed: number}> = ({text, charsRevealed}) => {
  const visible = text.slice(0, charsRevealed);
  return (
    <pre
      style={{
        fontFamily: "monospace",
        fontSize: 26,
        color: colors.emerald,
        lineHeight: 1.6,
        margin: 0,
        whiteSpace: "pre-wrap",
      }}
    >
      {visible}
      <span style={{opacity: charsRevealed % 20 < 10 ? 1 : 0}}>|</span>
    </pre>
  );
};
