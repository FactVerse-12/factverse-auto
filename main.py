import os, json, random, textwrap, datetime, asyncio, requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

VOICE = "hi-IN-MadhurNeural"

# Topic ke saath usse related image keyword bhi
FACTS_LONG = [
    ("Samudra Ke Andar Behti Nadi Ka Raaz", "Atlantic Ocean ke neeche scientists ne ek aisi nadi khoji hai jo samudra ke andar behti hai. Iska paani samudra se 10 guna zyada namkeen hai. Iski lambai 35 kilometer hai. Aaj tak koi submarine iske andar nahi ja payi.", "deep ocean river underwater, dark sea mystery"),
    ("Bermuda Triangle Me 75 Ships Gayab", "Pichle 100 saalon me Bermuda Triangle me 75 ships aur 20 planes achanak gayab ho gaye. Pilot ne aakhri message me kaha tha aasman hara dikh raha hai. Uske baad signal hamesha ke liye khatam.", "bermuda triangle storm ship, mysterious ocean"),
    ("Insaan Sote Hue Bhi Jagta Hai", "Jab aap sote ho tab aapka dimaag 20 percent zyada tez kaam karta hai. Wo aapki yaadon ko delete aur save karta hai. Isiliye sapne me aap aisi jagah dekhte ho jaha aap kabhi gaye hi nahi.", "human brain neurons sleep dream"),
]

FACTS_SHORT = [
    ("Chand Par 96 Bags Kachra", "Apollo ke astronauts chand par 96 bags kachra chhod aaye the jo aaj bhi wahi pada hai.", "moon surface apollo"),
    ("Octopus Ke 3 Dil Hote Hain", "Octopus ke 3 dil aur 9 dimaag hote hain. Tairte waqt uska ek dil band ho jata hai.", "octopus underwater deep sea"),
    ("Samudra Ka 80% Hissa Andekha", "Humne chand ko poora dekh liya lekin apne samudra ka 80 percent hissa aaj tak nahi dekha.", "deep ocean unexplored dark"),
]

def get_type():
    h = datetime.datetime.utcnow().hour
    return "LONG" if h in [0,9,15] else "SHORT"

def download_real_image(keyword, filename):
    # Real HD image Unsplash se - 100% free, no API key needed
    try:
        url = f"https://source.unsplash.com/1280x720/?{keyword.replace(' ', ',')}"
        r = requests.get(url, timeout=20)
        with open(filename, 'wb') as f:
            f.write(r.content)
        return filename
    except:
        return None

async def make_human_voice(text, out="voice.mp3"):
    ssml = f"<speak><voice name='{VOICE}'><prosody pitch='-12%' rate='-8%' volume='+30%'>{text}<break time='400ms'/></prosody></voice></speak>"
    comm = edge_tts.Communicate(ssml, VOICE)
    await comm.save("raw.mp3")
    # HARD + LOUD + CLEAR + BASS
    os.system('ffmpeg -y -i raw.mp3 -af "loudnorm=I=-12:TP=-1:LRA=8, bass=g=10:f=120, treble=g=2:f=4000" -ar 48000 -b:a 192k voice.mp3')
    return "voice.mp3"

def make_viral_thumbnail_with_picture(title, image_file, out="thumb.jpg"):
    # Real picture ke upar viral design
    base = Image.open(image_file).convert("RGB").resize((1280,720))
    base = base.filter(ImageFilter.GaussianBlur(1))
    # Dark gradient for text readability
    overlay = Image.new('RGBA', (1280,720), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([0, 400, 1280, 720], fill=(0,0,0,180))
    draw.rectangle([15,15,1265,705], outline=(255,215,0), width=6)

    combined = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(combined)

    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    clean = title.replace("|","").replace("#Shorts","")[:70]
    lines = textwrap.wrap(clean, width=22)
    y=420
    for line in lines[:3]:
        for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2)]:
            draw.text((40+dx, y+dy), line, font=font_big, fill="black")
        draw.text((40, y), line, font=font_big, fill="#FFD60A")
        y+=85

    draw.ellipse([1050, 30, 1240, 220], fill="#FF0000")
    draw.text((1120, 75), "?", font=font_big, fill="white")
    draw.text((40, 640), "FactVerse India • DEKHO PURA SACH", font=font_small, fill="white")

    combined.save(out, quality=95)
    return out

def make_visual_video(image_files, duration, out="final.mp4"):
    # 3-4 real pictures ka slideshow video - Visualization
    # Har picture ko utna time do
    per_img = duration // len(image_files)

    # Image list file for ffmpeg
    with open("list.txt","w") as f:
        for img in image_files:
            f.write(f"file '{img}'\nduration {per_img}\n")
        f.write(f"file '{image_files[-1]}'\n") # last image

    # Slideshow + Voice + Zoom effect
    os.system(f'ffmpeg -y -f concat -safe 0 -i list.txt -i voice.mp3 -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2, zoompan=d=1:s=1280x720:fps=30" -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p {out}')
    return out

def upload(title, desc, file, is_short):
    creds = Credentials.from_authorized_user_info(json.loads(os.environ['YOUTUBE_CREDENTIALS']))
    yt = build('youtube','v3', credentials=creds)
    body = {"snippet": {"title": title[:95], "description": desc, "tags": ["facts","mystery","viral"], "categoryId": "27"}, "status": {"privacyStatus": "public"}}
    media = MediaFileUpload(file, mimetype='video/mp4', resumable=True)
    yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    print(f"UPLOADED {title}")

async def main():
    vtype = get_type()
    if vtype == "LONG":
        t, s, keyword = random.choice(FACTS_LONG)
        title = f"{t} | 99% Log Nahi Jante 😱"
        script = f"{t}. {s} {s} NASA ki secret files me iska zikr hai. Scientists aaj tak iska jawab nahi de paye. Aapko kya lagta hai comment me likho. Aise hi mysteries ke liye FactVerse India ko Subscribe karo."
        duration = random.randint(200, 460)
    else:
        t, s, keyword = random.choice(FACTS_SHORT)
        title = f"{t} #Shorts"
        script = f"{s} Aise hi facts ke liye FactVerse India ko Subscribe karo."
        duration = 30
        keyword = keyword

    # 1. Real Pictures Download Karo
    img1 = download_real_image(keyword, "pic1.jpg")
    img2 = download_real_image(keyword+" mystery", "pic2.jpg")
    img3 = download_real_image(keyword+" dark", "pic3.jpg")
    images = [x for x in [img1, img2, img3] if x]

    # 2. Human Hard Voice
    await make_human_voice(script)
    # 3. Thumbnail Real Picture Se
    make_viral_thumbnail_with_picture(title, images[0], "thumb.jpg")
    # 4. Video Visualization
    make_visual_video(images, duration, "final.mp4")

    desc = f"{script}\n\n#facts #mystery #viral #factverse\n{title}"
    upload(title, desc, "final.mp4", vtype=="SHORT")

if __name__ == "__main__":
    asyncio.run(main())
