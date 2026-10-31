import os, random, textwrap, asyncio, requests, urllib.parse
from PIL import Image, ImageFilter, ImageDraw, ImageFont
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
from moviepy.editor import *
import moviepy.video.fx.all as vfx
import edge_tts

W, H = (1080,1920)
story_raw = "My boyfriend told me he goes to gym every night at 9pm. Last night I followed him. He didn't go to gym. He parked at my best friend's apartment. She opened wearing my lost dress."

def get_better_prompts():
    # THESE PROMPTS ARE TESTED TO BE CATCHY - closeup face = subs
    return [
        "extremely beautiful young woman shocked face closeup, big eyes tears, betrayal expression, dramatic cinematic lighting, inside car night, photorealistic skin texture, 8k, ultra detailed face, instagram model",
        "beautiful woman mouth open shocked at apartment door catching cheating boyfriend, best friend behind in dress, dramatic lighting, photorealistic",
        "stunning heartbroken woman crying in dark bedroom alone, tears on cheeks, emotional, beautiful, photorealistic closeup, cinematic"
    ]

def download_images():
    prompts = get_better_prompts()
    pairs = []
    for idx, prompt in enumerate(prompts):
        full = f"{prompt}, portrait photo, sharp focus on face, center framed, looking at camera, bokeh background, highly detailed"
        safe = urllib.parse.quote(full)
        # TRY FLUX + TURBO for best quality
        for model in ["flux", "flux-realism", "turbo"]:
            try:
                url = f"https://image.pollinations.ai/prompt/{safe}?width=768&height=1280&model={model}&nologo=true&seed={random.randint(1,999999)}&enhance=true"
                print(f"Trying {model} for image {idx+1}")
                r = requests.get(url, timeout=120)
                if r.status_code == 200 and len(r.content) > 15000:
                    open(f"bg_{idx}.jpg","wb").write(r.content)
                    # MAKE BLURRED BG - LIGHT, NOT DARK
                    im = Image.open(f"bg_{idx}.jpg")
                    blurred = im.filter(ImageFilter.GaussianBlur(12))
                    blurred.save(f"bg_{idx}_blur.jpg")
                    pairs.append((f"bg_{idx}.jpg", f"bg_{idx}_blur.jpg"))
                    print(f"✅ Image {idx+1} GOOD - {len(r.content)} bytes")
                    break
            except Exception as e:
                print(f"fail {e}")
                continue
    if not pairs:
        r = requests.get(f"https://picsum.photos/768/1280?random={random.randint(1,5000)}", timeout=20)
        open("bg_0.jpg","wb").write(r.content)
        Image.open("bg_0.jpg").filter(ImageFilter.GaussianBlur(12)).save("bg_0_blur.jpg")
        pairs = [("bg_0.jpg","bg_0_blur.jpg")]*3
    while len(pairs) < 3:
        pairs.append(pairs[0])
    return pairs

async def make_voice(text, file="voice.mp3"):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural", rate="+8%")
    words = []
    with open(file, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary": 
                words.append((chunk["offset"]/10000000, (chunk["offset"]+chunk["duration"])/10000000, chunk["text"]))
    print(f"Words detected: {len(words)}")
    return file, words

def make_caption(text, duration, start):
    img = Image.new('RGBA', (W, 600), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 85)
    except:
        font = ImageFont.load_default()
    lines = textwrap.wrap(text.upper(), width=14)
    y = 10
    for line in lines[:2]:
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        x = (W - tw)//2
        # THICK BLACK STROKE FOR READABILITY
        for dx in range(-7,8):
            for dy in range(-7,8):
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0,255))
        draw.text((x, y), line, font=font, fill=(255,255,255,255))
        y += th + 15
    path = f"cap_{int(start*1000)}_{random.randint(0,9999)}.png"
    img.save(path)
    clip = ImageClip(path, duration=duration).set_start(start).set_position(("center", H*0.62))
    # POP
    clip = clip.resize(lambda t: 0.7 + 0.3*min(t*6,1) if t < 0.15 else 1)
    return clip

def make_video():
    audio_file, word_data = asyncio.run(make_voice(story_raw))
    voice = AudioFileClip(audio_file)
    total = min(voice.duration, 44)
    print(f"Total duration: {total}s")

    image_pairs = download_images()
    change = total / len(image_pairs)
    print(f"Change every: {change}s")

    # FIX 1: NO DARK - bright blurred bg + bright center image
    video_parts = []
    for i, (sharp_path, blur_path) in enumerate(image_pairs):
        start = i * change
        # Blurred bg - COVERS FULL SCREEN, BRIGHT
        bg = ImageClip(blur_path, duration=change).set_start(start)
        bg = bg.resize(height=H) if bg.w/bg.h < W/H else bg.resize(width=W)
        if bg.w < W: bg = bg.resize(width=W)
        if bg.h < H: bg = bg.resize(height=H)
        bg = bg.crop(x_center=bg.w/2, y_center=bg.h/2, width=W, height=H)
        bg = bg.fx(vfx.colorx, 0.9)  # NOT DARK - 0.9 bright

        # Sharp center - NORMAL SIZE, BRIGHT
        fg = ImageClip(sharp_path, duration=change).set_start(start)
        fg = fg.resize(height=1400)
        if fg.w > 1000: fg = fg.resize(width=1000)
        fg = fg.set_position(("center", "center")).fx(vfx.colorx, 1.1)  # BRIGHTER

        part = CompositeVideoClip([bg, fg], size=(W,H)).set_duration(change).set_start(start)
        video_parts.append(part)

    # This composite NEVER goes dark / disappear
    background = CompositeVideoClip(video_parts, size=(W,H)).set_duration(total)

    # FIX 2: GUARANTEED CAPTIONS - even if edge_tts timing fails
    captions = []
    if len(word_data) < 5:  # FALLBACK if no timing
        print("Using fallback captions")
        words = story_raw.split()
        chunk_size = 3
        cap_duration = total / (len(words)//chunk_size + 1)
        for idx in range(0, len(words), chunk_size):
            phrase = " ".join(words[idx:idx+chunk_size])
            s = idx//chunk_size * cap_duration
            captions.append(make_caption(phrase, cap_duration, s))
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

    print(f"Creating {len(captions)} captions")
    final = CompositeVideoClip([background] + captions, size=(W,H)).set_duration(total).set_audio(voice)
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
    print("✅ VIDEO DONE - bright, changing, with captions")

if __name__ == "__main__":
    make_video()
