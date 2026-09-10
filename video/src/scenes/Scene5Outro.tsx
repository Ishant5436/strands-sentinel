import React from "react";
import {interpolate, useCurrentFrame, useVideoConfig} from "remotion";
import {SceneBg, GlassCard, springIn} from "../components/primitives";
import {colors, fonts} from "../theme";
import {outro} from "../data";

export const Scene5Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cardP = springIn(frame, fps, 0);

  return (
    <SceneBg>
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: `translate(-50%, -50%) scale(${interpolate(cardP, [0, 1], [0.9, 1])})`,
          opacity: cardP,
          width: 1100,
        }}
      >
        <GlassCard glow={colors.cyanDim} style={{textAlign: "center", padding: 56}}>
          <div
            style={{
              fontFamily: fonts.mono,
              fontSize: 56,
              fontWeight: 800,
              letterSpacing: 5,
              color: colors.textPrimary,
              textShadow: `0 0 40px ${colors.cyanDim}`,
            }}
          >
            {outro.headline}
          </div>
          <div style={{fontSize: 24, color: colors.textMuted, marginTop: 14}}>{outro.subtitle}</div>

          <div style={{marginTop: 34, height: 1, background: colors.border}} />

          <div style={{marginTop: 30, fontSize: 22, color: colors.cyan, fontWeight: 600}}>{outro.event}</div>

          <div style={{marginTop: 24, display: "flex", flexDirection: "column", gap: 8}}>
            <MetaLine label="Author" value={outro.author} delay={70} frame={frame} fps={fps} />
            <MetaLine label="GitHub" value={outro.github} delay={90} frame={frame} fps={fps} />
            <MetaLine label="Demo Space" value={outro.demoSpace} delay={110} frame={frame} fps={fps} />
          </div>
        </GlassCard>
      </div>
    </SceneBg>
  );
};

const MetaLine: React.FC<{label: string; value: string; delay: number; frame: number; fps: number}> = ({
  label,
  value,
  delay,
  frame,
  fps,
}) => {
  const p = springIn(frame, fps, delay);
  return (
    <div style={{opacity: p, fontFamily: fonts.mono, fontSize: 19, color: colors.textMuted}}>
      <span style={{color: colors.emerald}}>{label}:</span> {value}
    </div>
  );
};
