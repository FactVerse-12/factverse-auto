import os, json, random, textwrap, datetime, asyncio, requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageOps
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

VOICE = "hi-IN-MadhurNeural"
FACE_FILE = "my_face.jpg"

FACTS_LONG = [
    ("Samudra Ke Andar Behti Nadi Ka Raaz", "Atlantic Ocean ke neeche scientists ne ek aisi nadi khoji hai jo samudra ke andar behti hai. Iska paani samudra se 10 guna zyada namkeen hai. Iski lambai 35 kilometer hai.", (5,40,80)),
    ("Bermuda Triangle Me 75 Ships Gayab", "Pichle 100 saalon me Bermuda Triangle me 75 ships aur 20 planes achanak gayab ho gaye. Pilot ne aakhri message me kaha aasman hara dikh raha hai.", (20,20,20)),
]
FACTS_SHORT = [
    ("Chand Par 96 Bags Kachra", "Apollo ke astronauts chand par 96 bags kachra chhod aaye the jo aaj bhi wahi pada hai.", (30,30,60)),
]

def get_type():
    h = datetime.datetime.utcnow().hour
    return "LONG" if h in [0,9,15] else "SHORT"

def safe_image(keyword, name, fallback_color):
    try:
        url = f"https://picsum.photos/1280/720?random={random.randint(1,10000)}"
        r = requests.get(url, timeout=20)
        open(name, 'wb').write(r.content)
        # Validate
        Image.open(name).verify()
        return name
    except:
        # Agar download fail to apna khud ka HD background banao
        img = Image.new('RGB', (1280,720), fallback_color)
        d = ImageDraw.Draw(img)
        try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except: f = ImageFont.load_default()
        d.text((100,300), keyword.upper(), font=f, fill="white")
        img.save(name)
        return name

async def make_voice(text):
    ssml = f"<speak><voice name='{VOICE}'><prosody pitch='-12%' rate='-8%' volume='+30%'>{text}</prosody></voice></speak>"
    comm = edge_tts.Communicate(ssml, VOICE)
    await comm.save("raw.mp3")
    os.system('ffmpeg -y -i raw.mp3 -af "loudnorm=I=-11:TP=-1, bass=g=10" -ar 48000 -b:a 192k voice.mp3')

def make_thumb(title, bg_img):
    bg = Image.open(bg_img).convert("RGB").resize((1280,720))
    draw = ImageDraw.Draw(bg, 'RGBA')
    draw.rectangle([0,400,1280,720], fill=(0,0,0,180))
    draw.rectangle([10,10,1270,710], outline="#FFD60A", width=6)
    if os.path.exists(FACE_FILE):
        try:
            face = Image.open(FACE_FILE).convert("RGB")
            face = ImageOps.fit(face, (300,300), centering=(0.5,0.3))
            mask = Image.new('L', (300,300), 0)
            ImageDraw.Draw(mask).ellipse((0,0,300,300), fill=255)
            face.putalpha(mask)
            bg.paste(face, (30, 30), face)
        except: pass
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except: font = ImageFont.load_default()
    lines = textwrap.wrap(title[:60], width=20)
    y=420
    for l in lines[:3]:
        draw.text((30+2, y+2), l, font=font, fill="black")
        draw.text((30, y), l, font=font, fill="#FFD60A")
        y+=70
    bg.save("thumb.jpg")
    return "thumb.jpg"

def make_video(imgs, duration):
    with open("list.txt","w") as f:
        for im in imgs:
            f.write(f"file '{im}'\nduration {duration//len(imgs)}\n")
        f.write(f"file '{imgs[-1]}'\n")
    os.system(f'ffmpeg -y -f concat -safe 0 -i list.txt -i voice.mp3 -vf "scale=1280:720" -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p final.mp4')
    return "final.mp4"

def upload_yt(title, desc, file):
    creds = Credentials.from_authorized_user_info(json.loads(os.environ['YOUTUBE_CREDENTIALS']))
    yt = build('youtube','v3', credentials=creds)
    body = {"snippet": {"title": title[:95], "description": desc, "tags": ["facts","viral"], "categoryId": "27"}, "status": {"privacyStatus": "public"}}
    media = MediaFileUpload(file, mimetype='video/mp4', resumable=True)
    yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()

async def main():
    vtype = get_type()
    t, s, color = random.choice(FACTS_LONG if vtype=="LONG" else FACTS_SHORT)
    title = f"{t} | 99% Log Nahi Jante 😱" if vtype=="LONG" else f"{t} #Shorts"
    script = f"{t}. {s} Aise hi facts ke liye FactVerse India ko subscribe karo."
    dur = random.randint(200,400) if vtype=="LONG" else 28

    imgs = [safe_image(t, f"p{i}.jpg", color) for i in range(3)]

    await make_voice(script)
    make_thumb(title, imgs[0])
    make_video(imgs, dur)
    upload_yt(title, script + "\n#FactVerse #Facts", "final.mp4")

if __name__ == "__main__":
    asyncio.run(main())
