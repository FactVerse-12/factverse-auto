import os, random, json, textwrap, asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_viral_fact():
    facts = [
        {"fact": "Aap sote hue bhi awaze sunte hain, isiliye alarm se aapki neend khulti hai", "title": "Neend ka science 😱"},
        {"fact": "Samudra ke 80 percent jeev aaj tak khoje hi nahi gaye", "title": "Samudra ka rahasya 🤯"},
        {"fact": "Aapka dimaag 20 watt bijli banata hai, ek bulb jala sakta hai", "title": "Dimaag ki power 🔥"},
        {"fact": "Ek din Venus par, ek saal se bhi bada hota hai", "title": "Venus ka jadu 🪐"},
        {"fact": "Shark pedo se bhi pehle se dharti par hain", "title": "Shark ka sach 😨"},
    ]
    return random.choice(facts)

# === HINDI HEAVY MALE VOICE ===
async def make_hindi_heavy(text):
    # hi-IN-MadhurNeural = Deep Hindi Male (Best)
    voice = "hi-IN-MadhurNeural"
    # -15% slow + -30Hz deep = Extra Heavy
    comm = edge_tts.Communicate(text, voice=voice, rate="-15%", pitch="-30Hz")
    await comm.save("voice.mp3")
    print("Heavy Hindi voice ready!")

def create_final_video(fact_text):
    W, H = 1080, 1920
    img = Image.new('RGB', (W, H), (8, 10, 40))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 70)
    except:
        font = ImageFont.load_default()

    wrapped = textwrap.wrap(fact_text, width=18)
    y = 650
    for line in wrapped:
        draw.text((50, y), line, font=font, fill=(255,221,0), stroke_width=7, stroke_fill=(0,0,0))
        y += 120
    draw.text((50, y+100), "FactVerse India", font=font, fill=(255,255,255))
    img.save("frame.jpg")

    os.system("ffmpeg -y -loop 1 -i frame.jpg -t 10 -vf scale=1080:1920 -c:v libx264 -pix_fmt yuv420p -r 30 temp.mp4")
    os.system("ffmpeg -y -i temp.mp4 -i voice.mp3 -c:v copy -map 0:v:0 -map 1:a:0 -shortest final.mp4")
    return "final.mp4"

def main():
    fact = get_viral_fact()
    voice_text = f"{fact['fact']}. Aise hi amazing facts ke liye, FactVerse India ko subscribe karo!"
    title = f"{fact['title']} - {fact['fact'][:30]} #shorts"
    desc = f"{fact['fact']}\n\nFollow FactVerse India 👇\n\n#factverseindia #hindifacts #shorts #viral #facts"

    print(f"VOICE TEXT: {voice_text}")
    
    asyncio.run(make_hindi_heavy(voice_text))
    video = create_final_video(fact['fact'])

    creds = Credentials.from_authorized_user_info(json.loads(os.environ.get('YOUTUBE_CREDENTIALS')))
    yt = build('youtube', 'v3', credentials=creds)

    req = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title[:95], "description": desc, "tags": ["hindifacts","factverse","shorts"], "categoryId": 27},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
        },
        media_body=MediaFileUpload(video, resumable=True)
    )
    res = req.execute()
    print(f"UPLOADED: https://youtu.be/{res['id']}")

if __name__ == "__main__":
    main()
