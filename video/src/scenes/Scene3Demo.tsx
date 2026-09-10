import React from "react";
import {interpolate, useCurrentFrame} from "remotion";
import {AlertTriangle, CheckCircle2, MousePointer2, ShieldAlert} from "lucide-react";
import {SceneBg, GlassCard, KineticCaption, CodeBlock, springIn} from "../components/primitives";
import {colors, fonts} from "../theme";
import {cleanCode, dangerousCodeBefore, dangerousCodeAfter, violations, remediationGuidance} from "../data";

const PART_A_END = 600;
const MODAL_START = 780;
const CURSOR_START = 900;
const GUIDANCE_START = 1040;
const DIFF_START = 1220;
const TESTS_START = 1460;
const CAPTION_B_START = 1640;

const Hud: React.FC<{frame: number}> = ({frame}) => {
  const p = springIn(frame, 60, 130);
  return (
    <div
      style={{
        position: "absolute",
        top: 60,
        right: 60,
        opacity: p,
        transform: `translateX(${interpolate(p, [0, 1], [40, 0])}px)`,
      }}
    >
      <GlassCard glow={colors.emeraldDim} style={{padding: "16px 24px"}}>
        <div style={{display: "flex", alignItems: "center", gap: 10, color: colors.emerald, fontFamily: fonts.mono, fontSize: 20}}>
          <CheckCircle2 size={22} />
          <span>AST Scan: 13.6ms (0 violations)</span>
        </div>
        <div style={{display: "flex", alignItems: "center", gap: 10, color: colors.emerald, fontFamily: fonts.mono, fontSize: 20, marginTop: 8}}>
          <CheckCircle2 size={22} />
          <span>Secrets: 2.6ms (Clean)</span>
        </div>
      </GlassCard>
    </div>
  );
};

const InterventionModal: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - MODAL_START;
  const p = springIn(Math.max(0, local), 60, 0);
  const clicked = frame >= CURSOR_START + 40;
  return (
    <div
      style={{
        position: "absolute",
        top: 190,
        left: "50%",
        transform: `translate(-50%, ${interpolate(p, [0, 1], [-60, 0])}px)`,
        opacity: p,
        width: 1180,
      }}
    >
      <GlassCard glow={colors.roseDim} style={{border: `1.5px solid ${colors.rose}`}}>
        <div style={{display: "flex", alignItems: "center", gap: 12, color: colors.rose, fontSize: 26, fontWeight: 700}}>
          <ShieldAlert size={30} />
          STRANDS SENTINEL: HUMAN INTERVENTION REQUIRED
        </div>
        <div style={{marginTop: 20, display: "flex", flexDirection: "column", gap: 12}}>
          {violations.map((v) => (
            <div key={v.rule} style={{display: "flex", gap: 12, alignItems: "flex-start"}}>
              <AlertTriangle size={22} color={colors.rose} style={{marginTop: 2, flexShrink: 0}} />
              <div>
                <div style={{color: colors.textPrimary, fontSize: 21}}>{v.label}</div>
                <div style={{color: colors.textMuted, fontFamily: fonts.mono, fontSize: 16}}>{v.rule}</div>
              </div>
            </div>
          ))}
        </div>
        <div style={{marginTop: 26, display: "flex", gap: 20}}>
          <ModalButton label="[ A ] View Remediation Guidance" active={clicked} tone="emerald" />
          <ModalButton label="[ B ] Abort & Reject Commit" active={false} tone="rose" />
        </div>
      </GlassCard>
    </div>
  );
};

const ModalButton: React.FC<{label: string; active: boolean; tone: "emerald" | "rose"}> = ({label, active, tone}) => {
  const toneColor = tone === "emerald" ? colors.emerald : colors.rose;
  return (
    <div
      style={{
        padding: "12px 22px",
        borderRadius: 10,
        border: `1.5px solid ${toneColor}`,
        color: active ? colors.bg : toneColor,
        background: active ? toneColor : "transparent",
        fontSize: 19,
        fontWeight: 600,
        fontFamily: fonts.mono,
        transition: "none",
      }}
    >
      {label}
    </div>
  );
};

const Cursor: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - CURSOR_START;
  if (local < 0 || local > 90) return null;
  const p = interpolate(local, [0, 40], [0, 1], {extrapolateRight: "clamp"});
  const startX = 1400;
  const startY = 760;
  const endX = 1010;
  const endY = 700;
  const x = interpolate(p, [0, 1], [startX, endX]);
  const y = interpolate(p, [0, 1], [startY, endY]);
  const clickPulse = interpolate(local, [40, 55, 70], [0, 1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return (
    <div style={{position: "absolute", left: x, top: y}}>
      <MousePointer2 size={30} color={colors.textPrimary} fill={colors.textPrimary} />
      <div
        style={{
          position: "absolute",
          top: -10,
          left: -10,
          width: 50,
          height: 50,
          borderRadius: "50%",
          border: `2px solid ${colors.emerald}`,
          opacity: clickPulse,
          transform: `scale(${1 + clickPulse})`,
        }}
      />
    </div>
  );
};

const GuidancePanel: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - GUIDANCE_START;
  if (local < 0) return null;
  return (
    <div style={{position: "absolute", top: 620, left: "50%", transform: "translateX(-50%)", width: 1180}}>
      <GlassCard glow={colors.emeraldDim}>
        <div style={{color: colors.emerald, fontSize: 20, fontWeight: 700, marginBottom: 14}}>
          Remediation guidance (from strands_sentinel.agent):
        </div>
        {remediationGuidance.map((g, i) => {
          const p = springIn(local, 60, i * 20);
          return (
            <div
              key={g}
              style={{
                opacity: p,
                transform: `translateX(${interpolate(p, [0, 1], [-16, 0])}px)`,
                color: colors.textPrimary,
                fontSize: 20,
                marginBottom: 10,
                fontFamily: fonts.mono,
              }}
            >
              {`> ${g}`}
            </div>
          );
        })}
      </GlassCard>
    </div>
  );
};

const DiffView: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - DIFF_START;
  if (local < 0) return null;
  const showAfter = local > 110;
  return (
    <div style={{position: "absolute", top: 260, left: "50%", transform: "translateX(-50%)", width: 1000}}>
      <GlassCard glow={showAfter ? colors.emeraldDim : colors.roseDim}>
        <div style={{color: colors.textMuted, fontSize: 16, marginBottom: 10}}>
          {showAfter ? "calculate_spread() — after developer applies the fix" : "calculate_spread() — before"}
        </div>
        <CodeBlock code={showAfter ? dangerousCodeAfter : dangerousCodeBefore} fontSize={24} />
      </GlassCard>
    </div>
  );
};

const TestRun: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - TESTS_START;
  if (local < 0) return null;
  const p = interpolate(local, [0, 120], [0, 85], {extrapolateRight: "clamp"});
  const passed = Math.floor(p);
  return (
    <div style={{position: "absolute", top: 300, left: "50%", transform: "translateX(-50%)", width: 700, textAlign: "center"}}>
      <GlassCard glow={colors.emeraldDim}>
        <div style={{color: colors.textMuted, fontSize: 18, marginBottom: 12}}>make test</div>
        <div style={{fontFamily: fonts.mono, fontSize: 56, fontWeight: 700, color: colors.emerald}}>
          {passed} / 85 passed
        </div>
        <div
          style={{
            marginTop: 16,
            height: 10,
            borderRadius: 6,
            background: "rgba(255,255,255,0.08)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${(passed / 85) * 100}%`,
              background: colors.emerald,
            }}
          />
        </div>
      </GlassCard>
    </div>
  );
};

export const Scene3Demo: React.FC = () => {
  const frame = useCurrentFrame();
  const isPartA = frame < PART_A_END;

  return (
    <SceneBg>
      {isPartA && (
        <>
          <div style={{position: "absolute", top: 110, left: "50%", transform: "translateX(-50%)", width: 900}}>
            <GlassCard glow={colors.emeraldDim}>
              <div style={{color: colors.textMuted, fontSize: 18, marginBottom: 12}}>risk_engine.py</div>
              <CodeBlock code={cleanCode} fontSize={26} />
            </GlassCard>
          </div>
          <Hud frame={frame} />
          {frame >= 320 && (
            <div style={{position: "absolute", bottom: 90, left: 0, right: 0, padding: "0 160px"}}>
              <KineticCaption
                text="Compliant code passes silently. Developer flow is never broken."
                startFrame={320}
                fontSize={36}
              />
            </div>
          )}
        </>
      )}

      {!isPartA && (
        <>
          {frame < MODAL_START && (
            <div style={{position: "absolute", top: 300, left: "50%", transform: "translateX(-50%)", width: 900}}>
              <GlassCard glow={colors.roseDim} style={{border: `1.5px solid ${colors.rose}`}}>
                <div style={{color: colors.textMuted, fontSize: 18, marginBottom: 12}}>risk_engine.py</div>
                <CodeBlock code={dangerousCodeBefore} fontSize={26} />
              </GlassCard>
            </div>
          )}
          {frame >= MODAL_START && frame < GUIDANCE_START + 10 && <InterventionModal frame={frame} />}
          {frame >= CURSOR_START && <Cursor frame={frame} />}
          {frame >= GUIDANCE_START && frame < DIFF_START && <GuidancePanel frame={frame} />}
          {frame >= DIFF_START && frame < TESTS_START && <DiffView frame={frame} />}
          {frame >= TESTS_START && <TestRun frame={frame} />}
          {frame >= CAPTION_B_START && (
            <div style={{position: "absolute", bottom: 70, left: 0, right: 0, padding: "0 130px"}}>
              <KineticCaption
                text="The agent only interrupts when a human decision is required."
                startFrame={CAPTION_B_START}
                fontSize={36}
              />
            </div>
          )}
        </>
      )}
    </SceneBg>
  );
};
