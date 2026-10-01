"""Build 'BlockPix', an original pixel font, from the 5x7 glyph grid in pixelfont.py.

    python scripts/build_font.py          # needs: pip install fonttools

Output: pit-strategy/assets/fonts/blockpix.woff

Every glyph is a set of square contours drawn from the hand-authored bitmaps,
so the font is original work and ships with the repo (no third-party font CDN).
Lowercase letters map to the same shapes as uppercase.
"""

import sys
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pixelfont as px  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "pit-strategy" / "assets" / "fonts" / "blockpix.woff"

PX = 100            # font units per pixel
ROWS, COLS = 7, 5
ASCENT, DESCENT = 800, -200
ADVANCE = 600
SPACE = 400


def glyph_for(rows):
    pen = TTGlyphPen(None)
    for r, row in enumerate(rows):
        c = 0
        width = len(row)
        while c < width:
            if row[c] != "1":
                c += 1
                continue
            start = c
            while c < width and row[c] == "1":
                c += 1
            x0, x1 = start * PX, c * PX
            y1 = (ROWS - r) * PX          # row 0 is the top of the glyph
            y0 = y1 - PX
            pen.moveTo((x0, y0))          # clockwise = filled in TrueType
            pen.lineTo((x0, y1))
            pen.lineTo((x1, y1))
            pen.lineTo((x1, y0))
            pen.closePath()
    return pen.glyph()


def main():
    names = [".notdef", "space"]
    cmap = {0x20: "space", 0xA0: "space"}
    glyphs = {".notdef": None, "space": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (ADVANCE, 0), "space": (SPACE, 0)}

    def add(codepoint, name, rows):
        if name not in glyphs:
            names.append(name)
            glyphs[name] = glyph_for(rows)
            metrics[name] = (px.advance(chr(codepoint)) * PX, 0)
        cmap[codepoint] = name

    for ch, rows in px.GLYPHS.items():
        name = f"u{ord(ch):04X}"
        add(ord(ch), name, rows)
        if ch.isalpha():
            cmap[ord(ch.lower())] = name

    # .notdef: hollow box
    glyphs[".notdef"] = glyph_for(["11111", "10001", "10001", "10001", "10001", "10001", "11111"])  # hollow box, 5 wide

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable({"familyName": "BlockPix", "styleName": "Regular",
                       "uniqueFontIdentifier": "BlockPix-Regular", "fullName": "BlockPix Regular",
                       "psName": "BlockPix-Regular"})
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT, usWinAscent=ASCENT, usWinDescent=-DESCENT,
                sxHeight=700, sCapHeight=700)
    fb.setupPost()
    fb.font.flavor = "woff"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fb.save(str(OUT))
    print("wrote", OUT.relative_to(ROOT), OUT.stat().st_size, "bytes,", len(cmap), "codepoints")


if __name__ == "__main__":
    main()
