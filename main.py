import asyncio
import random
import textwrap
import re
import os
import json
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip
import edge_tts

# === CONFIG ===
IS_SHORT = True
VOICE = "en-US-ChristopherNeural"  # Deep male viral voice

# === STORIES ===
STORIES = [
    "My wife said she was going to the gym at 5am. I decided to follow her one morning. She didn't go to the gym. She went to an apartment building across town. I watched her go inside.",
    "I found my husband's old phone in the garage. The messages inside made me realize our entire marriage was a lie. I confronted him that night.",
    "My girlfriend said she was working late. I drove to her office and her car wasn't there. I called her boss and he said she left at 3pm. Then I saw her at a restaurant with someone else.",
    "My husband has been acting strange for months. He hides his phone and stays up late. Last night I checked his laptop while he was sleeping and found everything.",
    "I thought my wife was cheating so I put a voice recorder in her car. What I heard the next day changed everything I thought I knew."
]

story_raw = random.choice(STORIES)
print(f"Story: {story_raw}")

# === VOICE ===
async def make_voice(text):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save("voice.mp3")
    print("Voice saved")

# === 3x CINEMATIC BACKGROUNDS ===
def get_story_prompts(story):
    s = story.lower()
    if "phone" in s or "message" in s:
        return [
            "woman alone in dark bedroom holding phone, calm, cinematic 4k",
            "woman looking shocked at phone screen in bed, tension, moody",
            "phone screen glowing in dark, secrets revealed, cinematic"
        ]
    if "gym" in s:
        return [
            "empty gym early morning 5am, cinematic moody",
            "man walking into gym suspicious, dark street, cinematic",
            "gym locker room secret, tension, 4k moody"
        ]
    if "office" in s or "work" in s or "boss" in s:
        return [
            "empty office desk at night, lonely, cinematic 4k",
            "woman walking out of office building late, dark street",
            "boss office door closed, secret, moody cinematic"
        ]
    return [
        "sad couple sitting apart in living room, distance, cinematic 4k",
        "person crying alone in bedroom at night, moody atmosphere",
        "shocking argument in house, emotional climax, dark cinematic"
    ]

def download_backgrounds(story, W, H):
    prompts = get_story_prompts(story)
    paths = []
    for i, prompt in enumerate(prompts):
        path = f"bg_{i}.jpg"
        try:
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width={W}&height={H}&nologo=true&seed={random.randint(1,99999)}"
            print(f"Downloading BG {i+1}: {prompt}")
            r = requests.get(url, timeout=40)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(r.content)
                paths.append(path)
            else:
                raise Exception("bad status")
        except Exception as e:
            print(f"BG {i} failed: {e}")
            img = Image.new('RGB', (W, H), color=(25 + i*10, 20, 35))
            img.save(path)
            paths.append(path)
    return paths

def create_text_image(text, W, H, bg_path, highlight=False):
    try:
        bg = Image.open(bg_path).convert('RGB')
        bg = bg.resize((W, H))
    except:
        bg = Image.new('RGB', (W, H), color=(20, 20, 30))
    
    overlay = Image.new('RGB', (W, H), color=(0, 0, 0))
    bg = Image.blend(bg, overlay, 0.55)
    
    draw = ImageDraw.Draw(bg)
    draw.rectangle([0, H-10, W, H], fill=(80, 80, 80))
    
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 44)
    except:
        font = ImageFont.load_default()
    
    lines = textwrap.wrap(text, width=22)
    total_h = len(lines) * 68
    y = (H // 2) - (total_h // 2)
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (W - w) // 2
        
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if abs(dx) + abs(dy) != 0:
                    draw.text((x+dx, y+dy), line, font=font, fill=(0, 0, 0))
        color = (255, 235, 59) if highlight else (255, 255, 255)
        draw.text((x, y), line, font=font, fill=color)
        y += 68
    
    return bg

def make_video():
    asyncio.run(make_voice(story_raw))
    W, H = (1080, 1920) if IS_SHORT else (1280, 720)
    audio = AudioFileClip("voice.mp3")
    duration = min(audio.duration, 34 if IS_SHORT else 590)
    
    bg_paths = download_backgrounds(story_raw, W, H)
    
    sentences = re.split(r'(?<=[.!?]) +', story_raw)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    clips = []
    total_chars = sum(len(s) for s in sentences)
    current_time = 0
    
    for idx, sent in enumerate(sentences):
        sent_duration = (len(sent) / total_chars) * duration
        if sent_duration < 0.9:
            sent_duration = 0.9
        
        bg_index = min((idx // 2), len(bg_paths)-1)
        bg_path = bg_paths[bg_index]
        
        pil_img = create_text_image(sent, W, H, bg_path, highlight=True)
        path = f"frame_{idx}.jpg"
        pil_img.save(path)
        
        img_clip = ImageClip(path).set_duration(sent_duration).set_start(current_time)
        if idx > 0:
            img_clip = img_clip.crossfadein(0.3)
        
        clips.append(img_clip)
        current_time += sent_duration
        if current_time >= duration:
            break
    
    final_video = CompositeVideoClip(clips, size=(W, H)).set_duration(duration)
    final_video = final_video.set_audio(audio.set_duration(duration))
    final_video.write_videofile("final.mp4", fps=24, codec='libx264', audio_codec='aac')
    return "final.mp4"

# === UPLOAD TO YOUTUBE ===
def upload_youtube(video_path):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    
    creds_info = json.loads(os.environ['YT_CREDENTIALS'])
    creds = Credentials.from_authorized_user_info(creds_info)
    youtube = build('youtube', 'v3', credentials=creds)
    
    title = "He Didn't Go To The Gym... #reddit #story"
    if len(story_raw) > 20:
        title = story_raw[:60] + "..."
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title[:95],
                "description": story_raw + "\n\n#redditstories #cheating #storytime",
                "tags": ["reddit", "story", "cheating"]
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )
    response = request.execute()
    print(f"Uploaded: {response['id']}")
    return response

if __name__ == "__main__":
    video_file = make_video()
    print(f"Video made: {video_file}")
    upload_youtube(video_file)
    print("DONE")
