import os, random, textwrap, asyncio
from datetime import datetime, timezone
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

# === AUTO 2 SHORTS + 1 LONG ===
utc_hour = datetime.now(timezone.utc).hour
env_val = os.getenv("IS_SHORT")
if env_val is not None:
    IS_SHORT = env_val == "true"
else:
    IS_SHORT = False if utc_hour == 0 else True

print(f"UTC Hour: {utc_hour} - Making {'SHORT' if IS_SHORT else 'LONG'}")

# === STORIES BANK ===
STORIES = [
    "My boyfriend told me he goes to the gym every night at 9pm. Last night I decided to follow him. He didn't go to the gym. He parked at my best friend's apartment. I waited 20 minutes then knocked. She opened it wearing the dress I lost last month. And my boyfriend was on her bed. I froze. Now my best friend is texting me saying it was a mistake. What should I do?",
    "My wife said she was working late for 3 weeks straight. One night her coworker posted a story at a hotel bar and my wife was in background laughing with a man. I drove to that hotel. When she opened the door in room 204, she wasn't alone. She begged me not to tell our kids.",
    "My mother in law told my husband I am cheating on him. She showed him fake messages from a fake Instagram she created with my pictures. She wanted her son to marry her friend's daughter. Now my husband is begging for forgiveness. Should I take him back?",
    "I found my girlfriend's second phone hidden in her closet. There were 200 messages with a guy named David. She told me David is just a coworker. But messages said I love you and hotel pictures. When I confronted her, she said I invaded her privacy. Am I wrong?",
    "My husband and I have been married for 5 years. Last month I found lipstick on his shirt that wasn't mine. He said it was from his sister hugging him. Yesterday I found a receipt for a diamond necklace for 500 dollars. He never bought me one. I checked his messages while he slept.",
]

story_raw = random.choice(STORIES)

def viral_pack(story, is_short):
    short_titles = ["I Followed Him And Regretted It Instantly", "She Was Wearing MY Clothes When I Caught Them", "My Girlfriend's Phone Revealed Everything", "He Said Gym, But Went To Her House"]
    long_titles = ["My Partner Cheated For Months, Until I Did THIS", "She Thought I Would Never Find Out, But I Followed Her", "My Best Friend Betrayed Me With My Own Boyfriend", "I Caught My Husband Lying, His Reaction Was Insane"]
    thumb_texts = ["I CAUGHT THEM!", "SHE LIED!", "CHEATED WITH HER?", "MY BEST FRIEND?!", "HE LIED!", "NO WAY!"]
    title = random.choice(short_titles if is_short else long_titles)
    if is_short: title += " #shorts"
    thumb = random.choice(thumb_texts)
    if is_short:
        desc = f"""{story}\n\nFull story on my channel, you won't believe what happened next.\n\n#shorts #redditstories #cheatingstories #relationship #storytime #reddit #confession\n\nSubscribe for daily stories 12pm, 5pm, 8pm WAT!"""
    else:
        desc = f"""{story}\n\nWhat would you have done? Comment below.\n\nTIMESTAMPS:\n00:00 - How it started\n01:30 - I started suspecting\n03:45 - The day I found out\n06:00 - What I did next\n\nSubscribe for daily shocking true stories!\n\n#redditstories #relationships #cheating #storytime #reddit #confession #truestory #betrayal #drama\n\nDisclaimer: Names changed for privacy."""
    tags = ["reddit stories","cheating stories","relationship stories","storytime","true story","confession","drama","betrayal"] if not is_short else ["shorts","reddit stories","cheating","storytime","drama"]
    return title, desc, tags, thumb

title, desc, tags, thumb_text = viral_pack(story_raw, IS_SHORT)

def make_thumbnail(text, is_short):
    W, H = (1080, 1920) if is_short else (1280, 720)
    img = Image.new('RGB', (W, H), color=(255, 215, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([W*0.65, 0, W, H], fill=(0,0,0))
    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 180 if is_short else 125)
        font_mid = ImageFont.truetype("DejaVuSans-Bold.ttf", 70 if is_short else 45)
    except:
        font_big = ImageFont.load_default()
        font_mid = font_big
    lines = textwrap.wrap(text.upper(), width=10)
    y = 120
    for line in lines:
        x = 40
        draw.text((x+8, y+8), line, font=font_big, fill=(0,0,0))
        for dx in [-3,3]:
            for dy in [-3,3]:
                draw.text((x+dx, y+dy), line, font=font_big, fill=(255,255,255))
        draw.text((x, y), line, font=font_big, fill=(0,0,0))
        y += 200 if is_short else 150
    draw.rounded_rectangle([40, H-180, 500, H-90], radius=20, fill=(255,0,0))
    draw.text((70, H-170), "REDDIT STORY", font=font_mid, fill=(255,255,255))
    img.save("thumb.jpg", quality=95)
    return "thumb.jpg"

async def make_voice(text, file="voice.mp3"):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural", rate="+10%")
    await communicate.save(file)
    return file

# === FIXED: REAL VIDEO WITH TEXT, NOT BLACK ===
def make_text_image(text, W, H, duration):
    # Cinematic background
    bg_colors = [(18,18,35), (35,18,18), (18,35,35), (25,25,25)]
    bg_color = random.choice(bg_colors)
    img = Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 58 if W==1080 else 48)
    except:
        font = ImageFont.load_default()

    # Wrap text to fit
    wrap_width = 28 if W==1080 else 60
    lines = textwrap.wrap(text, width=wrap_width)
    # Only show first ~8 lines so it fits
    lines = lines[:8]
    
    # Calculate text block height
    line_h = 75 if W==1080 else 62
    total_h = len(lines) * line_h
    y_start = (H - total_h)//2

    for line in lines:
        # Get text size for centering
        try:
            bbox = draw.textbbox((0,0), line, font=font)
            tw = bbox[2]-bbox[0]
        except:
            tw = len(line)*20
        x = (W - tw)//2
        y = y_start
        # Stroke for readability
        for dx in [-3,3]:
            for dy in [-3,3]:
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0))
        draw.text((x, y), line, font=font, fill=(255,255,255))
        y_start += line_h

    # Small brand bottom
    try:
        small_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
    except:
        small_font = font
    draw.text((40, H-80), "@MohVeritas", font=small_font, fill=(255,215,0))

    img.save("bg_text.png")
    return "bg_text.png"

def make_video():
    asyncio.run(make_voice(story_raw))
    W,H = (1080,1920) if IS_SHORT else (1920,1080)
    audio = AudioFileClip("voice.mp3")
    duration = min(audio.duration, 35 if IS_SHORT else 480)
    
    # Create image with text
    text_img_path = make_text_image(story_raw, W, H, duration)
    image_clip = ImageClip(text_img_path, duration=duration)
    
    final = image_clip.set_audio(audio.set_duration(duration))
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final.mp4"

video_file = make_video()
thumb_file = make_thumbnail(thumb_text, IS_SHORT)

# === UPLOAD ===
creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token", scopes=["https://www.googleapis.com/auth/youtube.upload"])
youtube = build("youtube", "v3", credentials=creds)
body = {"snippet": {"title": title[:100], "description": desc, "tags": tags, "categoryId": "22"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
video = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file)).execute()
print(f"UPLOADED: {video['id']} | {title}")
if not IS_SHORT:
    youtube.thumbnails().set(videoId=video["id"], media_body=MediaFileUpload(thumb_file, mimetype='image/jpeg')).execute()
    print(f"THUMBNAIL: {thumb_text}")
