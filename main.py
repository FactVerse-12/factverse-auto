import os, random, json, textwrap
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === VIRAL DATABASE ===
def get_viral_fact():
    facts = [
        {"fact": "Octopuses have 3 hearts and blue blood!", "hook": "This animal will SHOCK you!"},
        {"fact": "Bananas are berries but strawberries are not!", "hook": "You've been LIED to!"},
        {"fact": "NASA found a planet made of diamonds!", "hook": "NASA Hid This For Years!"},
        {"fact": "Your phone has more bacteria than toilet seat!", "hook": "Stop touching your phone!"},
        {"fact": "Sharks existed before trees!", "hook": "This is IMPOSSIBLE!"},
        {"fact": "Honey never expires, 3000 year old honey is still edible!", "hook": "Scientists are SHOCKED!"},
        {"fact": "Your brain generates 20 watts of power!", "hook": "Your brain is POWERFUL!"},
    ]
    return random.choice(facts)

def make_viral_title(f):
    t = [
        f"{f['hook']} 😱 #shorts",
        f"Wait Till You Hear This! {f['fact']} 🤯",
        f"Nobody Knows This! {f['fact']} #viral",
        f"This Will Blow Your Mind! 🤯",
        f"Google Hid This! {f['fact']}"
    ]
    return random.choice(t)[:95]

def create_video_from_fact(fact_text, filename="video.mp4"):
    # Creates a 9:16 video with text - no moviepy needed, uses PIL + image sequence
    # For GitHub Actions, we will create a simple MP4 using Pillow frames
    from PIL import Image
    import subprocess
    
    # Create 5 second video with text
    W, H = 1080, 1920
    img = Image.new('RGB', (W, H), (10,10,10))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 70)
        small = ImageFont.truetype("DejaVuSans-Bold.ttf", 50)
    except:
        font = ImageFont.load_default()
        small = ImageFont.load_default()

    wrapped = textwrap.wrap(fact_text, width=22)
    y = 600
    for line in wrapped:
        draw.text((80, y), line, font=font, fill=(255,255,0), stroke_width=5, stroke_fill=(0,0,0))
        y += 100
    draw.text((80, y+100), "Follow FactVerse! 👇", font=small, fill=(255,255,255))

    # Save as jpg then convert to mp4 using ffmpeg (available in Actions)
    img.save("frame.jpg")
    # 6 second video loop
    os.system("ffmpeg -y -loop 1 -i frame.jpg -t 6 -vf \"scale=1080:1920\" -c:v libx264 -pix_fmt yuv420p -r 30 video.mp4")
    return filename

# === MAIN ===
def main():
    fact_data = get_viral_fact()
    title = make_viral_title(fact_data)
    desc = f"""{fact_data['fact']}

{fact_data['hook']}

Follow for daily facts! 👇

#factverse #shorts #viral #amazingfacts #facts #trending #didyouknow #india #sciencefacts #viralshorts
"""
    print(f"TITLE: {title}")
    
    # 1. Create video
    create_video_from_fact(fact_data['fact'])
    
    # 2. Upload to YouTube
    creds_json = os.environ.get('YOUTUBE_CREDENTIALS')
    if not creds_json:
        print("ERROR: YOUTUBE_CREDENTIALS secret missing!")
        return
    creds = Credentials.from_authorized_user_info(json.loads(creds_json))
    youtube = build('youtube', 'v3', credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": desc, "tags": ["factverse","shorts","viral","facts"], "categoryId": "27"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
        },
        media_body=MediaFileUpload("video.mp4", chunksize=-1, resumable=True)
    )
    res = request.execute()
    print(f"SUCCESS: https://youtu.be/{res['id']}")

if __name__ == "__main__":
    main()
