# strands-sentinel demo video

Remotion project that renders `assets/strands_sentinel_demo.mp4`: a 1920x1080,
60fps, ~83 second broadcast-style demo of strands-sentinel. Every number,
code snippet, and rule name shown is either measured directly from the
Python package's own tests/lint/audit output or computed live from its
actual `secret_scanner` code (see `src/data.ts` for the source of each
value) -- nothing in the video is an invented figure.

## Known issue: `npx remotion render` does not work here

`@remotion/cli` 4.0.523's `render` command fails with a misleading
`ENOENT ... bundle.js` error while trying to symbolicate a stack trace,
reproducible even with the sandbox disabled and on both Node 22 and 26.
The underlying `@remotion/bundler` + `@remotion/renderer` APIs work fine
when called directly. Use the scripts in this project instead of the CLI:

```bash
# install (Node 22 LTS recommended; Node 26 hits the same renderer/CLI
# incompatibility independently of the bug above)
npm i

# render a handful of still frames to spot-check the timeline without a
# full render (writes to out/preview/frame-<n>.png)
node preview.mjs 60 700 2900 4500

# full render, silent (no audio track yet)
node render.mjs out/video-silent.mp4

# regenerate the synthesized ambient pad + UI sound cues (ffmpeg lavfi
# only -- no licensed music or recorded samples, no TTS)
./audio/generate_audio.sh

# mux video + audio into the final deliverable
ffmpeg -y -i out/video-silent.mp4 -i audio/full_track.wav \
  -c:v copy -c:a aac -b:a 192k -shortest \
  ../assets/strands_sentinel_demo.mp4
```

## Structure

- `src/theme.ts` -- color tokens, fonts (Google Fonts via `@remotion/google-fonts`), scene frame durations.
- `src/data.ts` -- every fact/number shown on screen, with where it came from.
- `src/scenes/Scene{1..5}*.tsx` -- the five storyboard beats, sequenced via `@remotion/transitions` `TransitionSeries` with a 24-frame crossfade between each.
- `src/components/primitives.tsx` -- reusable glassmorphism cards, kinetic-typography captions, animated counters, and a Prism-based syntax-highlighted code block.
- `audio/generate_audio.sh` -- synthesizes the entire audio track from ffmpeg `lavfi` sources (sine tones + tremolo for the ambient pad, short tone sequences for UI cues), gain-staged and mixed at timestamps computed from `src/theme.ts`'s own scene durations. `.wav` outputs are gitignored; only the script is tracked.

`video/audio/*.wav`, `video/out/`, and `video/node_modules/` are gitignored as regenerable build output.
