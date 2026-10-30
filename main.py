import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# AUTO SWITCH - 2 Shorts + 1 Long
utc_hour = datetime.utcnow().hour
IS_SHORT = False if utc_hour == 0 else True
print(f"UTC Hour: {utc_hour} - Making {'LONG' if not IS_SHORT else 'SHORT'} video")

# --- YOUR STORY AND VIDEO LOGIC STAYS HERE ---
# Make sure you keep your story_raw variable
# Example:
story_raw = "Your story logic here... replace this with your actual story generation code"
# If your file already has story generation, keep that part and only replace below

def upload_youtube(video_path):
    client_id = os.environ['YT_CLIENT_ID']
    client_secret = os.environ['YT_CLIENT_SECRET']
    refresh_token = os.environ['YT_REFRESH_TOKEN']
    
    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    
    youtube = build('youtube', 'v3', credentials=creds)
    
    title = story_raw[:95] if len(story_raw) > 20 else "He Didn't Go To The Gym... #reddit #story"
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
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

# --- YOUR VIDEO CREATION CODE ---
# Keep your moviepy / video creation code here
# At the end, it should call: upload_youtube("final_video.mp4")
