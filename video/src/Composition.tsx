import React from "react";
import {Composition} from "remotion";
import {TransitionSeries, linearTiming} from "@remotion/transitions";
import {fade} from "@remotion/transitions/fade";
import {SCENE_FRAMES, TOTAL_FRAMES, FPS} from "./theme";
import {Scene1Problem} from "./scenes/Scene1Problem";
import {Scene2Architecture} from "./scenes/Scene2Architecture";
import {Scene3Demo} from "./scenes/Scene3Demo";
import {Scene4Benchmarks} from "./scenes/Scene4Benchmarks";
import {Scene5Outro} from "./scenes/Scene5Outro";

const TRANSITION_FRAMES = 24;

export const StrandsSentinelVideo: React.FC = () => (
  <TransitionSeries>
    <TransitionSeries.Sequence durationInFrames={SCENE_FRAMES.problem}>
      <Scene1Problem />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition
      presentation={fade()}
      timing={linearTiming({durationInFrames: TRANSITION_FRAMES})}
    />
    <TransitionSeries.Sequence durationInFrames={SCENE_FRAMES.architecture}>
      <Scene2Architecture />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition
      presentation={fade()}
      timing={linearTiming({durationInFrames: TRANSITION_FRAMES})}
    />
    <TransitionSeries.Sequence durationInFrames={SCENE_FRAMES.demo}>
      <Scene3Demo />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition
      presentation={fade()}
      timing={linearTiming({durationInFrames: TRANSITION_FRAMES})}
    />
    <TransitionSeries.Sequence durationInFrames={SCENE_FRAMES.benchmarks}>
      <Scene4Benchmarks />
    </TransitionSeries.Sequence>
    <TransitionSeries.Transition
      presentation={fade()}
      timing={linearTiming({durationInFrames: TRANSITION_FRAMES})}
    />
    <TransitionSeries.Sequence durationInFrames={SCENE_FRAMES.outro}>
      <Scene5Outro />
    </TransitionSeries.Sequence>
  </TransitionSeries>
);

const effectiveDuration = TOTAL_FRAMES - TRANSITION_FRAMES * 4;

export const MyComposition = () => {
  return (
    <Composition
      id="StrandsSentinelDemo"
      component={StrandsSentinelVideo}
      durationInFrames={effectiveDuration}
      fps={FPS}
      width={1920}
      height={1080}
    />
  );
};
