"""Gera assets/card.svg: card de perfil em ASCII animado para o README.

Só biblioteca padrão. Uso:
    python tools/gen_card.py [saida.svg]

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
import sys

ROOT = Path(__file__).resolve().parents[1]
SAIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets/card.svg"

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
PX, PY, PW, PH = M, 120, 408, 300          # painel esquerdo
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


def chips(y):
    out, x = [], M
    fs = 12
    for a in PERFIL["areas"]:
        w = len(a) * 0.6 * fs + 24
        out.append(f'<rect x="{x}" y="{y}" width="{w:.1f}" height="26" rx="4" '
                   f'fill="{COR["painel"]}" stroke="{COR["borda"]}"/>')
        out.append(txt(x + 12, y + 17, a, fs, COR["texto"]))
        x += w + 10
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
    nome = PERFIL["nome"]
    fs_nome = 28
    larg_nome = len(nome) * 0.6 * fs_nome
    passos = len(nome)
    y_areas = PY + PH + 40
    y_proj = y_areas + 64
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
        # painel esquerdo: campo em duas camadas + monograma
        f'<rect x="{PX - 1}" y="{PY - 1}" width="{PW + 2}" height="{PH + 2}" fill="{COR["painel"]}" stroke="{COR["borda"]}"/>',
        f'<g clip-path="url(#cp)">',
        camada("l1", COR["campo"], 0.0, 1.6, 0.9),
        camada("l2", COR["campo2"], 1.7, 3.2, 0.55),
        f'<rect x="{PX + PW / 2 - 170}" y="{PY + PH / 2 - 92}" width="340" height="184" rx="4" '
        f'fill="{COR["painel"]}" fill-opacity="0.78"/>',
        monograma(),
        "</g>",
        painel_info(),
        secao(y_areas, "ÁREAS DE ATUAÇÃO"),
        chips(y_areas + 12),
        secao(y_proj, "PROJETOS EM DESTAQUE"),
        projetos(y_proj + 12),
        "</svg>",
    ]
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(partes), encoding="utf-8")
    print(f"{SAIDA} ({SAIDA.stat().st_size / 1024:.1f} KB, {W}x{H})")


if __name__ == "__main__":
    main()
