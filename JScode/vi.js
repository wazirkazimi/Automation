import ffmpeg from "fluent-ffmpeg";
import ffmpegStatic from "ffmpeg-static";
import path from "path";
import fs from "fs";

ffmpeg.setFfmpegPath(ffmpegStatic);

const meme = "meme.mp4";
const gameplay = "gameplay.mp4";
const output = "output.mp4";

// Check if input files exist
if (!fs.existsSync(meme)) {
  console.error(`Error: Input file '${meme}' not found. Please ensure the file exists in the current directory.`);
  process.exit(1);
}

if (!fs.existsSync(gameplay)) {
  console.error(`Error: Input file '${gameplay}' not found. Please ensure the file exists in the current directory.`);
  process.exit(1);
}

// Final output size
const WIDTH = 1080;
const HEIGHT = 1920;

const command = ffmpeg()
  // Input videos
  .input(meme)
  .input(gameplay)

  // FFmpeg filter to:
  // 1. Resize both videos to 1080x960 (half of 1920)
  // 2. Stack them vertically
  // 3. Keep audio from the meme video
  .complexFilter([
    {
      filter: "scale",
      options: { w: WIDTH, h: HEIGHT / 2 },
      inputs: "0:v",
      outputs: "top",
    },
    {
      filter: "scale",
      options: { w: WIDTH, h: HEIGHT / 2 },
      inputs: "1:v",
      outputs: "bottom",
    },
    {
      filter: "vstack",
      options: { inputs: 2 },
      inputs: ["top", "bottom"],
      outputs: "stacked",
    },
  ])

  // Use meme.mp4 audio
  .audioCodec("aac")
  .videoCodec("libx264")
  .outputOptions(["-map [stacked]", "-map 0:a?", "-preset ultrafast"])

  // Output file
  .save(output)
  .on("start", () => console.log("Processing..."))
  .on("end", () => console.log("Done! output.mp4 created"))
  .on("error", (err) => console.error("Error:", err));
