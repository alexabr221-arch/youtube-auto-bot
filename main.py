import os, random, textwrap, asyncio, requests, urllib.parse, json
from PIL import Image, ImageFilter
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
from datetime import datetime, timezone, date
from moviepy.editor import *
from moviepy.video.fx.all import colorx
import moviepy.video.fx.all as vfx
from PIL import ImageDraw, ImageFont
import edge_tts
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

utc_hour = datetime.now(timezone.utc).hour
env_val = os.getenv("IS_SHORT")
IS_SHORT = (env_val == "true") if env_val else (False if utc_hour == 0 else True)
print(f"UTC Hour: {utc_hour} - Making {'SHORT' if IS_SHORT else 'LONG'}")

STORIES = [
"My boyfriend told me he goes to gym every night at 9pm. Last night I followed him. He didn't go to gym. He parked at my best friend's apartment. She opened wearing my lost dress.",
"My wife said working late for 3 weeks. Her coworker posted hotel bar story and my wife was laughing with a man in background. I drove to that hotel room 204.",
"My fiance said he lost his engagement ring. I found same ring in his best friend's drawer with a love note saying miss you.",
"I found my girlfriend's second phone hidden in closet. 200 messages with David. She said coworker but messages said I love you and hotel pics.",
"My husband's phone rang at 2am, said work. Call log showed saved as Gym Coach but was a girl with heart emoji.",
"My girlfriend said she hates clubs. Saw her TikTok in club last night with my cousin grinding on her.",
"My boyfriend said he's broke. Saw alert of 200k transfer to another woman named Amaka.",
"My wife said fasting for church. Saw meat in her bag when she came back home smiling.",
"My girlfriend said ex is just friend. Found his boxers in her room under pillow.",
"My wife said girls night. Location showed at her ex's house till 2am.",
"My husband said business trip to Abuja. Saw Instagram story of him in Lagos beach with another woman.",
"My boyfriend said he doesn't know my friend Sarah. Saw Sarah's lipstick on his shirt collar.",
"My fiancee said virgin. Found chat with ex last week saying last night was amazing.",
"My wife said she went to mother house. Mother called me asking where is my wife.",
"My girlfriend left her laptop open. WhatsApp Web showed my best friend sending her nude pics.",
"My boyfriend said phone battery dead. Was online on WhatsApp all night with another girl.",
"My husband said he working overtime. Colleague told me he resigned 2 weeks ago.",
"My wife said she at salon. Salon girl said she didn't come today.",
"My boyfriend said he at church vigil. Saw him entering hotel with my classmate.",
"My girlfriend said she's sleeping. Heard man voice when I called again.",
"My husband said he hates cheating. Found condom in his car, we don't use condom.",
"My wife said no money for food. Saw her send money to another man for shoes.",
"My boyfriend said he allergic to perfume. Came home smelling female perfume.",
"My fiance said he never been married before. Found divorce papers in his drawer.",
"My girlfriend said she broke up with ex 2 years ago. Saw recent pics of them kissing last month.",
"My wife said she's pregnant. Doctor report says she not pregnant but was last month.",
"My boyfriend said he traveling with guys. Only girls in his trip photos.",
"My husband said phone fell inside water. Found chat backup showing he blocked me on second account.",
"My girlfriend said she with her sister. Her sister was with me at same time.",
"My boyfriend said he doesn't drink. Saw video of him drunk kissing another girl.",
"My wife said she went to pray. Pastor's wife called asking why my wife missed meeting but she left house 3 hours ago.",
"My girlfriend said she lost her phone. Used Find My iPhone, phone was at a boy's hostel.",
"My husband said he hates my best friend. Saw him hugging her tightly at mall when he thought I traveled.",
"My fiance said he sent money to his mom. Mom called saying she didn't receive anything.",
"My boyfriend said he sleeping at his friend house. Friend posted sleeping alone.",
"My wife said she doesn't know that guy. That guy has her photo as wallpaper.",
"My girlfriend said she at work. Boss said she took leave today.",
"My husband said he went to barber. Came back without haircut but with lipstick stain.",
"My boyfriend said he doesn't have car. Girl posted inside his car saying my baby's car.",
"My wife said she miscarried. Found pregnancy test of another woman in her bag.",
"My best friend stole my girlfriend. I came home early and found them on my couch. I didn't shout, I left and did something they never expected.",
"My sister borrowed my car for interview. Returned empty fuel and scratch. When I confronted, she said I'm selfish and should buy new one.",
"My boss promised promotion if I work weekend 3 months. I did, then he gave promotion to his nephew who just joined.",
"My friend asked me keep secret. Then told everyone my secret instead and laughed.",
"My dad said no money for school fees. Same day bought new iPhone for my stepmom.",
"My neighbor uses my WiFi without asking. I changed password, he came to fight me.",
"My brother sold my PlayStation without asking to buy shoes and said I don't use it anyway.",
"My coworker took credit for my project in front of boss and got award for it.",
"My uncle promised help me travel abroad. Collected 500k and blocked me.",
"My best friend dated my ex 2 weeks after breakup and said it was accident, love is blind.",
"My sister ate my food I saved for work next day and said I should have labeled it.",
"My friend borrowed 50k promised tomorrow. Tomorrow reached 6 months now.",
"My cousin reported me to landlord that I smoke weed but I don't even smoke.",
"My friend used my picture to scam people online and now police looking for me.",
"My best friend told my crush I have disease so she would leave me for him.",
"My brother used my certificate to apply for job without telling me.",
"My friend posted my private chat on status to get likes.",
"My sister used my makeup kit worth 100k and ruined everything.",
"My friend invited me to party only to insult me in front of everyone.",
"My landlord increased rent without notice and said take it or leave, I have many tenants.",
"My friend promised to link me to job. Collected my CV and applied for himself.",
"My sister lied to my parents I stole money but she was the one who stole.",
"My best friend slept with my brother and said it was mistake, she was drunk.",
"My friend broke my phone screen and said it was already broken.",
"My cousin stole my business idea and opened same shop opposite my shop.",
"My friend said she doesn't like my boyfriend. Now she pregnant for him.",
"My brother withdrew money from my account with my ATM without permission.",
"My friend gossiped that I'm barren, I'm just 22 and not married.",
"My sister threw away my books saying I'm wasting money on school.",
"My friend recorded my voice when I was crying and posted online.",
"My mother in law moved into our house without asking and started controlling what I cook, wear, say. Yesterday she told my husband I'm bad wife, so I made her pack same night.",
"My mother in law told my husband I am cheating on him. She showed fake messages from fake Instagram she created with my pictures.",
"My mother in law said my child is not fair like her son, so child not his. DNA proved she's lying.",
"My father said he will give house to my brother only because I'm female. I paid for roof of that house.",
"My family said I should marry old man because he has money. I am 20 and in school.",
"My mother in law said I should not work because her son can provide. Her son doesn't provide.",
"My brother said I should leave his house because I'm not paying rent but I pay light and water and food.",
"My family used my school fees to do burial party for grandma I never knew.",
"My father-in-law said I should kneel to greet him every morning at 5am or leave his house.",
"My mother said if I don't send money monthly, she will curse me.",
"My husband said his mother will control my salary because I'm now wife.",
"My sister said she will not allow me marry before her even though she not dating anyone.",
"My family said I should abort my pregnancy because I'm not married yet, I'm 28.",
"My mother in law said my cooking is bad and threw my soup away while I was at work.",
"My father said I should give my salary to my brother because he's first son.",
"My husband's family said I should not go to church because their church different.",
"My mother in law searched my bag when I visited and said she looking for stolen meat.",
"My family said I should not build house because I'm woman, house will go to husband.",
"My husband said I should stop talking to my own mother because she disrespectful.",
"My mother in law said my child looks like my ex, my child is 2 months old and she never saw my ex.",
"My brother said I stole his destiny spiritually and I should go for deliverance.",
"My family sold my land I bought with my salary and said I'm still young I will buy another.",
"My husband said his sister will live with us forever and I should accept.",
"My mother in law said I should wash her clothes with my hands even though we have washing machine.",
"My father said I should not go for NYSC because I'm girl.",
"My husband's family collected my bride price back saying I'm disrespectful because I said no to cooking at midnight.",
"My mother in law said I bewitched her son because he now helps me in kitchen.",
"My sister said my boyfriend is hers because she saw him first 5 years ago.",
"My family said I should marry my cousin to keep property in family.",
"My mother in law said I should not lock my bedroom because what am I hiding.",
"My ex said I will never find love again after him. I married his best friend 1 year later.",
"My boss said I'm useless and fired me. 6 months later his company begged me to come back as consultant for double salary.",
"My girlfriend said I'm broke and left me. I started business she laughed at, now she wants me back.",
"My friend said I will never blow. My first video hit 1M views and she now comments first on every post.",
"My landlord said I will never own house in Lagos. I built house and he now my tenant.",
"My teacher said I will never pass. I passed and now teaching his children.",
"My ex said no man will marry me with child. My husband loves my child more than me.",
"My family said I will suffer because I refused to marry old man. I now pay their rent.",
"My boyfriend said I'm too fat to love. Lost weight but didn't take him back.",
"My boss said I can't do business and job together. My business now pays his salary 5 times.",
"My friend said I can't live without her. Blocked her 1 year and I'm happier.",
"My ex said I will beg him to come back. He now begging me with new account.",
"My mother in law said I will cry in this marriage. She crying now because son left her house for me.",
"My brother said I will never travel abroad. Sent him picture from Canada last week.",
"My sister said I will never find husband because I'm rude. Married before her.",
"My girlfriend said I'm boring. Her new boyfriend boring pass me and broke.",
"My landlord said I will run away owing rent. I left with extra month rent paid.",
"My friend said my YouTube will never grow. I now monetized before her.",
"My ex said I'm not beautiful. My husband tells me daily I'm most beautiful.",
"My boss said I will never be manager. I now manager in his competitor company with double pay."
]
today_str = str(date.today())
START_DATE = date(2026, 10, 31)
days_since_start = (date.today() - START_DATE).days
if days_since_start < 0: days_since_start = 0
story_index = days_since_start % len(STORIES)
story_raw_full = STORIES[story_index]
words = story_raw_full.split()
if len(words) <= 70:
    part1_text = story_raw_full + " To be continued at 5pm. Full story at 8pm!"
    part2_text = story_raw_full + " Full shocking ending at 8pm tonight!"
    full_text = story_raw_full
else:
    part1_text = " ".join(words[:70]) + "... To be continued at 5pm! Part 2 drops next. Full story at 8pm!"
    part2_text = " ".join(words[70:140]) + " ... Final full story at 8pm tonight! Don't miss it!"
    full_text = story_raw_full
if utc_hour == 11:
    story_raw = part1_text
    part_label = "Part 1"
elif utc_hour == 16:
    story_raw = part2_text
    part_label = "Part 2"
else:
    story_raw = full_text
    part_label = "Full Story"
print(f"DAY {days_since_start} / {len(STORIES)} - Story {story_index}: {part_label}")


# === NEW: ONE IMAGE LOGIC - BRIGHT + CATCHY + MATCHES STORY ===
def get_one_ai_prompt(story):
    s = story.lower()
    if "best friend" in s and "boyfriend" in s: 
        return "extremely beautiful young woman in car at night shocked betrayed face closeup tears, watching apartment, dramatic lighting, photorealistic skin texture, 8k"
    if "best friend" in s and "girlfriend" in s:
        return "handsome heartbroken man shocked in rain at night betrayal tears closeup photorealistic 8k dramatic"
    if "hotel" in s: 
        return "man standing in dark hotel hallway shocked face closeup noir cinematic photorealistic"
    if "second phone" in s or "phone" in s:
        return "woman holding two phones shocked discovery cheating bedroom night photorealistic closeup"
    if "mother in law" in s:
        return "beautiful young wife crying angry mother in law shouting living room drama photorealistic closeup"
    if "boss" in s:
        return "young man shocked angry boss shouting office cinematic photorealistic"
    if "sister" in s or "brother" in s:
        return "siblings fighting shouting house family drama closeup photorealistic"
    # default emotional
    return f"beautiful heartbroken person shocked betrayed face closeup tears emotional photorealistic, story about {story[:50]}"

def download_ai_background(W, H):
    prompt = get_one_ai_prompt(story_raw)
    full = f"{prompt}, portrait photo, sharp focus on eyes, center framed, instagram model, highly detailed face, 8k"
    safe = urllib.parse.quote(full)
    url = f"https://image.pollinations.ai/prompt/{safe}?width=768&height=1280&model=flux&nologo=true&enhance=true&seed={random.randint(1,999999)}"
    try:
        print(f"Generating ONE image matching story...")
        r = requests.get(url, timeout=120)
        if r.status_code == 200 and len(r.content) > 12000:
            open("bg.jpg","wb").write(r.content)
            # CREATE BRIGHT BLURRED BG - NO DARK
            im = Image.open("bg.jpg")
            blurred = im.filter(ImageFilter.GaussianBlur(15))
            blurred.save("bg_blur.jpg")
            print(f"✅ ONE image good - {len(r.content)} bytes")
            return "bg.jpg", "bg_blur.jpg"
    except Exception as e:
        print(f"AI fail {e}")
    r = requests.get(f"https://picsum.photos/768/1280?random={random.randint(1,5000)}", timeout=20)
    open("bg.jpg","wb").write(r.content)
    Image.open("bg.jpg").filter(ImageFilter.GaussianBlur(15)).save("bg_blur.jpg")
    return "bg.jpg", "bg_blur.jpg"
def viral_pack(story, is_short, part_label, full_story_for_title):
    s = full_story_for_title.lower()
    rand = random.randint(100,999)
    if "best friend" in s and ("boyfriend" in s or "girlfriend" in s):
        titles_p1 = ["I Followed My Boyfriend And My Heart Shattered", "My Boyfriend Said Gym But Parked At My Best Friend House"]
        titles_p2 = ["She Opened Door Wearing MY Lost Dress", "My Best Friend Was Wearing My Clothes For Him"]
        titles_full = ["My Boyfriend Cheated With My Best Friend And I Caught Them Red Handed", "My Best Friend Stole My Boyfriend - Full Story"]
    elif "hotel" in s:
        titles_p1 = ["My Wife Said Working Late But Hotel Camera Showed Different", "I Tracked Her To Room 204 And My Heart Stopped"]
        titles_p2 = ["I Knocked On That Hotel Room And A Man Opened", "Room 204 Had My Wife And Another Man Inside"]
        titles_full = ["My Wife Said Working Late But Was In Hotel With Another Man - Full Story", "I Caught My Wife Cheating In Hotel Room 204"]
    elif "second phone" in s or "phone" in s:
        titles_p1 = ["I Found Her Second Phone Hidden In Closet", "Her Hidden Phone Had 200 Messages From David"]
        titles_p2 = ["I Opened The Second Phone And Saw Hotel Pics", "200 Messages And She Still Said Its Nothing"]
        titles_full = ["My Girlfriend Hid Second Phone With 200 Cheating Messages - Full Story", "I Found My Girlfriends Secret Phone"]
    elif "mother in law" in s:
        titles_p1 = ["My Mother In Law Moved In Without Asking", "She Started Controlling What I Cook And Wear"]
        titles_p2 = ["She Told My Husband I Am Cheating With Fake Messages", "My Mother In Law Created Fake Instagram To Ruin Me"]
        titles_full = ["My Mother In Law Tried To Destroy My Marriage With Lies - Full Story", "My Toxic Mother In Law Created Fake Messages"]
    elif "boss" in s:
        titles_p1 = ["My Boss Promised Promotion If I Work Weekends", "I Worked Weekends For 3 Months For Promotion"]
        titles_p2 = ["He Gave My Promotion To His Nephew Who Just Joined", "My Boss Betrayed Me After 3 Months Of Free Work"]
        titles_full = ["My Boss Used Me For 3 Months Then Gave My Promotion Away - Full Story", "I Worked Weekends For Nothing - Boss Gave Promotion To Nephew"]
    else:
        first_10 = " ".join(full_story_for_title.split()[:10])
        titles_p1 = [f"{first_10} - I Could Not Believe It", f"I Caught Them And My Heart Broke"]
        titles_p2 = [f"{first_10} - The Truth Came Out", f"What Happened Next Broke Me Completely"]
        titles_full = [f"{full_story_for_title[:70]} - Full Story", f"My Partners Lie Destroyed Everything - Full Story"]
    if part_label == "Part 1":
        title = random.choice(titles_p1)
        desc = f"{story}\n\nPART 2 drops at 5PM WAT! Full shocking ending at 8PM WAT tonight! Subscribe so you don't miss it!\n\n#shorts #redditstories #cheating #storytime"
    elif part_label == "Part 2":
        title = random.choice(titles_p2)
        desc = f"{story}\n\nFULL STORY drops at 8PM WAT tonight! What would YOU do?\n\n#shorts #redditstories #cheating #storytime"
    else:
        title = random.choice(titles_full)
        desc = f"{story}\n\nThis is the FULL story from todays shorts. What would YOU do? Comment below!\n\nSubscribe for daily shocking true stories!\n\n#redditstories #cheating #storytime #drama #aitah #relationships"
    title = f"{title} | True Story {rand}"
    if is_short: title += " #shorts"
    tags = ["shorts","reddit stories","cheating","storytime","betrayal","drama","relationship","true story", f"story{rand}"]
    return title[:100], desc, tags

    else:
        titles = ["My Partner Cheated For Months Until I Did THIS - Full Story","My Best Friend Stole My Girlfriend And I Got Ultimate Revenge - Full Story","My Mother In Law Tried To Destroy My Marriage - Full Story"]
        desc = f"{story}\n\nThis is the FULL story from today's shorts. What would YOU do? Comment below!\n\nSubscribe for daily shocking true stories!\n\n#redditstories #cheating #storytime #drama #aitah #relationships"
    title = random.choice(titles)
    rand = random.randint(100,999)
    title = f"{title} | True Story {rand}"
    if is_short: title += " #shorts"
    tags = ["shorts","reddit stories","cheating","storytime","betrayal","drama","relationship","true story", f"story{rand}"]
    return title, desc, tags

title, desc, tags = viral_pack(story_raw, IS_SHORT, part_label, story_raw_full)

def download_music():
    s = story_raw.lower()
    sad_piano = ["https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3","https://cdn.pixabay.com/download/audio/2021/10/25/audio_8ef06f090a.mp3?filename=sad-piano-110694.mp3"]
    emotional_chill = ["https://cdn.pixabay.com/download/audio/2022/03/10/audio_c8c8a65019.mp3?filename=lofi-chill-113561.mp3","https://cdn.pixabay.com/download/audio/2022/06/07/audio_b9bd4170e8.mp3?filename=emotional-piano-112199.mp3"]
    tense_suspense = ["https://cdn.pixabay.com/download/audio/2022/01/18/audio_d1718ab41b.mp3?filename=suspense-ambient-110410.mp3","https://cdn.pixabay.com/download/audio/2021/11/25/audio_852d8aad6c.mp3?filename=dark-ambient-110998.mp3"]
    hopeful = ["https://cdn.pixabay.com/download/audio/2021/08/04/audio_0625c1539c.mp3?filename=little-break-110364.mp3"]
    if any(x in s for x in ["cheat","boyfriend","girlfriend","wife","husband","caught"]): pool = sad_piano
    elif any(x in s for x in ["best friend","friend","betray","stole"]): pool = emotional_chill
    elif any(x in s for x in ["mother in law","family","father","angry","fight"]): pool = tense_suspense
    else: pool = hopeful
    url = random.choice(pool)
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and len(r.content) > 10000:
            open("music.mp3","wb").write(r.content)
            return "music.mp3"
    except: pass
    return None

def detect_gender(story):
    s = story.lower()
    if "my wife" in s or "my girlfriend" in s or "my fiancee" in s: return "male"
    if "my husband" in s or "my boyfriend" in s: return "female"
    if "mother in law" in s and "my wife" not in s: return "female"
    he_count = s.count(" he ") + s.count(" him ")
    she_count = s.count(" she ") + s.count(" her ")
    if she_count > he_count: return "male"
    return "female"

async def make_voice_with_timing(text, file="voice.mp3"):
    gender = detect_gender(text)
    if gender == "male":
        voice_name = "en-US-GuyNeural"
        rate = "+5%"
        print(f"Using MALE voice - male is victim")
    else:
        voice_name = "en-US-AriaNeural"
        rate = "+8%"
        print(f"Using FEMALE voice - female is victim")
    if IS_SHORT:
        text = text + " ... Want full shocking ending? Full story drops tonight at 8pm West Africa Time. Subscribe!"
    else:
        text = text + " ... What would you do in my place? Comment below, I read every comment. Subscribe for daily shocking true stories."
    communicate = edge_tts.Communicate(text, voice_name, rate=rate)
    words = []
    with open(file, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary": words.append((chunk["offset"]/10000000, chunk["offset"]/10000000 + chunk["duration"]/10000000, chunk["text"]))
    print(f"Words detected: {len(words)}")
    return file, words

def make_caption_clip(text, W, H, duration, start):
    img = Image.new('RGBA', (W, 400), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58 if W==1080 else 46)
    except: font = ImageFont.load_default()
    lines = textwrap.wrap(text.upper(), width=18 if W==1080 else 32)
    y = 10
    for line in lines[:2]:
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        x = (W - tw)//2
        # THICK stroke for viral look
        for dx in range(-4,5):
            for dy in range(-4,5):
                if dx!=0 or dy!=0: draw.text((x+dx, y+dy), line, font=font, fill=(0,0,0,255))
        draw.text((x, y), line, font=font, fill=(255,255,255,255))
        y += th + 12
    path = f"cap_{int(start*1000)}_{random.randint(0,99999)}.png"
    img.save(path)
    clip = ImageClip(path, duration=duration).set_start(start).set_position(("center", H*0.62))
    # POP effect
    clip = clip.resize(lambda t: 0.7 + 0.3*min(t*6,1) if t < 0.15 else 1)
    return clip

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

def make_thumbnail_for_long(bg_image_path, story_text):
    W, H = 1280, 720
    try:
        bg = Image.open(bg_image_path).convert("RGB")
        bg = bg.resize((W, H), Image.LANCZOS)
        dark = Image.new("RGBA", (W,H), (0,0,0,100))
        bg = Image.alpha_composite(bg.convert("RGBA"), dark).convert("RGB")
    except:
        bg = Image.new("RGB", (W,H), (20,20,20))
    draw = ImageDraw.Draw(bg)
    s = story_text.lower()
    if "best friend" in s: top_text = "MY BEST FRIEND?!"; bottom_text = "SHE STOLE HIM!"
    elif "wife" in s or "husband" in s: top_text = "CAUGHT CHEATING!"; bottom_text = "IN A HOTEL!"
    elif "mother in law" in s: top_text = "MY MOTHER-IN-LAW"; bottom_text = "DESTROYED ME!"
    elif "boss" in s: top_text = "MY BOSS BETRAYED ME!"; bottom_text = "THEN THIS HAPPENED!"
    else: top_text = "SHE LIED TO ME!"; bottom_text = "I CAUGHT HER!"
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        font_big = ImageFont.load_default(); font_small = font_big
    for y_text, txt, fnt, col in [(40, top_text, font_big, (255,255,0)), (H-150, bottom_text, font_small, (255,255,255))]:
        bbox = draw.textbbox((0,0), txt, font=fnt)
        tw = bbox[2]-bbox[0]
        x = (W - tw)//2
        for dx in range(-6,7):
            for dy in range(-6,7):
                draw.text((x+dx, y_text+dy), txt, font=fnt, fill=(0,0,0))
        draw.text((x, y_text), txt, font=fnt, fill=col)
    border = 12
    draw.rectangle([(0,0),(W-1, border-1)], fill=(255,0,0))
    draw.rectangle([(0,H-border),(W-1,H-1)], fill=(255,0,0))
    draw.rectangle([(0,0),(border-1,H-1)], fill=(255,0,0))
    draw.rectangle([(W-border,0),(W-1,H-1)], fill=(255,0,0))
    bg.save("thumb.jpg", quality=95)
    return "thumb.jpg"

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

    # === ONE IMAGE ONLY - NEVER DISAPPEARS, BRIGHT ===
    sharp_path, blur_path = download_ai_background(W, H)
    
    bg_blur = ImageClip(blur_path, duration=duration)
    if bg_blur.w / bg_blur.h < W / H: bg_blur = bg_blur.resize(width=W)
    else: bg_blur = bg_blur.resize(height=H)
    bg_blur = bg_blur.crop(x1=bg_blur.w//2 - W//2, y1=bg_blur.h//2 - H//2, width=W, height=H).fx(vfx.colorx, 0.9)

    fg = ImageClip(sharp_path, duration=duration)
    if IS_SHORT:
        fg = fg.resize(height=1350)
        if fg.w > 950: fg = fg.resize(width=950)
        fg = fg.set_position(("center", "center")).fx(vfx.colorx, 1.1)
    else:
        fg = fg.resize(height=H*0.85)
        if fg.w > W*0.6: fg = fg.resize(width=W*0.6)
        fg = fg.set_position(("center", "center")).fx(vfx.colorx, 1.1)

    bg_clip = CompositeVideoClip([bg_blur, fg], size=(W,H)).set_duration(duration)

    # === GUARANTEED CAPTIONS - ALWAYS SHOW ===
    caps = []
    if word_data and len(word_data) > 3:
        i = 0
        while i < len(word_data):
            start_time = word_data[i][0]
            phrase_words = []
            for k in range(4):
                if i + k >= len(word_data): break
                phrase_words.append(word_data[i + k][2])
            if not phrase_words: break
            text = " ".join(phrase_words)
            i += len(phrase_words)
            if i < len(word_data):
                next_start = word_data[i][0]
                dur = next_start - start_time
            else:
                dur = (word_data[-1][1] - start_time) + 0.3
            dur = max(0.5, min(dur, 1.5))
            if start_time < duration:
                caps.append(make_caption_clip(text, W, H, dur, start_time))
    else:
        # FALLBACK - will still show captions even if edge_tts timing fails
        print("Fallback captions")
        words = story_raw.split()
        chunk_duration = duration / max(1, len(words)//4 + 1)
        for idx in range(0, len(words), 4):
            text = " ".join(words[idx:idx+4])
            caps.append(make_caption_clip(text, W, H, chunk_duration, idx//4*chunk_duration))

    print(f"Creating {len(caps)} captions")
    end_card = make_end_card(W, H, duration)
    final = CompositeVideoClip([bg_clip]+caps+[end_card], size=(W,H)).set_duration(duration).set_audio(final_audio)
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
    return "final.mp4", sharp_path

video_file, bg_used = make_video()
creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token", scopes=["https://www.googleapis.com/auth/youtube.upload"])
youtube = build("youtube", "v3", credentials=creds)
body = {"snippet": {"title": title[:100], "description": desc, "tags": tags, "categoryId": "22"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
video = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_file)).execute()
vid_id = video["id"]
print(f"UPLOADED {today_str} {'SHORT' if IS_SHORT else 'LONG'}: {vid_id} | {title}")

if not IS_SHORT:
    try:
        thumb_file = make_thumbnail_for_long(bg_used, story_raw)
        youtube.thumbnails().set(videoId=vid_id, media_body=MediaFileUpload(thumb_file, mimetype="image/jpeg")).execute()
        print(f"Viral thumbnail with image uploaded!")
    except Exception as e:
        print(f"Thumbnail failed: {e}")
