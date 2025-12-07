"""
Simplified video processing module for AWS Lambda.
No progress callbacks, optimized for serverless environment.
"""

from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip
from moviepy.video.fx.resize import resize as vfx_resize
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger()

# Pillow compatibility for Image.ANTIALIAS
try:
    RESAMPLING_FILTER = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING_FILTER = Image.ANTIALIAS


def pad_to_size(clip, size, color=(0, 0, 0)):
    """Pad video clip to exact size with colored background."""
    target_width, target_height = size
    
    # Get clip dimensions
    clip_width, clip_height = int(clip.w), int(clip.h)
    
    # Calculate scale to fit within target while maintaining aspect ratio
    scale_w = target_width / clip_width
    scale_h = target_height / clip_height
    scale = min(scale_w, scale_h)
    
    # Resize clip
    new_width = int(clip_width * scale)
    new_height = int(clip_height * scale)
    resized_clip = vfx_resize(clip, newsize=(new_width, new_height))
    
    # Create background
    background = ColorClip(size=size, color=color)
    
    # Calculate position to center
    x = (target_width - new_width) // 2
    y = (target_height - new_height) // 2
    
    # Composite
    final_clip = CompositeVideoClip(
        [background, resized_clip.set_position((x, y))],
        size=size
    )
    
    return final_clip.set_duration(resized_clip.duration)


def stack_videos(meme_path, gameplay_path, output_path, caption=""):
    """
    Stack meme video on top of gameplay video.
    Output: 1080x1920 (9:16 reel format)
    """
    
    logger.info(f"Loading videos: {meme_path}, {gameplay_path}")
    
    meme_clip = VideoFileClip(meme_path)
    gameplay_clip = VideoFileClip(gameplay_path)
    
    target_size = (1080, 1920)
    
    # Pad both videos to target size
    logger.info("Padding videos to 1080x1920")
    meme_padded = pad_to_size(meme_clip, target_size, color=(0, 0, 0))
    gameplay_padded = pad_to_size(gameplay_clip, target_size, color=(0, 0, 0))
    
    # Make both clips same duration (use shorter one)
    min_duration = min(meme_padded.duration, gameplay_padded.duration)
    meme_padded = meme_padded.subclipped(0, min_duration)
    gameplay_padded = gameplay_padded.subclipped(0, min_duration)
    
    # Split screen: meme on left, gameplay on right
    logger.info("Creating split-screen composition")
    meme_resized = vfx_resize(meme_padded, newsize=(540, 1920))
    gameplay_resized = vfx_resize(gameplay_padded, newsize=(540, 1920))
    
    # Create final composition (1080x1920)
    final = CompositeVideoClip(
        [
            meme_resized.set_position((0, 0)),
            gameplay_resized.set_position((540, 0))
        ],
        size=(1080, 1920)
    )
    
    # Set audio from gameplay
    if gameplay_padded.audio:
        final = final.set_audio(gameplay_padded.audio)
    
    # Add caption if provided
    if caption:
        logger.info(f"Adding caption: {caption}")
        
        # Create caption image
        font_size = 40
        img_width, img_height = 1080, 200
        
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 200))
        draw = ImageDraw.Draw(img)
        
        # Wrap text
        words = caption.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_text = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), test_text, font=font)
            if bbox[2] - bbox[0] > img_width - 40:
                lines.append(' '.join(current_line[:-1]))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw text
        y_offset = 20
        for line in lines:
            draw.text((20, y_offset), line, fill=(255, 255, 255, 255), font=font)
            y_offset += font_size + 10
        
        img.save('/tmp/caption.png')
        
        # Add caption to video
        caption_clip = VideoFileClip('/tmp/caption.png').set_duration(min(3, final.duration))
        final = CompositeVideoClip([final, caption_clip.set_position((0, 1720))], size=(1080, 1920))
    
    # Write output with optimal encoding
    logger.info(f"Encoding video: {output_path}")
    final.write_videofile(
        output_path,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        ffmpeg_params=['-pix_fmt', 'yuv420p', '-movflags', 'faststart'],
        verbose=False,
        logger=None
    )
    
    logger.info(f"Video saved: {output_path}")
    
    # Cleanup
    meme_clip.close()
    gameplay_clip.close()
    final.close()
