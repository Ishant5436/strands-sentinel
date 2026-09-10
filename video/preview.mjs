import {bundle} from "@remotion/bundler";
import {selectComposition, renderStill} from "@remotion/renderer";
import path from "path";
import fs from "fs";

const FRAMES = process.argv.slice(2).map(Number);
if (FRAMES.length === 0) {
  console.error("usage: node preview.mjs <frame> [frame...]");
  process.exit(1);
}

async function main() {
  const bundleLocation = await bundle({entryPoint: path.resolve("src/index.ts")});
  const composition = await selectComposition({serveUrl: bundleLocation, id: "StrandsSentinelDemo"});
  console.log("composition:", composition.width, "x", composition.height, composition.durationInFrames, "frames @", composition.fps, "fps");
  fs.mkdirSync("out/preview", {recursive: true});
  for (const frame of FRAMES) {
    const outputLocation = `out/preview/frame-${frame}.png`;
    await renderStill({composition, serveUrl: bundleLocation, frame, output: outputLocation});
    console.log("rendered", outputLocation);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
