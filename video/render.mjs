import {bundle} from "@remotion/bundler";
import {selectComposition, renderMedia} from "@remotion/renderer";
import path from "path";

const outputLocation = process.argv[2] || "out/video-silent.mp4";

async function main() {
  console.log("bundling...");
  const bundleLocation = await bundle({entryPoint: path.resolve("src/index.ts")});
  console.log("bundled at", bundleLocation);

  const composition = await selectComposition({serveUrl: bundleLocation, id: "StrandsSentinelDemo"});
  console.log(
    "composition:",
    composition.width,
    "x",
    composition.height,
    composition.durationInFrames,
    "frames @",
    composition.fps,
    "fps =",
    (composition.durationInFrames / composition.fps).toFixed(2),
    "seconds"
  );

  const start = Date.now();
  await renderMedia({
    composition,
    serveUrl: bundleLocation,
    codec: "h264",
    outputLocation,
    concurrency: 4,
    onProgress: ({renderedFrames, encodedFrames}) => {
      if (renderedFrames % 100 === 0) {
        process.stdout.write(`rendered ${renderedFrames}/${composition.durationInFrames} encoded ${encodedFrames}\n`);
      }
    },
  });
  const elapsed = ((Date.now() - start) / 1000).toFixed(1);
  console.log(`done in ${elapsed}s -> ${outputLocation}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
