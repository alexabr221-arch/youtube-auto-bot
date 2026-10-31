import os, random, textwrap, asyncio, requests, urllib.parse
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
from moviepy.editor import *
import moviepy.video.fx.all as vfx
from PIL import ImageDraw, ImageFont
import edge_tts

IS_SHORT = True

STORIES = ["My boyfriend told me he goes to gym every night at 9pm. Last night I followed him. He didn't go to gym. He parked at my best friend's apartment. She opened wearing my lost dress."]

story_raw = STORIES[0]

def download_ai_background(W, H):
    try:
        r = requests.get(f"https://picsum.photos/{W}/{H}?random={random.randint(1,5000)}", timeout=20)
        open("bg.jpg","wb").write(r.content)
        return "bg.jpg"
    except:
        Image.new("RGB", (W,H), (30,30,30)).save("bg.jpg")
        return "bg.jpg"

async def make_voice_with_timing(text, file="voice.mp3"):
    voice_name = "en-US-AriaNeural"
    communicate = edge_tts.Communicate(text, voice_name, rate="+8%")
    words = []
    with open(file, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary": 
                words.append((chunk["offset"]/10000000, (chunk["offset"]+chunk["duration"])/10000000, chunk["text"]))
    print(f"Got {len(words)} words timed")
    return file, words

def make_caption_clip(text, W, H, duration, start):
    # FIXED: Bigger, always visible
    img = Image.new('RGBA', (W, 400), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
    except: font = ImageFont.load_default()
    
    lines = textwrap.wrap(text.upper(), width=18)
    y = 10
    for line in lines[:2]:
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        x = (W - tw)//2
        # THICK BLACK BORDER FOR VISIBILITY
        for dx in range(-4,5):
            for dy in range(-4,5):
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0,255))
        draw.text((x, y), line, font=font, fill=(255,255,255,255))
        y += th + 15
    path = f"cap_{int(start*1000)}_{random.randint(0,9999)}.png"
    img.save(path)
    print(f"Caption: {text} at {start:.2f}s for {duration:.2f}s")
    return ImageClip(path, duration=duration).set_start(start).set_position(("center", H//2))

def make_video():
    W,H = 1080,1920
    audio_file, word_data = asyncio.run(make_voice_with_timing(story_raw))
    voice_audio = AudioFileClip(audio_file)
    duration = voice_audio.duration
    print(f"Audio duration: {duration}s")

    bg_path = download_ai_background(W, H)
    bg_clip = ImageClip(bg_path, duration=duration).resize((W,H)).fx(vfx.colorx, 0.6)

    caps = []
    # FORCE CAPTIONS - if word_data empty, use time-based
    if word_data and len(word_data) > 5:
        i = 0
        while i < len(word_data):
            start_time = word_data[i][0]
            phrase = " ".join([word_data[i+k][2] for k in range(5) if i+k < len(word_data)])
            i += 5
            if i < len(word_data):
                dur = word_data[i][0] - start_time
            else:
                dur = word_data[-1][1] - start_time + 0.5
            dur = max(0.6, min(dur, 2.0))
            caps.append(make_caption_clip(phrase, W, H, dur, start_time))
    else:
        print("Using fallback captions")
        words = story_raw.split()
        for idx in range(0, len(words), 5):
            text = " ".join(words[idx:idx+5])
            start = (idx/5)*1.5
            caps.append(make_caption_clip(text, W, H, 1.5, start))

    print(f"Total captions: {len(caps)}")
    final = CompositeVideoClip([bg_clip]+caps, size=(W,H)).set_audio(voice_audio)
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final.mp4"

if __name__ == "__main__":
    make_video()
    print("DONE - final.mp4 ready with captions!")
