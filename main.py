import os, json, random, asyncio, requests, subprocess, datetime
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageOps
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

VOICE = "en-IN-PrabhatNeural"
FACE_FILE = "my_face.jpg"

FACTS_DB = [
    ("Chand par kachra", "Chand par abhi bhi chhyanve bory kachra pada hai, jo astronauts wahan chhod aaye the"),
    ("Samudra ke andar nadi", "Samudra ke andar paintis kilometer lambi ek nadi behti hai"),
    ("Ped baat karte hain", "Ped ek dusre se baat karte hain, zameen ke niche unki jadein judi hui hain"),
    ("Shahad kharab nahi hota", "Teen hazar saal purana shahad bhi khane layak hota hai"),
    ("Octopus ke teen dil", "Octopus ke teen dil hote hain aur khoon neele rang ka hota hai"),
    ("Dharti ka garam dil", "Dharti ke andar lohe ki gend hai jo Suraj jitni garam hai"),
    ("Space me aansu", "Space me rone par aansu neeche nahi girte"),
    ("Barmuda Triangle", "Barmuda Triangle me pachattar jahaz gayab ho gaye hain"),
]

HOOKS = [
    "Kya aapko pata hai",
    "Sun kar aap chauk jaoge",
    "99 percent log ye nahi jante",
    "Ye sabse shocking baat hai",
    "Ye kamaal ki baat dekho",
]

def get_duration():
    try:
        out = subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1','voice.mp3']).decode().strip()
        return float(out)
    except:
        return 38.0

def safe_image(i):
    name = f"p{i}.jpg"
    try:
        r = requests.get(f"https://picsum.photos/seed/{random.randint(1,9999999)}/1280/720", timeout=15)
        open(name,'wb').write(r.content)
        Image.open(name).verify()
        return name
    except:
        Image.new('RGB',(1280,720),(30,30,80)).save(name)
        return name

async def make_human_voice(full_text):
    clean_text = full_text.replace(". ", "... ")
    comm = edge_tts.Communicate(clean_text, VOICE, rate="-5%", pitch="+2Hz", volume="+15%")
    await comm.save("voice.mp3")
    os.system('ffmpeg -y -i voice.mp3 -af loudnorm=I=-11:TP=-1.5 -ar 48000 -b:a 192k v2.mp3 && mv v2.mp3 voice.mp3')

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
    sub = Image.new('RGBA',(650,160),(255,0,0,255))
    d = ImageDraw.Draw(sub)
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
    except:
        f = ImageFont.load_default()
    d.text((25,45), "SUBSCRIBE KARO!", font=f, fill="white")
    sub.save("sub.png")
    return face_path

def make_final_video(imgs, face_path):
    dur = get_duration()
    per = dur / len(imgs)
    with open("list.txt","w") as f:
        for im in imgs:
            f.write(f"file '{im}'\nduration {per}\n")
        f.write(f"file '{imgs[-1]}'\n")
    os.system('ffmpeg -y -f concat -safe 0 -i list.txt -vf scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720 -r 30 -pix_fmt yuv420p base.mp4')
    if face_path:
        filt = f"[0:v][1:v]overlay=W-w-20:H-h-20:format=auto[face];[face][2:v]overlay=(W-w)/2:(H-h)/2:enable='between(t,14,17)'[m1];[m1][2:v]overlay=(W-w)/2:(H-h)/2:enable='gte(t,{dur-3})'"
        os.system(f'ffmpeg -y -i base.mp4 -i {face_path} -i sub.png -i voice.mp3 -filter_complex "{filt}" -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p final.mp4')
    else:
        os.system('ffmpeg -y -i base.mp4 -i voice.mp3 -c:v libx264 -c:a aac -shortest final.mp4')

def upload_video(title, desc):
    creds = Credentials.from_authorized_user_info(json.loads(os.environ['YOUTUBE_CREDENTIALS']))
    yt = build('youtube','v3', credentials=creds)
    body = {
        "snippet": {
            "title": title,
            "description": desc,
            "tags": ["facts", "hindi facts", "viral"],
            "categoryId": "27"
        },
        "status": {"privacyStatus": "public"}
    }
    media = MediaFileUpload("final.mp4", mimetype='video/mp4', resumable=True)
    vid = yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    print("UPLOADED:", vid['id'])

async def main():
    selected = random.sample(FACTS_DB, 5)
    script_lines = ["Namaste dosto, FactVerse India me aapka swagat hai"]
    for t,d in selected:
        hook = random.choice(HOOKS)
        script_lines.append(f"{hook}, {t}, {d}")
    script_lines.append("Aise hi amazing facts ke liye abhi subscribe karo")
    full_script = "... ".join(script_lines)
    title = "5 Facts Jo 99 Percent Log Nahi Jante"
    imgs = [safe_image(i) for i in range(10)]
    face = prepare_assets()
    await make_human_voice(full_script)
    make_final_video(imgs, face)
    upload_video(title, full_script)

if __name__ == "__main__":
    asyncio.run(main())
