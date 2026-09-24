from rembg import new_session, remove
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import urllib.parse
import urllib.request
import os

session = new_session("isnet-general-use")

def clean_remove_background(input_path, output_path):
    """Haath aur baal preserve karne wala Alpha Matting Cutout"""
    with open(input_path, 'rb') as i:
        input_data = i.read()
        output_data = remove(
            input_data, 
            session=session,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=5
        )
        with open(output_path, 'wb') as o:
            o.write(output_data)

def apply_photo_filter(input_path, output_path, filter_type="normal"):
    img = Image.open(input_path).convert("RGB")
    
    if filter_type == "cyberpunk":
        # Cool Blue & Pink tint
        r, g, b = img.split()
        r = r.point(lambda i: i * 1.2)
        b = b.point(lambda i: i * 1.4)
        img = Image.merge('RGB', (r, g, b))
        img = ImageEnhance.Contrast(img).enhance(1.3)
    elif filter_type == "vintage":
        # Sepia / Warm retro tone
        gray = ImageOps.grayscale(img)
        img = ImageOps.colorize(gray, "#704214", "#ffecb3")
    elif filter_type == "bw":
        # High contrast Black & White
        img = ImageOps.grayscale(img)
        img = ImageEnhance.Contrast(img).enhance(1.5)
    elif filter_type == "glow":
        # Soft romantic blur & glow
        blurred = img.filter(ImageFilter.GaussianBlur(radius=2))
        img = Image.blend(img, blurred, alpha=0.4)
        img = ImageEnhance.Brightness(img).enhance(1.1)
        
    img.save(output_path, quality=95)

def upscale_image(input_path, output_path):
    img = Image.open(input_path)
    w, h = img.size
    img_hd = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    enhancer = ImageEnhance.Sharpness(img_hd)
    enhancer.enhance(1.5).save(output_path, quality=95)

def generate_ai_image(prompt, output_path):
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(output_path, 'wb') as out_file:
        out_file.write(response.read())