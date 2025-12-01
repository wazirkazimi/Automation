from moviepy import VideoFileClip, clips_array, CompositeVideoClip
import os

# Check if files exist
if not os.path.exists("meme.mp4"):
    raise FileNotFoundError("meme.mp4 not found")
if not os.path.exists("gameplay.mp4"):
    raise FileNotFoundError("gameplay.mp4 not found")

# Load videos
top = VideoFileClip("meme.mp4")
bottom = VideoFileClip("gameplay.mp4")

# Target reel size (9:16)
WIDTH, HEIGHT = 1080, 1920
SECTION_HEIGHT = HEIGHT // 2  # = 960

# Resize videos to fit half screen each
top_resized = top.resized(height=SECTION_HEIGHT).resized(width=WIDTH)
bottom_resized = bottom.resized(height=SECTION_HEIGHT).resized(width=WIDTH)

# Stack videos vertically
stacked = clips_array([[top_resized], [bottom_resized]])

# Create final composite video (no text)
final = CompositeVideoClip([stacked], size=(WIDTH, HEIGHT))

# Add audio from the top video (meme)
if top.audio is not None:
    final = final.with_audio(top.audio)
else:
    print("⚠ meme.mp4 has no audio")

# Export video with audio
final.write_videofile(
    "output.mp4",
    fps=30,
    codec="libx264",
    audio_codec="aac"
)

# Cleanup
top.close()
bottom.close()
