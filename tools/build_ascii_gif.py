"""Render the portfolio's actual hero painting as animated ASCII for GitHub.

Usage: python build_ascii_gif.py /path/to/portfolio
Requires Pillow. The source image and fonts belong to pacheco.dev.br.
"""
from pathlib import Path
from math import sin, pi
import sys
from PIL import Image, ImageDraw, ImageFont

SITE = Path(sys.argv[1])
DEST = Path(__file__).resolve().parents[1] / "assets" / "ascii-pacheco.gif"
SOURCE = SITE / "public/assets/hero-dark-1280.webp"
W, H = 960, 430
COLS, ROWS = 120, 32
CW, CH = 8, 14
RAMP = "   .,:-~=+*#%@"
BG = (15, 28, 61)
CREAM = (240, 233, 210)
GOLD = (242, 201, 76)
MONO = ImageFont.truetype(str(SITE / "public/fonts/jetbrains-mono.woff2"), 13)
SANS = ImageFont.truetype(str(SITE / "public/fonts/space-grotesk.woff2"), 17)
SERIF = ImageFont.truetype(str(SITE / "public/fonts/instrument-serif.woff2"), 74)
ITALIC = ImageFont.truetype(str(SITE / "public/fonts/instrument-serif-italic.woff2"), 80)

source = Image.open(SOURCE).convert("RGB")
frames = []
for frame in range(20):
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    # Sample the actual hero image at a character grid. Tiny shifts create
    # motion in its painted swirls; every visible brushstroke is still a glyph.
    pixels = source.resize((COLS + 4, ROWS + 2), Image.Resampling.LANCZOS)
    for row in range(ROWS):
        for col in range(COLS):
            dx = int(round(1.5 * sin(frame * 2 * pi / 20 + row * .23 + col * .045)))
            color = pixels.getpixel((min(COLS + 3, max(0, col + 2 + dx)), row + 1))
            brightness = .2126 * color[0] + .7152 * color[1] + .0722 * color[2]
            index = min(len(RAMP) - 1, int(brightness / 225 * len(RAMP)))
            char = RAMP[index]
            if char != " ":
                draw.text((col * CW, row * CH - 5), char, font=MONO,
                          fill=tuple(min(255, int(c * 1.35)) for c in color))

    # Match the site's shaded left edge behind the editorial hero copy.
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for x in range(760):
        opacity = 255 if x < 430 else int(255 * (1 - (x - 430) / 330) ** 1.35)
        sd.line((x, 0, x, H), fill=(*BG, opacity))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shade).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    draw.text((42, 34), "PACHECO.DEV", font=MONO, fill=CREAM)
    draw.text((42, 90), "DESENVOLVEDOR DE SOFTWARE SÊNIOR — FULL STACK", font=MONO,
              fill=(170, 189, 224))
    draw.text((37, 127), "João Gabriel", font=SERIF, fill=CREAM)
    draw.text((37, 201), "Pacheco", font=ITALIC, fill=GOLD)
    draw.text((42, 300), "Código que resolve, do banco ao browser.", font=SANS,
              fill=CREAM)
    draw.line((42, 363, 918, 363), fill=(125, 144, 186), width=1)
    draw.text((42, 382), "FULL STACK  *  PYTHON  *  FASTAPI  *  REACT  *  NEXT.JS", font=MONO,
              fill=(170, 189, 224))
    frames.append(canvas.quantize(colors=128, method=Image.Quantize.MEDIANCUT))

DEST.parent.mkdir(exist_ok=True)
frames[0].save(DEST, save_all=True, append_images=frames[1:], duration=135,
               loop=0, disposal=2, optimize=True)
print(f"{DEST}: {len(frames)} frames; {DEST.stat().st_size} bytes")
