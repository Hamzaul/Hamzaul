"""Tiny 5x7 bitmap font + sprite helpers shared by the SVG generators.

Why this exists: SVGs shown through <img> on GitHub cannot load web fonts, so
"Minecraft-style" lettering is drawn as filled pixels instead of text. Every
glyph below is hand-authored; nothing is copied from a game asset or font.
"""

GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "00110", "00100", "01000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "/": ["00001", "00001", "00010", "00100", "01000", "10000", "10000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    ">": ["10000", "01000", "00100", "00010", "00100", "01000", "10000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "|": ["00100", "00100", "00100", "00100", "00100", "00100", "00100"],
    "*": ["00000", "10101", "01110", "11111", "01110", "10101", "00000"],
    "#": ["01010", "01010", "11111", "01010", "11111", "01010", "01010"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "[": ["01110", "01000", "01000", "01000", "01000", "01000", "01110"],
    "]": ["01110", "00010", "00010", "00010", "00010", "00010", "01110"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    "<": ["00001", "00010", "00100", "01000", "00100", "00010", "00001"],
    "\u00b7": ["00000", "00000", "00000", "01100", "01100", "00000", "00000"],
    "\u2014": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
}
SPACE_ADVANCE = 4


def _trim(rows):
    """Drop empty columns on both sides so narrow glyphs (I, ., :, !) stay narrow."""
    used = [c for c in range(5) if any(r[c] == "1" for r in rows)]
    if not used:
        return rows
    lo, hi = min(used), max(used)
    return [r[lo:hi + 1] for r in rows]


GLYPHS = {ch: _trim(rows) for ch, rows in GLYPHS.items()}


def advance(ch):
    """Horizontal advance of a glyph in pixels: its width plus 1px spacing."""
    if ch == " ":
        return SPACE_ADVANCE
    return len(GLYPHS.get(ch, GLYPHS["?"])[0]) + 1


def text_width(text, scale):
    total = sum(advance(ch) for ch in text.upper())
    return max(total - 1, 0) * scale


def _glyph_path(text, x, y, scale):
    """One SVG path 'd' string; horizontal runs of pixels are merged."""
    d = []
    cx = x
    for ch in text.upper():
        if ch == " ":
            cx += SPACE_ADVANCE * scale
            continue
        rows = GLYPHS.get(ch, GLYPHS["?"])
        for r, row in enumerate(rows):
            c = 0
            width = len(row)
            while c < width:
                if row[c] == "1":
                    start = c
                    while c < width and row[c] == "1":
                        c += 1
                    d.append(f"M{cx + start * scale:g} {y + r * scale:g}"
                             f"h{(c - start) * scale:g}v{scale:g}h{-(c - start) * scale:g}z")
                else:
                    c += 1
        cx += advance(ch) * scale
    return "".join(d)


def pixel_text(x, y, text, scale=2, fill="#F1F1EA", shadow="#000000",
               anchor="start", shadow_offset=None):
    """Return SVG for pixel lettering. y is the TOP of the glyph row."""
    w = text_width(text, scale)
    if anchor == "middle":
        x = x - w / 2
    elif anchor == "end":
        x = x - w
    off = scale if shadow_offset is None else shadow_offset
    out = []
    if shadow:
        out.append(f'<path d="{_glyph_path(text, x + off, y + off, scale)}" fill="{shadow}"/>')
    out.append(f'<path d="{_glyph_path(text, x, y, scale)}" fill="{fill}"/>')
    return "".join(out)


# ---------------------------------------------------------------------------
# 8x8 sprites. Palette letters map to colours per sprite.
# ---------------------------------------------------------------------------

GEM = ["..aaaa..",
       ".abbbba.",
       "abbbbbca",
       "abbbbbca",
       ".abbbca.",
       "..abca..",
       "...aa...",
       "........"]

HEART = [".aa..aa.",
         "abbaabba",
         "abbbbbba",
         "abbbbbca",
         ".abbbca.",
         "..abca..",
         "...aa...",
         "........"]

BLOCK = ["aaaaaaaa",
         "abbbbbbc",
         "abbbbbbc",
         "abbbbbbc",
         "abbbbbbc",
         "abbbbbbc",
         "abbbbbbc",
         "acccccc."]

GRASS = ["gggggggg",
         "gGgggGgg",
         "dgdgddgd",
         "dddddddd",
         "ddDdddDd",
         "dddddddd",
         "dDdddDdd",
         "dddddddd"]

PICKAXE = ["..aaaaa.",
           ".abbbbba",
           "abb..cbb",
           "ab..cc.b",
           "...cc...",
           "..cc....",
           ".cc.....",
           "cc......"]


def sprite(rows, palette, x, y, scale=4):
    """Render a sprite as merged rects. palette: {letter: colour}."""
    out = []
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            ch = row[c]
            if ch == "." or ch not in palette:
                c += 1
                continue
            start = c
            while c < len(row) and row[c] == ch:
                c += 1
            out.append(f'<rect x="{x + start * scale:g}" y="{y + r * scale:g}" '
                       f'width="{(c - start) * scale:g}" height="{scale:g}" fill="{palette[ch]}"/>')
    return "".join(out)


def shade(hex_color, factor):
    """Lighten (factor>1) or darken (factor<1) a #RRGGBB colour."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if factor >= 1:
        r, g, b = (round(v + (255 - v) * (factor - 1)) for v in (r, g, b))
    else:
        r, g, b = (round(v * factor) for v in (r, g, b))
    return f"#{max(0, min(255, r)):02X}{max(0, min(255, g)):02X}{max(0, min(255, b)):02X}"


def gem_sprite(color, x, y, scale=4):
    pal = {"a": shade(color, 0.55), "b": color, "c": shade(color, 1.55)}
    return sprite(GEM, pal, x, y, scale)


def heart_sprite(color, x, y, scale=4):
    pal = {"a": shade(color, 0.5), "b": color, "c": shade(color, 0.75)}
    return sprite(HEART, pal, x, y, scale)


def block_sprite(color, x, y, scale=4):
    pal = {"a": shade(color, 1.35), "b": color, "c": shade(color, 0.6)}
    return sprite(BLOCK, pal, x, y, scale)


def grass_sprite(x, y, scale=4):
    pal = {"g": "#5B8731", "G": "#79B13D", "d": "#7A5230", "D": "#5E3E22"}
    return sprite(GRASS, pal, x, y, scale)


def pickaxe_sprite(head, x, y, scale=4):
    pal = {"a": shade(head, 0.6), "b": head, "c": "#7A5230"}
    return sprite(PICKAXE, pal, x, y, scale)
