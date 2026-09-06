import os, json, random, textwrap, datetime
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

hour = datetime.datetime.now().hour
VIDEO_TYPE = "short" if hour in [0, 14] else "long"

facts_short = ["Madhumakkhi kabhi soti nahi hai!", "Insaan ke dimag me 86 billion neurons hote hain!", "Samudra ka 80% hissa abhi bhi unexplored hai!", "Octopus ke 3 dil hote hain!", "Honey kabhi kharab nahi hota!"]
facts_long = ["Samudra ke rahasya: 80% samudra abhi bhi anjara hai. Wahan aise jeev hain jo roshni paida karte hain. Oxygen ka 70% samudra se aata hai.", "Octopus ke 3 dil aur 9 dimag hote hain. Uska khoon neela hota hai aur woh itna smart hai ki jar khol sakta hai."]

fact = random.choice(facts_short if VIDEO_TYPE=="short" else facts_long)
title = (fact[:85] + " #Shorts") if VIDEO_TYPE=="short" else (fact[:50] + " | Amazing Fact")

gTTS(fact, lang='hi').save('voice.mp3')
W,H = (1080,1920) if VIDEO_TYPE=="short" else (1920,1080)
img = Image.new('RGB', (W,H), (15,15,50))
ImageDraw.Draw(img).text((80,700) if VIDEO_TYPE=="short" else (100,400), textwrap.fill(fact, width=22 if VIDEO_TYPE=="short" else 45), fill=(255,255,0), spacing=15)
img.save('frame.jpg')

audio = AudioFileClip('voice.mp3')
ImageClip('frame.jpg').set_duration(audio.duration+0.5).set_audio(audio).write_videofile('video.mp4', fps=24, logger=None)

creds = Credentials.from_authorized_user_info(json.loads(os.environ['TOKEN_JSON']))
youtube = build('youtube','v3', credentials=creds)
res = youtube.videos().insert(part="snippet,status", body={"snippet":{"title":title,"description":fact+"\n#FactVerseIndia #Shorts"},"status":{"privacyStatus":"public"}}, media_body=MediaFileUpload('video.mp4', mimetype='video/mp4', resumable=True)).execute()
print(f"UPLOADED: https://youtube.com/watch?v={res['id']}")
