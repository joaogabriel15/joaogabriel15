"""Gera assets/card.svg: card de perfil em ASCII animado para o README.

Uso:
    python tools/gen_card.py --foto joao.png -o assets/card.svg
Sem --foto, o painel esquerdo mostra o monograma sobre um campo ASCII
(só biblioteca padrão). Com --foto, precisa de Pillow.

Regras do SVG (o GitHub serve via <img> com CSP sandbox):
- sem JavaScript; só CSS
- espaço vira U+00A0, senão o Chrome colapsa espaços repetidos
- textLength em todo texto com mais de 1 caractere (Consolas tem avanço
  0,55 em; DejaVu/Liberation 0,60 em)
- animação de entrada com fill-mode backwards: sem animação, tudo aparece
- anima só elementos da árvore de renderização (g, text, rect)
"""
from pathlib import Path
from math import sin, cos, pi
from xml.sax.saxutils import escape
import argparse

ROOT = Path(__file__).resolve().parents[1]

PERFIL = {
    "nome": "João Gabriel Pacheco",
    "subtitulo": "@joaogabriel15 · desenvolvedor sênior full stack",
    "canto": "[ pacheco.dev.br ]",
    "monograma": "JGP",
    "usuario": "joao@pacheco.dev.br",
    "info": [
        ("Função", "Desenvolvedor sênior full stack"),
        ("Experiência", "8+ anos, web e mobile"),
        ("Backend", "Python, FastAPI, Django, Node.js"),
        ("Frontend", "TypeScript, React, Next.js, Vue"),
        ("Mobile", "React Native, Expo"),
        ("Dados", "PostgreSQL, MongoDB, Redis"),
        ("Infra", "Docker, RabbitMQ, CI/CD"),
        ("IA", "Agentes, automações, prompts"),
    ],
    "contato": [
        ("Portfólio", "pacheco.dev.br"),
        ("LinkedIn", "in/pacheco-dev-br"),
        ("E-mail", "pacheco.code@gmail.com"),
    ],
    "areas": ["Frontend", "Backend", "Mobile", "Dados", "Arquitetura", "IA"],
    "projetos": [
        ("ArchPrompts", "arch-prompts.com",
         "Marketplace de prompts para arquitetura de sistemas"),
        ("Portfólio", "pacheco.dev.br",
         "Outros trabalhos, experiências e contato"),
    ],
}

COR = {
    "fundo": "#0d1117", "painel": "#10151c", "borda": "#30363d",
    "texto": "#e6edf3", "fraco": "#7d8590", "acento": "#a3e635",
    "rotulo": "#58a6ff", "campo": "#1f6f8b", "campo2": "#d4a72c",
}
FONTE = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace"
W = 960
M = 32  # margem


def txt(x, y, s, fs, cor, extra=""):
    """<text> com espaços U+00A0 e textLength calculado a 0,6 em por caractere."""
    s = s.replace(" ", " ")
    tl = f' textLength="{len(s) * 0.6 * fs:.1f}" lengthAdjust="spacing"' if len(s) > 1 else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{fs}" fill="{cor}"{tl}{extra}>'
            f"{escape(s)}</text>")


# ---------------------------------------------------------------- campo ASCII
FS_C, CW, LH = 10, 6.0, 12.0
PX, PY, PW, PH = M, 120, 408, 408          # painel esquerdo
COLS, ROWS = int(PW / CW), int(PH / LH)    # 68 x 25
RAMPA = " .:-=+*#%@"

LETRAS = {
    "J": ["  #####", "     # ", "     # ", "     # ", "#    # ", "#    # ", " ####  "],
    "G": [" ##### ", "#      ", "#      ", "#  ####", "#     #", "#     #", " ##### "],
    "P": ["###### ", "#     #", "#     #", "###### ", "#      ", "#      ", "#      "],
}


def campo(cols, rows, fase, gamma):
    """Campo periódico em x (período = cols), para o loop não ter emenda."""
    linhas = []
    for r in range(rows):
        row = []
        for c in range(cols):
            a = 2 * pi * c / cols
            v = (sin(3 * a + r * 0.35 + fase) + sin(5 * a - r * 0.21 + 2 * fase)
                 + 0.6 * cos(2 * a + r * 0.5)) / 2.6
            v = max(0.0, min(1.0, (v + 1) / 2)) ** gamma
            row.append(RAMPA[min(len(RAMPA) - 1, int(v * len(RAMPA)))])
        linhas.append("".join(row))
    return linhas


def camada(cls, cor, fase, gamma, opac):
    linhas = campo(COLS, ROWS, fase, gamma)
    out = [f'<g class="{cls}" fill-opacity="{opac}">']
    for r, ln in enumerate(linhas):
        # duas cópias lado a lado; a animação desloca uma largura inteira
        out.append(txt(PX, PY + (r + 1) * LH - 2, ln + ln, FS_C, cor))
    out.append("</g>")
    return "\n".join(out)


def monograma():
    texto = PERFIL["monograma"]
    rows = []
    for i in range(7):
        linha = "  ".join(LETRAS[ch][i] for ch in texto)
        rows.append("".join(c * 2 for c in linha))  # escala 2x na horizontal
    largura = len(rows[0]) * CW
    x0 = PX + (PW - largura) / 2
    y0 = PY + (PH - 14 * LH) / 2
    out = ['<g class="mono">']
    for i, ln in enumerate(rows):
        for k in range(2):                           # escala 2x na vertical
            y = y0 + (2 * i + k + 1) * LH - 2
            out.append(txt(x0, y, ln.replace("#", "@"), FS_C, COR["acento"], ' font-weight="700"'))
    out.append("</g>")
    return "\n".join(out)


# -------------------------------------------------------------- retrato ASCII
# sem "-" e "=": em fileira, viram listras horizontais no fundo
RAMPA_R = " .:;+*#%@"
NB = "\u00a0"


def retrato(foto, colunas, zoom, foco, foco_y, fundo):
    """Retrato em ASCII colorido: caractere pelo brilho, cor pelo matiz do pixel.

    Em 96 colunas o traço fino da fonte cobre pouca área, então o texto vai
    em negrito e a cor fica clara; o brilho vai só para a escolha do caractere.

    O fundo é escurecido por uma máscara elíptica centrada no foco (sem
    modelo de recorte); `fundo` é o brilho que sobra fora dela.
    """
    from PIL import Image, ImageFilter
    import colorsys
    im = Image.open(foto).convert("RGB")
    w, h = im.size
    cw = PW / colunas
    fs = cw / 0.6
    lh = cw * 2
    linhas = int(PH / lh)
    lado = min(w, h) / zoom
    alt = lado * (linhas * lh) / PW
    cx, cy = foco * w, foco_y * h
    x0 = max(0, min(w - lado, cx - lado / 2))
    y0 = max(0, min(h - alt, cy - alt / 2))
    im = im.crop((int(x0), int(y0), int(x0 + lado), int(y0 + alt)))
    # as pinceladas viram ruído em 96 colunas: borra antes, realça contorno depois
    im = im.filter(ImageFilter.GaussianBlur(lado / colunas * 0.6))
    im = im.resize((colunas, linhas), Image.BOX)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140, threshold=0))
    px = im.load()

    # brilho mascarado de cada célula
    cel = []
    for r in range(linhas):
        for c in range(colunas):
            red, g, b = px[c, r]
            dx = (c / colunas - (cx - x0) / lado) / 0.40
            dy = (r / linhas - (cy - y0) / alt) / 0.58
            m = max(fundo, min(1.0, 1.3 - (dx * dx + dy * dy)))
            lum = (0.299 * red + 0.587 * g + 0.114 * b) / 255
            cel.append((red, g, b, m, lum * m))
    # equaliza o brilho: a pele deixa de saturar no fim da rampa
    ordem = sorted(v[4] for v in cel)
    n = len(ordem)

    def rank(v):
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if ordem[mid] < v:
                lo = mid + 1
            else:
                hi = mid
        return lo / n

    out = ['<g class="foto">']
    for r in range(linhas):
        runs, atual, cor_atual = [], [], None
        for c in range(colunas):
            red, g, b, m, lm = cel[r * colunas + c]
            v = 0.5 * rank(lm) + 0.5 * lm      # meio equalizado, meio linear
            ch = " " if v < 0.06 else RAMPA_R[min(len(RAMPA_R) - 1, int(v * len(RAMPA_R)))]
            hh, ss, _ = colorsys.rgb_to_hsv(red / 255, g / 255, b / 255)
            cor = colorsys.hsv_to_rgb(hh, min(1.0, ss * 1.15), min(1.0, (0.6 + 0.45 * v) * (0.5 + 0.5 * m)))
            cor = "#%02x%02x%02x" % tuple(int(x * 255) // 16 * 16 + 8 for x in cor)
            if ch == " ":
                cor = cor_atual  # espaço não tem cor: não quebra o trecho
            if cor != cor_atual and atual:
                runs.append((cor_atual, "".join(atual)))
                atual = []
            atual.append(ch)
            cor_atual = cor
        runs.append((cor_atual, "".join(atual)))
        n_chars = sum(len(t) for _, t in runs)
        spans = "".join(f'<tspan fill="{cor or COR["fundo"]}">{escape(t.replace(" ", NB))}</tspan>'
                        for cor, t in runs)
        y = PY + (r + 1) * lh - lh * 0.2
        out.append(f'<text class="in" style="animation-delay:{0.3 + r * 0.02:.2f}s" '
                   f'x="{PX}" y="{y:.1f}" font-size="{fs:.2f}" font-weight="700" '
                   f'textLength="{n_chars * cw:.1f}" lengthAdjust="spacing">{spans}</text>')
    out.append("</g>")
    return "\n".join(out)


# ------------------------------------------------------------- painel direito
def painel_info():
    fs, cw, lh = 13, 7.8, 19
    x = PX + PW + 24
    y = PY + 16
    col_val = 15  # coluna onde começa o valor
    out = []
    n = 0

    def linha(partes):
        nonlocal y, n
        out.append(f'<g class="in" style="animation-delay:{0.9 + n * 0.08:.2f}s">'
                   + "".join(partes) + "</g>")
        y += lh
        n += 1

    def par(rot, val):
        pontos = "." * (col_val - len(rot) - 2)
        return [txt(x, y, rot, fs, COR["rotulo"]),
                txt(x + (len(rot) + 1) * cw, y, pontos, fs, COR["borda"]),
                txt(x + col_val * cw, y, val, fs, COR["texto"])]

    u = PERFIL["usuario"]
    linha([txt(x, y, u, fs, COR["acento"], ' font-weight="700"')])
    linha([txt(x, y - 6, "─" * len(u), fs, COR["borda"])])
    y -= 6
    for rot, val in PERFIL["info"]:
        linha(par(rot, val))
    y += 6
    linha([txt(x, y, "Contato", fs, COR["acento"], ' font-weight="700"')])
    for rot, val in PERFIL["contato"]:
        linha(par(rot, val))
    # paleta estilo neofetch
    cores = ["#f85149", "#d29922", "#a3e635", "#3fb950", "#58a6ff", "#bc8cff", "#e6edf3"]
    blocos = "".join(f'<rect x="{x + i * 24}" y="{y - 8}" width="20" height="10" fill="{c}"/>'
                     for i, c in enumerate(cores))
    out.append(f'<g class="in" style="animation-delay:{0.9 + n * 0.08:.2f}s">{blocos}</g>')
    return "\n".join(out)


# ------------------------------------------------------------ seções de baixo
def secao(y, titulo):
    return txt(M, y, f"[ {titulo} ]", 11, COR["fraco"], ' letter-spacing="0"')


def chips(x, y):
    out = []
    fs = 12
    for a in PERFIL["areas"]:
        w = len(a) * 0.6 * fs + 20
        out.append(f'<rect x="{x}" y="{y}" width="{w:.1f}" height="26" rx="4" '
                   f'fill="{COR["painel"]}" stroke="{COR["borda"]}"/>')
        out.append(txt(x + 10, y + 17, a, fs, COR["texto"]))
        x += w + 8
    return "\n".join(out)


def projetos(y):
    out = []
    n = len(PERFIL["projetos"])
    gap = 16
    w = (W - 2 * M - gap * (n - 1)) / n
    for i, (nome, url, desc) in enumerate(PERFIL["projetos"]):
        x = M + i * (w + gap)
        out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="70" rx="6" '
                   f'fill="{COR["painel"]}" stroke="{COR["borda"]}"/>')
        out.append(txt(x + 16, y + 26, nome, 14, COR["acento"], ' font-weight="700"'))
        out.append(txt(x + w - 16 - len(url) * 0.6 * 11, y + 26, url, 11, COR["fraco"]))
        out.append(txt(x + 16, y + 52, desc, 12, COR["texto"]))
    return "\n".join(out)


# --------------------------------------------------------------------- montar
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--foto", help="imagem de origem do retrato")
    ap.add_argument("--colunas", type=int, default=96, help="resolução do retrato")
    ap.add_argument("--zoom", type=float, default=1.65, help="aproximação do recorte")
    ap.add_argument("--foco", type=float, default=0.46, help="centro x do recorte (0 a 1)")
    ap.add_argument("--foco-y", type=float, default=0.38, help="centro y do recorte (0 a 1)")
    ap.add_argument("--fundo", type=float, default=0.3, help="brilho que sobra no fundo")
    ap.add_argument("-o", "--saida", type=Path, default=ROOT / "assets/card.svg")
    a = ap.parse_args()
    SAIDA = a.saida
    if a.foto:
        esquerda = [retrato(a.foto, a.colunas, a.zoom, a.foco, a.foco_y, a.fundo),
                    f'<rect class="scan" x="{PX}" y="{PY}" width="{PW}" height="3" '
                    f'fill="{COR["acento"]}" fill-opacity="0.18"/>']
    else:
        esquerda = [camada("l1", COR["campo"], 0.0, 1.6, 0.9),
                    camada("l2", COR["campo2"], 1.7, 3.2, 0.55),
                    f'<rect x="{PX + PW / 2 - 170}" y="{PY + PH / 2 - 92}" width="340" height="184" '
                    f'rx="4" fill="{COR["painel"]}" fill-opacity="0.78"/>',
                    monograma()]
    nome = PERFIL["nome"]
    fs_nome = 28
    larg_nome = len(nome) * 0.6 * fs_nome
    passos = len(nome)
    x_dir = PX + PW + 24
    y_areas = PY + PH - 38
    y_proj = PY + PH + 40
    H = y_proj + 70 + M

    css = f"""
text {{ font-family: {FONTE}; white-space: pre; }}
@keyframes desliza {{ from {{ transform: translateX(0) }} to {{ transform: translateX(-{COLS * CW:.1f}px) }} }}
@keyframes desliza2 {{ from {{ transform: translateX(-{COLS * CW:.1f}px) }} to {{ transform: translateX(0) }} }}
@keyframes digita {{ from {{ transform: translateX(0) }} to {{ transform: translateX({larg_nome + 4:.1f}px) }} }}
@keyframes cobre {{ from, to {{ opacity: 1 }} }}
@keyframes pisca {{ 0%, 49% {{ opacity: 1 }} 50%, 100% {{ opacity: 0 }} }}
@keyframes entra {{ from {{ opacity: 0; transform: translateY(6px) }} to {{ opacity: 1; transform: none }} }}
@keyframes pulsa {{ 0%, 100% {{ opacity: 1 }} 50% {{ opacity: .72 }} }}
.l1 {{ animation: desliza 40s linear infinite; }}
.l2 {{ animation: desliza2 26s linear infinite; }}
.capa {{ opacity: 0; animation: digita 1.4s steps({passos}) .2s backwards, cobre 1.6s backwards; }}
.cursor {{ animation: pisca 1s step-end infinite; }}
.in {{ animation: entra .5s ease-out backwards; }}
.scan {{ animation: varre 6s linear infinite; }}
@keyframes varre {{ from {{ transform: translateY(0) }} to {{ transform: translateY({PH - 3}px) }} }}
.mono {{ animation: pulsa 4s ease-in-out infinite; }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
"""
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{escape(nome)} — card de perfil">',
        f"<title>{escape(nome)}</title>",
        f"<style>{css}</style>",
        f'<defs><clipPath id="cp"><rect x="{PX}" y="{PY}" width="{PW}" height="{PH}"/></clipPath></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="{COR["fundo"]}" stroke="{COR["borda"]}"/>',
        # cabeçalho
        txt(M, 58, nome, fs_nome, COR["texto"], ' font-weight="700"'),
        # capa que "digita" o nome: some quando a animação não roda
        f'<rect class="capa" x="{M - 2}" y="28" width="{larg_nome + 40:.1f}" height="40" fill="{COR["fundo"]}"/>',
        f'<rect class="cursor" x="{M + larg_nome + 6:.1f}" y="36" width="12" height="26" fill="{COR["acento"]}"/>',
        txt(M, 86, PERFIL["subtitulo"], 13, COR["acento"]),
        txt(W - M - len(PERFIL["canto"]) * 0.6 * 11, 44, PERFIL["canto"], 11, COR["fraco"]),
        f'<line x1="{M}" y1="{PY - 18}" x2="{W - M}" y2="{PY - 18}" stroke="{COR["borda"]}"/>',
        # painel esquerdo: retrato, ou campo em duas camadas + monograma
        f'<rect x="{PX - 1}" y="{PY - 1}" width="{PW + 2}" height="{PH + 2}" fill="{COR["painel"]}" stroke="{COR["borda"]}"/>',
        f'<g clip-path="url(#cp)">',
        *esquerda,
        "</g>",
        painel_info(),
        txt(x_dir, y_areas, "[ ÁREAS DE ATUAÇÃO ]", 11, COR["fraco"]),
        chips(x_dir, y_areas + 12),
        secao(y_proj, "PROJETOS EM DESTAQUE"),
        projetos(y_proj + 12),
        "</svg>",
    ]
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(partes), encoding="utf-8")
    print(f"{SAIDA} ({SAIDA.stat().st_size / 1024:.1f} KB, {W}x{H})")


if __name__ == "__main__":
    main()
