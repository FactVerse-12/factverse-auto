import os, json, random, textwrap, datetime
from gtts import gTTS
from moviepy.editor import *
if not hasattr(Image, 'ANTIALIAS'): Image.ANTIALIAS = Image.LANCZOS
from PIL import Image, ImageDraw
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

hour = datetime.datetime.now().hour
VIDEO_TYPE = "short" if hour in [0, 14] else "long"

facts_short = ["Madhumakkhi kabhi soti nahi!", "Octopus ke 3 dil hote hain!", "Honey 3000 saal tak kharab nahi hota!"]
facts_long = ["Samudra ke rahasya: 80% samundar abhi bhi anjaana hai!"]

fact = random.choice(facts_short if VIDEO_TYPE=="short" else facts_long)
title = (fact[:85] + " #Shorts") if VIDEO_TYPE=="short" else fact[:90]

gTTS(fact, lang='hi').save('voice.mp3')
W,H = (1080,1920) if VIDEO_TYPE=="short" else (1920,1080)
img = Image.new('RGB', (W,H), (15,15,50))
ImageDraw.Draw(img).text((80,700) if VIDEO_TYPE=="short" else (100,500), textwrap.fill(fact, width=28), fill="white", stroke_width=3, stroke_fill="black")
img.save('frame.jpg')

try:
    if os.path.exists("host.jpg"):
        host = Image.open("host.jpg").convert("RGBA")
        w,h = host.size
        s = min(w,h)
        host = host.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2)).resize((400,400))
        mask = Image.new('L', (400,400), 0)
        ImageDraw.Draw(mask).ellipse((0,0,400,400), fill=255)
        circle = Image.new("RGBA", (400,400), (0,0,0,0))
        circle.paste(host, (0,0), mask)
        border = Image.new("RGBA", (440,440), (0,0,0,0))
        ImageDraw.Draw(border).ellipse((0,0,440,440), fill="white")
        border.paste(circle, (20,20), circle)
        border.save("host_circle.png")
except Exception as e:
    print(e)

audio = AudioFileClip('voice.mp3')
base_clip = ImageClip('frame.jpg').set_duration(audio.duration + 0.5)
clips = [base_clip]
if os.path.exists("host_circle.png"):
    host_clip = ImageClip('host_circle.png', duration=audio.duration + 0.5).resize(0.6 if VIDEO_TYPE=="short" else 0.35).set_position((W-320, H-400) if VIDEO_TYPE=="short" else (W-380, H-320))
    host_clip = host_clip.resize(lambda t: 1 + 0.04 * (t % 1))
    clips.append(host_clip)

final = CompositeVideoClip(clips).set_audio(audio)
final.write_videofile('final.mp4', fps=24, codec='libx264', audio_codec='aac')

creds = Credentials.from_authorized_user_info(json.loads(os.environ['YOUTUBE_TOKEN_JSON']))
youtube = build('youtube','v3', credentials=creds)
res = youtube.videos().insert(part="snippet,status", body={"snippet":{"title":title, "description":fact+" #FactVerse", "tags":["facts"]}, "status":{"privacyStatus":"public", "selfDeclaredMadeForKids":False}}, media_body=MediaFileUpload('final.mp4', chunksize=-1, resumable=True)).execute()
print("UPLOADED:", res['id'])
