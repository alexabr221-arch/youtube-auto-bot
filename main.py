import os, random, textwrap, asyncio, requests
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
IS_SHORT = (env_val == "true") if env_val else (False if utc_hour == 0 else True)
print(f"UTC Hour: {utc_hour} - Making {'SHORT' if IS_SHORT else 'LONG'}")

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
    desc = f"{story}\n\n#shorts #redditstories #cheatingstories #relationship #storytime" if is_short else f"{story}\n\nSubscribe for daily shocking true stories!\n\n#redditstories #relationships #cheating #storytime"
    tags = ["shorts","reddit stories","cheating","storytime","drama"] if is_short else ["reddit stories","cheating stories","relationship stories","storytime","true story"]
    return title, desc, tags, thumb

title, desc, tags, thumb_text = viral_pack(story_raw, IS_SHORT)

def make_thumbnail(text, is_short):
    W, H = (1080, 1920) if is_short else (1280, 720)
    img = Image.new('RGB', (W, H), color=(255, 215, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([W*0.65, 0, W, H], fill=(0,0,0))
    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 180 if is_short else 125)
    except:
        font_big = ImageFont.load_default()
    lines = textwrap.wrap(text.upper(), width=10)
    y = 120
    for line in lines:
        draw.text((40, y), line, font=font_big, fill=(0,0,0))
        y += 200 if is_short else 150
    img.save("thumb.jpg", quality=95)
    return "thumb.jpg"

async def make_voice(text, file="voice.mp3"):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural", rate="+10%")
    await communicate.save(file)
    return file

def download_background(W, H):
    try:
        # Free random aesthetic image - no API key needed
        url = f"https://picsum.photos/{W}/{H}?random={random.randint(1,1000)}"
        r = requests.get(url, timeout=15)
        open("bg.jpg","wb").write(r.content)
        print("Background downloaded from picsum")
        return "bg.jpg"
    except Exception as e:
        print(f"BG download failed {e}, using color")
        img = Image.new('RGB', (W,H), color=(20,20,35))
        img.save("bg.jpg")
        return "bg.jpg"

def make_caption_image(text, W, H):
    # Transparent image for captions
    img = Image.new('RGBA', (W, H), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 62 if W==1080 else 52)
    except:
        font = ImageFont.load_default()

    wrap_width = 24 if W==1080 else 55
    lines = textwrap.wrap(text, width=wrap_width)[:6]
    line_h = 78 if W==1080 else 68
    # Black box behind text
    box_h = len(lines)*line_h + 60
    y_box = (H//2 - box_h//2) if W==1080 else (H - box_h - 120)
    draw.rectangle([0, y_box-20, W, y_box+box_h], fill=(0,0,0,160))

    y = y_box
    for line in lines:
        try:
            bbox = draw.textbbox((0,0), line, font=font)
            tw = bbox[2]-bbox[0]
        except:
            tw = len(line)*18
        x = (W - tw)//2
        # Stroke
        for dx in [-3,3]:
            for dy in [-3,3]:
                draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0,255))
        draw.text((x, y), line, font=font, fill=(255,255,255,255))
        y += line_h

    img.save("caption.png")
    return "caption.png"

def make_video():
    asyncio.run(make_voice(story_raw))
    W,H = (1080,1920) if IS_SHORT else (1920,1080)
    audio = AudioFileClip("voice.mp3")
    duration = min(audio.duration, 35 if IS_SHORT else 480)

    bg_path = download_background(W, H)
    caption_path = make_caption_image(story_raw, W, H)

    bg_clip = ImageClip(bg_path, duration=duration).resize((W,H))
    # Darken background slightly so text pops
    bg_clip = bg_clip.fx(vfx.colorx, 0.7)

    caption_clip = ImageClip(caption_path, duration=duration).set_position(("center","center"))

    final = CompositeVideoClip([bg_clip, caption_clip], size=(W,H)).set_audio(audio.set_duration(duration))
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final.mp4"

video_file = make_video()
thumb_file = make_thumbnail(thumb_text, IS_SHORT)

creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token", scopes=["https://www.googleapis.com/auth/youtube.upload"])
youtube = build("youtube", "v3", credentials=creds)
body = {"snippet": {"title": title[:100], "description": desc, "tags": tags, "categoryId": "22"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
video = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file)).execute()
print(f"UPLOADED: {video['id']} | {title}")
if not IS_SHORT:
    youtube.thumbnails().set(videoId=video["id"], media_body=MediaFileUpload(thumb_file, mimetype='image/jpeg')).execute()
