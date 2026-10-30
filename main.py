import os, random, textwrap, asyncio, requests, urllib.parse
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
print(f"UTC Hour: {utc_hour} - Making {'SHORT' if IS_SHORT else 'LONG'}")

# === STORIES ===
STORIES = [
    "My boyfriend told me he goes to the gym every night at 9pm. Last night I decided to follow him. He didn't go to the gym. He parked at my best friend's apartment. I waited 20 minutes then knocked. She opened it wearing the dress I lost last month. And my boyfriend was on her bed.",
    "My wife said she was working late for 3 weeks straight. One night her coworker posted a story at a hotel bar and my wife was in background laughing with a man. I drove to that hotel. When she opened the door in room 204, she wasn't alone.",
    "My mother in law told my husband I am cheating on him. She showed him fake messages from a fake Instagram she created with my pictures. She wanted her son to marry her friend's daughter. Now my husband is begging for forgiveness.",
    "I found my girlfriend's second phone hidden in her closet. There were 200 messages with a guy named David. She told me David is just a coworker. But messages said I love you and hotel pictures.",
    "My best friend stole my girlfriend. I came home early and found them together on my couch. I didn't say anything. I just left. Then I did something they never expected.",
]

story_raw = random.choice(STORIES)

# === AI IMAGE PROMPTS - MATCHES STORY ===
def get_ai_prompt_from_story(story):
    s = story.lower()
    if "best friend" in s and "boyfriend" in s:
        return "shocked woman standing at apartment door at night catching cheating boyfriend and best friend, cinematic dramatic lighting"
    if "best friend" in s and "girlfriend" in s:
        return "sad young man sitting alone on bench at night in heavy rain heartbroken betrayal, hoodie, cinematic moody, ultra realistic"
    if "hotel" in s and "wife" in s:
        return "shocked man standing outside hotel room 204 door at night betrayal, cinematic noir lighting"
    if "second phone" in s or "phone" in s:
        return "man holding two phones shocked discovery cheating in dark bedroom, cinematic dramatic"
    if "mother in law" in s:
        return "crying woman alone in bedroom at night holding phone with fake messages betrayal family drama"
    return "lonely heartbroken person sitting alone in rain at night cinematic sad betrayal dark moody"

def download_ai_background(story, W, H):
    prompt = get_ai_prompt_from_story(story)
    safe = urllib.parse.quote(prompt + ", ultra realistic, 8k, cinematic, dramatic lighting")
    url = f"https://image.pollinations.ai/prompt/{safe}?width={W}&height={H}&model=flux&nologo=true&seed={random.randint(1,99999)}"
    try:
        print(f"Generating: {prompt}")
        r = requests.get(url, timeout=90)
        if r.status_code == 200 and len(r.content) > 5000:
            open("bg.jpg","wb").write(r.content)
            return "bg.jpg"
    except Exception as e:
        print(f"AI fail: {e}")
    # fallback
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

# === VOICE + WORD TIMESTAMPS ===
async def make_voice_with_timing(text, file="voice.mp3"):
    # Add CTA to voice
    if IS_SHORT:
        text = text + " ... Want the full shocking ending? Full story drops tonight at 8pm West Africa Time. Subscribe so you don't miss it!"
    else:
        text = text + " ... What would you do in my place? Comment below, I read every comment. And subscribe for daily shocking true stories."
    
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural", rate="+8%")
    words = []
    with open(file, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append((chunk["offset"]/10000000, chunk["offset"]/10000000 + chunk["duration"]/10000000, chunk["text"]))
    return file, words

def make_caption_clip(text, W, H, duration, start):
    img = Image.new('RGBA', (W, 500), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("DejaVuSans-Bold.ttf", 72 if W==1080 else 60)
    except: font = ImageFont.load_default()
    lines = textwrap.wrap(text.upper(), width=20 if W==1080 else 38)
    y=20
    for line in lines[:2]:
        try: tw = draw.textbbox((0,0), line, font=font)[2]-draw.textbbox((0,0), line, font=font)[0]
        except: tw = len(line)*22
        x = (W - tw)//2
        for dx in [-5,5]:
            for dy in [-5,5]:
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0))
        draw.text((x, y), line, font=font, fill=(255,255,255))
        y+=85
    path = f"cap_{int(start*1000)}.png"
    img.save(path)
    return ImageClip(path, duration=duration).set_start(start).set_position(("center", H//2 + 100))

def make_end_card(W, H, duration):
    img = Image.new('RGBA', (W, 350), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("DejaVuSans-Bold.ttf", 62 if W==1080 else 50)
    except: font = ImageFont.load_default()
    if IS_SHORT:
        lines = ["FULL STORY AT 8PM WAT!", "SUBSCRIBE FOR PART 2 🔔"]
    else:
        lines = ["SUBSCRIBE FOR MORE STORIES!", "COMMENT WHAT YOU WOULD DO"]
    y=20
    for line in lines:
        try: bbox = draw.textbbox((0,0), line, font=font); tw = bbox[2]-bbox[0]
        except: tw = len(line)*20
        x = (W - tw)//2
        for dx in [-4,4]:
            for dy in [-4,4]:
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0))
        draw.text((x, y), line, font=font, fill=(255,215,0))
        y+=75
    img.save("endcard.png")
    return ImageClip("endcard.png", duration=3).set_start(max(0, duration-3)).set_position(("center", H-400))

def make_video():
    W,H = (1080,1920) if IS_SHORT else (1920,1080)
    audio_file, word_data = asyncio.run(make_voice_with_timing(story_raw))
    audio = AudioFileClip(audio_file)
    duration = min(audio.duration, 44 if IS_SHORT else 480)
    
    bg_path = download_ai_background(story_raw, W, H)
    bg_clip = ImageClip(bg_path, duration=duration).resize((W,H)).fx(vfx.colorx, 0.6)

    phrases=[]; temp=[]; temp_start=0
    for i,(s,e,w) in enumerate(word_data):
        if not temp: temp_start=s
        temp.append(w)
        if len(temp)>=3 or i==len(word_data)-1:
            phrases.append((temp_start, min(e,duration)-temp_start, " ".join(temp)))
            temp=[]
    
    caps=[]
    for start,dur,txt in phrases:
        if dur<0.25: dur=0.35
        if start<duration: caps.append(make_caption_clip(txt,W,H,dur,start))

    end_card = make_end_card(W, H, duration)
    final = CompositeVideoClip([bg_clip]+caps+[end_card], size=(W,H)).set_audio(audio.set_duration(duration))
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final.mp4"

# === RUN ===
video_file = make_video()
thumb_file = make_thumbnail(thumb_text, IS_SHORT)

creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token", scopes=["https://www.googleapis.com/auth/youtube.upload"])
youtube = build("youtube", "v3", credentials=creds)
body = {"snippet": {"title": title[:100], "description": desc, "tags": tags, "categoryId": "22"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
video = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file)).execute()
vid_id = video["id"]
print(f"UPLOADED: {vid_id} | {title}")

# === PINNED COMMENT FOR SUBS ===
try:
    comment_text = "🔔 Full story drops at 8PM WAT tonight - it's INSANE. Subscribe so YouTube notifies you! What would YOU do if you were me? Comment below, I read all."
    if not IS_SHORT:
        comment_text = "What would YOU do in this situation? Comment below - I read every comment! Subscribe for daily shocking true stories 🔔"
    
    youtube.commentThreads().insert(
        part="snippet",
        body={"snippet": {"videoId": vid_id, "topLevelComment": {"snippet": {"textOriginal": comment_text}}}}
    ).execute()
    print("Pinned comment added!")
except Exception as e:
    print(f"Comment failed: {e}")
