"""Convert the supplied Starry Night image with Chafa, then animate the ASCII.

Requires Chafa and Pillow. Run from anywhere:
    python tools/build_ascii_gif.py [path/to/chafa]
"""
from pathlib import Path
from math import hypot, sin, pi
import glob
import re
import shutil
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/noite-estrelada-base.jpg"
DEST = ROOT / "assets/noite-estrelada-refinada.gif"
COLS, ROWS = 120, 63
CW, CH = 8, 12
BG = (15, 28, 61)

chafa = sys.argv[1] if len(sys.argv) > 1 else shutil.which("chafa")
if not chafa:
    found = glob.glob(str(Path.home() / "AppData/Local/Microsoft/WinGet/Packages/hpjansson.Chafa_*/**/Chafa.exe"), recursive=True)
    chafa = found[0] if found else None
if not chafa:
    raise SystemExit("Chafa não encontrado: instale hpjansson.Chafa ou passe o executável como argumento")

command = [chafa, "-f", "symbols", "-c", "full", "--symbols", "ascii",
           "--relative", "off", "--dither", "none", "--color-space", "din99d",
           "--stretch", "-s", f"{COLS}x{ROWS}", str(SOURCE)]
result = subprocess.run(command, capture_output=True, check=True)
raw = result.stdout.decode("utf-8", errors="replace")

# Chafa emits truecolor ANSI for the ASCII glyph and its cell background.
# Keep both colors while discarding terminal controls.
tokens = re.split(r"(\x1b\[[0-9;?]*[A-Za-z])", raw)
cells = [[]]
color = (215, 225, 245)
background = BG
for token in tokens:
    if token.startswith("\x1b["):
        if token.endswith("m"):
            values = token[2:-1].split(";")
            for index in range(len(values) - 4):
                if values[index:index + 2] == ["38", "2"]:
                    color = tuple(map(int, values[index + 2:index + 5]))
                if values[index:index + 2] == ["48", "2"]:
                    background = tuple(map(int, values[index + 2:index + 5]))
        continue
    for char in token:
        if char == "\n":
            cells.append([])
        elif char != "\r":
            cells[-1].append((char, color, background))
cells = [row[:COLS] for row in cells if row]
if len(cells) != ROWS or any(len(row) != COLS for row in cells):
    raise SystemExit(f"Grade Chafa inesperada: {len(cells)} linhas, comprimentos {[len(r) for r in cells[:4]]}")

font_path = "C:/Windows/Fonts/CascadiaMono.ttf" if Path("C:/Windows/Fonts/CascadiaMono.ttf").exists() else "DejaVuSansMono.ttf"
font = ImageFont.truetype(font_path, 12)
source_image = Image.open(SOURCE).convert("RGB")
source = source_image.resize((COLS, ROWS), Image.Resampling.LANCZOS)
shared_palette = source_image.resize((320, 240), Image.Resampling.LANCZOS).quantize(
    colors=192, method=Image.Quantize.MEDIANCUT)
stars = [(.105, .045, .05), (.235, .175, .04), (.346, .538, .06),
         (.705, .237, .05), (.897, .17, .10), (.610, .085, .05),
         (.335, .335, .04), (.132, .485, .04)]
frames = []
for frame in range(20):
    canvas = Image.new("RGB", (COLS * CW, ROWS * CH), BG)
    draw = ImageDraw.Draw(canvas)
    for row, line in enumerate(cells):
        for col, (char, base, cell_bg) in enumerate(line):
            red, green, blue = source.getpixel((col, row))
            light = .2126 * red + .7152 * green + .0722 * blue
            # The bright brushstrokes carry a slow sweep; star halos pulse.
            wave = sin(col * .14 - row * .07 - frame * 2 * pi / 20)
            glow = .18 * max(0.0, (wave - .65) / .35) * max(0.0, (light - 90) / 160)
            for number, (sx, sy, radius) in enumerate(stars):
                distance = hypot(col / COLS - sx, row / ROWS - sy)
                if distance < radius:
                    pulse = (1 + sin(frame * 2 * pi / 20 + number * 1.7)) / 2
                    glow += .22 * pulse * (1 - distance / radius)
            glow = min(.32, glow)
            background_color = tuple(min(255, round(cell_bg[i] * (1 - glow) + (255, 233, 170)[i] * glow)) for i in range(3))
            draw.rectangle((col * CW, row * CH, (col + 1) * CW, (row + 1) * CH), fill=background_color)
            color = tuple(min(255, round(base[i] * (1 - glow) + (255, 246, 215)[i] * glow)) for i in range(3))
            if char != " ":
                draw.text((col * CW, row * CH - 3), char, font=font, fill=color)
    frames.append(canvas.quantize(palette=shared_palette, dither=Image.Dither.NONE))

frames[0].save(DEST, save_all=True, append_images=frames[1:], duration=110,
               loop=0, disposal=2, optimize=True)
print(f"{DEST}: {len(frames)} quadros, {DEST.stat().st_size} bytes")
