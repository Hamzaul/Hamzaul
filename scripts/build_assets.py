"""Generate the static Minecraft-edition artwork (original pixel art, no game assets).

    python scripts/build_assets.py            # SVGs + PNGs (PNG needs: pip install cairosvg)

Outputs
    assets/minecraft-hero.svg                   README hero banner
    assets/pixel-divider.svg                    section divider
    assets/game-thumbnail.svg                   game card for the README
    pit-strategy/assets/social-preview.svg/.png 1200x630 link preview (PNG for crawlers)
    pit-strategy/assets/favicon.svg/.png        square favicon set (32 px, 180 px touch icon)
"""

import html
import math
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pixelfont as px  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

C = dict(
    obsidian="#0E0D14", night="#14131C", night2="#1B1A26", grass="#5B8731", leaf="#3F6B22",
    grass_hi="#79B13D", dirt="#7A5230", dirt_dk="#5E3E22", stone="#7F8580", stone_dk="#4A4E4B",
    deepslate="#2A2D2B", text="#F1F1EA", dim="#9AA09A", emerald="#17DD62", diamond="#5DECEC",
    gold="#FAC846", redstone="#D1342A", amethyst="#8B3FD9", wood="#9C6B3A", leaf_dk="#2A4C17",
)


def svg_open(w, h, title, desc):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="t d" shape-rendering="crispEdges">'
            f'<title id="t">{html.escape(title)}</title><desc id="d">{html.escape(desc)}</desc>')


def rect(x, y, w, h, fill, extra=""):
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}"{extra}/>'


def hills(w, base, step, amp, seed, color, offset):
    """Stepped, blocky hill silhouette."""
    out = []
    for x in range(0, w, step):
        h = offset + amp * (0.55 * math.sin((x + seed) / 130) + 0.35 * math.sin((x + seed * 2) / 57) + 0.1)
        h = max(8, round(h / step) * step)
        out.append(rect(x, base - h, step, h, color))
    return "".join(out)


def tree(x, base, scale=1):
    t = 10 * scale
    out = [rect(x, base - 4 * t, t, 4 * t, C["wood"]),
           rect(x + t * 0.7, base - 4 * t, 2, 4 * t, C["dirt_dk"])]
    for (dx, dy, w) in [(-1, -6, 3), (-2, -5, 5), (-2, -4, 5), (-1, -7, 3)]:
        out.append(rect(x + dx * t, base + dy * t + 2 * t - 2 * t, w * t, t, C["leaf"] if dy % 2 else C["grass"]))
    return "".join(out)


def stars(w, h, n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rng.randrange(8, w - 8, 4), rng.randrange(6, h, 4)
        s = rng.choice([2, 2, 4])
        out.append(rect(x, y, s, s, "#FFFFFF", f' opacity="{rng.choice([0.25, 0.4, 0.6])}"'))
    return "".join(out)


def ground(w, y, depth_h, seed=3):
    """Grass strip over dirt with stone/ore speckles."""
    rng = random.Random(seed)
    out = [rect(0, y, w, depth_h, C["dirt"]), rect(0, y, w, 12, C["grass"])]
    for x in range(0, w, 12):
        out.append(rect(x, y, 12, 4, C["grass_hi"] if (x // 12) % 3 == 0 else C["grass"]))
        out.append(rect(x, y + 12, 12, 4 + ((x // 12) * 7 % 3) * 4, C["dirt_dk"] if (x // 12) % 2 else C["dirt"]))
    for _ in range(w // 22):
        x, y2 = rng.randrange(0, w, 6), rng.randrange(y + 22, y + depth_h - 6, 6)
        out.append(rect(x, y2, 12, 6, C["stone"] if rng.random() > 0.2 else C["diamond"], ' opacity="0.8"'))
    return "".join(out)


# ---------------------------------------------------------------- hero
def hero():
    w, h = 1000, 300
    s = [svg_open(w, h, "Hamzaul Rahman \u2014 Data Analyst, AI & Data Science",
                  "Pixel-art night landscape with the name, role and a hotbar of material blocks."),
         '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{C["obsidian"]}"/><stop offset="1" stop-color="#1D2A2A"/></linearGradient></defs>',
         f'<rect width="{w}" height="{h}" fill="url(#sky)"/>', stars(w, 200, 46, 11)]
    s.append(rect(868, 28, 36, 36, "#E9EEE9") + rect(868, 28, 36, 4, "#FFFFFF") + rect(900, 28, 4, 36, "#C8CFC8"))
    s.append(hills(w, 238, 10, 70, 40, "#16251A", 80))
    s.append(hills(w, 238, 10, 46, 170, "#1E3A1E", 52))
    for tx, sc in ((60, 1), (150, 1), (860, 1), (940, 1), (30, 1)):
        s.append(tree(tx, 238, sc))
    s.append(ground(w, 236, 64))
    s.append(f'<rect x="0" y="0" width="{w}" height="4" fill="{C["emerald"]}"/>')
    s.append(px.pixel_text(w / 2, 52, "HAMZAUL RAHMAN", 7, C["text"], anchor="middle"))
    s.append(px.pixel_text(w / 2, 118, "DATA ANALYST", 4, C["emerald"], anchor="middle"))
    s.append(px.pixel_text(w / 2, 156, "AI & DATA SCIENCE", 3, C["diamond"], anchor="middle"))
    s.append(px.pixel_text(w / 2 - 6, 196, "WELCOME TO MY WORLD", 2, C["dim"], anchor="middle"))
    s.append(f'<rect x="{w / 2 + px.text_width("WELCOME TO MY WORLD", 2) / 2 + 2}" y="196" width="10" height="14" fill="{C["emerald"]}" class="cursor"/>')
    # hotbar of material blocks (decorative palette, carries no data)
    mats = [C["grass"], C["dirt"], C["stone"], C["wood"], C["gold"], C["emerald"], C["diamond"], C["amethyst"], C["redstone"]]
    hx = (w - (9 * 34 + 8 * 4)) / 2
    for i, m in enumerate(mats):
        sx = hx + i * 38
        s.append(rect(sx - 2, 250, 38, 38, "#050605") + rect(sx, 252, 34, 34, "#1F211F"))
        s.append(rect(sx, 284, 34, 2, "#3E433F") + rect(sx + 32, 252, 2, 34, "#3E433F"))
        s.append(px.grass_sprite(sx + 5, 257, 3) if i == 0 else px.block_sprite(m, sx + 5, 257, 3))
    s.append(rect(hx - 4, 248, 9 * 38 + 4, 2, C["emerald"], ' opacity="0.9"'))
    s.append('<style>@media (prefers-reduced-motion:no-preference){.cursor{animation:b 1s steps(1) infinite}'
             '@keyframes b{50%{opacity:0}}}</style></svg>')
    return "".join(s)


# ------------------------------------------------------------- divider
def divider():
    w, h, bs = 1200, 12, 12
    seq = [C["grass"], C["grass_hi"], C["dirt"], C["stone"], C["dirt"], C["grass"], C["leaf"], C["stone"]]
    n = w // bs
    s = [svg_open(w, h, "Divider", "Row of pixel blocks fading out at both ends.")]
    for i in range(n):
        dist = abs(i - n / 2) / (n / 2)
        op = max(0.0, min(1.0, 1.15 - dist * 1.25))
        if op <= 0.03:
            continue
        col = seq[i % len(seq)]
        s.append(rect(i * bs, 0, bs, h, col, f' opacity="{op:.2f}"'))
        s.append(rect(i * bs, 0, bs, 2, "#FFFFFF", f' opacity="{op * 0.2:.2f}"'))
        s.append(rect(i * bs, h - 2, bs, 2, "#000000", f' opacity="{op * 0.3:.2f}"'))
    mid = n // 2
    s.append(px.gem_sprite(C["emerald"], mid * bs - 2, 2, 1))
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------ game thumbnail
def cave_scene(w, h, seed=5):
    rng = random.Random(seed)
    s = [f'<rect width="{w}" height="{h}" fill="#17181A"/>']
    for y in range(0, h, 20):
        for x in range(0, w, 20):
            g = rng.choice(["#1C1E1D", "#202221", "#191B1A", "#232524"])
            s.append(rect(x, y, 20, 20, g))
            s.append(rect(x, y, 20, 1, "#FFFFFF", ' opacity="0.04"'))
    return "".join(s), rng


def torch(x, y):
    return (rect(x + 3, y + 8, 4, 18, C["wood"]) + rect(x + 1, y + 2, 8, 8, C["gold"])
            + rect(x + 3, y, 4, 4, "#FFF3B0") + rect(x - 6, y - 6, 22, 40, C["gold"], ' opacity="0.07"'))


def thumbnail():
    w, h = 900, 300
    body, rng = cave_scene(w, h)
    s = [svg_open(w, h, "Mining Expedition", "Pixel-art cave with ore blocks, torches and the game title."), body]
    s.append(rect(0, 236, w, 64, C["stone_dk"]))
    for x in range(0, w, 20):
        s.append(rect(x, 236, 20, 4, C["stone"], ' opacity="0.7"'))
        s.append(rect(x, 244 + (x // 20 % 3) * 4, 20, 8, "#3C403D"))
    for ox, oy, col in ((70, 250, C["diamond"]), (170, 262, C["emerald"]), (770, 254, C["gold"]),
                        (840, 266, C["redstone"]), (690, 262, C["diamond"])):
        s.append(px.block_sprite(col, ox, oy, 3))
    for tx in (36, 862):
        s.append(torch(tx, 120))
    s.append(px.pixel_text(w / 2, 64, "MINING EXPEDITION", 6, C["text"], anchor="middle"))
    s.append(px.pixel_text(w / 2, 122, "YOU ARE THE EXPEDITION LEAD", 3, C["emerald"], anchor="middle"))
    s.append(px.pixel_text(w / 2, 158, "MAKE THE CALL", 3, C["dim"], anchor="middle"))
    # tool tier row
    tiers = [("GOLD", C["gold"]), ("IRON", "#D8DBD8"), ("DIAMOND", C["diamond"]), ("AQUA", "#3C8DFF")]
    cx = (w - (4 * 134 + 3 * 14)) / 2
    for i, (n, col) in enumerate(tiers):
        x = cx + i * 148
        s.append(rect(x - 2, 188, 138, 38, "#050605") + rect(x, 190, 134, 34, "#1B1D1C"))
        s.append(rect(x, 222, 134, 2, "#3E433F"))
        s.append(px.pickaxe_sprite(col, x + 6, 194, 3))
        s.append(px.pixel_text(x + 38, 202, n, 2, col))
    s.append(rect(0, 0, w, 4, C["emerald"]))
    s.append("</svg>")
    return "".join(s)


# ------------------------------------------------------- social preview
def social():
    w, h = 1200, 630
    s = [svg_open(w, h, "Hamzaul Rahman \u2014 Data Analyst, AI & Data Science",
                  "Minecraft-inspired developer portfolio preview."),
         '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{C["obsidian"]}"/><stop offset="1" stop-color="#1D2A2A"/></linearGradient></defs>',
         f'<rect width="{w}" height="{h}" fill="url(#sky)"/>', stars(w, 330, 70, 21)]
    s.append(rect(1040, 56, 56, 56, "#E9EEE9") + rect(1040, 56, 56, 6, "#FFFFFF") + rect(1090, 56, 6, 56, "#C8CFC8"))
    s.append(hills(w, 470, 10, 120, 60, "#16251A", 130))
    s.append(hills(w, 470, 10, 80, 210, "#1E3A1E", 80))
    for tx in (60, 140, 1050, 1120, 1000, 30):
        s.append(tree(tx, 470, 2))
    s.append(ground(w, 468, 162, 9))
    s.append(rect(0, 0, w, 8, C["emerald"]))
    s.append(px.pixel_text(90, 120, "HAMZAUL", 14, C["text"]))
    s.append(px.pixel_text(90, 236, "RAHMAN", 14, C["text"]))
    s.append(px.pixel_text(94, 366, "DATA ANALYST", 6, C["emerald"]))
    s.append(px.pixel_text(94, 426, "AI & DATA SCIENCE", 4, C["diamond"]))
    # hotbar
    mats = [C["grass"], C["dirt"], C["stone"], C["wood"], C["gold"], C["emerald"], C["diamond"], C["amethyst"], C["redstone"]]
    hx = 90
    for i, m in enumerate(mats):
        sx = hx + i * 64
        s.append(rect(sx - 3, 520, 62, 62, "#050605") + rect(sx, 523, 56, 56, "#1F211F"))
        s.append(rect(sx, 575, 56, 4, "#3E433F") + rect(sx + 52, 523, 4, 56, "#3E433F"))
        s.append(px.grass_sprite(sx + 8, 531, 5) if i == 0 else px.block_sprite(m, sx + 8, 531, 5))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------- favicon
def favicon():
    s = [svg_open(64, 64, "Favicon", "Pixel grass block."), rect(0, 0, 64, 64, "#0E0D14"),
         px.grass_sprite(4, 4, 7), "</svg>"]
    return "".join(s)


def write(path, content):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print("wrote", path.relative_to(ROOT))
    return path


def to_png(svg_path, png_path, width=None, height=None):
    try:
        import cairosvg
    except ImportError:
        print("  (skipped PNG: pip install cairosvg)")
        return
    cairosvg.svg2png(url=str(svg_path), write_to=str(ROOT / png_path), output_width=width, output_height=height)
    print("wrote", png_path)


def main():
    write("assets/minecraft-hero.svg", hero())
    write("assets/pixel-divider.svg", divider())
    write("assets/game-thumbnail.svg", thumbnail())
    sp = write("pit-strategy/assets/social-preview.svg", social())
    to_png(sp, "pit-strategy/assets/social-preview.png", 1200, 630)
    fv = write("pit-strategy/assets/favicon.svg", favicon())
    to_png(fv, "pit-strategy/assets/favicon-32.png", 32, 32)
    to_png(fv, "pit-strategy/assets/apple-touch-icon.png", 180, 180)


if __name__ == "__main__":
    main()
