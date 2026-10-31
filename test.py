import os, random, textwrap, asyncio, requests, urllib.parse
from PIL import Image, ImageFilter, ImageDraw, ImageFont
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
from moviepy.editor import *
import moviepy.video.fx.all as vfx
import edge_tts

W, H = (1080,1920)
story_raw = "My boyfriend told me he goes to gym every night at 9pm. Last night I followed him. He didn't go to gym. He parked at my best friend's apartment. She opened wearing my lost dress."

def download_one_image(story):
    # ONE perfect prompt that matches your story
    s = story.lower()
    if "best friend" in s and "boyfriend" in s:
        prompt = "beautiful young woman sitting in car at night shocked betrayed face closeup watching apartment, tears, heartbroken, dramatic cinematic lighting, ultra realistic, 8k, detailed skin, looking through window"
    else:
        prompt = f"beautiful woman emotional shocked face closeup, story about {story[:60]}, cinematic, ultra realistic, 8k"

    full = f"{prompt}, portrait photo, sharp focus on eyes, center framed, photorealistic, instagram model"
    safe = urllib.parse.quote(full)
    url = f"https://image.pollinations.ai/prompt/{safe}?width=768&height=1280&model=flux&nologo=true&enhance=true&seed={random.randint(1,999999)}"
    
    try:
        print(f"Generating ONE image: {prompt[:50]}...")
        r = requests.get(url, timeout=120)
        if r.status_code == 200 and len(r.content) > 10000:
            open("bg.jpg","wb").write(r.content)
            im = Image.open("bg.jpg")
            blurred = im.filter(ImageFilter.GaussianBlur(15))
            blurred.save("bg_blur.jpg")
            print(f"✅ ONE image ready - {len(r.content)} bytes")
            return "bg.jpg", "bg_blur.jpg"
    except Exception as e:
        print(f"Error {e}")

    # fallback
    r = requests.get(f"https://picsum.photos/768/1280?random={random.randint(1,5000)}", timeout=20)
    open("bg.jpg","wb").write(r.content)
    Image.open("bg.jpg").filter(ImageFilter.GaussianBlur(15)).save("bg_blur.jpg")
    return "bg.jpg", "bg_blur.jpg"

async def make_voice(text, file="voice.mp3"):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural", rate="+8%")
    words = []
    with open(file, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary": 
                words.append((chunk["offset"]/10000000, (chunk["offset"]+chunk["duration"])/10000000, chunk["text"]))
    return file, words

def make_caption(text, duration, start):
    img = Image.new('RGBA', (W, 650), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 85)
    except: font = ImageFont.load_default()
    lines = textwrap.wrap(text.upper(), width=14)
    y = 10
    for line in lines[:2]:
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        x = (W - tw)//2
        for dx in range(-7,8):
            for dy in range(-7,8):
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0,255))
        draw.text((x, y), line, font=font, fill=(255,255,255,255))
        y += th + 15
    path = f"cap_{int(start*1000)}_{random.randint(0,9999)}.png"
    img.save(path)
    clip = ImageClip(path, duration=duration).set_start(start).set_position(("center", H*0.62))
    clip = clip.resize(lambda t: 0.7 + 0.3*min(t*6,1) if t < 0.15 else 1)
    return clip

def make_video():
    audio_file, word_data = asyncio.run(make_voice(story_raw))
    voice = AudioFileClip(audio_file)
    total = min(voice.duration, 44)
    print(f"Duration: {total}s")

    sharp_path, blur_path = download_one_image(story_raw)

    # ONE BACKGROUND - NEVER DISAPPEARS, NEVER DARK
    bg = ImageClip(blur_path, duration=total)
    bg = bg.resize(height=H) if bg.w/bg.h < W/H else bg.resize(width=W)
    if bg.w < W: bg = bg.resize(width=W)
    if bg.h < H: bg = bg.resize(height=H)
    bg = bg.crop(x_center=bg.w/2, y_center=bg.h/2, width=W, height=H)
    bg = bg.fx(vfx.colorx, 0.85) # BRIGHT

    fg = ImageClip(sharp_path, duration=total)
    fg = fg.resize(height=1400)
    if fg.w > 1000: fg = fg.resize(width=1000)
    fg = fg.set_position(("center", "center")).fx(vfx.colorx, 1.1)

    background = CompositeVideoClip([bg, fg], size=(W,H)).set_duration(total)

    # GUARANTEED CAPTIONS
    captions = []
    if len(word_data) < 5:
        print("Using fallback captions")
        words = story_raw.split()
        cap_dur = total / (len(words)//3 + 1)
        for idx in range(0, len(words), 3):
            phrase = " ".join(words[idx:idx+3])
            s = idx//3 * cap_dur
            captions.append(make_caption(phrase, cap_dur, s))
    else:
        i = 0
        while i < len(word_data):
            s = word_data[i][0]
            phrase = " ".join([word_data[i+k][2] for k in range(3) if i+k < len(word_data)])
            i += 3
            e = word_data[i][0] if i < len(word_data) else total
            d = max(0.6, min(e - s + 0.2, 1.3))
            if s < total:
                captions.append(make_caption(phrase, d, s))

    print(f"{len(captions)} captions")
    final = CompositeVideoClip([background] + captions, size=(W,H)).set_duration(total).set_audio(voice)
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
    print("✅ DONE - ONE image, bright, with captions")

if __name__ == "__main__":
    make_video()
