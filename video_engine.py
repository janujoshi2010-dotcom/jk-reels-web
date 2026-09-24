import os
try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.video.VideoClip import ImageClip
except ImportError:
    from moviepy.editor import VideoFileClip, ImageClip

import photo_engine

def create_ai_video(prompt, output_path, duration=5):
    temp_img = f"temp_{os.path.basename(output_path)}.png"
    photo_engine.generate_ai_image(prompt, temp_img)
    clip = ImageClip(temp_img)
    if hasattr(clip, 'with_duration'):
        clip = clip.with_duration(duration)
    else:
        clip = clip.set_duration(duration)
    clip.write_videofile(output_path, fps=24, codec="libx264", audio=False, logger=None)
    clip.close()
    if os.path.exists(temp_img):
        os.remove(temp_img)

def crop_vertical_reel(input_path, output_path):
    clip = VideoFileClip(input_path)
    w, h = clip.size
    new_w = int(h * (9 / 16))
    x_c = w / 2
    if hasattr(clip, 'cropped'):
        cropped = clip.cropped(x1=x_c - (new_w/2), y1=0, x2=x_c + (new_w/2), y2=h)
    else:
        cropped = clip.crop(x1=x_c - (new_w/2), y1=0, x2=x_c + (new_w/2), y2=h)
    cropped.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    cropped.close()