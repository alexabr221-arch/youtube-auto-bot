import os, random, asyncio, requests, urllib.parse, glob
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
from datetime import datetime, timezone
from moviepy.editor import *
from PIL import ImageDraw, ImageFont
import edge_tts
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

utc_hour = datetime.now(timezone.utc).hour
env_val = os.getenv("IS_SHORT")
IS_SHORT = (env_val == "true") if env_val else (False if utc_hour == 0 else True)

STORIES = [
    "My boyfriend told me he goes to the gym every night at 9pm. Last night I decided to follow him. He didn't go to the gym. He parked at my best friend's apartment. I waited 20 minutes then knocked. She opened it wearing the dress I lost last month. And my boyfriend was on her bed.",
    "My wife said she was working late for 3 weeks straight. One night her coworker posted a story at a hotel bar and my wife was in background laughing with a man. I drove to that hotel. When she opened the door in room 204, she wasn't alone.",
    "My mother in law told my husband I am cheating on him. She showed him fake messages from a fake Instagram she created with my pictures. She wanted her son to marry her friend's daughter. Now my husband is begging for forgiveness.",
]

story_raw = random.choice(STORIES)

def get_ai_prompt_from_story(story):
    s = story.lower()
    if "best friend" in s and "boyfriend" in s:
        return "shocked woman at apartment door night catching cheating boyfriend cinematic dramatic"
    if "best friend" in s and "girlfriend" in s:
        return "sad young man alone bench night heavy rain heartbroken hoodie cinematic moody"
    if "hotel" in s:
        return "beautiful young woman white sweater anxious hands near mouth dark hallway cinematic portrait centered ultra realistic"
    return "lonely heartbroken person rain night cinematic sad dark moody"

def download_ai_background(story, W, H):
    prompt = get_ai_prompt_from_story(story)
    safe = urllib.parse.quote(prompt + ", ultra realistic, 8k, cinematic, centered portrait, not stretched")
    url = f"https://image.pollinations.ai/prompt/{safe}?width={W}&height={H}&model=flux&nologo=true&seed={random.randint(1,999999)}"
    try:
        r = requests.get(url, timeout=90)
        if r.status_code == 200 and len(r.content) > 5000:
            open("bg.jpg","wb").write(r.content)
            return "bg.jpg"
    except: pass
    r = requests.get(f"https://picsum.photos/{W}/{H}?random={random.randint(1,1000)}", timeout=20)
    open("bg.jpg","wb").write(r.content)
    return "bg.jpg"

def viral_pack(story, is_short):
    titles = ["I Followed Him And My Heart Shattered Instantly", "My Best Friend Was Wearing MY Clothes When I Caught Them"]
    title = random.choice(titles) + (" #shorts" if is_short else "")
    desc = f"{story}\n\n#shorts #redditstories"
    return title, desc, ["shorts","reddit"], "SHE CHEATED?!"

title, desc, tags, thumb_text = viral_pack(story_raw, IS_SHORT)

def make_thumbnail(text, is_short):
    W, H = (1080, 1920) if is_short else (1280, 720)
    img = Image.new('RGB', (W, H), color=(255, 215, 0))
    draw = ImageDraw.Draw(img)
    try: font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 180)
    except: font_big = ImageFont.load_default()
    draw.text((40, 120), text, font=font_big, fill=(0,0,0))
    img.save("thumb.jpg", quality=95)
    return "thumb.jpg"

async def make_voice_with_timing(text, file="voice.mp3"):
    for f in glob.glob("cap_*.png"):
        try: os.remove(f)
        except: pass
    if IS_SHORT:
        text = text + " Want the full shocking ending? Full story drops tonight at 8pm West Africa Time. Subscribe!"
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural", rate="+12%")
    words = []
    with open(file, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                s = chunk["offset"] / 10000000
                e = s + (chunk["duration"] / 10000000)
                words.append((s, e, chunk["text"]))
    return file, words

def make_caption_image(text, W, path):
    # PIL CAPTION - THIS ALWAYS SHOWS
    img = Image.new('RGBA', (W, 400), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 85)
    except:
        try: font = ImageFont.truetype("DejaVuSans-Bold.ttf", 85)
        except: font = ImageFont.load_default()
    line = text.upper().strip()
    bbox = draw.textbbox((0,0), line, font=font)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    x = (W - tw)//2
    y = (400 - th)//2
    # thick black outline
    for dx in (-5,-3,0,3,5):
        for dy in (-5,-3,0,3,5):
            if dx or dy:
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0,255))
    draw.text((x, y), line, font=font, fill=(255,255,255,255))
    img.save(path)
    return path

def make_video():
    W,H = (1080,1920) if IS_SHORT else (1920,1080)
    audio_file, word_data = asyncio.run(make_voice_with_timing(story_raw))
    audio = AudioFileClip(audio_file)
    duration = audio.duration
    
    bg_path = download_ai_background(story_raw, W, H)
    raw_bg = ImageClip(bg_path)
    if raw_bg.w / raw_bg.h < W / H:
        raw_bg = raw_bg.resize(width=W)
    else:
        raw_bg = raw_bg.resize(height=H)
    bg_clip = raw_bg.crop(x1=(raw_bg.w-W)/2, y1=(raw_bg.h-H)/2, width=W, height=H).set_duration(duration).fx(vfx.colorx, 0.6)

    clips = [bg_clip]
    print(f"Creating {len(word_data)} captions with exact timing")
    for i, (s, e, w) in enumerate(word_data):
        if s >= duration: break
        # PERFECT SYNC: cut at next word start
        if i+1 < len(word_data):
            next_s = word_data[i+1][0]
            if e > next_s:
                e = next_s
        dur = e - s
        if dur < 0.18:
            dur = 0.18
        if s + dur > duration:
            dur = duration - s
        cap_path = f"cap_{i}_{random.randint(0,999999)}.png"
        make_caption_image(w, W, cap_path)
        cap_clip = ImageClip(cap_path, duration=dur).set_start(s).set_position(('center', H//2))
        clips.append(cap_clip)

    final = CompositeVideoClip(clips, size=(W,H)).set_audio(audio)
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final.mp4"

video_file = make_video()
thumb_file = make_thumbnail(thumb_text, IS_SHORT)

creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token", scopes=["https://www.googleapis.com/auth/youtube.upload"])
youtube = build("youtube", "v3", credentials=creds)
body = {"snippet": {"title": title[:100], "description": desc, "tags": tags, "categoryId": "22"}, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}
video = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file)).execute()
print(f"UPLOADED PRIVATE WITH CAPTION: {video['id']}")
