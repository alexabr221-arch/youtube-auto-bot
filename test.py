import os, random, textwrap, asyncio, requests, urllib.parse
from PIL import Image, ImageFilter
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
from moviepy.editor import *
import moviepy.video.fx.all as vfx
from PIL import ImageDraw, ImageFont
import edge_tts

W, H = (1080,1920)
story_raw = "My boyfriend told me he goes to gym every night at 9pm. Last night I followed him. He didn't go to gym. He parked at my best friend's apartment. She opened wearing my lost dress."

def get_ai_prompts_from_story(story):
    s = story.lower()
    if "best friend" in s and "boyfriend" in s:
        return [
            "beautiful young woman shocked betrayed face closeup tears inside car at night cinematic ultra realistic 8k",
            "stunning girl shocked catching boyfriend cheating at door best friend behind dramatic lighting",
            "gorgeous sad woman crying lonely dark bedroom heartbroken betrayal tears closeup"
        ]
    return ["beautiful woman shocked betrayed face closeup tears dramatic 8k"]*3

def download_ai_backgrounds(story, W, H):
    prompts = get_ai_prompts_from_story(story)
    images = []
    for idx, prompt in enumerate(prompts):
        full_prompt = f"{prompt}, portrait, beautiful face centered, sharp focus on eyes, looking at camera, shallow depth of field, ultra realistic skin, 8k"
        safe = urllib.parse.quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{safe}?width=768&height=1024&model=flux&nologo=true&enhance=true&seed={random.randint(1,999999)}"
        try:
            print(f"Generating image {idx+1}/3...")
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and len(r.content) > 8000:
                fname = f"bg_{idx}.jpg"
                open(fname,"wb").write(r.content)
                # CREATE BLURRED VERSION FOR BACKGROUND - this fixes black bars + failure
                img = Image.open(fname)
                blurred = img.filter(ImageFilter.GaussianBlur(radius=15))
                blurred.save(f"bg_{idx}_blur.jpg")
                images.append((fname, f"bg_{idx}_blur.jpg"))
                print(f"✅ Image {idx+1} ready")
        except Exception as e:
            print(f"Error {e}")
    
    while len(images) < 3 and images:
        images.append(images[0])
    if not images:
        r = requests.get(f"https://picsum.photos/768/1024?random={random.randint(1,5000)}", timeout=20)
        open("bg_0.jpg","wb").write(r.content)
        Image.open("bg_0.jpg").filter(ImageFilter.GaussianBlur(15)).save("bg_0_blur.jpg")
        images = [("bg_0.jpg","bg_0_blur.jpg")]*3
    return images

async def make_voice_with_timing(text, file="voice.mp3"):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural", rate="+8%")
    words = []
    with open(file, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary": 
                words.append((chunk["offset"]/10000000, (chunk["offset"]+chunk["duration"])/10000000, chunk["text"]))
    return file, words

def make_caption_clip_pop(text, W, H, duration, start):
    img = Image.new('RGBA', (W, 500), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except: font = ImageFont.load_default()
    lines = textwrap.wrap(text.upper(), width=15)
    y = 10
    for line in lines[:2]:
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        x = (W - tw)//2
        for dx in range(-6,7):
            for dy in range(-6,7):
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0,255))
        draw.text((x, y), line, font=font, fill=(255,255,255,255))
        y += th + 12
    path = f"cap_{int(start*1000)}_{random.randint(0,99999)}.png"
    img.save(path)
    clip = ImageClip(path, duration=duration).set_start(start).set_position(("center", H//2 + 100))
    clip = clip.resize(lambda t: 0.5 + 1.0*min(t*5,1) if t < 0.2 else 1)
    return clip

def create_perfect_bg_clip(image_pair, duration, start_time):
    sharp_path, blur_path = image_pair
    # 1. Blurred background fills full screen - NO BLACK BARS
    bg_blur = ImageClip(blur_path).set_duration(duration).set_start(start_time)
    bg_blur = bg_blur.resize(height=H) if bg_blur.w/bg_blur.h < W/H else bg_blur.resize(width=W)
    if bg_blur.w < W: bg_blur = bg_blur.resize(width=W)
    if bg_blur.h < H: bg_blur = bg_blur.resize(height=H)
    bg_blur = bg_blur.crop(x_center=bg_blur.w/2, y_center=bg_blur.h/2, width=W, height=H)
    bg_blur = bg_blur.fx(vfx.colorx, 0.5)

    # 2. Sharp NORMAL image center - catchy
    fg = ImageClip(sharp_path).set_duration(duration).set_start(start_time)
    fg = fg.resize(height=1450) if fg.h > fg.w else fg.resize(width=950)
    if fg.h > 1450: fg = fg.resize(height=1450)
    if fg.w > 950: fg = fg.resize(width=950)
    fg = fg.set_position(("center", "center"))
    fg = fg.resize(lambda t: 1 + 0.02*t)
    
    return CompositeVideoClip([bg_blur, fg], size=(W,H)).set_duration(duration).set_start(start_time)

def make_video():
    audio_file, word_data = asyncio.run(make_voice_with_timing(story_raw))
    voice_audio = AudioFileClip(audio_file)
    duration = min(voice_audio.duration, 44)
    
    bg_files = download_ai_backgrounds(story_raw, W, H)
    change_every = duration / len(bg_files)
    
    bg_clips = [create_perfect_bg_clip(pair, change_every, i*change_every) for i, pair in enumerate(bg_files)]
    bg_final = CompositeVideoClip(bg_clips, size=(W,H)).set_duration(duration)

    caps = []
    i = 0
    while i < len(word_data):
        start = word_data[i][0]
        phrase = " ".join([word_data[i+k][2] for k in range(3) if i+k < len(word_data)])
        i += 3
        dur = word_data[i][0] - start if i < len(word_data) else word_data[-1][1] - start + 0.3
        dur = max(0.5, min(dur, 1.4))
        if start < duration:
            caps.append(make_caption_clip_pop(phrase, W, H, dur, start))

    final = CompositeVideoClip([bg_final]+caps, size=(W,H)).set_audio(voice_audio)
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final.mp4"

if __name__ == "__main__":
    print("TEST V5.1 STABLE START...")
    make_video()
    print("✅ DONE")
