"""Convert the supplied Starry Night image with Chafa, then animate the ASCII.

Requires Chafa and Pillow. Run from anywhere:
    python tools/build_ascii_gif.py [path/to/chafa]
"""
from pathlib import Path
from math import sin, pi
import glob
import re
import shutil
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/noite-estrelada-base.jpg"
DEST = ROOT / "assets/noite-estrelada-chafa.gif"
COLS, ROWS = 100, 52
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
source = Image.open(SOURCE).convert("RGB").resize((COLS, ROWS), Image.Resampling.LANCZOS)
frames = []
for frame in range(20):
    canvas = Image.new("RGB", (COLS * CW, ROWS * CH), BG)
    draw = ImageDraw.Draw(canvas)
    for row, line in enumerate(cells):
        for col, (char, base, cell_bg) in enumerate(line):
            draw.rectangle((col * CW, row * CH, (col + 1) * CW, (row + 1) * CH), fill=cell_bg)
            red, green, blue = source.getpixel((col, row))
            light = .2126 * red + .7152 * green + .0722 * blue
            # A slow luminous sweep crosses only light brushstrokes and stars.
            wave = sin(col * .14 - row * .07 - frame * 2 * pi / 20)
            glow = max(0.0, (wave - .7) / .3) * max(0.0, (light - 95) / 160)
            color = tuple(min(255, round(base[i] * (1 - glow) + (255, 226, 156)[i] * glow)) for i in range(3))
            if char != " ":
                draw.text((col * CW, row * CH - 3), char, font=font, fill=color)
    frames.append(canvas.quantize(colors=128, method=Image.Quantize.MEDIANCUT))

frames[0].save(DEST, save_all=True, append_images=frames[1:], duration=110,
               loop=0, disposal=2, optimize=True)
print(f"{DEST}: {len(frames)} quadros, {DEST.stat().st_size} bytes")
