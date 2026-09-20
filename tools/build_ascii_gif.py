"""Render the self-hosted animated ASCII artwork used by the profile README.

Requires Pillow. The GIF uses only drawn text and shapes; no remote assets.
"""
from pathlib import Path
from math import atan2, cos, hypot, pi, sin
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "assets" / "ascii-pacheco.gif"
W, H = 900, 420
BG = (15, 28, 61)
PANEL = (10, 20, 48)
INK = (240, 233, 210)
GOLD = (242, 201, 76)
BLUE = (125, 144, 186)
SOFT = (170, 189, 224)
FONT = ImageFont.truetype("C:/Windows/Fonts/CascadiaMono.ttf", 13)
FONT_SM = ImageFont.truetype("C:/Windows/Fonts/CascadiaMono.ttf", 12)
FONT_BIG = ImageFont.truetype("C:/Windows/Fonts/CascadiaMono.ttf", 21)
FONT_TITLE = ImageFont.truetype("C:/Windows/Fonts/CascadiaMono.ttf", 26)
random.seed(15)
STARS = [(random.randrange(0, 58), random.randrange(0, 17), random.randrange(3)) for _ in range(38)]
FRAMES = []


def painting(draw, frame):
    """A moving starry night made of characters, never bitmap pixels."""
    x0, y0, cw, ch = 425, 67, 8, 17
    for row in range(18):
        for col in range(57):
            x, y = col / 56, row / 17
            px, py = x0 + col * cw, y0 + row * ch
            star = next((s for s in STARS if s[:2] == (col, row)), None)
            if y > .70 + .07 * sin(7 * x) - .05 * cos(13 * x):
                ch_out = "#/\\|"[(col + row) % 4] if y > .89 else "^~/\\"[(col + row) % 4]
                color = (58, 80, 124) if y < .91 else (43, 61, 99)
            elif x < .13 and y > .23:
                ch_out, color = "|/\\"[(col + row) % 3], (34, 51, 76)
            else:
                dx, dy = x - .52, (y - .38) * 1.18
                radius = hypot(dx, dy)
                angle = atan2(dy, dx)
                flow = sin(18 * radius - 2.5 * angle + frame * .20)
                moon = hypot(x - .83, y - .14)
                if moon < .095:
                    ch_out = "@O0o"[min(3, int(moon * 40))]
                    color = GOLD if moon < .06 else (183, 164, 100)
                elif star and (frame + star[2]) % 5 != 0:
                    ch_out = "+*·"[(frame // 2 + star[2]) % 3]
                    color = GOLD if star[2] == 0 else SOFT
                elif abs(flow) > .86 and radius < .40:
                    ch_out = "~-=~"[(col + row + frame // 2) % 4]
                    color = (101, 125, 180)
                elif abs(flow) > .57:
                    ch_out = ".~·"[(col + row) % 3]
                    color = (65, 88, 145)
                else:
                    continue
            draw.text((px, py), ch_out, font=FONT, fill=color)


for frame in range(24):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((1, 1, W - 2, H - 2), radius=13, fill=BG, outline=(43, 59, 99), width=2)
    d.rectangle((1, 44, W - 2, 45), fill=(43, 59, 99))
    for cx, color in ((23, (255, 95, 86)), (43, (255, 189, 46)), (63, (39, 201, 63))):
        d.ellipse((cx - 5, 18, cx + 5, 28), fill=color)
    d.text((91, 16), "pacheco@github  ~  live canvas", font=FONT_SM, fill=BLUE)
    d.text((25, 72), "pacheco@github", font=FONT_SM, fill=GOLD)
    d.text((142, 72), ":~$ render noite-estrelada", font=FONT_SM, fill=SOFT)

    d.text((26, 136), "João Gabriel", font=FONT_TITLE, fill=INK)
    d.text((26, 171), "Pacheco", font=FONT_TITLE, fill=GOLD)
    d.text((27, 226), "Código que resolve,", font=FONT, fill=INK)
    d.text((27, 250), "do banco ao browser.", font=FONT, fill=INK)
    d.line((26, 297, 365, 297), fill=(43, 59, 99), width=1)
    d.text((27, 315), "Python  /  FastAPI  /  React", font=FONT_SM, fill=BLUE)
    d.text((27, 335), "Next.js  /  TypeScript", font=FONT_SM, fill=BLUE)
    d.text((27, 379), "pacheco.dev.br", font=FONT_SM, fill=GOLD)
    d.text((144, 379), "  ·  full stack", font=FONT_SM, fill=SOFT)
    if frame % 8 < 5:
        d.rectangle((333, 74, 340, 87), fill=INK)
    painting(d, frame)
    FRAMES.append(im.quantize(colors=96, method=Image.Quantize.MEDIANCUT))

DEST.parent.mkdir(exist_ok=True)
FRAMES[0].save(DEST, save_all=True, append_images=FRAMES[1:], duration=120,
               loop=0, disposal=2, optimize=False)
print(f"{DEST}: {len(FRAMES)} frames, {DEST.stat().st_size} bytes")
