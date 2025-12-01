from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ColorClip
from moviepy.video.fx.resize import resize as vfx_resize  # type: ignore


# Pillow compatibility shim: newer Pillow versions (>=10) moved resampling
try:
    from PIL import Image as _PIL_Image
    # Backwards-compatible aliases for removed constants
    if not hasattr(_PIL_Image, 'ANTIALIAS') and hasattr(_PIL_Image, 'Resampling'):
        _PIL_Image.ANTIALIAS = _PIL_Image.Resampling.LANCZOS
    if not hasattr(_PIL_Image, 'BILINEAR') and hasattr(_PIL_Image, 'Resampling'):
        _PIL_Image.BILINEAR = _PIL_Image.Resampling.BILINEAR
    if not hasattr(_PIL_Image, 'BICUBIC') and hasattr(_PIL_Image, 'Resampling'):
        _PIL_Image.BICUBIC = _PIL_Image.Resampling.BICUBIC
except Exception:
    # If Pillow isn't available or something unexpected happens, continue —
    # MoviePy will raise a clear error later when trying to use PIL.
    _PIL_Image = None
import os

# Target reel size (9:16)
WIDTH, HEIGHT = 1080, 1920
SECTION_HEIGHT = HEIGHT // 2

def pad_to_size(clip, size, color=(0, 0, 0)):
    """Return a CompositeVideoClip with the clip centered on a background of `size`."""
    bg = ColorClip(size, color=color, duration=clip.duration)
    return CompositeVideoClip([bg, clip.set_position(("center", "center"))]).set_duration(clip.duration)

def stack_videos(meme_path, gameplay_path, output_path, caption="", progress_callback=None):
    """Stack two videos vertically: meme on top, gameplay on bottom. Audio from meme.

    progress_callback: optional callable(progress_percent:int, message:str)
    """
    def _report(p, msg=''):
        try:
            if progress_callback:
                progress_callback(int(p), str(msg))
        except Exception:
            pass

    _report(5, 'loading clips')
    # Load videos
    top = VideoFileClip(meme_path)
    bottom = VideoFileClip(gameplay_path)
    
    # Resize and pad
    # Use the fx `resize` function (vfx_resize) for compatibility across MoviePy versions
    _report(20, 'resizing top')
    top_resized = vfx_resize(top, height=SECTION_HEIGHT)
    top_resized = pad_to_size(top_resized, (WIDTH, SECTION_HEIGHT))

    _report(35, 'resizing bottom')
    bottom_resized = vfx_resize(bottom, height=SECTION_HEIGHT)
    bottom_resized = pad_to_size(bottom_resized, (WIDTH, SECTION_HEIGHT))
    
    # Stack videos vertically by positioning them
    duration = max(top_resized.duration, bottom_resized.duration)
    
    # Create main background
    bg = ColorClip((WIDTH, HEIGHT), color=(0, 0, 0), duration=duration)
    
    # Position clips at top and bottom
    _report(50, 'compositing')
    stacked = CompositeVideoClip([
        bg,
        top_resized.set_position((0, 0)),
        bottom_resized.set_position((0, SECTION_HEIGHT))
    ]).set_duration(duration)
    
    # Attach audio from meme if available (use set_audio for CompositeVideoClip)
    if top_resized.audio is not None:
        stacked = stacked.set_audio(top_resized.audio)

    _report(70, 'encoding')
    
    # Export with compatible encoding
    stacked.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        audio=True,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    )

    _report(100, 'done')
    
    # Cleanup
    top.close()
    bottom.close()
    
    return output_path

if __name__ == "__main__":
    # Test mode: process meme.mp4 and gameplay.mp4 if they exist
    if os.path.exists("meme.mp4") and os.path.exists("gameplay.mp4"):
        stack_videos("meme.mp4", "gameplay.mp4", "output.mp4")
        print("✅ Video created: output.mp4")
