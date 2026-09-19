"""Build self-contained SVG banners from the portfolio's original assets.

Usage: python build-banner.py /path/to/portfolio
Requires: pip install fonttools brotli
"""
from pathlib import Path
import base64
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

site = Path(sys.argv[1])
out = Path(__file__).parent / 'assets'
out.mkdir(exist_ok=True)

def lettering(text, font, size, x, y, color):
    face = TTFont(site / 'public/fonts' / (font + '.woff2'))
    glyphs, cmap = face.getGlyphSet(), face.getBestCmap()
    scale = size / face['head'].unitsPerEm
    parts = []
    for char in text:
        name = cmap[ord(char)]
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        parts.append(f'<path d="{pen.getCommands()}" transform="translate({x:.2f} {y}) scale({scale} {-scale})"/>')
        x += glyphs[name].width * scale
    return f'<g fill="{color}">' + ''.join(parts) + '</g>'

for theme, bg, ink, accent, sub in [
    ('dark', '#0f1c3d', '#f0e9d2', '#f2c94c', '#aabde0'),
    ('light', '#f2ead3', '#2b2416', '#b0741c', '#55492f'),
]:
    art = base64.b64encode((site / f'public/assets/hero-{theme}-1280.webp').read_bytes()).decode()
    texts = ''.join([
        lettering('PACHECO.DEV', 'jetbrains-mono', 13, 46, 42, ink),
        lettering('Desenvolvedor sênior · Full Stack', 'space-grotesk', 17, 46, 104, sub),
        lettering('João Gabriel', 'instrument-serif', 76, 44, 184, ink),
        lettering('Pacheco', 'instrument-serif-italic', 86, 44, 263, accent),
        lettering('Código que resolve,', 'space-grotesk', 21, 46, 314, ink),
        lettering('do banco ao browser.', 'space-grotesk', 21, 46, 344, ink),
        lettering('Python / FastAPI / React / Next.js / TypeScript', 'jetbrains-mono', 14, 46, 414, sub),
    ])
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="960" height="450" viewBox="0 0 960 450" role="img" aria-labelledby="title desc">
<title id="title">João Gabriel Pacheco — Desenvolvedor sênior Full Stack</title>
<desc id="desc">Código que resolve, do banco ao browser. Pintura em movimento suave, inspirada no portfólio pacheco.dev.br.</desc>
<defs><linearGradient id="veil"><stop offset="0" stop-color="{bg}"/><stop offset=".35" stop-color="{bg}" stop-opacity=".98"/><stop offset=".62" stop-color="{bg}" stop-opacity=".5"/><stop offset="1" stop-color="{bg}" stop-opacity=".08"/></linearGradient><clipPath id="frame"><rect width="960" height="450" rx="12"/></clipPath></defs>
<style>
.painting {{ transform-origin: 740px 215px; animation: drift 16s ease-in-out infinite; }}
.signature {{ animation: breathe 6s ease-in-out infinite; }}
@keyframes drift {{ 0%,100% {{ transform:scale(1.03) rotate(-.4deg); }} 50% {{ transform:scale(1.085) rotate(.5deg); }} }}
@keyframes breathe {{ 0%,100% {{ opacity:.45; }} 50% {{ opacity:1; }} }}
@media (prefers-reduced-motion:reduce) {{ .painting,.signature {{ animation:none; }} }}
</style>
<g clip-path="url(#frame)"><rect width="960" height="450" fill="{bg}"/>
<image class="painting" x="240" y="-16" width="760" height="475" preserveAspectRatio="xMidYMid slice" xlink:href="data:image/webp;base64,{art}"/>
<rect width="960" height="450" fill="url(#veil)"/>
<path d="M46 377H914" stroke="{ink}" stroke-opacity=".2"/>
{texts}
<g class="signature" stroke="{accent}" stroke-width="1.5" transform="translate(904 42)"><path d="M-9 0H9M0-9V9M-6-6L6 6M-6 6L6-6"/></g>
</g></svg>'''
    (out / f'header-{theme}.svg').write_text(svg, encoding='utf-8')
print('Built both animated banners.')
