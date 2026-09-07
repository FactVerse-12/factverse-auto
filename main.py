import os, json, random, textwrap, datetime, asyncio, requests, re
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageOps
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

VOICE = "hi-IN-MadhurNeural"
FACE_FILE = "my_face.jpg"

# World Facts - Simple Hindi words for perfect pronunciation
FACTS = [
    ("Chand Par Kachra", "Kya aap jante hain, Chand par abhi bhi chhyanve bag kachra pada hai. Apollo mission ke astronauts wahan apna kachra chhod aaye the.", (10,15,40)),
    ("Samudra Ke Andar Nadi", "Samudra ke andar ek nadi behti hai. Atlantic Ocean me is nadi ki lambai paintis kilometer hai. Iska pani samudra se das guna jyada namkeen hai.", (0,50,80)),
    ("Ped Bhi Baat Karte Hain", "Vaigyanikon ne khoja hai ki ped ek dusre se baat karte hain. Zameen ke niche unki jaden internet ki tarah judi hui hain.", (10,60,20)),
    ("Pani Me Bijli Ka Raaz", "Agar aap antariksh me roye to aapke aansu neeche nahi girenge. Wahan gurutvakarshan nahi hai isliye aansu aankh me hi chipke rahenge.", (20,20,50)),
    ("Bermuda Triangle", "Bermuda Triangle me pichle sau saalon me pachattar jahaz gayab ho gaye. Pilot ne aakhri sandesh me kaha tha ki aasman hara dikh raha hai.", (20,20,20)),
    ("Dharti Ka Dil", "Dharti ke andar ek lohe ki gend hai jo Chand ke barabar badi hai. Uska temperature suraj jitna garam hai.", (80,20,10)),
    ("Honey Kabhi Kharab Nahi Hota", "Shahad kabhi kharab nahi hota. Vaigyanikon ko teen hazar saal purana shahad mila jo abhi bhi khane layak tha.", (60,40,10)),
    ("Octopus Ke Teen Dil", "Octopus ke teen dil hote hain. Aur uska khoon neele rang ka hota hai. Kya aap ye jante the?", (0,40,60)),
]

def get_clean_script(title, desc):
    # Hinglish ko saaf Hindi me badlo taaki voice atke nahi
    full = f"{title}. {desc} Kya aapko ye baat pata thi? Aise hi amazing facts ke liye FactVerse India ko subscribe karo."
    # Numbers ko shabdo me
    full = full.replace("96", "chhyanve").replace("75", "pachattar").replace("35", "paintis").replace("100", "sau")
    return full

def safe_image(keyword, name, fallback_color):
    try:
        url = f"https://picsum.photos/seed/{random.randint(1,999999)}/1280/720"
        r = requests.get(url, timeout=20)
        open(name, 'wb').write(r.content)
        Image.open(name).verify()
        return name
    except:
        img = Image.new('RGB', (1280,720), fallback_color)
        d = ImageDraw.Draw(img)
        try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        except: f = ImageFont.load_default()
        d.text((200,300), keyword[:15].upper(), font=f, fill="white")
        img.save(name)
        return name

async def make_voice(text):
    # Best Indian Accent Settings
    ssml = f"<speak><voice name='{VOICE}'><prosody pitch='-5%' rate='-10%' volume='+20%'>{text}</prosody></voice></speak>"
    comm = edge_tts.Communicate(ssml, VOICE)
    await comm.save("raw.mp3")
    os.system('ffmpeg -y -i raw.mp3 -af "loudnorm=I=-12:TP=-1.5, equalizer=f=200:t=h:width=100:g=3" -ar 48000 -b:a 192k voice.mp3')

def prepare_face():
    if not os.path.exists(FACE_FILE): return None
    try:
        face = Image.open(FACE_FILE).convert("RGB")
        face = ImageOps.fit(face, (280,280), centering=(0.5,0.3))
        mask = Image.new('L', (280,280), 0)
        ImageDraw.Draw(mask).ellipse((0,0,280,280), fill=255)
        # Yellow border for face
        border = Image.new('RGB', (300,300), "#FFD60A")
        bm = Image.new('L', (300,300), 0)
        ImageDraw.Draw(bm).ellipse((0,0,300,300), fill=255)
        border.putalpha(bm)
        final = Image.new('RGBA', (300,300), (0,0,0,0))
        final.paste(border, (0,0), border)
        face_rgba = Image.new('RGBA', (280,280))
        face_rgba.paste(face, mask=mask)
        final.paste(face_rgba, (10,10), face_rgba)
        final.save("face_circle.png")
        return "face_circle.png"
    except: return None

def make_thumb(title, bg_img):
    bg = Image.open(bg_img).convert("RGB").resize((1280,720))
    draw = ImageDraw.Draw(bg, 'RGBA')
    draw.rectangle([0,380,1280,720], fill=(0,0,0,200))
    draw.rectangle([8,8,1272,712], outline="#FFD60A", width=8)
    if os.path.exists("face_circle.png"):
        try:
            face = Image.open("face_circle.png").convert("RGBA").resize((320,320))
            bg.paste(face, (20, 20), face)
        except: pass
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
    except: font = ImageFont.load_default()
    lines = textwrap.wrap(title[:65], width=22)
    y=400
    for l in lines[:3]:
        draw.text((32, y+3), l, font=font, fill="black")
        draw.text((30, y), l, font=font, fill="#FFD60A")
        y+=70
    bg.save("thumb.jpg")
    return "thumb.jpg"

def make_video_with_face(imgs, duration, face_path):
    # 1. Make slideshow with zoom effect + captions + face
    # Create list file
    with open("list.txt","w") as f:
        per_img = duration / len(imgs)
        for im in imgs:
            f.write(f"file '{im}'\nduration {per_img}\n")
        f.write(f"file '{imgs[-1]}'\n")

    # Base video from images with zoompan (Ken Burns)
    os.system(f'ffmpeg -y -f concat -safe 0 -i list.txt -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,zoompan=d=1:s=1280x720:fps=30" -c:v libx264 -pix_fmt yuv420p -t {duration} temp_base.mp4')

    if face_path and os.path.exists(face_path):
        # Overlay your face bottom-right + add yellow border text background
        os.system(f'ffmpeg -y -i temp_base.mp4 -i {face_path} -i voice.mp3 -filter_complex "[0:v][1:v]overlay=W-w-20:H-h-20:format=auto,drawbox=x=0:y=ih-180:w=iw:h=180:color=black@0.6:t=fill" -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p final.mp4')
    else:
        os.system(f'ffmpeg -y -i temp_base.mp4 -i voice.mp3 -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p final.mp4')
    return "final.mp4"

def upload_yt(title, desc, file, thumb):
    creds = Credentials.from_authorized_user_info(json.loads(os.environ['YOUTUBE_CREDENTIALS']))
    yt = build('youtube','v3', credentials=creds)
    is_short = "Shorts" in title or len(open("voice.mp3","rb").read()) < 60*1024*15 # rough
    body = {"snippet": {"title": title[:95], "description": desc + "\n\n#FactVerse #Facts #Viral #India", "tags": ["facts","viral","factverse"], "categoryId": "27"}, "status": {"privacyStatus": "public"}}
    media = MediaFileUpload(file, mimetype='video/mp4', resumable=True)
    vid = yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    if os.path.exists(thumb):
        try: yt.thumbnails().set(videoId=vid['id'], media_body=MediaFileUpload(thumb, mimetype='image/jpeg')).execute()
        except: pass

async def main():
    t, s, color = random.choice(FACTS)
    title = f"{t} | 99% Log Nahi Jante 😱 #Shorts"
    clean_script = get_clean_script(t, s)
    dur = 32 # Shorts ke liye perfect

    # 8 Images for high engagement
    imgs = [safe_image(t, f"p{i}.jpg", color) for i in range(8)]
    face = prepare_face()
    await make_voice(clean_script)
    make_thumb(title, imgs[0])
    make_video_with_face(imgs, dur, face)
    upload_yt(title, clean_script, "final.mp4", "thumb.jpg")

if __name__ == "__main__":
    asyncio.run(main())
