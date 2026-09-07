import os, json, random, asyncio, requests, subprocess
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageOps
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

VOICE = "hi-IN-MadhurNeural"
FACE_FILE = "my_face.jpg"

FACTS_DB = [
    ("Chand par kachra", "Chand par chhyanve bory kachra pada hai jo astronauts chhod aaye the"),
    ("Samudra ke andar nadi", "Samudra ke andar paintis kilometer lambi nadi behti hai"),
    ("Ped baat karte hain", "Ped zameen ke niche internet ki tarah baat karte hain"),
    ("Shahad kharab nahi hota", "Teen hazar saal purana shahad bhi khane layak hota hai"),
    ("Octopus ke teen dil", "Octopus ke teen dil aur neele rang ka khoon hota hai"),
    ("Dharti ka dil garam hai", "Dharti ke andar lohe ki gend hai jo suraj jitni garam hai"),
    ("Pani me aansu nahi girte", "Antariksh me rone par aansu aankh me hi chipke rehte hain"),
    ("Bermuda Triangle", "Wahan pachattar jahaz gayab ho gaye, aasman hara dikha tha"),
    ("Honey Bees soti nahi", "Madhumakhi kabhi nahi soti, poori zindagi kaam karti hai"),
    ("Insan ka dimaag", "Aapka dimaag ek second me ek hazar faisle leta hai"),
]

def get_audio_duration():
    try:
        out = subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1','voice.mp3']).decode().strip()
        return float(out)
    except: return 35.0

def safe_image(idx):
    name = f"p{idx}.jpg"
    try:
        r = requests.get(f"https://picsum.photos/seed/{random.randint(1,99999999)}/1280/720", timeout=15)
        open(name,'wb').write(r.content)
        Image.open(name).verify()
        return name
    except:
        Image.new('RGB',(1280,720),(random.randint(0,80),random.randint(0,80),random.randint(0,80))).save(name)
        return name

async def make_voice(text):
    # Slow, clear Indian accent
    text = text.replace("96","chhyanve").replace("75","pachattar").replace("35","paintis")
    ssml = f"<speak><voice name='{VOICE}'><prosody rate='-18%' pitch='-5%'>{text}</prosody></voice></speak>"
    await edge_tts.Communicate(ssml, VOICE).save("voice.mp3")
    os.system('ffmpeg -y -i voice.mp3 -af "loudnorm=I=-14:TP=-1" -ar 48000 -b:a 192k voice_final.mp3 && mv voice_final.mp3 voice.mp3')

def prepare_face_and_subscribe():
    face_path = None
    if os.path.exists(FACE_FILE):
        face = Image.open(FACE_FILE).convert("RGB")
        face = ImageOps.fit(face, (300,300), centering=(0.5,0.3))
        mask = Image.new('L', (300,300), 0)
        ImageDraw.Draw(mask).ellipse((0,0,300,300), fill=255)
        out = Image.new('RGBA',(320,320),(0,0,0,0))
        ImageDraw.Draw(out).ellipse((0,0,320,320), fill="#FFD60A")
        out.paste(face, (10,10), mask)
        out.save("face.png")
        face_path = "face.png"

    # Subscribe image banao
    sub = Image.new('RGBA',(600,150),(255,0,0,255))
    d = ImageDraw.Draw(sub)
    try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
    except: f = ImageFont.load_default()
    d.text((30,35), "SUBSCRIBE KARO! 🔔", font=f, fill="white")
    sub.save("sub.png")
    return face_path

def make_video(imgs, face_path):
    dur = get_audio_duration()
    per_img = dur / len(imgs)

    with open("list.txt","w") as f:
        for im in imgs:
            f.write(f"file '{im}'\nduration {per_img}\n")
        f.write(f"file '{imgs[-1]}'\n")

    # Base slideshow - FIXED (1 sec bug khatam)
    os.system(f'ffmpeg -y -f concat -safe 0 -i list.txt -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720" -r 30 -pix_fmt yuv420p base.mp4')

    # Face + Subscribe overlay + Voice
    if face_path:
        # Face poori video me, Subscribe beech me 3 sec aur end me 3 sec
        filter_c = f"[0:v][1:v]overlay=W-w-20:H-h-20:format=auto[face];[face][2:v]overlay=(W-w)/2:(H-h)/2:enable='between(t,15,18)'[mid];[mid][2:v]overlay=(W-w)/2:(H-h)/2:enable='gte(t,{dur-3})'"
        os.system(f'ffmpeg -y -i base.mp4 -i {face_path} -i sub.png -i voice.mp3 -filter_complex "{filter_c}" -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p final.mp4')
    else:
        os.system(f'ffmpeg -y -i base.mp4 -i voice.mp3 -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p final.mp4')
    return "final.mp4"

def upload_yt(title, desc):
    creds = Credentials.from_authorized_user_info(json.loads(os.environ['YOUTUBE_CREDENTIALS']))
    yt = build('youtube','v3', credentials=creds)
    body = {"snippet": {"title": title[:95], "description": desc, "tags": ["facts","viral","hindi facts"], "categoryId": "27"}, "status": {"privacyStatus": "public"}}
    media = MediaFileUpload("final.mp4", mimetype='video/mp4', resumable=True)
    vid = yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    print("Uploaded:", vid['id'])

async def main():
    # SHORT = 5 facts, LONG = 8 facts
    import datetime
    h = datetime.datetime.utcnow().hour
    is_long = h in [0,9,15] # Raat/subah long video
    num_facts = 8 if is_long else 5

    selected = random.sample(FACTS_DB, num_facts)

    script_parts = []
    for i,(t,d) in enumerate(selected,1):
        script_parts.append(f"Fact number {i}, {t}. {d}.")

    full_script = "Dekho bachcho aur bado, aaj ke sabse zabardast facts. " + " ".join(script_parts) + " Aise hi duniya ke facts ke liye FactVerse India ko subscribe karo. Bell icon dabana mat bhoolna."

    title = f"5 Facts Jo Aap Nahi Jante 😱 | Part {random.randint(1,100)} #Shorts" if not is_long else f"Duniya Ke 8 Sabse Hairan Karne Wale Facts | Aap Chauk Jaoge"

    # 10 images for 5 facts (2 per fact)
    imgs = [safe_image(i) for i in range(num_facts*2)]

    # Thumb
    thumb = Image.open(imgs[0]).convert("RGB").resize((1280,720))
    d = ImageDraw.Draw(thumb)
    d.rectangle([0,400,1280,720], fill=(0,0,0,180))
    d.rectangle([10,10,1270,710], outline="#FFD60A", width=8)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except: font = ImageFont.load_default()
    d.text((30,500), title[:50], font=font, fill="#FFD60A")
    thumb.save("thumb.jpg")

    face = prepare_face_and_subscribe()
    await make_voice(full_script)
    make_video(imgs, face)
    upload_yt(title, full_script + "\n\n#FactVerse #Facts #Viral")

if __name__ == "__main__":
    asyncio.run(main())
