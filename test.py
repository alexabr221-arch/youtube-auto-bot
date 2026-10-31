import os, random, textwrap, asyncio, requests, urllib.parse
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
from moviepy.editor import *
import moviepy.video.fx.all as vfx
from PIL import ImageDraw, ImageFont, ImageFilter
import edge_tts

W, H = (1080,1920)
story_raw = "My boyfriend told me he goes to gym every night at 9pm. Last night I followed him. He didn't go to gym. He parked at my best friend's apartment. She opened wearing my lost dress."

def get_ai_prompts_from_story(story):
    s = story.lower()
    # BEST PERFECTION PROMPTS - face closeup, emotional, viral thumbnail style
    if "best friend" in s and "boyfriend" in s:
        return [
            "beautiful young woman with shocked betrayed face closeup, tears in eyes, dramatic lighting, inside car at night watching cheating, ultra realistic, 8k, highly detailed face, emotional, viral thumbnail",
            "stunning girl with mouth open shocked catching boyfriend cheating at door, best friend behind, dramatic cinematic lighting, closeup face",
            "gorgeous sad woman crying lonely dark bedroom, heartbroken betrayal, tears, cinematic closeup face, ultra realistic"
        ]
    return [
        "beautiful woman shocked betrayed face closeup tears dramatic lighting ultra realistic 8k viral",
        "emotional crying woman face closeup heartbroken cinematic",
        "shocked woman face dramatic betrayal discovery closeup"
    ]

def download_ai_backgrounds(story, W, H):
    prompts = get_ai_prompts_from_story(story)
    images = []
    for idx, prompt in enumerate(prompts):
        # PERFECTION KEYWORDS for catchy subs
        full_prompt = f"{prompt}, portrait orientation, beautiful face centered, looking at camera, sharp focus on eyes, shallow depth of field, cinematic bokeh, ultra realistic skin, 8k"
        safe = urllib.parse.quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{safe}?width=768&height=1024&model=flux&nologo=true&enhance=true&seed={random.randint(1,999999)}"
        try:
            print(f"Generating CATCHY image {idx+1}/3...")
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and len(r.content) > 8000:
                fname = f"bg_{idx}.jpg"
                open(fname,"wb").write(r.content)
                images.append(fname)
                print(f"✅ Catchy image {idx+1} ready")
        except Exception as e:
            print(f"Error {e}")
    
    while len(images) < 3 and images:
        images.append(images[0])
    if not images:
        r = requests.get(f"https://picsum.photos/768/1024?random={random.randint(1,5000)}", timeout=20)
        open("bg_0.jpg","wb").write(r.content)
        images = ["bg_0.jpg"]*3
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

def create_perfect_bg_clip(image_path, duration, start_time):
    """PERFECT CATCHY STYLE: Blurred background fill + sharp normal image center"""
    # 1. Blurred background that fills full screen (no black bars)
    bg_blur = ImageClip(image_path).set_duration(duration).set_start(start_time)
    # Resize to COVER full screen
    bg_blur = bg_blur.resize(height=H) if bg_blur.w/bg_blur.h < W/H else bg_blur.resize(width=W)
    if bg_blur.w < W: bg_blur = bg_blur.resize(width=W)
    if bg_blur.h < H: bg_blur = bg_blur.resize(height=H)
    bg_blur = bg_blur.crop(x_center=bg_blur.w/2, y_center=bg_blur.h/2, width=W, height=H)
    bg_blur = bg_blur.fx(vfx.colorx, 0.4).fx(vfx.blur, 8)  # dark + blurred

    # 2. Sharp NORMAL image in center (not stretched) - 85% of screen
    fg = ImageClip(image_path).set_duration(duration).set_start(start_time)
    # Keep normal aspect, fit inside 950x1500
    fg = fg.resize(height=1450) if fg.h > fg.w else fg.resize(width=950)
    if fg.h > 1450: fg = fg.resize(height=1450)
    if fg.w > 950: fg = fg.resize(width=950)
    fg = fg.set_position(("center", "center"))
    fg = fg.resize(lambda t: 1 + 0.02*t)  # subtle zoom
    
    return CompositeVideoClip([bg_blur, fg], size=(W,H)).set_duration(duration).set_start(start_time)

def make_video():
    audio_file, word_data = asyncio.run(make_voice_with_timing(story_raw))
    voice_audio = AudioFileClip(audio_file)
    duration = min(voice_audio.duration, 44)
    
    bg_files = download_ai_backgrounds(story_raw, W, H)
    change_every = duration / len(bg_files)
    
    bg_clips = []
    for i, path in enumerate(bg_files):
        clip = create_perfect_bg_clip(path, change_every, i*change_every)
        bg_clips.append(clip)
    
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
    make_video()
