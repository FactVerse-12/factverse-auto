import os, random, json
from PIL import Image, ImageDraw, ImageFont
import googleapiclient.discovery
import googleapiclient.errors

# === 1. VIRAL TITLE GENERATOR ===
def get_viral_fact():
    viral_facts = [
        {"fact": "Octopuses have 3 hearts and blue blood!", "hook": "This animal will SHOCK you!"},
        {"fact": "Bananas are berries but strawberries are not!", "hook": "You've been lied to!"},
        {"fact": "NASA found a planet made of diamonds!", "hook": "NASA Hid This For Years!"},
        {"fact": "Your brain generates 20 watts of power!", "hook": "Your brain is POWERFUL!"},
        # AI will pick random
    ]
    return random.choice(viral_facts)

def make_viral_title(fact):
    templates = [
        f"{fact['hook']} 😱 #shorts",
        f"Wait Till You Hear This! {fact['fact']} 🤯",
        f"Nobody Knows This Fact! {fact['fact']} #viral",
        f"This Will Blow Your Mind! 🤯 {fact['fact']}",
        f"Google Hid This! {fact['fact']} #facts"
    ]
    return random.choice(templates)

# === 2. VIRAL THUMBNAIL MAKER ===
def create_thumbnail(text, filename="thumbnail.jpg"):
    img = Image.new('RGB', (1080, 1920), color=(0,0,0))
    draw = ImageDraw.Draw(img)
    # Big Bold Text
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 90)
    except:
        font = ImageFont.load_default()
    
    # Center text with yellow color
    draw.text((80, 700), text[:30] + "...", font=font, fill=(255, 255, 0), stroke_width=8, stroke_fill=(0,0,0))
    draw.text((80, 900), "FACT!", font=font, fill=(255,0,0), stroke_width=10, stroke_fill=(255,255,255))
    img.save(filename)
    print(f"Thumbnail created: {filename}")
    return filename

# === 3. YOUR UPLOAD FUNCTION ===
# Use this title + description
fact_data = get_viral_fact()
viral_title = make_viral_title(fact_data)
viral_desc = f"""{fact_data['fact']}

{fact_data['hook']}

Follow for daily mind-blowing facts! 👇

#factverse #shorts #viral #amazingfacts #facts #trending #didyouknow #india #psychologyfacts #sciencefacts #viralshorts
"""

print(f"TITLE: {viral_title}")
print(f"DESC: {viral_desc}")

# Create thumbnail
create_thumbnail(fact_data['fact'])

# --- YOUR EXISTING UPLOAD CODE BELOW ---
# youtube = ... 
# Just use viral_title and viral_desc in your insert request
# And upload thumbnail.jpg as custom thumbnail
