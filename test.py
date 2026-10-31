import os, random, textwrap, asyncio, requests, urllib.parse, json
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
from datetime import datetime, timezone, date
from moviepy.editor import *
from moviepy.video.fx.all import colorx
import moviepy.video.fx.all as vfx
from PIL import ImageDraw, ImageFont
import edge_tts

# FORCE SHORT FOR TEST - change to False to test LONG
IS_SHORT = True
print(f"TEST MODE - Making {'SHORT' if IS_SHORT else 'LONG'}")

STORIES = [
"My boyfriend told me he goes to gym every night at 9pm. Last night I followed him. He didn't go to gym. He parked at my best friend's apartment. She opened wearing my lost dress.",
"My wife said working late for 3 weeks. Her coworker posted hotel bar story and my wife was laughing with a man in background. I drove to that hotel room 204.",
"My mother in law moved into our house without asking and started controlling what I cook, wear, say. Yesterday she told my husband I'm bad wife, so I made her pack same night.",
]

story_raw = STORIES[0] # Test with first story

def get_ai_prompt_from_story(story):
    s = story.lower()
    if "best friend" in s and "boyfriend" in s: return "shocked woman catching cheating boyfriend and best friend at apartment door night cinematic dramatic"
    if "hotel" in s: return "man walking down dark hotel hallway at night noir cinematic dramatic"
    if "mother in law" in s: return "angry mother in law shouting at young wife in living room family drama cinematic"
    return "lonely heartbroken person sitting alone at night sad betrayal cinematic dramatic"

def download_ai_background(story, W, H):
    prompt = get_ai_prompt_from_story(story)
    safe = urllib.parse.quote(prompt + ", ultra realistic, 8k, cinematic, dramatic lighting")
    url = f"https://image.pollinations.ai/prompt/{safe}?width={W}&height={H}&model=flux&nologo=true&seed={random.randint(1,999999)}"
    try:
        r = requests.get(url, timeout=90)
        if r.status_code == 200 and len(r.content) > 5000:
            open("bg.jpg","wb").write(r.content)
            return "bg.jpg"
    except Exception as e:
        print(f"AI fail {e}")
    r = requests.get(f"https://picsum.photos/{W}/{H}?random={random.randint(1,5000)}", timeout=20)
    open("bg.jpg","wb").write(r.content)
    return "bg.jpg"

def download_music():
    s = story_raw.lower()
    sad_piano = ["https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3"]
    url = random.choice(sad_piano)
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and len(r.content) > 10000:
            open("music.mp3","wb").write(r.content)
            return "music.mp3"
    except: pass
    return None

def detect_gender(story):
    s = story.lower()
    if "my wife" in s or "my girlfriend" in s: return "male"
    if "my husband" in s or "my boyfriend" in s: return "female"
    return "female"

async def make_voice_with_timing(text, file="voice.mp3"):
    gender = detect_gender(text)
    voice_name = "en-US-GuyNeural" if gender == "male" else "en-US-AriaNeural"
    rate = "+5%" if gender == "male" else "+8%"
    print(f"Using {gender.upper()} voice")
    if IS_SHORT:
        text = text + " ... Want full shocking ending? Full story drops tonight at 8pm West Africa Time. Subscribe!"
    communicate = edge_tts.Communicate(text, voice_name, rate=rate)
    words = []
    with open(file, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary": words.append((chunk["offset"]/10000000, chunk["offset"]/10000000 + chunk["duration"]/10000000, chunk["text"]))
    return file, words

def make_caption_clip(text, W, H, duration, start):
    img = Image.new('RGBA', (W, 300), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52 if W==1080 else 42)
    except: font = ImageFont.load_default()
    lines = textwrap.wrap(text.upper(), width=20 if W==1080 else 35)
    y = 10
    for line in lines[:2]:
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        x = (W - tw)//2
        for dx in [-3,0,3]:
            for dy in [-3,0,3]:
                if dx!=0 or dy!=0: draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0,255))
        draw.text((x, y), line, font=font, fill=(255,255,255,255))
        y += th + 10
    path = f"cap_{int(start*1000)}_{random.randint(0,99999)}.png"
    img.save(path)
    return ImageClip(path, duration=duration).set_start(start).set_position(("center", H//2))

def make_end_card(W, H, duration):
    img = Image.new('RGBA', (W, 180), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38 if W==1080 else 32)
    except: font = ImageFont.load_default()
    lines = ["FULL STORY AT 8PM WAT!", "SUBSCRIBE 🔔"] if IS_SHORT else ["SUBSCRIBE FOR MORE!", "COMMENT BELOW"]
    y=10
    for line in lines:
        try: bbox = draw.textbbox((0,0), line, font=font); tw = bbox[2]-bbox[0]
        except: tw = len(line)*18
        x = (W - tw)//2
        for dx in [-2,2]:
            for dy in [-2,2]:
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0))
        draw.text((x, y), line, font=font, fill=(255,215,0))
        y+=55
    img.save("endcard.png")
    return ImageClip("endcard.png", duration=3).set_start(max(0, duration-3)).set_position(("center", H-250))

def make_video():
    W,H = (1080,1920) if IS_SHORT else (1920,1080)
    audio_file, word_data = asyncio.run(make_voice_with_timing(story_raw))
    voice_audio = AudioFileClip(audio_file)
    duration = min(voice_audio.duration, 44 if IS_SHORT else 480)
    music_path = download_music()
    if music_path:
        try:
            music = AudioFileClip(music_path).volumex(0.06).set_duration(duration).audio_fadeout(2)
            final_audio = CompositeAudioClip([voice_audio.set_duration(duration), music])
        except:
            final_audio = voice_audio.set_duration(duration)
    else:
        final_audio = voice_audio.set_duration(duration)
    bg_path = download_ai_background(story_raw, W, H)
    raw_bg = ImageClip(bg_path, duration=duration)
    if raw_bg.w / raw_bg.h < W / H: raw_bg = raw_bg.resize(width=W)
    else: raw_bg = raw_bg.resize(height=H)
    bg_clip = raw_bg.crop(x1=raw_bg.w//2 - W//2, y1=raw_bg.h//2 - H//2, width=W, height=H).fx(vfx.colorx, 0.6)

    # === INSTANT SYNC ===
    caps = []
    if word_data and len(word_data) > 2:
        i = 0
        while i < len(word_data):
            start_time = word_data[i][0]
            phrase_words = []
            for k in range(5):
                if i + k >= len(word_data): break
                phrase_words.append(word_data[i + k][2])
                if word_data[i + k][2].endswith(('.', '!', '?')) and len(phrase_words) >= 3:
                    break
            if not phrase_words: break
            text = " ".join(phrase_words)
            i += len(phrase_words)
            if i < len(word_data):
                next_start = word_data[i][0]
                dur = next_start - start_time
            else:
                dur = (word_data[-1][1] - start_time) + 0.3
            dur = max(0.4, min(dur, 1.8))
            if start_time < duration:
                caps.append(make_caption_clip(text, W, H, dur, start_time))
    
    end_card = make_end_card(W, H, duration)
    final = CompositeVideoClip([bg_clip]+caps+[end_card], size=(W,H)).set_audio(final_audio)
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final.mp4", bg_path

if __name__ == "__main__":
    print("TEST START...")
    video_file, bg = make_video()
    print(f"✅ DONE! Video saved as {video_file}")
    print("Download final.mp4 and check: caption appears exact moment voice says it!")
