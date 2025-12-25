from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from tqdm import tqdm
import os


def add_day_overlay():
    today = datetime.now().strftime("%Y-%m-%d")
    prefix = f"Screenshot {today}"
    suffix = ".png"

    files = [f for f in os.listdir(".") if f.startswith(prefix) and f.endswith(suffix) and os.path.isfile(f)]

    day_text = (datetime.now() - timedelta(days=1)).strftime("%d")

    for file in tqdm(files, desc=f"Add overlay to images"):
        img = Image.open(file).convert("RGBA")
        draw = ImageDraw.Draw(img)

        font_size = 48
        padding = 12
        bg_color = (0, 0, 0, 180)
        text_color = (255, 255, 255)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), day_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = (img.width - (text_w + padding * 2)) // 2
        y = 0

        draw.rectangle(
            (x, y, x + text_w + padding * 2, y + text_h + padding * 2 + 10),
            fill=bg_color,
        )
        draw.text(
            (x + padding, y + padding),
            day_text,
            font=font,
            fill=text_color,
        )

        img.save(f"stamped_{file}")
