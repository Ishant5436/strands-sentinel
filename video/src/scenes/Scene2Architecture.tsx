import React from "react";
import {interpolate, useCurrentFrame, useVideoConfig} from "remotion";
import {SceneBg, KineticCaption, Pill, springIn} from "../components/primitives";
import {colors, fonts} from "../theme";
import {badges} from "../data";

type Node = {id: string; label: string; x: number; y: number};

const NODES: Node[] = [
  {id: "source", label: "Source Code", x: 960, y: 330},
  {id: "ast", label: "AST Invariant Engine\n(NASA Power of 10)", x: 540, y: 560},
  {id: "secrets", label: "Shannon Entropy\nSecret Scanner", x: 1380, y: 560},
  {id: "agent", label: "Strands Agent\nOrchestrator", x: 960, y: 780},
  {id: "intervention", label: "InterventionHandler", x: 960, y: 960},
];

const EDGES: Array<[string, string]> = [
  ["source", "ast"],
  ["source", "secrets"],
  ["ast", "agent"],
  ["secrets", "agent"],
  ["agent", "intervention"],
];

const byId = (id: string): Node => {
  const found = NODES.find((n) => n.id === id);
  if (!found) {
    throw new Error(`unknown node id: ${id}`);
  }
  return found;
};

const Edge: React.FC<{from: Node; to: Node; progress: number}> = ({from, to, progress}) => {
  const length = Math.hypot(to.x - from.x, to.y - from.y);
  return (
    <line
      x1={from.x}
      y1={from.y}
      x2={to.x}
      y2={to.y}
      stroke={colors.cyan}
      strokeWidth={3}
      strokeDasharray={length}
      strokeDashoffset={length * (1 - progress)}
      opacity={0.75}
    />
  );
};

const NodeBox: React.FC<{node: Node; progress: number}> = ({node, progress}) => (
  <div
    style={{
      position: "absolute",
      left: node.x,
      top: node.y,
      transform: `translate(-50%, -50%) scale(${interpolate(progress, [0, 1], [0.6, 1])})`,
      opacity: progress,
    }}
  >
    <div
      style={{
        background: "rgba(20,27,38,0.9)",
        border: `1.5px solid ${colors.cyan}`,
        borderRadius: 14,
        padding: "14px 22px",
        color: colors.textPrimary,
        fontSize: 22,
        fontWeight: 600,
        textAlign: "center",
        whiteSpace: "pre-line",
        boxShadow: `0 0 30px ${colors.cyanDim}`,
        minWidth: 210,
      }}
    >
      {node.label}
    </div>
  </div>
);

export const Scene2Architecture: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const titleP = springIn(frame, fps, 0);
  const subtitleP = springIn(frame, fps, 20);
  const diagramStart = 260;
  const diagramFrame = Math.max(0, frame - diagramStart);
  const captionStart = 980;

  return (
    <SceneBg>
      <div style={{position: "absolute", top: 70, left: 0, right: 0, textAlign: "center"}}>
        <div
          style={{
            fontFamily: fonts.mono,
            fontSize: 64,
            fontWeight: 800,
            color: colors.textPrimary,
            letterSpacing: 6,
            opacity: titleP,
            transform: `translateY(${interpolate(titleP, [0, 1], [-20, 0])}px)`,
            textShadow: `0 0 40px ${colors.cyanDim}`,
          }}
        >
          STRANDS SENTINEL
        </div>
        <div
          style={{
            fontSize: 26,
            color: colors.textMuted,
            marginTop: 10,
            opacity: subtitleP,
          }}
        >
          Autonomous Mission-Critical AST Safety Auditor
        </div>
        <div style={{marginTop: 22, display: "flex", justifyContent: "center", gap: 16}}>
          {badges.map((b, i) => (
            <Pill key={b} text={b} delay={70 + i * 12} />
          ))}
        </div>
      </div>

      {frame >= diagramStart && (
        <>
          <svg
            width={1920}
            height={1080}
            style={{position: "absolute", top: 0, left: 0}}
            viewBox="0 0 1920 1080"
          >
            {EDGES.map(([a, b], i) => {
              const edgeProgress = interpolate(diagramFrame, [40 + i * 30, 100 + i * 30], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });
              return <Edge key={`${a}-${b}`} from={byId(a)} to={byId(b)} progress={edgeProgress} />;
            })}
          </svg>
          {NODES.map((node, i) => {
            const nodeProgress = springIn(diagramFrame, fps, i * 20);
            return <NodeBox key={node.id} node={node} progress={nodeProgress} />;
          })}
        </>
      )}

      {frame >= captionStart && (
        <div style={{position: "absolute", bottom: 70, left: 0, right: 0, padding: "0 140px"}}>
          <KineticCaption
            text="Built on AWS Strands Agents SDK and MCP. Zero noise. Runs silently in the background."
            startFrame={captionStart}
            fontSize={36}
          />
        </div>
      )}
    </SceneBg>
  );
};
