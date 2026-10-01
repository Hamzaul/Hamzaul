"""World Activity dashboard generator (Minecraft edition).

Pipeline (unchanged from the original design):
    GitHub GraphQL API  ->  compute_stats()  ->  render()  ->  assets/world-activity.svg

Run by .github/workflows/minecraft-dashboard.yml with GH_TOKEN in the environment.

Local use:
    python scripts/dashboard.py                  # real data (needs GH_TOKEN, e.g. in .env)
    python scripts/dashboard.py --placeholder    # empty "first sync pending" world, no token
    python scripts/dashboard.py --demo --out preview.svg   # synthetic data for design QA only

Data semantics: the GitHub contribution calendar counts commits AND issues,
pull requests and reviews. This dashboard therefore calls the number "XP"
or "contributions" -- never "commits".
"""

import argparse
import datetime
import math
import os
import random
import sys
from pathlib import Path

import requests

try:  # python-dotenv is in requirements.txt; tolerate its absence for --demo runs
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*_a, **_k):
        return False

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pixelfont as px  # noqa: E402

load_dotenv()

OUTPUT_PATH = os.path.join("assets", "world-activity.svg")

PROFILE = {
    "name": "Hamzaul Rahman",
    "tagline": "Aspiring Data Analyst \u2014 Power BI \u00b7 Python \u00b7 EDA",
    "github_username": "Hamzaul",

    # Inventory: skills grouped by category (carried over unchanged from the
    # original dashboard configuration). Colour follows the rarity palette.
    "skills": {
        "LANGUAGES": ["Python", "Java", "C"],
        "DATA ANALYTICS": ["Pandas", "NumPy", "Matplotlib", "Seaborn", "EDA", "Regression", "Statistics"],
        "BI TOOLS": ["Power BI", "DAX", "Excel", "Pivot Tables", "XLOOKUP"],
        "DATABASES": ["MySQL", "MongoDB"],
        "DEV TOOLS": ["Git", "GitHub"],
    },

    # Personal yearly XP target, chosen by the profile owner. It is a goal
    # shown on the XP bar, NOT a value calculated from GitHub.
    "goal": 3000,

    # Deliberately excluded: phone number and email. This SVG sits in a public
    # README, and a hardcoded phone number there is spam-bait.

    # Featured builds. Statistics here are the owner's own project figures
    # (carried over unchanged from the original dashboard configuration).
    # rarity: common | uncommon | rare | epic | legendary
    "highlights": [
        {
            "title": "PhonePe Transaction Analysis",
            "stack": "Power BI \u00b7 DAX",
            "stat_value": "300K+",
            "stat_label": "TRANSACTIONS",
            "detail": "\u20b93.47bn value \u00b7 96% success rate",
            "rarity": "rare",
        },
        {
            "title": "Car Models Analysis",
            "stack": "Power BI",
            "stat_value": "337 HP",
            "stat_label": "AVG HORSEPOWER",
            "detail": "~$58K avg price, cross-brand comparison",
            "rarity": "uncommon",
        },
        {
            "title": "Student Performance Analysis",
            "stack": "Python \u00b7 Pandas \u00b7 Seaborn",
            "stat_value": "74.8",
            "stat_label": "AVG SCORE",
            "detail": "100 records \u00b7 correlation heatmaps",
            "rarity": "uncommon",
        },
    ],
}

USERNAME = PROFILE["github_username"]
GOAL = PROFILE["goal"]
W = 800

QUERY = """
query($login:String!) {
  user(login:$login) {
    name
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node { name color }
          }
        }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
"""

# --------------------------------------------------------------------------
# Design tokens
# --------------------------------------------------------------------------

C = {
    "bg": "#101211",
    "panel": "#1B1D1C",
    "panel_alt": "#222523",
    "black": "#050605",
    "bevel_hi": "#3E433F",
    "bevel_lo": "#0C0D0C",
    "text": "#F1F1EA",
    "dim": "#9AA09A",
    "faint": "#5C625D",
    "grass": "#5B8731",
    "leaf": "#3F6B22",
    "dirt": "#7A5230",
    "wood": "#9C6B3A",
    "stone": "#7F8580",
    "emerald": "#17DD62",
    "diamond": "#5DECEC",
    "gold": "#FAC846",
    "redstone": "#D1342A",
    "amethyst": "#8B3FD9",
    "iron": "#D8DBD8",
    "xp": "#7CFC3A",
}

RARITY = {
    "common": C["dim"],
    "uncommon": C["emerald"],
    "rare": C["diamond"],
    "epic": C["amethyst"],
    "legendary": C["gold"],
}

# Contribution "ore" scale for the chunk map, low -> high.
CHUNK_SCALE = ["#2A2D2B", C["dirt"], C["grass"], C["emerald"], C["diamond"]]
CHUNK_NAMES = ["EMPTY", "DIRT", "GRASS", "EMERALD", "DIAMOND"]

# Milestone tiers, mirroring the pickaxe tiers used in the game.
TIERS = [("STONE", "#9AA09A"), ("IRON", "#D8DBD8"), ("GOLD", C["gold"]), ("DIAMOND", C["diamond"])]

FONT_UI = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
FONT_MONO = "'SF Mono', Consolas, Menlo, 'DejaVu Sans Mono', monospace"


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------
# Data fetch
# --------------------------------------------------------------------------

def fetch_user(token):
    if not token:
        print("ERROR: GH_TOKEN is not set. Add it to .env locally or as the GH_TOKEN Actions secret.")
        sys.exit(1)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            "https://api.github.com/graphql",
            json={"query": QUERY, "variables": {"login": USERNAME}},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:  # network / HTTP errors
        print(f"ERROR: API request failed: {e}")
        sys.exit(1)

    if "data" not in data or data["data"] is None or data["data"]["user"] is None:
        print("ERROR: GitHub API returned unexpected response:")
        print(data)
        sys.exit(1)
    return data["data"]["user"]


def _calendar(weeks_of_counts, today):
    """Build a GraphQL-shaped contribution calendar ending at `today`."""
    sunday = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
    weeks = []
    for w in range(len(weeks_of_counts)):
        start = sunday - datetime.timedelta(weeks=len(weeks_of_counts) - 1 - w)
        days = []
        for d in range(7):
            date = start + datetime.timedelta(days=d)
            if date > today:
                continue
            days.append({"contributionCount": weeks_of_counts[w][d], "date": date.isoformat(), "weekday": d})
        weeks.append({"contributionDays": days})
    return weeks


def placeholder_user():
    """Empty world: used for the committed 'first sync pending' asset."""
    today = datetime.date.today()
    return {
        "followers": {"totalCount": 0},
        "repositories": {"totalCount": 0, "nodes": []},
        "contributionsCollection": {"contributionCalendar": {
            "totalContributions": 0,
            "weeks": _calendar([[0] * 7 for _ in range(53)], today),
        }},
    }


def demo_user():
    """Synthetic data for visual QA ONLY. Never committed as the live asset."""
    rng = random.Random(7)
    today = datetime.date.today()
    counts = [[(rng.choice([0, 0, 1, 2, 3, 5, 8]) if rng.random() > 0.35 else 0) for _ in range(7)] for _ in range(53)]
    langs = [("Python", "#3572A5", 520), ("Jupyter Notebook", "#DA5B0B", 300), ("JavaScript", "#F1E05A", 180),
             ("HTML", "#E34C26", 90), ("CSS", "#563D7C", 40), ("Shell", "#89E051", 10), ("Batchfile", "#C1F12E", 5)]
    return {
        "followers": {"totalCount": 12},
        "repositories": {"totalCount": 14, "nodes": [{"languages": {"edges": [
            {"size": s, "node": {"name": n, "color": c}} for n, c, s in langs]}}]},
        "contributionsCollection": {"contributionCalendar": {
            "totalContributions": sum(map(sum, counts)),
            "weeks": _calendar(counts, today),
        }},
    }


# --------------------------------------------------------------------------
# Stat computation
# --------------------------------------------------------------------------

MONTHS_FULL = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST",
               "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]
MONTHS_ABBR = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def compute_stats(user, last_updated=None):
    today = datetime.date.today()
    year, month = today.year, today.month

    followers = user["followers"]["totalCount"] or 0
    repos = user["repositories"]["totalCount"] or 0
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]

    all_days = sorted(
        ((d["date"], d["contributionCount"], d["weekday"]) for w in weeks for d in w["contributionDays"]),
        key=lambda t: t[0],
    )
    dated = [(datetime.date.fromisoformat(s), c) for s, c, _ in all_days]

    # XP = contributions (commits + issues + PRs + reviews) in the current year
    xp = sum(c for d, c in dated if d.year == year)
    xp_month = sum(c for d, c in dated if d.year == year and d.month == month)
    active_days = sum(1 for d, c in dated if d.year == year and c > 0)
    avg_per_day = round(xp / max(active_days, 1), 1)
    best_day = max((c for d, c in dated if d.year == year), default=0)

    longest, run = 0, 0
    for _, c in dated:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)

    current_streak = 0
    for d, c in reversed(dated):
        if d > today:
            continue
        if c > 0:
            current_streak += 1
        elif d == today:
            continue  # today may legitimately still be at 0
        else:
            break

    week_start = today - datetime.timedelta(days=today.weekday())
    this_week = sum(c for d, c in dated if d >= week_start)

    monthly = {m: 0 for m in range(1, month + 1)}
    for d, c in dated:
        if d.year == year and d.month <= month:
            monthly[d.month] += c
    month_vals = [monthly[m] for m in range(1, month + 1)]

    lang_totals, lang_colors = {}, {}
    for repo in user["repositories"]["nodes"]:
        if repo and repo.get("languages"):
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                lang_totals[name] = lang_totals.get(name, 0) + edge["size"]
                lang_colors[name] = edge["node"].get("color") or "#888888"
    total_lang = sum(lang_totals.values()) or 1
    ranked = sorted(lang_totals.items(), key=lambda kv: kv[1], reverse=True)
    lang_list = [(n, s / total_lang * 100, lang_colors[n]) for n, s in ranked[:5]]
    rest = sum(s for _, s in ranked[5:])
    if rest > 0:
        lang_list.append(("Others", rest / total_lang * 100, C["faint"]))
    top_language = ranked[0][0] if ranked else "N/A"

    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    stamp = last_updated or datetime.datetime.now(ist).strftime("%b %d, %Y  %I:%M %p IST")

    return dict(
        today=today, year=year, month=month, month_name=MONTHS_FULL[month - 1],
        followers=followers, repos=repos, weeks=weeks,
        xp=xp, xp_month=xp_month, active_days=active_days, avg_per_day=avg_per_day,
        best_day=best_day, longest_streak=longest, current_streak=current_streak,
        this_week=this_week, month_vals=month_vals, lang_list=lang_list,
        top_language=top_language, progress=min(xp / max(GOAL, 1), 1.0), last_updated=stamp,
    )


# --------------------------------------------------------------------------
# Drawing helpers
# --------------------------------------------------------------------------

def notch(x, y, w, h, n):
    return (f"M{x + n} {y}H{x + w - n}V{y + n}H{x + w}V{y + h - n}H{x + w - n}V{y + h}"
            f"H{x + n}V{y + h - n}H{x}V{y + n}H{x + n}Z")


def panel(x, y, w, h, fill=None):
    """Pixel-bevelled UI panel with notched corners."""
    fill = fill or C["panel"]
    return (
        f'<path d="{notch(x, y, w, h, 4)}" fill="{C["black"]}"/>'
        f'<path d="{notch(x + 3, y + 3, w - 6, h - 6, 3)}" fill="{fill}"/>'
        f'<rect x="{x + 6}" y="{y + 3}" width="{w - 12}" height="2" fill="{C["bevel_hi"]}"/>'
        f'<rect x="{x + 3}" y="{y + 6}" width="2" height="{h - 12}" fill="{C["bevel_hi"]}"/>'
        f'<rect x="{x + 6}" y="{y + h - 5}" width="{w - 12}" height="2" fill="{C["bevel_lo"]}"/>'
        f'<rect x="{x + w - 5}" y="{y + 6}" width="2" height="{h - 12}" fill="{C["bevel_lo"]}"/>'
    )


def slot(x, y, size, border=None):
    """Inventory slot: dark top-left edge, light bottom-right edge."""
    b = border or C["bevel_hi"]
    return (
        f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="#0B0C0B"/>'
        f'<rect x="{x + 2}" y="{y + 2}" width="{size - 4}" height="{size - 4}" fill="#171918"/>'
        f'<rect x="{x}" y="{y + size - 2}" width="{size}" height="2" fill="{b}"/>'
        f'<rect x="{x + size - 2}" y="{y}" width="2" height="{size}" fill="{b}"/>'
    )


def text(x, y, value, size=13, fill=None, weight=400, anchor="start", family=None, spacing=0):
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x:g}" y="{y:g}" font-family="{family or FONT_UI}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill or C["text"]}" text-anchor="{anchor}"{sp}>{esc(value)}</text>')


def mono(x, y, value, size=12, fill=None, weight=400, anchor="start"):
    return text(x, y, value, size, fill or C["dim"], weight, anchor, FONT_MONO)


def section_title(x, y, label, sub=None):
    s = [f'<rect x="{x}" y="{y + 3}" width="8" height="8" fill="{C["emerald"]}"/>',
         px.pixel_text(x + 16, y, label, 2, C["text"])]
    if sub:
        s.append(mono(x + 16 + px.text_width(label, 2) + 14, y + 12, sub, 12, C["dim"]))
    return "".join(s)


def seam_overlay(x, y, w, h):
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="url(#seam)"/>'


def block_bar(x, y, w, h, color):
    """Solid bar with block seams and a lit top edge (reads as stacked blocks)."""
    w = max(w, 2)
    return (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{color}"/>'
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="2" fill="{px.shade(color, 1.45)}"/>'
            f'{seam_overlay(x, y, w, h)}')


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------

def draw_header(stats, x, y, w, h):
    s = [panel(x, y, w, h)]
    # grass-and-dirt strip along the top edge
    i, bx = 0, x + 6
    while bx < x + w - 6:
        bw = min(10, x + w - 6 - bx)
        s.append(f'<rect x="{bx}" y="{y + 4}" width="{bw}" height="6" fill="{C["grass"] if i % 3 else C["leaf"]}"/>')
        drip = 4 + (i * 5 % 3) * 3
        s.append(f'<rect x="{bx}" y="{y + 10}" width="{bw}" height="{drip}" fill="{C["dirt"]}"/>')
        bx += 10
        i += 1
    s.append(px.grass_sprite(x + 24, y + 40, 6))
    s.append(px.pixel_text(x + 86, y + 42, "WORLD ACTIVITY", 4, C["text"]))
    s.append(px.pixel_text(x + 86, y + 78, PROFILE["name"].upper(), 2, C["emerald"]))
    s.append(mono(x + 86, y + 110, PROFILE["tagline"].upper(), 12, C["dim"]))
    rx = x + w - 214
    s.append(px.pixel_text(rx, y + 44, "LAST SYNC", 2, C["dim"]))
    s.append(mono(rx, y + 76, stats["last_updated"], 12, C["text"], 700))
    return "".join(s)


def draw_xp(stats, x, y, w, h):
    s = [panel(x, y, w, h)]
    bx, bw, by, bh = x + 24, w - 48, y + 52, 16
    s.append(px.pixel_text(x + 24, y + 20, f"XP {stats['year']}", 2, C["dim"]))
    s.append(px.pixel_text(x + w - 24, y + 20, f"TARGET {GOAL:,}", 2, C["dim"], anchor="end"))
    s.append(px.pixel_text(x + w / 2, y + 16, f"{stats['xp']:,}", 3, C["xp"], anchor="middle"))
    # track + segmented fill, like the in-game XP bar
    s.append(f'<rect x="{bx - 2}" y="{by - 2}" width="{bw + 4}" height="{bh + 4}" fill="{C["black"]}"/>')
    s.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="#2E322F"/>')
    fill_w = round(bw * stats["progress"])
    if fill_w > 0:
        s.append(f'<rect x="{bx}" y="{by}" width="{fill_w}" height="{bh}" fill="{C["xp"]}"/>')
        s.append(f'<rect x="{bx}" y="{by}" width="{fill_w}" height="4" fill="{px.shade(C["xp"], 1.5)}"/>')
    seg = bw / 20
    for i in range(1, 20):
        s.append(f'<rect x="{bx + i * seg - 1:.1f}" y="{by}" width="2" height="{bh}" fill="{C["black"]}" opacity="0.55"/>')
    for frac in (0.25, 0.5, 0.75):
        tx = bx + bw * frac
        s.append(mono(tx, by + bh + 17, f"{round(GOAL * frac):,}", 11, C["faint"], anchor="middle"))
    pct = int(stats["progress"] * 100)
    s.append(mono(bx, by + bh + 17, f"{pct}%", 11, C["dim"]))
    s.append(mono(bx + bw, by + bh + 17, "personal yearly target", 11, C["faint"], anchor="end"))
    return "".join(s)


def draw_stat_cards(stats, x, y, w):
    gap, cols, ch = 10, 4, 76
    cw = (w - gap * (cols - 1)) / cols
    cards = [
        ("XP EARNED", f"{stats['xp']:,}", f"contributions in {stats['year']}", C["emerald"], "gem"),
        ("BEST DAY", str(stats["best_day"]), "most in a single day", C["diamond"], "gem"),
        ("STREAK", str(stats["current_streak"]), "days in a row, live", C["gold"], "block"),
        ("BEST RUN", str(stats["longest_streak"]), "longest streak, days", C["amethyst"], "block"),
        ("BUILDS", str(stats["repos"]), "owned repositories", C["leaf"], "grass"),
        ("PARTY", str(stats["followers"]), "followers", C["redstone"], "heart"),
        ("AVG/DAY", str(stats["avg_per_day"]), "per active day", C["stone"], "block"),
        ("THIS WEEK", str(stats["this_week"]), "contributions", C["wood"], "block"),
    ]
    out = []
    for i, (label, value, sub, col, icon) in enumerate(cards):
        cx = x + (i % cols) * (cw + gap)
        cy = y + (i // cols) * (ch + gap)
        out.append(panel(cx, cy, cw, ch, C["panel_alt"]))
        out.append(slot(cx + 12, cy + 14, 48))
        ix, iy = cx + 12 + 8, cy + 14 + 8
        if icon == "gem":
            out.append(px.gem_sprite(col, ix, iy, 4))
        elif icon == "heart":
            out.append(px.heart_sprite(col, ix, iy, 4))
        elif icon == "grass":
            out.append(px.grass_sprite(ix, iy, 4))
        else:
            out.append(px.block_sprite(col, ix, iy, 4))
        out.append(px.pixel_text(cx + 70, cy + 12, label, 2, C["dim"]))
        vcol = col if col not in (C["leaf"], C["stone"], C["wood"]) else C["text"]
        out.append(px.pixel_text(cx + 70, cy + 31, value, 3, vcol))
        out.append(text(cx + 70, cy + 68, sub, 11, C["faint"]))
    return "".join(out)


def draw_chunk_map(stats, x, y, w, h):
    s = [panel(x, y, w, h), section_title(x + 24, y + 22, "CHUNK MAP")]
    s.append(mono(x + 24, y + 58, "contributions per day, last 52 weeks (commits, issues, PRs, reviews)", 12, C["dim"]))

    cell, gap = 10, 2
    step = cell + gap
    weeks = stats["weeks"][-52:]
    gx, gy = x + 58, y + 96
    max_val = max((d["contributionCount"] for wk in weeks for d in wk["contributionDays"]), default=0)

    def level(count):
        if count <= 0 or max_val <= 0:
            return 0
        r = count / max_val
        return 1 if r <= 0.25 else 2 if r <= 0.5 else 3 if r <= 0.75 else 4

    # month labels, placed where a new month's first week begins
    last_month, last_x = None, -99
    for wi, wk in enumerate(weeks):
        if not wk["contributionDays"]:
            continue
        d = datetime.date.fromisoformat(wk["contributionDays"][0]["date"])
        if d.month != last_month:
            if wi * step - last_x >= 36:
                s.append(mono(gx + wi * step, gy - 8, MONTHS_ABBR[d.month - 1], 11, C["dim"]))
                last_x = wi * step
            last_month = d.month

    for row, lbl in ((1, "MON"), (3, "WED"), (5, "FRI")):
        s.append(mono(gx - 10, gy + row * step + 9, lbl, 11, C["faint"], anchor="end"))

    for wi, wk in enumerate(weeks):
        col = [f'<g class="col" style="animation-delay:{wi * 0.035:.3f}s">']
        for d in wk["contributionDays"]:
            col.append(f'<use href="#c{level(d["contributionCount"])}" '
                       f'x="{gx + wi * step}" y="{gy + d["weekday"] * step}"/>')
        col.append("</g>")
        s.append("".join(col))

    ly = gy + 7 * step + 16
    s.append(mono(gx, ly + 9, "LESS", 11, C["faint"]))
    for i in range(5):
        s.append(f'<use href="#c{i}" x="{gx + 40 + i * 14}" y="{ly}"/>')
    s.append(mono(gx + 40 + 5 * 14 + 6, ly + 9, "MORE", 11, C["faint"]))
    s.append(mono(x + w - 24, ly + 9, f"ACTIVE DAYS {stats['active_days']}", 11, C["dim"], anchor="end"))
    return "".join(s)


def draw_month_chart(stats, x, y, w, h):
    s = [panel(x, y, w, h), section_title(x + 24, y + 22, "XP BY MONTH")]
    s.append(mono(x + 24, y + 58, f"contributions, {stats['year']}", 12, C["dim"]))

    vals = stats["month_vals"]
    n = max(len(vals), 1)
    mxv = max(max(vals, default=0), 1)
    gx, gy, gw, gh = x + 52, y + 84, w - 52 - 24, 150

    for i in range(5):
        yy = gy + gh - gh * i / 4
        s.append(f'<rect x="{gx}" y="{yy:.1f}" width="{gw}" height="1" fill="#2B2F2C"/>')
        s.append(mono(gx - 8, yy + 4, f"{int(mxv * i / 4)}", 11, C["faint"], anchor="end"))

    bw = min(gw / n * 0.62, 26)
    for i, v in enumerate(vals):
        cx = gx + gw * (i + 0.5) / n
        bh = (v / mxv) * gh
        col = C["diamond"] if i == len(vals) - 1 else C["emerald"]
        if v > 0:
            s.append(block_bar(round(cx - bw / 2), round(gy + gh - bh), round(bw), max(round(bh), 3), col))
        s.append(mono(cx, gy + gh + 17, MONTHS_ABBR[i].title(), 11, C["dim"], anchor="middle"))

    s.append(f'<rect x="{x + 24}" y="{y + h - 52}" width="{w - 48}" height="30" fill="#141615"/>')
    s.append(px.pixel_text(x + w / 2, y + h - 44, f"{stats['month_name']} XP: {stats['xp_month']}", 2, C["text"], anchor="middle"))
    return "".join(s)


def draw_languages(stats, x, y, w, h):
    s = [panel(x, y, w, h), section_title(x + 24, y + 22, "LANGUAGE VEINS")]
    s.append(mono(x + 24, y + 58, "share of repository code by size", 12, C["dim"]))

    bx, by, bw, bh, gap = x + 24, y + 80, w - 48, 24, 8
    for i, (name, pct, color) in enumerate(stats["lang_list"]):
        ry = by + i * (bh + gap)
        fill_w = max((pct / 100) * bw, 4)
        s.append(f'<rect x="{bx}" y="{ry}" width="{bw}" height="{bh}" fill="#141615"/>')
        s.append(block_bar(bx, ry, round(fill_w), bh, color))
        inside = fill_w > 120
        s.append(text(bx + 8 if inside else bx + fill_w + 8, ry + bh / 2 + 4.5, name, 12.5, "#0A0A0A" if inside else C["text"], 700))
        s.append(mono(bx + bw - 8, ry + bh / 2 + 4.5, f"{pct:.1f}%", 12, C["dim"], anchor="end"))

    if stats["lang_list"] and stats["top_language"] != "N/A":
        s.append(px.pixel_text(bx, y + h - 46, "MAIN VEIN", 2, C["dim"]))
        s.append(text(bx + px.text_width("MAIN VEIN", 2) + 14, y + h - 32, stats["top_language"], 16, C["text"], 800))
    else:
        s.append(mono(bx, y + 110, "no repository languages yet", 12, C["faint"]))
    return "".join(s)


def draw_advancements(stats, x, y, w, h):
    s = [panel(x, y, w, h), section_title(x + 24, y + 22, "ADVANCEMENTS", "next tier shown on each bar")]
    goals = [
        ("XP EARNED", stats["xp"], [100, 750, 1500, GOAL]),
        ("BEST RUN", stats["longest_streak"], [3, 7, 14, 30]),
        ("BUILDS", stats["repos"], [5, 10, 20, 40]),
        ("BEST DAY", stats["best_day"], [5, 10, 20, 40]),
        ("ACTIVE DAYS", stats["active_days"], [30, 90, 180, 300]),
    ]
    gap = 10
    cw = (w - 48 - gap * (len(goals) - 1)) / len(goals)
    for i, (title, value, thresholds) in enumerate(goals):
        cx, cy = x + 24 + i * (cw + gap), y + 56
        reached = -1
        for ti, t in enumerate(thresholds):
            if value >= t:
                reached = ti
        has = reached >= 0
        tier, color = TIERS[reached] if has else ("LOCKED", C["faint"])
        nxt = thresholds[reached + 1] if reached + 1 < len(thresholds) else None

        s.append(panel(cx, cy, cw, h - 80, C["panel_alt"]))
        s.append(slot(cx + 10, cy + 12, 36))
        icon = px.block_sprite(color, cx + 10 + 6, cy + 12 + 6, 3) if has else px.block_sprite("#3A3E3B", cx + 16, cy + 18, 3)
        s.append(icon)
        s.append(px.pixel_text(cx + 54, cy + 14, tier, 2, color))
        s.append(text(cx + 54, cy + 42, title, 11.5, C["text"] if has else C["faint"], 700))

        bx, by, bw = cx + 12, cy + 62, cw - 24
        s.append(f'<rect x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="8" fill="#0B0C0B"/>')
        if nxt:
            lo = thresholds[reached] if has else 0
            frac = min(max((value - lo) / (nxt - lo), 0), 1)
        else:
            frac = 1.0
        if frac > 0:
            s.append(block_bar(round(bx), by, round(bw * frac), 8, color))
        caption = f"{value:,} / {nxt:,}" if nxt else f"{value:,} \u2014 MAX"
        s.append(mono(bx, by + 24, caption, 11, C["dim"]))
    return "".join(s)


SKILL_COLORS = {
    "LANGUAGES": C["emerald"], "DATA ANALYTICS": C["diamond"], "BI TOOLS": C["diamond"],
    "DATABASES": C["gold"], "DEV TOOLS": C["stone"],
}


def inventory_layout(w):
    """Wrap skill chips into rows; returns (blocks, total_height)."""
    label_w, chip_h, row_gap, avail = 168, 28, 8, w - 48 - 168
    blocks, total = [], 0
    for cat, items in PROFILE["skills"].items():
        rows, cur, cur_w = [], [], 0
        for it in items:
            cw = round(len(it) * 7.6 + 28)
            if cur and cur_w + cw + 8 > avail:
                rows.append(cur)
                cur, cur_w = [], 0
            cur.append((it, cw))
            cur_w += cw + 8
        if cur:
            rows.append(cur)
        bh = len(rows) * chip_h + (len(rows) - 1) * row_gap + 14
        blocks.append((cat, rows, bh))
        total += bh
    return blocks, 56 + total + 10


def draw_inventory(x, y, w, h, blocks):
    s = [panel(x, y, w, h), section_title(x + 24, y + 22, "PLAYER INVENTORY", "every skill, by category")]
    cy = y + 56
    for cat, rows, bh in blocks:
        col = SKILL_COLORS.get(cat, C["stone"])
        s.append(px.pixel_text(x + 24, cy + 8, cat, 2, col))
        for ri, row in enumerate(rows):
            cx = x + 24 + 168
            ry = cy + ri * 36
            for name, cw in row:
                s.append(slot(cx, ry, 28))  # corner bevel base
                s.append(f'<rect x="{cx}" y="{ry}" width="{cw}" height="28" fill="#0B0C0B"/>'
                         f'<rect x="{cx + 2}" y="{ry + 2}" width="{cw - 4}" height="24" fill="#171918"/>'
                         f'<rect x="{cx}" y="{ry + 26}" width="{cw}" height="2" fill="{C["bevel_hi"]}"/>'
                         f'<rect x="{cx + cw - 2}" y="{ry}" width="2" height="28" fill="{C["bevel_hi"]}"/>'
                         f'<rect x="{cx + 2}" y="{ry + 2}" width="4" height="24" fill="{col}"/>')
                s.append(text(cx + 14, ry + 19, name, 12.5, C["text"], 700))
                cx += cw + 8
        cy += bh
    return "".join(s)


def draw_builds(x, y, w, h):
    s = [panel(x, y, w, h), section_title(x + 24, y + 22, "MAJOR BUILDS", "featured projects")]
    items = PROFILE["highlights"]
    gap = 12
    cw = (w - 48 - gap * (len(items) - 1)) / len(items)
    for i, b in enumerate(items):
        cx, cy = x + 24 + i * (cw + gap), y + 56
        col = RARITY[b["rarity"]]
        s.append(panel(cx, cy, cw, h - 80, C["panel_alt"]))
        s.append(f'<rect x="{cx + 6}" y="{cy + 3}" width="{cw - 12:.1f}" height="3" fill="{col}"/>')
        s.append(px.pixel_text(cx + 14, cy + 18, f"BUILD {i + 1:02d}", 2, col))
        s.append(px.pixel_text(cx + cw - 14, cy + 18, b["rarity"].upper(), 1, col, anchor="end", shadow_offset=1))
        s.append(text(cx + 14, cy + 54, b["title"], 12.5, C["text"], 700))
        s.append(mono(cx + 14, cy + 72, b["stack"], 11, C["dim"]))
        s.append(px.pixel_text(cx + 14, cy + 82, b["stat_value"], 3, col))
        s.append(px.pixel_text(cx + 14, cy + 107, b["stat_label"], 1, C["dim"], shadow_offset=1))
        s.append(text(cx + 14, cy + h - 80 - 8, b["detail"], 11, C["dim"]))
    return "".join(s)


def draw_footer(x, y, w, h):
    return (panel(x, y, w, h)
            + px.pixel_text(x + w / 2, y + 14, "WORLD AUTOSAVED", 2, C["emerald"], anchor="middle")
            + text(x + w / 2, y + 44, "Data: GitHub GraphQL API \u00b7 contributions include commits, issues, PRs and reviews",
                   11, C["faint"], anchor="middle"))


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------

def defs():
    cells = []
    for i, col in enumerate(CHUNK_SCALE):
        cells.append(
            f'<g id="c{i}"><rect width="10" height="10" fill="{col}"/>'
            f'<rect width="10" height="1" fill="#fff" opacity="0.22"/><rect width="1" height="10" fill="#fff" opacity="0.14"/>'
            f'<rect y="9" width="10" height="1" fill="#000" opacity="0.35"/><rect x="9" width="1" height="10" fill="#000" opacity="0.28"/></g>')
    return (
        "<defs>"
        '<pattern id="seam" width="8" height="8" patternUnits="userSpaceOnUse">'
        '<path d="M0 7.5H8M7.5 0V8" stroke="#000" stroke-opacity="0.28" stroke-width="1"/></pattern>'
        + "".join(cells)
        + "</defs>"
        "<style>"
        "@keyframes reveal{from{opacity:0}to{opacity:1}}"
        "@media (prefers-reduced-motion:no-preference){.col{animation:reveal .35s ease-out backwards}}"
        "</style>"
    )


def render(stats):
    y = 16
    body = []
    body.append(draw_header(stats, 20, y, 760, 124)); y += 124 + 16
    body.append(draw_xp(stats, 20, y, 760, 92)); y += 92 + 18
    body.append(section_title(24, y, "PLAYER STATS")); y += 24
    body.append(draw_stat_cards(stats, 20, y, 760)); y += 76 * 2 + 10 + 20
    body.append(draw_chunk_map(stats, 20, y, 760, 214)); y += 214 + 16
    body.append(draw_month_chart(stats, 20, y, 374, 330))
    body.append(draw_languages(stats, 406, y, 374, 330)); y += 330 + 16
    inv_blocks, inv_h = inventory_layout(760)
    body.append(draw_inventory(20, y, 760, inv_h, inv_blocks)); y += inv_h + 16
    body.append(draw_advancements(stats, 20, y, 760, 170)); y += 170 + 16
    body.append(draw_builds(20, y, 760, 216)); y += 216 + 16
    body.append(draw_footer(20, y, 760, 64)); y += 64 + 16
    height = y

    head = (f'<svg width="{W}" height="{height}" viewBox="0 0 {W} {height}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-labelledby="t d" font-family="{FONT_UI}" shape-rendering="crispEdges">'
            f'<title id="t">World Activity \u2014 {esc(PROFILE["name"])}</title>'
            f'<desc id="d">Minecraft-style GitHub activity dashboard: XP, streaks, contribution chunk map, '
            f'monthly XP, language veins, inventory, advancements and major builds.</desc>')
    return head + defs() + f'<rect width="{W}" height="{height}" fill="{C["bg"]}"/>' + "".join(body) + "</svg>\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--placeholder", action="store_true", help="render an empty 'first sync pending' world (no API call)")
    mode.add_argument("--demo", action="store_true", help="render synthetic data for design QA (no API call)")
    ap.add_argument("--out", default=OUTPUT_PATH, help=f"output path (default: {OUTPUT_PATH})")
    args = ap.parse_args()

    if args.placeholder:
        stats = compute_stats(placeholder_user(), last_updated="PENDING FIRST SYNC")
    elif args.demo:
        stats = compute_stats(demo_user(), last_updated="DEMO DATA")
    else:
        stats = compute_stats(fetch_user(os.environ.get("GH_TOKEN")))

    svg = render(stats)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)

    print(f"World activity generated: {args.out}")
    print(f"  XP: {stats['xp']} | Builds: {stats['repos']} | Party: {stats['followers']}")
    print(f"  Target progress: {int(stats['progress'] * 100)}% | Best run: {stats['longest_streak']} "
          f"(live {stats['current_streak']}) | Main vein: {stats['top_language']}")
    print(f"  Best day: {stats['best_day']} | {stats['month_name']} XP: {stats['xp_month']}")


if __name__ == "__main__":
    main()
