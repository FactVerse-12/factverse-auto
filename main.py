import os, json, random, textwrap, datetime
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw
if not hasattr(Image, 'ANTIALIAS'): Image.ANTIALIAS = Image.LANCZOS
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

hour = datetime.datetime.now().hour
VIDEO_TYPE = "short" if hour in [0, 14] else "long"
facts_short = ["Madhumakkhi kabhi soti nahi!", "Octopus ke 3 dil hote hain!", "Paani garam hone par jaldi jamta hai!", "Insan ka dimag 20 watt bijli se chalta hai!"]
facts_long = ["Samudra ke rahasya: 80% samundar abhi tak explore nahi hua hai, waha aliens jaise jeev hain!", "Bermuda Triangle ka sach: Waha bhoot nahi, kharab mausam ki wajah se jahaj gayab hote hain!", "Neend ka science: Aap sote hue bhi awaze sunte hain, isiliye alarm se jaagte hain!"]
fact = random.choice(facts_short if VIDEO_TYPE=="short" else facts_long)
title = (fact[:85] + " #Shorts") if VIDEO_TYPE=="short" else fact[:90]
gTTS(fact, lang='hi').save('voice.mp3')
W,H = (1080,1920) if VIDEO_TYPE=="short" else (1920,1080)
img = Image.new('RGB', (W,H), (15,15,50))
draw = ImageDraw.Draw(img)
wrapped = "\n".join(textwrap.wrap(fact, width=30 if VIDEO_TYPE=="short" else 50))
draw.text((80,700) if VIDEO_TYPE=="short" else (100,400), wrapped, fill=(255,255,255))
if os.path.exists('host.jpg'):
    try:
        host = Image.open('host.jpg').resize((300,300))
        img.paste(host, (W-400, H-400))
    except: pass
img.save('frame.jpg')
audio = AudioFileClip('voice.mp3')
video = ImageClip('frame.jpg').set_duration(audio.duration).set_audio(audio)
video.write_videofile('final.mp4', fps=24, codec='libx264', audio_codec='aac')
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/youtube.upload'])
    youtube = build('youtube', 'v3', credentials=creds)
    req = youtube.videos().insert(part="snippet,status", body={"snippet": {"title": title, "description": fact+" #FactVerse", "tags": ["facts"], "categoryId": "27"}, "status": {"privacyStatus": "public"}}, media_body=MediaFileUpload('final.mp4'))
    req.execute()
