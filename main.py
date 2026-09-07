import os, random, json, textwrap, asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_viral_fact():
    facts = [
        {"fact": "Aap sote hue bhi awaze sunte hain, isiliye alarm se neend khulti hai!", "en": "You can hear sounds even while sleeping, that's why alarm wakes you up!"},
        {"fact": "Samudra me 80 percent jeev abhi bhi khoje nahi gaye hain!", "en": "80 percent of ocean life is still undiscovered!"},
        {"fact": "Aapka dimaag 20 watt bijli banata hai!", "en": "Your brain generates 20 watts of power!"},
    ]
    return random.choice(facts)

# === HEAVY MALE VOICE GENERATOR ===
async def make_heavy_voice(text, filename="voice.mp3"):
    # HEAVY MALE VOICES - Best for Fact Channel:
    # Hindi Heavy: hi-IN-MadhurNeural (Deep Male Hindi)
    # English Heavy: en-US-GuyNeural or en-US-ChristopherNeural
    
    voice = "hi-IN-MadhurNeural"  # Heavy Hindi Male - Change to "en-US-GuyNeural" for English heavy
    # Make it deeper and slower
    communicate = edge_tts.Communicate(text, voice=voice, rate="-10%", pitch="-25Hz")
    await communicate.save(filename)
    print(f"Heavy voice created: {filename}")
    return filename

def create_video_with_voice(fact_text):
    W, H = 1080, 1920
    img = Image.new('RGB', (W, H), (5, 5, 25)) # Dark blue background
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 65)
    except:
        font = ImageFont.load_default()

    wrapped = textwrap.wrap(fact_text, width=20)
    y = 700
    for line in wrapped:
        draw.text((60, y), line, font=font, fill=(255, 255, 0), stroke_width=6, stroke_fill=(0,0,0))
        y += 110
    draw.text((60, y+150), "FactVerse India", font=font, fill=(255,255,255))
    img.save("frame.jpg")
    
    # Create 8 sec video from frame
    os.system("ffmpeg -y -loop 1 -i frame.jpg -t 8 -vf \"scale=1080:1920\" -c:v libx264 -pix_fmt yuv420p -r 30 temp_video.mp4")
    
    # Merge heavy voice + video
    os.system("ffmpeg -y -i temp_video.mp4 -i voice.mp3 -c:v copy -map 0:v:0 -map 1:a:0 -shortest final_video.mp4")
    return "final_video.mp4"

def main():
    fact = get_viral_fact()
    full_text = f"{fact['fact']}. Follow FactVerse India for more amazing facts!"
    title = f"{fact['fact'][:60]} #shorts"
    desc = f"{fact['fact']}\n\n{fact['en']}\n\n#factverse #shorts #viral #facts #hindifacts"
    
    print(f"Making heavy voice for: {full_text}")
    
    # 1. Make Heavy Voice
    asyncio.run(make_heavy_voice(full_text))
    
    # 2. Make Video with that voice
    video_file = create_video_with_voice(fact['fact'])
    
    # 3. Upload
    creds = Credentials.from_authorized_user_info(json.loads(os.environ.get('YOUTUBE_CREDENTIALS')))
    youtube = build('youtube', 'v3', credentials=creds)
    
    req = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": desc, "tags": ["factverse","shorts","hindifacts"], "categoryId": "27"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
        },
        media_body=MediaFileUpload(video_file, resumable=True)
    )
    res = req.execute()
    print(f"UPLOADED HEAVY VOICE VIDEO: https://youtu.be/{res['id']}")

if __name__ == "__main__":
    main()
