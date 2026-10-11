import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1])
for size, name in [(180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)
    for y in range(size):
        t = y / size
        draw.line([(0, y), (size, y)], fill=(int(34 + (139 - 34) * t), int(211 - (211 - 92) * t), int(238 + (246 - 238) * t)))
    font = ImageFont.truetype("C:/Windows/Fonts/seguisym.ttf", int(size * 0.72))
    draw.text((size / 2, size / 2 + size * 0.04), "\u265e", font=font, fill=(11, 10, 31), anchor="mm")
    img.save(out / name)
