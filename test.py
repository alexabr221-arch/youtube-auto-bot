import os, random, textwrap, asyncio, requests, urllib.parse
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
from moviepy.editor import *
import moviepy.video.fx.all as vfx
from PIL import ImageDraw, ImageFont
import edge_tts

IS_SHORT = True

STORIES = [
    "My boyfriend told me he goes to gym every night at 9pm. Last night I followed him. He didn't go to gym. He parked at my best friend's apartment. She opened wearing my lost dress. I sat in my car for 20 minutes crying. Then I walked up and knocked. You should have seen their faces."
]

story_raw = STORIES[0]

def get_ai_prompts_from_story(story, is_short):
    s = story.lower()
    
    if "best friend" in s and ("boyfriend" in s or "girlfriend" in s):
        return [
            "beautiful young woman crying alone in car at night watching apartment, heartbroken betrayal, cinematic lighting tears, ultra realistic 8k",
            "shocked woman standing outside apartment door catching cheating boyfriend with best friend, dramatic noir emotional",
            "lonely woman sitting on floor hugging knees crying betrayal, dark room moody cinematic"
        ]
    elif "wife" in s and "hotel" in s:
        return [
            "sad husband standing in dark hotel hallway heartbroken cinematic dramatic shadows 8k",
            "man looking shocked through hotel door, suspense betrayal noir film style",
            "empty luxury hotel bar at night lonely melancholic cinematic"
        ]
    elif "mother in law" in s:
        return [
            "angry older woman shouting at young woman in modern living room family drama intense cinematic",
            "young wife crying while mother in law yelling domestic fight emotional realistic",
            "tense family dinner table argument mother in law vs wife dramatic lighting"
        ]
    elif "boss" in s or "promotion" in s:
        return [
            "young man being yelled at by boss in office sad corporate drama cinematic office",
            "employee packing desk box after being fired lonely office emotional 8k",
            "successful man in luxury office smiling after revenge confident cinematic"
        ]
    elif "phone" in s or "second phone" in s or "messages" in s:
        return [
            "person discovering cheating messages on second phone in dark shocked face illuminated by phone screen cinematic ultra realistic",
            "two phones on bed one hidden betrayal discovery dark bedroom dramatic lighting",
            "person crying looking at phone at 2am heartbreak cinematic"
        ]
    elif "sister" in s or "brother" in s or "family" in s:
        return [
            "siblings arguing loudly in living room family betrayal intense emotion cinematic",
            "young person crying alone after family fight sad bedroom night realistic",
            "family house at night tension dramatic lighting emotional"
        ]
    else:
        return [
            "heartbroken person alone at night looking out window rain sad cinematic emotional ultra realistic 8k",
            "lonely person in dark bedroom crying betrayal dramatic moody lighting",
            "shocked woman face dramatic betrayal discovery cinematic"
        ]

def download_ai_backgrounds(story, W, H, is_short):
    prompts = get_ai_prompts_from_story(story, is_short)
    images = []
    
    for idx, prompt in enumerate(prompts):
        full_prompt = f"{prompt}, vertical portrait, ultra realistic, 8k, cinematic, dramatic lighting, emotional, highly detailed, viral youtube thumbnail style"
        safe = urllib.parse.quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{safe}?width={W}&height={H}&model=flux&nologo=true&enhance=true&seed={random.randint(1,999999)}"
        try:
            print(f"Generating AI image {idx+1}/3...")
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and len(r.content) > 8000:
                fname = f"bg_{idx}.jpg"
                open(fname,"wb").write(r.content)
                images.append(fname)
                print(f"✅ AI image {idx+1} ready - {len(r.content)} bytes")
            else:
                print(f"Failed {r.status_code}")
        except Exception as e:
            print(f"AI error {idx}: {e}")
    
    if not images:
        print("Fallback to picsum")
        r = requests.get(f"https://picsum.photos/{W}/{H}?random={random.randint(1,5000)}", timeout=20)
        open("bg_0.jpg","wb").write(r.content)
        images.append("bg_0.jpg")
    
    return images

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
    img = Image.new('RGBA', (W, 400), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
    except: font = ImageFont.load_default()
    
    lines = textwrap.wrap(text.upper(), width=18)
    y = 10
    for line in lines[:2]:
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        x = (W - tw)//2
        for dx in range(-4,5):
            for dy in range(-4,5):
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0,255))
        draw.text((x, y), line, font=font, fill=(255,255,255,255))
        y += th + 12
    
    path = f"cap_{int(start*1000)}_{random.randint(0,9999)}.png"
    img.save(path)
    return ImageClip(path, duration=duration).set_start(start).set_position(("center", H//2))

def make_video():
    W,H = 1080,1920
    audio_file, word_data = asyncio.run(make_voice_with_timing(story_raw))
    voice_audio = AudioFileClip(audio_file)
    duration = min(voice_audio.duration, 44)
    print(f"Audio duration: {duration}s")

    # VIRAL: 3 AI images matching story
    bg_files = download_ai_backgrounds(story_raw, W, H, IS_SHORT)
    print(f"Backgrounds: {bg_files}")
    
    bg_clips = []
    segment_duration = duration / len(bg_files)
    for i, bg_path in enumerate(bg_files):
        clip = ImageClip(bg_path, duration=segment_duration).set_start(i*segment_duration)
        if clip.w / clip.h < W / H: clip = clip.resize(width=W)
        else: clip = clip.resize(height=H)
        clip = clip.crop(x1=clip.w//2 - W//2, y1=clip.h//2 - H//2, width=W, height=H).fx(vfx.colorx, 0.7)
        clip = clip.resize(lambda t: 1 + 0.03*t)  # slow zoom
        bg_clips.append(clip)
    
    bg_clip = CompositeVideoClip(bg_clips, size=(W,H)).set_duration(duration)

    caps = []
    if word_data and len(word_data) > 5:
        i = 0
        while i < len(word_data):
            start_time = word_data[i][0]
            phrase_words = [word_data[i+k][2] for k in range(5) if i+k < len(word_data)]
            phrase = " ".join(phrase_words)
            i += 5
            if i < len(word_data): dur = word_data[i][0] - start_time
            else: dur = word_data[-1][1] - start_time + 0.5
            dur = max(0.6, min(dur, 2.2))
            caps.append(make_caption_clip(phrase, W, H, dur, start_time))
    else:
        words = story_raw.split()
        for idx in range(0, len(words), 5):
            text = " ".join(words[idx:idx+5])
            start = (idx/5)*1.4
            caps.append(make_caption_clip(text, W, H, 1.4, start))

    print(f"Total captions: {len(caps)}")
    final = CompositeVideoClip([bg_clip]+caps, size=(W,H)).set_audio(voice_audio)
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final.mp4"

if __name__ == "__main__":
    make_video()
    print("DONE - VIRAL VIDEO READY!")
