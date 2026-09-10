import React from "react";
import {interpolate, useCurrentFrame, useVideoConfig} from "remotion";
import {SceneBg, GlassCard, CountUpNumber, springIn} from "../components/primitives";
import {colors, fonts} from "../theme";
import {benchmarkTiles, techStack} from "../data";

const TILE_POSITIONS = [
  {top: 210, left: 340},
  {top: 210, left: 1080},
  {top: 470, left: 340},
  {top: 470, left: 1080},
];

export const Scene4Benchmarks: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const titleP = springIn(frame, fps, 0);
  const stripStart = 480;

  return (
    <SceneBg>
      <div style={{position: "absolute", top: 70, left: 0, right: 0, textAlign: "center", opacity: titleP}}>
        <div style={{fontSize: 40, fontWeight: 700, color: colors.textPrimary}}>Measured, Not Marketed</div>
      </div>

      {benchmarkTiles.map((tile, i) => {
        const pos = TILE_POSITIONS[i];
        const delay = 60 + i * 25;
        const p = springIn(frame, fps, delay);
        return (
          <div
            key={tile.label}
            style={{
              position: "absolute",
              top: pos.top,
              left: pos.left,
              width: 500,
              opacity: p,
              transform: `translateY(${interpolate(p, [0, 1], [30, 0])}px)`,
            }}
          >
            <GlassCard glow={colors.cyanDim} style={{textAlign: "center"}}>
              <CountUpNumber value={tile.value} startFrame={delay} fontSize={64} />
              <div style={{color: colors.textMuted, fontSize: 20, marginTop: 10}}>{tile.label}</div>
            </GlassCard>
          </div>
        );
      })}

      {frame >= stripStart && (
        <div
          style={{
            position: "absolute",
            bottom: 90,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            gap: 28,
          }}
        >
          {techStack.map((t, i) => {
            const p = springIn(frame, fps, stripStart + i * 10);
            return (
              <div
                key={t}
                style={{
                  fontFamily: fonts.mono,
                  color: colors.emerald,
                  fontSize: 22,
                  opacity: p,
                  border: `1px solid ${colors.emeraldDim}`,
                  borderRadius: 8,
                  padding: "8px 18px",
                }}
              >
                {t}
              </div>
            );
          })}
        </div>
      )}
    </SceneBg>
  );
};
