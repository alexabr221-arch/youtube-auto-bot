import os, random, textwrap, asyncio, re
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

IS_SHORT = os.getenv("IS_SHORT") == "true"

# === STORIES BANK ===
STORIES = [
    "My boyfriend told me he goes to the gym every morning at 5am. I decided to follow him one day and what I saw broke me completely. He was not at the gym.",
    "My wife said she was working late for 3 weeks straight. I brought her dinner to her office and her boss said she left 3 weeks ago. She was fired.",
    "My mother in law told my husband I am cheating on him. I found out she hired someone to send me fake messages to frame me.",
    "I found my girlfriend's second phone hidden in her closet. The messages inside made me freeze. She has a whole second life.",
    "My husband and I have been married for 5 years and yesterday I found out his first wife never divorced him. I am not his wife."
]
story_raw = random.choice(STORIES)

# === VIRAL BRAIN ===
def viral_pack(story, is_short):
    short_titles = ["I Followed Him And Regretted It Immediately", "She Lied For 3 Weeks Straight", "I Found Her Second Phone", "My Wife's Boss Told Me The Truth"]
    long_titles = ["My Partner Cheated For Months, Here Is How I Found Out", "The Day I Discovered The Truth Changed Everything"]
    thumb_texts = ["I CAUGHT THEM!", "SHE LIED!", "I FOLLOWED HIM!", "HE CHEATED!"]
    title = random.choice(short_titles if is_short else long_titles)
    if is_short: title += " #shorts"
    thumb = random.choice(thumb_texts)
    if is_short:
        desc = f"""{story}

Full story on my channel, you won't believe what happened next.

#shorts #redditstories #cheatingstories #relationship

Subscribe for daily stories 12pm, 5pm, 8pm WAT!"""
    else:
        desc = f"""{story}

What would you have done? Comment below.

TIMESTAMPS:
00:00 - How it started
01:30 - I started suspecting
03:45 - The day I found out
06:00 - What I did next

Subscribe for daily shocking true stories!

#redditstories #relationships #cheating #storytime

Disclaimer: Names changed for privacy."""
    tags = ["reddit stories","cheating stories","relationship stories"]
    return title, desc, tags, thumb

title, desc, tags, thumb_text = viral_pack(story_raw, IS_SHORT)

# === PRO THUMBNAIL ===
def make_thumbnail(text, is_short):
    W, H = (1080, 1920) if is_short else (1280, 720)
    img = Image.new('RGB', (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([W*0.65, 0, W, H], fill=(0,0,0))
    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 110 if is_short else 80)
        font_mid = ImageFont.truetype("DejaVuSans.ttf", 50)
    except:
        font_big = ImageFont.load_default()
        font_mid = font_big
    lines = textwrap.wrap(text.upper(), width=12 if is_short else 18)
    y = 120
    for line in lines:
        x = 40
        draw.text((x+8, y+8), line, font=font_big, fill=(0,0,0))
        for dx in [-3,3]:
            for dy in [-3,3]:
                draw.text((x+dx, y+dy), line, font=font_big, fill=(255,255,0))
        draw.text((x, y), line, font=font_big, fill=(0,0,0))
        y += 200 if is_short else 150
    draw.rounded_rectangle([40, H-180, 500, H-90], radius=20, fill=(255,0,0))
    draw.text((70, H-170), "REDDIT STORY", font=font_mid, fill=(255,255,255))
    draw.ellipse([W*0.68, 80, W*0.95, 380], fill=(255,230,0))
    try:
        draw.text((W*0.72, 130), "😱", font=ImageFont.truetype("DejaVuSans.ttf", 150), fill=(0,0,0))
    except:
        draw.text((W*0.72, 130), "!!", font=font_big, fill=(0,0,0))
    img.save("thumb.jpg", quality=95)
    return "thumb.jpg"

# === VIRAL VIDEO WITH WORD HIGHLIGHT ===
async def make_voice(text, file="voice.mp3"):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural") # DEEP MALE VIRAL VOICE
    await communicate.save(file)
    return file

def create_text_image(text, W, H, highlight=False):
    img = Image.new('RGB', (W, H), color=(15,15,15))
    draw = ImageDraw.Draw(img)
    # Progress bar background
    draw.rectangle([0, H-12, W, H], fill=(50,50,50))
    
    lines = textwrap.wrap(text, width=20)
    y = H//2 - len(lines)*45
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 42)
    except:
        font = ImageFont.load_default()
    
    for line in lines:
        bbox = draw.textbbox((0,0), line, font=font)
        w = bbox[2]-bbox[0]
        x = (W-w)//2
        # Glow + highlight
        if highlight:
            draw.text((x+4, y+4), line, font=font, fill=(0,0,0))
            draw.text((x, y), line, font=font, fill=(255,235,59)) # YELLOW VIRAL
        else:
            draw.text((x+3, y+3), line, font=font, fill=(0,0,0))
            draw.text((x, y), line, font=font, fill=(255,255,255))
        y += 85
    return img

def make_video():
    asyncio.run(make_voice(story_raw))
    W,H = (1080, 1920) if IS_SHORT else (1280, 720)
    audio = AudioFileClip("voice.mp3")
    duration = min(audio.duration, 34 if IS_SHORT else 590)
    
    # Split story into sentences for word highlight effect
    sentences = re.split(r'(?<=[.!?]) +', story_raw)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    clips = []
    total_chars = sum(len(s) for s in sentences)
    current_time = 0
    
    for sent in sentences:
        sent_duration = (len(sent)/total_chars) * duration
        if sent_duration < 0.8: sent_duration = 0.8
        
        # Create image with this sentence highlighted
        pil_img = create_text_image(sent, W, H, highlight=True)
        path = f"frame_{current_time}.jpg"
        pil_img.save(path)
        
        img_clip = ImageClip(path).set_duration(sent_duration).set_start(current_time)
        clips.append(img_clip)
        current_time += sent_duration
        if current_time >= duration: break
    
    # Background + audio
    final_video = CompositeVideoClip(clips, size=(W,H)).set_duration(duration)
    final_video = final_video.set_audio(audio.set_duration(duration))
    
    # Add moving progress bar
    def make_progress_bar(t):
        img = Image.new('RGBA', (W, 12), (0,0,0,0))
        d = ImageDraw.Draw(img)
        progress = int((t/duration)*W)
        d.rectangle([0,0,progress,12], fill=(255,0,0))
        return np.array(img)
    
    # Write final
    final_video.write_videofile("final.mp4", fps=24, codec='libx264', audio_codec='aac')
    return "final.mp4"

import numpy as np
video_file = make_video()
thumb_file = make_thumbnail(thumb_text, IS_SHORT)

# === UPLOAD ===
creds = Credentials(None, refresh_token=os.getenv("YT_REFRESH_TOKEN"), token_uri="https://oauth2.googleapis.com/token", client_id=os.getenv("YT_CLIENT_ID"), client_secret=os.getenv("YT_CLIENT_SECRET"))
youtube = build("youtube", "v3", credentials=creds)
body = {"snippet": {"title": title[:100], "description": desc, "tags": tags, "categoryId": "22"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
video = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)).execute()
print(f"UPLOADED: {video['id']} | {title}")
if not IS_SHORT:
    youtube.thumbnails().set(videoId=video["id"], media_body=MediaFileUpload(thumb_file)).execute()
    print(f"THUMBNAIL: {thumb_text}")
