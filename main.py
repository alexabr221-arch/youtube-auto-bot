import os, random, asyncio, requests, urllib.parse, glob, subprocess
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
print(f"Making {'SHORT 1080x1920' if IS_SHORT else 'LONG 1920x1080'}")

STORIES = [
    "My boyfriend told me he goes to the gym every night at 9pm. Last night I decided to follow him. He didn't go to the gym. He parked at my best friend's apartment. I waited 20 minutes then knocked. She opened it wearing the dress I lost last month. And my boyfriend was on her bed.",
    "My wife said she was working late for 3 weeks straight. One night her coworker posted a story at a hotel bar and my wife was in background laughing with a man. I drove to that hotel. When she opened the door in room 204, she wasn't alone.",
    "My mother in law told my husband I am cheating on him. She showed him fake messages from a fake Instagram she created with my pictures. She wanted her son to marry her friend's daughter. Now my husband is begging for forgiveness.",
    "I found my girlfriend's second phone hidden in her closet. There were 200 messages with a guy named David. She told me David is just a coworker. But messages said I love you and hotel pictures.",
    "My best friend stole my girlfriend. I came home early and found them together on my couch. I didn't say anything. I just left. Then I did something they never expected.",
]

story_raw = random.choice(STORIES)

def get_ai_prompt_from_story(story):
    s = story.lower()
    if "best friend" in s and "boyfriend" in s:
        return "shocked woman at apartment door at night catching cheating boyfriend, cinematic dramatic lighting"
    if "best friend" in s and "girlfriend" in s:
        return "sad young man alone bench night heavy rain heartbroken hoodie cinematic moody"
    if "hotel" in s and "wife" in s:
        return "beautiful young woman white sweater anxious hands near mouth dark hallway cinematic portrait centered ultra realistic"
    if "second phone" in s or "phone" in s:
        return "man holding two phones shocked discovery cheating dark bedroom cinematic"
    if "mother in law" in s:
        return "crying woman alone bedroom night holding phone fake messages betrayal"
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
    except Exception as e:
        print(f"AI fail: {e}")
    r = requests.get(f"https://picsum.photos/{W}/{H}?random={random.randint(1,1000)}", timeout=20)
    open("bg.jpg","wb").write(r.content)
    return "bg.jpg"

def viral_pack(story, is_short):
    if is_short:
        titles = ["I Followed Him And My Heart Shattered Instantly", "My Best Friend Was Wearing MY Clothes When I Caught Them", "My Girlfriend Hid A Second Phone... What I Found BROKE Me"]
    else:
        titles = ["My Partner Cheated For Months Until I Did THIS", "My Best Friend Stole My Girlfriend And I Got Revenge"]
    title = random.choice(titles)
    if is_short: title += " #shorts"
    desc = f"{story}\n\nFull story drops tonight at 8PM WAT. Subscribe so you don't miss it!\n\n#shorts #redditstories #cheatingstories #storytime"
    if not is_short:
        desc = f"{story}\n\nWhat would YOU do? Comment below!\n\n#redditstories #cheatingstories #storytime #drama"
    tags = ["shorts","reddit stories","cheating","storytime","betrayal","drama"]
    return title, desc, tags, "SHE CHEATED?!"

title, desc, tags, thumb_text = viral_pack(story_raw, IS_SHORT)

def make_thumbnail(text, is_short):
    W, H = (1080, 1920) if is_short else (1280, 720)
    img = Image.new('RGB', (W, H), color=(255, 215, 0))
    draw = ImageDraw.Draw(img)
    try: font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 180 if is_short else 125)
    except: font_big = ImageFont.load_default()
    draw.text((40, 120), text, font=font_big, fill=(0,0,0))
    img.save("thumb.jpg", quality=95)
    return "thumb.jpg"

async def make_voice_with_timing(text, file="voice.mp3"):
    for f in glob.glob("cap_*.png"):
        try: os.remove(f)
        except: pass
    if IS_SHORT:
        text = text + " Want the full shocking ending? Full story drops tonight at 8pm West Africa Time. Subscribe so you don't miss it!"
    else:
        text = text + " What would you do in my place? Comment below. Subscribe for daily shocking true stories."
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
    print(f"Got {len(words)} words with exact timing")
    return file, words

def format_srt_time(seconds):
    ms = int((seconds - int(seconds)) * 1000)
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"

def make_video():
    W,H = (1080,1920) if IS_SHORT else (1920,1080)
    audio_file, word_data = asyncio.run(make_voice_with_timing(story_raw))
    audio = AudioFileClip(audio_file)
    duration = audio.duration
    print(f"Audio duration: {duration}")
    
    bg_path = download_ai_background(story_raw, W, H)
    raw_bg = ImageClip(bg_path)
    if raw_bg.w / raw_bg.h < W / H:
        raw_bg = raw_bg.resize(width=W)
    else:
        raw_bg = raw_bg.resize(height=H)
    x1 = (raw_bg.w - W)/2
    y1 = (raw_bg.h - H)/2
    bg_clip = raw_bg.crop(x1=x1, y1=y1, width=W, height=H).set_duration(duration).fx(vfx.colorx, 0.6)

    # CREATE SRT - FRAME PERFECT
    with open("subs.srt", "w", encoding="utf-8") as f:
        for i, (s, e, w) in enumerate(word_data):
            if s >= duration: break
            # Cut exactly at next word start = PERFECT SYNC
            if i+1 < len(word_data):
                next_s = word_data[i+1][0]
                e = min(e + 0.05, next_s)  # tiny overlap to avoid flicker
            if e > duration: e = duration
            if e - s < 0.2: e = s + 0.22
            f.write(f"{i+1}\n{format_srt_time(s)} --> {format_srt_time(e)}\n{w.upper()}\n\n")

    temp_video = "temp_no_cap.mp4"
    CompositeVideoClip([bg_clip], size=(W,H)).set_audio(audio).write_videofile(temp_video, fps=24, codec="libx264", audio_codec="aac")

    # BURN WITH FFMPEG - ZERO LAG
    final_video = "final.mp4"
    # White text, thick black border, bold, centered middle
    style = "FontName=DejaVu Sans,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H00000000,BorderStyle=3,Outline=8,Shadow=0,Bold=1,Alignment=5,MarginV=650"
    cmd = f'ffmpeg -y -i {temp_video} -vf "subtitles=subs.srt:force_style=\'{style}\'" -c:a copy {final_video}'
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)
    
    # Add end card with MoviePy again for subscribe text
    try:
        img = Image.new('RGBA', (W, 300), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("DejaVuSans-Bold.ttf", 62)
        except: font = ImageFont.load_default()
        txt = "FULL STORY AT 8PM WAT! SUBSCRIBE 🔔"
        bbox = draw.textbbox((0,0), txt, font=font)
        tw = bbox[2]-bbox[0]
        x = (W-tw)//2
        draw.text((x, 20), txt, font=font, fill=(255,215,0), stroke_width=4, stroke_fill=(0,0,0))
        img.save("endcard.png")
        end_clip = ImageClip("endcard.png", duration=3).set_position(("center", H-400))
        video_with_cap = VideoFileClip(final_video)
        final = CompositeVideoClip([video_with_cap, end_clip.set_start(max(0, video_with_cap.duration-3))], size=(W,H))
        final.write_videofile("final2.mp4", fps=24, codec="libx264", audio_codec="aac")
        return "final2.mp4"
    except:
        return final_video

# === RUN - PRIVATE FOR TEST ===
video_file = make_video()
thumb_file = make_thumbnail(thumb_text, IS_SHORT)

creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token", scopes=["https://www.googleapis.com/auth/youtube.upload"])
youtube = build("youtube", "v3", credentials=creds)
body = {"snippet": {"title": title[:100], "description": desc, "tags": tags, "categoryId": "22"}, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}
video = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file)).execute()
vid_id = video["id"]
print(f"UPLOADED PRIVATE PERFECT SYNC: {vid_id} - Check on PHONE, not GitHub preview!")

try:
    youtube.commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid_id, "topLevelComment": {"snippet": {"textOriginal": "🔔 Full story at 8PM WAT - Subscribe so YouTube notifies you! What would YOU do?"}}}}).execute()
except Exception as e:
    print(f"Comment failed: {e}")
