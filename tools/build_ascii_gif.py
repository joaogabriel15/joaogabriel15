"""Render the full portfolio hero painting as animated ASCII for GitHub.

Usage: python build_ascii_gif.py /path/to/portfolio
Requires Pillow. The source image and fonts belong to pacheco.dev.br.
"""
from pathlib import Path
from math import cos, sin, pi
import sys
from PIL import Image, ImageDraw, ImageFont

SITE = Path(sys.argv[1])
DEST = Path(__file__).resolve().parents[1] / "assets" / "noite-estrelada-ascii.gif"
SOURCE = SITE / "public/assets/hero-dark-1280.webp"
W, H = 960, 600
COLS, ROWS = 120, 50
CW, CH = 8, 12
RAMP = "  .,:-~=+*#%@"
BG = (15, 28, 61)
GOLD = (242, 201, 76)
MONO = ImageFont.truetype(str(SITE / "public/fonts/jetbrains-mono.woff2"), 12)

source = Image.open(SOURCE).convert("RGB")
frames = []
for frame in range(20):
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    # Convert the entire painting to glyphs. The sampled position flows gently
    # along the brushstrokes, while small gold glyphs orbit the painted swirl.
    pixels = source.resize((COLS + 4, ROWS + 2), Image.Resampling.LANCZOS)
    for row in range(ROWS):
        for col in range(COLS):
            dx = int(round(1.5 * sin(frame * 2 * pi / 20 + row * .14 + col * .055)))
            color = pixels.getpixel((min(COLS + 3, max(0, col + 2 + dx)), row + 1))
            brightness = .2126 * color[0] + .7152 * color[1] + .0722 * color[2]
            index = min(len(RAMP) - 1, int(brightness / 240 * len(RAMP)))
            char = RAMP[index]
            if char != " ":
                draw.text((col * CW, row * CH - 5), char, font=MONO,
                          fill=tuple(min(255, int(c * 1.3)) for c in color))
    for particle in range(18):
        phase = particle * 2 * pi / 18 + frame * 2 * pi / 20
        radius = 38 + particle * 4.7
        x = int(480 + radius * cos(phase))
        y = int(200 + radius * .55 * sin(phase))
        draw.text((x, y), "+" if particle % 3 else "*", font=MONO,
                  fill=GOLD if particle % 2 else (200, 214, 243))
    frames.append(canvas.quantize(colors=128, method=Image.Quantize.MEDIANCUT))

DEST.parent.mkdir(exist_ok=True)
frames[0].save(DEST, save_all=True, append_images=frames[1:], duration=135,
               loop=0, disposal=2, optimize=True)
print(f"{DEST}: {len(frames)} frames; {DEST.stat().st_size} bytes")
