import os, json, random, textwrap, datetime, asyncio, requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

VOICE = "hi-IN-MadhurNeural" # Hard loud male
FACE_IMAGE = "my_face.jpg" # Aapka face jo aapne diya hai

FACTS = [
    ("Samudra Ke Andar Behti Nadi", "Atlantic Ocean ke neeche ek aisi nadi hai jo samudra ke andar behti hai. Scientists kehte hain ye 35 KM lambi hai aur aaj tak iske andar koi nahi ja paya. Kya ye dusri duniya ka rasta hai?", "deep ocean underwater river, dark sea"),
    ("Bermuda Triangle Ka Kala Sach", "Bermuda Triangle me 75 ships achanak gayab ho gayi. Last message me pilot ne kaha aasman hara ho gaya hai. NASA kehta hai yaha methane gas blast hota hai. Sach kya hai aaj tak raaz hai.", "bermuda triangle ship storm mystery"),
    ("Insaan Sote Hue Jagta Hai", "Sote waqt aapka dimaag 20% zyada active hota hai. Wo din bhar ki yaadon ko save karta hai. Isiliye aap sapne me aisi jagah dekhte ho jaha aap kabhi gaye hi nahi.", "human brain neurons dream sleep"),
]

def get_type():
    h = datetime.datetime.utcnow().hour
    return "LONG" if h in [0,9,15] else "SHORT"

def download_image(keyword, name):
    url = f"https://source.unsplash.com/1280x720/?{keyword.replace(' ', ',')}"
    r = requests.get(url, timeout=15)
    open(name, 'wb').write(r.content)
    return name

def make_circle_face(face_path, size=280):
    # Aapke face ko gol cut karke corner me lagane ke liye
    im = Image.open(face_path).convert("RGB")
    # Auto face crop (center)
    im = ImageOps.fit(im, (size, size), centering=(0.5, 0.3))
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    # Yellow border - viral look
    border = Image.new('RGB', (size+12, size+12), "#FFD60A")
    bd_mask = Image.new('L', (size+12, size+12), 0)
    ImageDraw.Draw(bd_mask).ellipse((0,0,size+12,size+12), fill=255)
    border.putalpha(bd_mask)
    im.putalpha(mask)
    return im, border

async def make_voice(text):
    ssml = f"<speak><voice name='{VOICE}'><prosody pitch='-14%' rate='-10%' volume='+35%'>{text}<break time='500ms'/></prosody></voice></speak>"
    comm = edge_tts.Communicate(ssml, VOICE)
    await comm.save("raw.mp3")
    # HARD, LOUD, CLEAR - Studio filter
    os.system('ffmpeg -y -i raw.mp3 -af "loudnorm=I=-11:TP=-0.5:LRA=6, bass=g=12:f=100, aecho=0.8:0.88:40:0.3" -ar 48000 -b:a 192k voice.mp3')

def make_video_with_face_and_graphics(title, script, images, duration, face_path):
    # 1. Background slideshow
    with open("list.txt","w") as f:
        for img in images:
            f.write(f"file '{img}'\nduration {duration//len(images)}\n")
        f.write(f"file '{images[-1]}'\n")
    os.system(f'ffmpeg -y -f concat -safe 0 -i list.txt -i voice.mp3 -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p temp.mp4')

    # 2. Ab ispar aapka face + text graphics lagao (jaise us Short me hai)
    face, border = make_circle_face(face_path, 260 if duration>60 else 200)

    # Text overlay image banao
    base = Image.new('RGBA', (1280,720), (0,0,0,0))
    draw = ImageDraw.Draw(base)
    try:
        fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except:
        fnt = ImageFont.load_default()
        f_small = fnt

    # Bottom text bar - jaise us video me explanation aata hai
    draw.rectangle([0, 520, 1280, 720], fill=(0,0,0,200))
    lines = textwrap.wrap(script[:120], width=50)
    y=540
    for l in lines[:2]:
        draw.text((30, y), l, font=fnt, fill="white", stroke_width=2, stroke_fill="black")
        y+=45
    draw.text((30, 650), "FactVerse India 🔥", font=f_small, fill="#FFD60A")

    base.save("overlay.png")
    face.save("face_circle.png")
    border.save("border.png")

    # Final composite: video + text overlay + aapka face corner me
    # Face position: bottom-right, jaise aapne kaha
    os.system(f'ffmpeg -y -i temp.mp4 -i overlay.png -i face_circle.png -i border.png -filter_complex "[0:v][1:v]overlay=0:0[bg];[bg][3:v]overlay=980:20[bg2];[bg2][2:v]overlay=986:26" -c:a copy -c:v libx264 final.mp4')
    return "final.mp4"

def make_clickbait_thumbnail(title, bg_image, face_path, out="thumb.jpg"):
    bg = Image.open(bg_image).convert("RGB").resize((1280,720))
    bg = bg.filter(ImageFilter.GaussianBlur(0.5))
    draw = ImageDraw.Draw(bg, 'RGBA')
    draw.rectangle([0,0,1280,720], fill=(0,0,0,100))
    draw.rectangle([10,10,1270,710], outline="#FFD60A", width=7)

    # Aapka face left me bada
    face_big, _ = make_circle_face(face_path, 320)
    bg.paste(face_big, (40, 180), face_big)

    try:
        f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
        f_mid = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except:
        f_big = ImageFont.load_default()
        f_mid = f_big

    clean = title.replace("|","")[:50]
    lines = textwrap.wrap(clean, width=16)
    y=100
    for line in lines[:3]:
        for dx,dy in [(-3,-3),(3,-3),(-3,3),(3,3)]:
            draw.text((400+dx, y+dy), line, font=f_big, fill="black")
        draw.text((400, y), line, font=f_big, fill="#FFD60A")
        y+=90

    draw.ellipse([1050,30,1230,210], fill="red")
    draw.text((1110,70), "?", font=f_big, fill="white")
    draw.text((400, 600), "👁️ PURA SACH DEKHO", font=f_mid, fill="white")
    bg.save(out, quality=95)
    return out

def upload(title, desc, file, is_short):
    creds = Credentials.from_authorized_user_info(json.loads(os.environ['YOUTUBE_CREDENTIALS']))
    yt = build('youtube','v3', credentials=creds)
    body = {"snippet": {"title": title[:95], "description": desc, "tags": ["facts","viral","mystery"], "categoryId": "27"}, "status": {"privacyStatus": "public"}}
    media = MediaFileUpload(file, mimetype='video/mp4', resumable=True)
    yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()

async def main():
    # Aapka face image ko github me my_face.jpg naam se save karna hai
    if not os.path.exists(FACE_IMAGE):
        # Agar aapne abhi tak face upload nahi kiya to unsplash se kaam chalega
        download_image("indian man face", FACE_IMAGE)

    vtype = get_type()
    t, s, kw = random.choice(FACTS)
    if vtype == "LONG":
        title = f"{t} | 99% Log Nahi Jante 😱"
        script = f"{t}. {s} {s} NASA ki files me iska zikr hai. Aapko kya lagta hai? Comment karo. FactVerse India ko Subscribe karo."
        duration = random.randint(200, 450)
    else:
        title = f"{t} #Shorts"
        script = f"{s} Aise hi facts ke liye Subscribe karo."
        duration = 28

    # Real images
    imgs = [download_image(kw, f"p{i}.jpg") for i in range(3) for kw in [kw]][:3]
    # Actually 3 images
    imgs = []
    for i in range(3):
        imgs.append(download_image(kw + f" {i}", f"p{i}.jpg"))

    await make_voice(script)
    make_clickbait_thumbnail(title, imgs[0], FACE_IMAGE, "thumb.jpg")
    make_video_with_face_and_graphics(title, script, imgs, duration, FACE_IMAGE)

    desc = f"{script}\n\n#FactVerse #Viral #Facts"
    upload(title, desc, "final.mp4", vtype=="SHORT")

if __name__ == "__main__":
    asyncio.run(main())
