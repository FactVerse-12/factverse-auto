import os, json, random, asyncio, requests, subprocess, datetime
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageOps
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 100% HUMAN CONFIDENT MALE VOICE
VOICE = "en-IN-PrabhatNeural"
FACE_FILE = "my_face.jpg"

FACTS_DB = [
    ("Chand par kachra", "Chand par abhi bhi 96 bory kachra pada hai, jo astronauts wahan chhod aaye the"),
    ("Samudra ke andar nadi", "Samudra ke andar 35 kilometer lambi ek nadi behti hai, jiska paani das guna zyada namkeen hai"),
    ("Ped baat karte hain", "Ped ek dusre se baat karte hain, zameen ke niche unki jadein internet ki tarah judi hui hain"),
    ("Shahad kharab nahi hota", "3000 saal purana shahad bhi khane layak hota hai, ye kabhi kharab nahi hota"),
    ("Octopus ke teen dil", "Octopus ke teen dil hote hain aur uska khoon neele rang ka hota hai"),
    ("Dharti ka dil", "Dharti ke andar lohe ki ek gend hai jo Suraj jitni garam hai"),
    ("Antariksh me aansu", "Space me rone par aansu neeche nahi girte, aankh me hi chipke rehte hain"),
    ("Bermuda Triangle", "Bermuda Triangle me 75 jahaz gayab ho gaye hain, pilot ne aakhri baar hara aasman dekha tha"),
]

HOOKS = [
    "Kya aapko pata hai?",
    "Sun kar aap chauk jaoge!",
    "99 percent log ye baat nahi jante!",
    "Ye sabse shocking fact hai!",
    "Dekho ye kamaal ki baat!",
]

def get_duration():
    try:
        out = subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1','voice.mp3']).decode().strip()
        return float(out)
    except: return 38.0

def safe_image(i):
    name = f"p{i}.jpg"
    try:
        r = requests.get(f"https://picsum.photos/seed/{random.randint(1,99999999)}/1280/720", timeout=15)
        open(name,'wb').write(r.content)
        Image.open(name).verify()
        return name
    except:
        Image.new('RGB',(1280,720),(random.randint(10,60),random.randint(10,60),random.randint(50,100))).save(name)
        return name

async def make_human_voice(full_text):
    # Human-like SSML - breaks, confident, joyful
    ssml_text = full_text.replace(". ", '. <break time="400ms"/> ')
    ssml = f"""<speak><voice name='{VOICE}'><prosody rate="-5%" pitch="+2%" volume="+10%">{ssml_text}</prosody></voice></speak>"""
    await edge_tts.Communicate(ssml, VOICE).save("voice.mp3")
    # Bass + loudness for confident sound
    os.system('ffmpeg -y -i voice.mp3 -af "loudnorm=I=-11:TP=-1.5, bass=g=4:f=150" -ar 48000 -b:a 192k v2.mp3 && mv v2.mp3 voice.mp3')

def prepare_assets():
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
    # Subscribe
    sub = Image.new('RGBA',(650,160),(255,0,0,255))
    d = ImageDraw.Draw(sub)
    try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
    except: f = ImageFont.load_default()
    d.text((25,45), "SUBSCRIBE KARO! 🔔", font=f, fill="white")
    sub.save("sub.png")
    return face_path

def make_final_video(imgs, face_path):
    dur = get_duration()
    per = dur / len(imgs)
    with open("list.txt","w") as f:
        for im in imgs:
            f.write(f"file '{im}'\nduration {per}\n")
        f.write(f"file '{imgs[-1]}'\n")
    os.system(f'ffmpeg -y -f concat -safe 0 -i list.txt -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720" -r 30 -pix_fmt yuv420p base.mp4')
    # Face full time + Subscribe middle & end
    if face_path:
        filt = f"[0:v][1:v]overlay=W-w-20:H-h-20:format=auto[face];[face][2:v]overlay=(W-w)/2:(H-h)/2:enable='between(t,14,17)'[m1];[m1][2:v]overlay=(W-w)/2:(H-h)/2:enable='gte(t,{dur-3})'"
        os.system(f'ffmpeg -y -i base.mp4 -i {face_path} -i sub.png -i voice.mp3 -filter_complex "{filt}" -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p final.mp4')
    else:
        os.system(f'ffmpeg -y -i base.mp4 -i voice.mp3 -c:v libx264 -c:a aac -shortest final.mp4')

def upload(title, desc):
    creds = Credentials.from_authorized_user_info(json.loads(os.environ['YOUTUBE_CREDENTIALS']))
    yt = build('youtube','v3', credentials=creds)
    body = {"snippet": {"title": title[:95], "description": desc + "\n\n#FactVerse #HindiFacts #Viral", "tags": ["facts","hindi","viral"], "categoryId": "27"}, "status": {"privacyStatus": "public"}}
    vid = yt.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload("final.mp4", mimetype='video/mp4', resumable=True)).execute()
    print("UPLOADED:", vid['id'])

async def main():
    is_long = datetime.datetime.utcnow().hour in [0,9,15]
    num = 8 if is_long else 5
    selected = random.sample(FACTS_DB, num)

    script_lines = ["Namaste dosto, FactVerse India me aapka swagat hai!"]
    for (t,d) in selected:
        hook = random.choice(HOOKS)
        script_lines.append(f"{hook} {t}. {d}.")
    script_lines.append("Aise hi joyful aur amazing facts ke liye, abhi subscribe karo aur bell dabao!")

    full_script = " ".join(script_lines)

    title = f"5 Facts Jo 99% Log Nahi Jante 😱 #Shorts" if not is_long else f"8 Shocking Facts Jo Aapko Chauka Denge!"

    imgs = [safe_image(i) for i in range(num*2)]
    # Thumb
    th = Image.open(imgs[0]).resize((1280,720))
    d = ImageDraw.Draw(th)
    d.rectangle([0,450,1280,720], fill=(0,0,0,190))
    th.save("thumb.jpg")

    face = prepare_assets()
    await make_human_voice(full_script)
    make_final_video(imgs, face)
    upload(title, full_script)

if __name__ == "__main__":
    asyncio.run(main())
