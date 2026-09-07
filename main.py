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

facts_short = ["Madhumakkhi kabhi soti nahi!", "Octopus ke 3 dil hote hain!", "Paani garam hone par jaldi jamta hai!", "Insan ka dimag 20 watt bijli se chalta hai!", "Cheenti kabhi nahi thakti!"]
facts_long = ["Samudra ke rahasya: 80% samundar abhi tak explore nahi hua hai, waha aise jeev hain jo aliens jaise lagte hain!", "Bermuda Triangle ka sach: Waha koi bhoot nahi hai, waha ka mausam bahut kharab rehta hai isliye jahaj gayab hote hain!", "Neend ka science: Aap sote hue bhi apne aas paas ki awaze sunte hain, isiliye alarm se jaag jate hain!"]

fact = random.choice(facts_short if VIDEO_TYPE=="short" else facts_long)
title = (fact[:85] + " #Shorts") if VIDEO_TYPE=="short" else fact[:90]

gTTS(fact, lang='hi').save('voice.mp3')
W,H = (1080,1920) if VIDEO_TYPE=="short" else (1920,1080)
img = Image.new('RGB', (W,H), (15,15,50))
draw = ImageDraw.Draw(img)
wrapped = "\n".join(textwrap.wrap(fact, width=30 if
