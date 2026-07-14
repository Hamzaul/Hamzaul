"""
F1 TELEMETRY — GitHub contribution dashboard, personalized as a portfolio piece.

Renders a single SVG styled like a race-car telemetry cluster: carbon-fibre
panels, a radial gauge for season progress, sector-heat contribution map,
tyre-compound language bars, a skills "garage", career highlights as race
results, and tiered podium achievements.

Live data (commits, streaks, languages, followers) comes from the GitHub
GraphQL API for PROFILE["github_username"]. Static content (name, skills,
project highlights) comes from the PROFILE dict below — edit that block to
update the portfolio without touching any drawing code.

Usage: GH_TOKEN=... python scripts/dashboard.py
Output: assets/f1-dashboard.svg
"""

import os
import math
import datetime
import sys

import requests

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Profile — edit this block to update the portfolio content. Nothing else
# in the file needs to change when your name, skills, or projects change.
# --------------------------------------------------------------------------

PROFILE = {
    "name": "Hamzaul Rahman",
    "tagline": "Aspiring Data Analyst — Power BI · Python · EDA",
    # GitHub handle used to pull LIVE stats below (commits, streaks, languages).
    # Pulled from the hyperlink behind "GitHub" on the resume, not the link text.
    "github_username": "Hamzaul",
    "goal": 3000,  # season commit target shown on the gauge

    # Grouped skill tags for the GARAGE panel. Keys become category labels.
    "skills": {
        "LANGUAGES": ["Python", "Java", "C"],
        "DATA ANALYTICS": ["Pandas", "NumPy", "Matplotlib", "Seaborn", "EDA", "Regression", "Statistics"],
        "BI TOOLS": ["Power BI", "DAX", "Excel", "Pivot Tables", "XLOOKUP"],
        "DATABASES": ["MySQL", "MongoDB"],
        "DEV TOOLS": ["Git", "GitHub"],
    },

    # Top projects for the CAREER HIGHLIGHTS panel, ordered P1/P2/P3.
    # Each needs: title, stack, one headline stat, and a short supporting detail.
    "highlights": [
        {
            "title": "PhonePe Transaction Analysis",
            "stack": "Power BI · DAX",
            "stat_value": "300K+",
            "stat_label": "TRANSACTIONS",
            "detail": "₹3.47bn value · 96% success rate",
        },
        {
            "title": "Car Models Analysis",
            "stack": "Power BI",
            "stat_value": "337 HP",
            "stat_label": "AVG HORSEPOWER",
            "detail": "~$58K avg price, cross-brand comparison",
        },
        {
            "title": "Student Performance Analysis",
            "stack": "Python · Pandas · Seaborn",
            "stat_value": "74.8",
            "stat_label": "AVG SCORE",
            "detail": "100 records · correlation heatmaps",
        },
    ],

    # Deliberately excluded: phone number and email. This SVG is meant to sit
    # in a public README, and a hardcoded phone number there is spam-bait.
    # Add a "contact" field here if you'd rather show a LinkedIn/GitHub link.
}

USERNAME = PROFILE["github_username"]
TOKEN = os.environ.get("GH_TOKEN")
GOAL = PROFILE["goal"]
W, H = 1660, 1373

if not TOKEN:
    print("ERROR: GH_TOKEN not found in environment variables")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

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
      restrictedContributionsCount
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
    }
  }
}
"""

# --------------------------------------------------------------------------
# Theme — carbon-fibre HUD, not generic dark+red
# --------------------------------------------------------------------------

COLOR = {
    "bg": "#090B0F",
    "panel": "#12151C",
    "panel_alt": "#0D1015",
    "border": "#242832",
    "grid": "#1B1F27",
    "text": "#F2F4F8",
    "text_dim": "#848B9C",
    "text_faint": "#4B505C",
    "red": "#E8121C",
    "red_dark": "#5C0910",
    "gold": "#C6A15B",
    "silver": "#9CA3AF",
    "bronze": "#B0754A",
    "platinum": "#7FE7D8",
    "cyan": "#2FD3E0",
    "purple": "#9D6BFF",
    "green": "#28C76F",
    "amber": "#F2A93B",
}

FONT_DISPLAY = "'Segoe UI', Arial, sans-serif"
FONT_MONO = "'SF Mono', 'Consolas', 'Courier New', monospace"

# heat scale for the sector map (contribution calendar) — cool -> hot,
# like a tyre-temperature readout, instead of the generic GitHub green
HEAT_SCALE = ["#161A22", "#1B3A57", "#1C6E8C", "#2FD3E0", "#F2A93B", "#E8121C"]


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def polar(cx, cy, r, angle_deg):
    rad = math.radians(angle_deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


# --------------------------------------------------------------------------
# Data fetch
# --------------------------------------------------------------------------

def fetch_user():
    try:
        resp = requests.post(
            "https://api.github.com/graphql",
            json={"query": QUERY, "variables": {"login": USERNAME}},
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"ERROR: API request failed: {e}")
        sys.exit(1)

    if "data" not in data or data["data"] is None or data["data"]["user"] is None:
        print("ERROR: GitHub API returned unexpected response:")
        print(data)
        sys.exit(1)

    return data["data"]["user"]


# --------------------------------------------------------------------------
# Stat computation
# --------------------------------------------------------------------------

def compute_stats(user):
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    month_names_full = [
        "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
        "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
    ]

    followers = user["followers"]["totalCount"] or 0
    repos = user["repositories"]["totalCount"] or 0
    calendar = user["contributionsCollection"]["contributionCalendar"]
    weeks = calendar["weeks"]

    all_days = []
    for w in weeks:
        for d in w["contributionDays"]:
            all_days.append((d["date"], d["contributionCount"], d["weekday"]))
    all_days.sort(key=lambda x: x[0])

    current_year_commits = 0
    current_month_commits = 0
    for dstr, c, _ in all_days:
        try:
            day_date = datetime.date.fromisoformat(dstr)
        except ValueError:
            continue
        if day_date.year == current_year:
            current_year_commits += c
            if day_date.month == current_month:
                current_month_commits += c

    commits = current_year_commits

    # longest streak (all-time within window) + current live streak
    longest_streak = 0
    cur = 0
    for _, c, _ in all_days:
        if c > 0:
            cur += 1
            longest_streak = max(longest_streak, cur)
        else:
            cur = 0

    current_streak = 0
    for dstr, c, _ in reversed(all_days):
        d = datetime.date.fromisoformat(dstr)
        if d > today:
            continue
        if c > 0:
            current_streak += 1
        else:
            if d == today:
                continue  # today may legitimately still be at 0
            break

    week_start = today - datetime.timedelta(days=today.weekday())
    this_week = sum(c for dstr, c, _ in all_days if datetime.date.fromisoformat(dstr) >= week_start)

    active_days = sum(
        1 for dstr, c, _ in all_days
        if datetime.date.fromisoformat(dstr).year == current_year and c > 0
    )
    avg_per_day = round(commits / max(active_days, 1), 1)

    fastest_lap = max((c for dstr, c, _ in all_days
                        if datetime.date.fromisoformat(dstr).year == current_year), default=0)

    # last 12 completed weeks, total commits per week — "race pace"
    week_totals = []
    for w in weeks[-12:]:
        week_totals.append(sum(d["contributionCount"] for d in w["contributionDays"]))

    # monthly totals for the current year up to current month
    monthly = {}
    for dstr, c, _ in all_days:
        d = datetime.date.fromisoformat(dstr)
        if d.year == current_year and d.month <= current_month:
            key = (d.year, d.month)
            monthly[key] = monthly.get(key, 0) + c
    month_keys = [(current_year, m) for m in range(1, current_month + 1)]
    for k in month_keys:
        monthly.setdefault(k, 0)
    month_vals = [monthly[k] for k in month_keys]

    # languages
    lang_totals, lang_colors = {}, {}
    for repo in user["repositories"]["nodes"]:
        if repo and repo.get("languages"):
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                color = edge["node"].get("color") or "#888888"
                lang_totals[name] = lang_totals.get(name, 0) + edge["size"]
                lang_colors[name] = color

    total_lang = sum(lang_totals.values()) if lang_totals else 1
    sorted_langs = sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)
    top_langs = sorted_langs[:5]
    others = sum(v for _, v in sorted_langs[5:])
    lang_list = [(name, size / total_lang * 100, lang_colors.get(name, "#888"))
                 for name, size in top_langs]
    if others > 0:
        lang_list.append(("Others", others / total_lang * 100, "#4B505C"))
    if not lang_list:
        lang_list = [("No Data", 100, "#4B505C")]

    top_language = top_langs[0][0] if top_langs else "N/A"

    progress = min(commits / max(GOAL, 1), 1)

    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    last_updated = datetime.datetime.now(ist).strftime("%b %d, %Y  %I:%M %p IST")

    return dict(
        today=today, current_year=current_year, current_month=current_month,
        current_month_name=month_names_full[current_month - 1],
        followers=followers, repos=repos, weeks=weeks, all_days=all_days,
        commits=commits, current_month_commits=current_month_commits,
        longest_streak=longest_streak, current_streak=current_streak,
        this_week=this_week, active_days=active_days, avg_per_day=avg_per_day,
        fastest_lap=fastest_lap, week_totals=week_totals,
        month_keys=month_keys, month_vals=month_vals,
        lang_list=lang_list, top_language=top_language,
        progress=progress, last_updated=last_updated,
    )


def tier_for(value, thresholds):
    """thresholds = [(label, color, min_value)] ordered ascending."""
    reached = None
    for label, color, min_value in thresholds:
        if value >= min_value:
            reached = (label, color, min_value)
    return reached


# --------------------------------------------------------------------------
# Drawing helpers
# --------------------------------------------------------------------------

def panel(x, y, w, h, rx=14, fill=None):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill or COLOR["panel"]}" stroke="{COLOR["border"]}" stroke-width="1.5"/>')


def panel_title(x, y, text, size=15):
    return (f'<text x="{x}" y="{y}" font-family="{FONT_DISPLAY}" font-size="{size}" '
            f'font-weight="700" fill="{COLOR["text"]}" letter-spacing="2">{esc(text)}</text>')


def eyebrow(x, y, text, color=None):
    return (f'<text x="{x}" y="{y}" font-family="{FONT_MONO}" font-size="10.5" '
            f'font-weight="700" fill="{color or COLOR["text_dim"]}" letter-spacing="1.5">{esc(text)}</text>')


def carbon_texture(x, y, w, h, uid):
    """Subtle diagonal carbon-fibre hatch, clipped to a panel."""
    parts = [
        f'<pattern id="carbon{uid}" width="8" height="8" patternTransform="rotate(45)" '
        f'patternUnits="userSpaceOnUse">'
        f'<rect width="8" height="8" fill="{COLOR["panel"]}"/>'
        f'<line x1="0" y1="0" x2="0" y2="8" stroke="#1A1E27" stroke-width="4"/>'
        f'</pattern>'
    ]
    return "".join(parts)


def draw_header(stats):
    s = []
    # checkered flag mark
    cell = 7
    for r in range(4):
        for c in range(6):
            if (r + c) % 2 == 0:
                s.append(f'<rect x="{40 + c*cell}" y="{26 + r*cell}" width="{cell}" height="{cell}" fill="#fff"/>')
            else:
                s.append(f'<rect x="{40 + c*cell}" y="{26 + r*cell}" width="{cell}" height="{cell}" fill="#0a0a0a"/>')
    s.append(f'<rect x="40" y="26" width="{6*cell}" height="{4*cell}" fill="none" '
              f'stroke="{COLOR["border"]}" stroke-width="1"/>')

    name_words = PROFILE["name"].upper().split()
    first_name = " ".join(name_words[:-1]) if len(name_words) > 1 else name_words[0]
    last_name = name_words[-1] if len(name_words) > 1 else ""
    s.append(f'<text x="112" y="52" font-family="{FONT_DISPLAY}" font-size="42" font-weight="800" '
              f'fill="{COLOR["text"]}">{esc(first_name)} <tspan fill="{COLOR["red"]}">{esc(last_name)}</tspan></text>')
    s.append(f'<text x="112" y="76" font-family="{FONT_MONO}" font-size="13" letter-spacing="2" '
              f'fill="{COLOR["text_dim"]}">{esc(PROFILE["tagline"].upper())}</text>')

    # last updated + goal, styled like a dash readout
    for i, (label, value, x) in enumerate([
        ("LAST UPDATED", stats["last_updated"], 1085),
        ("SEASON TARGET", f"{GOAL:,} COMMITS", 1430),
    ]):
        pw = 220 if i == 1 else 335
        s.append(panel(x, 20, pw, 62, rx=10))
        s.append(eyebrow(x + 18, 42, label))
        s.append(f'<text x="{x + 18}" y="66" font-family="{FONT_MONO}" font-size="15" '
                  f'font-weight="700" fill="{COLOR["text"]}">{esc(value)}</text>')
    return "".join(s)


def draw_gauge_panel(stats, x, y, w, h):
    s = [panel(x, y, w, h), panel_title(x + 25, y + 35, "SEASON PROGRESS")]
    s.append(eyebrow(x + 25, y + 55, f"YEAR {stats['current_year']}"))

    cx, cy, R = x + w * 0.36, y + 178, 100
    start, sweep = 135, 270
    end = start + sweep

    # background track
    x1, y1 = polar(cx, cy, R, start)
    x2, y2 = polar(cx, cy, R, end)
    s.append(f'<path d="M {x1:.1f} {y1:.1f} A {R} {R} 0 1 1 {x2:.1f} {y2:.1f}" '
              f'fill="none" stroke="{COLOR["grid"]}" stroke-width="15" stroke-linecap="round"/>')

    # progress arc
    prog_end = start + sweep * stats["progress"]
    px1, py1 = polar(cx, cy, R, start)
    px2, py2 = polar(cx, cy, R, prog_end)
    large = 1 if (prog_end - start) > 180 else 0
    if stats["progress"] > 0.002:
        s.append(f'<path d="M {px1:.1f} {py1:.1f} A {R} {R} 0 {large} 1 {px2:.1f} {py2:.1f}" '
                  f'fill="none" stroke="{COLOR["red"]}" stroke-width="15" stroke-linecap="round"/>')

    # small tick marks only, no radial labels (avoids collisions with the panel title)
    checkpoints = [0, 0.25, 0.5, 0.75, 1.0]
    for frac in checkpoints:
        ang = start + sweep * frac
        ix, iy = polar(cx, cy, R - 18, ang)
        ox, oy = polar(cx, cy, R + 18, ang)
        tick_color = COLOR["red"] if frac <= stats["progress"] else COLOR["text_faint"]
        s.append(f'<line x1="{ix:.1f}" y1="{iy:.1f}" x2="{ox:.1f}" y2="{oy:.1f}" '
                  f'stroke="{tick_color}" stroke-width="2"/>')

    # needle
    needle_ang = start + sweep * stats["progress"]
    nx, ny = polar(cx, cy, R - 24, needle_ang)
    bx1, by1 = polar(cx, cy, 7, needle_ang + 90)
    bx2, by2 = polar(cx, cy, 7, needle_ang - 90)
    s.append(f'<polygon points="{nx:.1f},{ny:.1f} {bx1:.1f},{by1:.1f} {bx2:.1f},{by2:.1f}" '
              f'fill="{COLOR["gold"]}"/>')
    s.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="10" fill="{COLOR["panel_alt"]}" stroke="{COLOR["gold"]}" stroke-width="2.5"/>')

    # digital LCD readout in the open gap at the bottom of the gauge
    s.append(f'<text x="{cx:.1f}" y="{cy + 55}" font-family="{FONT_MONO}" font-size="34" '
              f'font-weight="700" fill="{COLOR["text"]}" text-anchor="middle">{int(stats["progress"]*100)}%</text>')
    s.append(f'<text x="{cx:.1f}" y="{cy + 76}" font-family="{FONT_MONO}" font-size="12" '
              f'text-anchor="middle"><tspan fill="{COLOR["red"]}" font-weight="700">{stats["commits"]:,}</tspan>'
              f'<tspan fill="{COLOR["text_dim"]}"> / {GOAL:,}</tspan></text>')

    # checkpoint legend as a vertical strip to the right of the gauge —
    # avoids radial-label collisions and doubles as a lap-board readout
    lx = x + w * 0.62
    ly0 = y + 82
    checkpoint_rows = [("START", 0), ("750", 0.25), ("1,500", 0.5), ("2,250", 0.75), (f"{GOAL:,}", 1.0)]
    for i, (label, frac) in enumerate(checkpoint_rows):
        ry = ly0 + i * 30
        reached = frac <= stats["progress"]
        dot_col = COLOR["red"] if reached else COLOR["text_faint"]
        s.append(f'<circle cx="{lx:.1f}" cy="{ry-4:.1f}" r="5" fill="{dot_col}"/>')
        txt_col = COLOR["text"] if reached else COLOR["text_dim"]
        s.append(f'<text x="{lx+16:.1f}" y="{ry:.1f}" font-family="{FONT_MONO}" font-size="12.5" '
                  f'font-weight="700" fill="{txt_col}">{esc(label)}</text>')

    return "".join(s)


def draw_pace_strip(stats, x, y, w, h):
    s = [panel(x, y, w, h, rx=10)]
    s.append(eyebrow(x + 22, y + 22, "RACE PACE // COMMITS PER WEEK, LAST 12 WEEKS"))

    spx, spy = x + 22, y + 30
    spw, sph = w - 44, h - 42
    wt = stats["week_totals"] or [0]
    mx = max(max(wt), 1)
    n = max(len(wt), 1)
    bw = spw / n
    for i, v in enumerate(wt):
        bh = (v / mx) * sph
        bx = spx + i * bw
        by = spy + sph - bh
        col = COLOR["red"] if i == len(wt) - 1 else COLOR["cyan"]
        op = 0.5 + 0.5 * (i / max(n - 1, 1))
        s.append(f'<rect x="{bx + 1.5:.1f}" y="{by:.1f}" width="{bw - 3:.1f}" height="{max(bh, 2):.1f}" '
                  f'rx="2" fill="{col}" opacity="{op:.2f}"/>')
    return "".join(s)


def draw_quick_stats(stats, x, y, w, h):
    s = [panel(x, y, w, h), panel_title(x + 25, y + 35, "TIMING SCREEN")]

    cards = [
        ("TOTAL COMMITS", f"{stats['commits']:,}", "This season", COLOR["red"]),
        ("FASTEST LAP", str(stats["fastest_lap"]), "Best single day", COLOR["amber"]),
        ("CURRENT STREAK", f"{stats['current_streak']}d", "Live", COLOR["green"]),
        ("BEST STREAK", f"{stats['longest_streak']}d", "Personal best", COLOR["purple"]),
        ("REPOSITORIES", str(stats["repos"]), "Active", COLOR["cyan"]),
        ("FOLLOWERS", str(stats["followers"]), "People", COLOR["silver"]),
        ("AVG / DAY", str(stats["avg_per_day"]), "Commits", COLOR["cyan"]),
        ("THIS WEEK", str(stats["this_week"]), "Commits", COLOR["green"]),
    ]
    cols = 4
    gap = 10
    cw = (w - 50 - gap * (cols - 1)) / cols
    ch = 92
    for i, (title, val, sub, col) in enumerate(cards):
        cx = x + 25 + (i % cols) * (cw + gap)
        cy = y + 50 + (i // cols) * (ch + gap)
        s.append(f'<rect x="{cx:.1f}" y="{cy}" width="{cw:.1f}" height="{ch}" rx="10" '
                  f'fill="{COLOR["panel_alt"]}" stroke="{COLOR["border"]}"/>')
        s.append(f'<rect x="{cx:.1f}" y="{cy}" width="3" height="{ch}" rx="1.5" fill="{col}"/>')
        s.append(eyebrow(cx + 16, cy + 24, title))
        s.append(f'<text x="{cx + 16:.1f}" y="{cy + 55}" font-family="{FONT_MONO}" font-size="24" '
                  f'font-weight="700" fill="{col}">{esc(val)}</text>')
        s.append(f'<text x="{cx + 16:.1f}" y="{cy + 76}" font-family="{FONT_DISPLAY}" font-size="11" '
                  f'fill="{COLOR["text_dim"]}">{esc(sub)}</text>')
    return "".join(s)


def draw_sector_map(stats, x, y, w, h):
    s = [panel(x, y, w, h), panel_title(x + 25, y + 35, "SECTOR MAP")]
    s.append(eyebrow(x + 25, y + 54, "CONTRIBUTION HEAT, LAST 52 WEEKS"))

    cell, gap = 7, 2
    gx, gy = x + 30, y + 72
    all_days = stats["all_days"]
    max_val = max((c for _, c, _ in all_days), default=1) or 1

    def heat(count):
        if count == 0:
            return HEAT_SCALE[0]
        r = count / max_val
        idx = min(int(r * (len(HEAT_SCALE) - 1)) + 1, len(HEAT_SCALE) - 1)
        return HEAT_SCALE[idx]

    weeks = stats["weeks"][-52:]
    for wi, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            wd = d["weekday"]
            px = gx + wi * (cell + gap)
            py = gy + wd * (cell + gap)
            s.append(f'<rect x="{px}" y="{py}" width="{cell}" height="{cell}" rx="1.5" '
                      f'fill="{heat(d["contributionCount"])}"/>')

    ly = gy + 7 * (cell + gap) + 16
    s.append(f'<text x="{gx}" y="{ly + 8}" font-family="{FONT_MONO}" font-size="10.5" '
              f'fill="{COLOR["text_dim"]}">COLD</text>')
    for i, col in enumerate(HEAT_SCALE):
        s.append(f'<rect x="{gx + 45 + i*14}" y="{ly}" width="{cell}" height="{cell}" rx="1.5" fill="{col}"/>')
    s.append(f'<text x="{gx + 45 + len(HEAT_SCALE)*14 + 8}" y="{ly + 8}" font-family="{FONT_MONO}" '
              f'font-size="10.5" fill="{COLOR["text_dim"]}">HOT</text>')

    mt_y = y + h - 100
    s.append(eyebrow(x + 25, mt_y, "SESSION METRICS"))
    metrics = [
        ("ACTIVE DAYS", str(stats["active_days"]), COLOR["text"]),
        ("AVG / DAY", str(stats["avg_per_day"]), COLOR["cyan"]),
        ("THIS WEEK", str(stats["this_week"]), COLOR["green"]),
    ]
    mw = (w - 50 - 16) / 3
    for i, (title, val, col) in enumerate(metrics):
        mx = x + 25 + i * (mw + 8)
        my = mt_y + 15
        s.append(f'<rect x="{mx:.1f}" y="{my}" width="{mw:.1f}" height="66" rx="10" '
                  f'fill="{COLOR["panel_alt"]}" stroke="{COLOR["border"]}"/>')
        s.append(eyebrow(mx + 14, my + 22, title))
        s.append(f'<text x="{mx + 14:.1f}" y="{my + 48}" font-family="{FONT_MONO}" font-size="20" '
                  f'font-weight="700" fill="{col}">{esc(val)}</text>')
    return "".join(s)


def draw_pace_chart(stats, x, y, w, h):
    s = [panel(x, y, w, h), panel_title(x + 25, y + 35, "COMMITS OVER TIME")]
    s.append(eyebrow(x + 25, y + 54, "MONTHLY LAP CHART"))

    gx, gy = x + 55, y + 74
    gw, gh = w - 85, 165
    vals = stats["month_vals"] or [0]
    mxv = max(max(vals), 1)

    # alternating sector background stripes
    n = len(vals)
    for i in range(n):
        if i % 2 == 0:
            bx = gx + gw * i / n
            bw2 = gw / n
            s.append(f'<rect x="{bx:.1f}" y="{gy}" width="{bw2:.1f}" height="{gh}" fill="{COLOR["panel_alt"]}"/>')

    for i in range(5):
        yy = gy + gh - gh * i / 4
        s.append(f'<line x1="{gx}" y1="{yy:.1f}" x2="{gx+gw}" y2="{yy:.1f}" stroke="{COLOR["grid"]}" stroke-width="1"/>')
        s.append(f'<text x="{gx-10}" y="{yy+4:.1f}" font-family="{FONT_MONO}" font-size="10" '
                  f'fill="{COLOR["text_dim"]}" text-anchor="end">{int(mxv*i/4)}</text>')

    # bars
    bw = gw / n * 0.5
    pts = []
    for i, v in enumerate(vals):
        cx = gx + gw * (i + 0.5) / n
        bh = (v / mxv) * gh
        s.append(f'<rect x="{cx - bw/2:.1f}" y="{gy + gh - bh:.1f}" width="{bw:.1f}" height="{max(bh,1):.1f}" '
                  f'rx="3" fill="{COLOR["red"]}" opacity="0.28"/>')
        pts.append((cx, gy + gh - bh))

    if len(pts) > 1:
        line = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts)
        s.append(f'<path d="{line}" fill="none" stroke="{COLOR["red"]}" stroke-width="2.5"/>')
    for px, py in pts:
        s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{COLOR["gold"]}"/>')

    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for i, k in enumerate(stats["month_keys"]):
        cx = gx + gw * (i + 0.5) / n
        lbl = f"{month_names[k[1]-1]} '{str(k[0])[2:]}"
        s.append(f'<text x="{cx:.1f}" y="{gy+gh+20}" font-family="{FONT_MONO}" font-size="10" '
                  f'fill="{COLOR["text_dim"]}" text-anchor="middle">{esc(lbl)}</text>')

    s.append(f'<rect x="{x+25}" y="{y+h-58}" width="{w-50}" height="42" rx="10" '
              f'fill="{COLOR["panel_alt"]}" stroke="{COLOR["border"]}"/>')
    s.append(f'<text x="{x+w/2:.1f}" y="{y+h-32}" font-family="{FONT_MONO}" font-size="13" '
              f'text-anchor="middle" fill="{COLOR["text"]}">{esc(stats["current_month_name"])} TOTAL: '
              f'<tspan fill="{COLOR["red"]}" font-weight="700">{stats["current_month_commits"]}</tspan></text>')
    return "".join(s)


def draw_compound_board(stats, x, y, w, h):
    """Language breakdown styled as tyre-compound strips."""
    s = [panel(x, y, w, h), panel_title(x + 25, y + 35, "COMPOUND BOARD")]
    s.append(eyebrow(x + 25, y + 54, "LANGUAGES BY REPO SIZE"))

    bx, by = x + 25, y + 78
    bw = w - 50
    bh = 30
    gap = 12
    for i, (name, pct, color) in enumerate(stats["lang_list"]):
        ry = by + i * (bh + gap)
        fill_w = max((pct / 100) * bw, 4)
        s.append(f'<rect x="{bx}" y="{ry}" width="{bw}" height="{bh}" rx="7" fill="{COLOR["panel_alt"]}" stroke="{COLOR["border"]}"/>')
        s.append(f'<rect x="{bx}" y="{ry}" width="{fill_w:.1f}" height="{bh}" rx="7" fill="{color}"/>')
        # tread marks for the tyre motif
        for t in range(int(fill_w // 10)):
            tx = bx + 8 + t * 10
            if tx > bx + fill_w - 6:
                break
            s.append(f'<line x1="{tx:.1f}" y1="{ry+5}" x2="{tx:.1f}" y2="{ry+bh-5}" '
                      f'stroke="#000" stroke-opacity="0.18" stroke-width="2"/>')
        # label placed to the right of the fill if it fits inside, else outside
        label_color = "#0A0A0A" if fill_w > 90 else COLOR["text"]
        label_x = bx + 12 if fill_w > 90 else bx + fill_w + 10
        s.append(f'<text x="{label_x:.1f}" y="{ry+bh/2+4:.1f}" font-family="{FONT_DISPLAY}" font-size="12.5" '
                  f'font-weight="700" fill="{label_color}">{esc(name)}</text>')
        s.append(f'<text x="{bx+bw-10}" y="{ry+bh/2+4:.1f}" font-family="{FONT_MONO}" font-size="12.5" '
                  f'font-weight="700" fill="{COLOR["text_dim"]}" text-anchor="end">{pct:.1f}%</text>')

    top_y = by + len(stats["lang_list"]) * (bh + gap) + 14
    s.append(eyebrow(bx, top_y, "TOP COMPOUND"))
    s.append(f'<text x="{bx}" y="{top_y+26}" font-family="{FONT_DISPLAY}" font-size="18" '
              f'font-weight="800" fill="{COLOR["text"]}">{esc(stats["top_language"])}</text>')
    return "".join(s)


def draw_chip_row(items, x, y, max_w, color, font_size=11.5, chip_h=24, gap=6, line_gap=8):
    """Wraps a list of skill strings into pill chips, wrapping to a new line
    when max_w is exceeded. Returns (svg_string, y_after_last_row)."""
    parts = []
    cx, cy = x, y
    for text in items:
        label = text.upper()
        chip_w = len(label) * font_size * 0.62 + 24
        if cx + chip_w > x + max_w and cx > x:
            cx = x
            cy += chip_h + line_gap
        parts.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{chip_w:.1f}" height="{chip_h}" '
                      f'rx="{chip_h/2:.1f}" fill="{COLOR["panel_alt"]}" stroke="{color}" stroke-width="1.3"/>')
        parts.append(f'<text x="{cx+chip_w/2:.1f}" y="{cy+chip_h/2+4:.1f}" font-family="{FONT_MONO}" '
                      f'font-size="{font_size}" font-weight="700" fill="{color}" '
                      f'text-anchor="middle">{esc(label)}</text>')
        cx += chip_w + gap
    return "".join(parts), cy + chip_h


def estimate_chip_lines(items, max_w, font_size=11.5, gap=6):
    """How many wrapped lines draw_chip_row will produce for this item list."""
    cx, lines = 0, 1
    for text in items:
        chip_w = len(text.upper()) * font_size * 0.62 + 24
        if cx + chip_w > max_w and cx > 0:
            lines += 1
            cx = 0
        cx += chip_w + gap
    return lines


def draw_garage(x, y, w, h):
    """Skill tags grouped by category, styled as a pit-crew equipment board."""
    s = [panel(x, y, w, h), panel_title(x + 25, y + 35, "GARAGE"), eyebrow(x + 25, y + 54, "SKILL SET")]

    cat_colors = [COLOR["red"], COLOR["cyan"], COLOR["gold"], COLOR["green"], COLOR["purple"]]
    categories = list(PROFILE["skills"].items())
    col_w = (w - 50 - 24) / 2
    col1_x, col2_x = x + 25, x + 25 + col_w + 24

    # Greedily balance categories across the two columns by estimated wrapped
    # height (label + N chip lines), rather than a blind positional split —
    # keeps this correct even as skills are added/removed in PROFILE later.
    weighted = [(i, cat, items, estimate_chip_lines(items, col_w) + 0.6)
                for i, (cat, items) in enumerate(categories)]
    weighted.sort(key=lambda t: -t[3])
    col1, col2, w1, w2 = [], [], 0.0, 0.0
    for i, cat, items, weight in weighted:
        if w1 <= w2:
            col1.append((i, cat, items))
            w1 += weight
        else:
            col2.append((i, cat, items))
            w2 += weight
    col1.sort(key=lambda t: t[0])  # restore original reading order within each column
    col2.sort(key=lambda t: t[0])

    for col_x, cats in [(col1_x, col1), (col2_x, col2)]:
        cy = y + 78
        for i, cat, items in cats:
            color = cat_colors[i % len(cat_colors)]
            s.append(eyebrow(col_x, cy, cat, color))
            chips_svg, end_y = draw_chip_row(items, col_x, cy + 10, col_w, color)
            s.append(chips_svg)
            cy = end_y + 20
    return "".join(s)


def draw_highlights(x, y, w, h):
    """Top projects rendered as race-result rows: P1 / P2 / P3."""
    s = [panel(x, y, w, h), panel_title(x + 25, y + 35, "CAREER HIGHLIGHTS")]
    s.append(eyebrow(x + 25, y + 54, "SELECTED RACE RESULTS"))

    items = PROFILE["highlights"]
    pos_colors = [COLOR["gold"], COLOR["silver"], COLOR["bronze"]]
    top = y + 70
    gap = 10
    row_h = (h - 70 - 20 - gap * (len(items) - 1)) / max(len(items), 1)

    for i, proj in enumerate(items):
        ry = top + i * (row_h + gap)
        pos_color = pos_colors[i] if i < len(pos_colors) else COLOR["text_dim"]
        s.append(f'<rect x="{x+25}" y="{ry:.1f}" width="{w-50}" height="{row_h:.1f}" rx="10" '
                  f'fill="{COLOR["panel_alt"]}" stroke="{COLOR["border"]}"/>')
        s.append(f'<rect x="{x+25}" y="{ry:.1f}" width="4" height="{row_h:.1f}" rx="2" fill="{pos_color}"/>')
        s.append(f'<text x="{x+46}" y="{ry+20:.1f}" font-family="{FONT_MONO}" font-size="11" '
                  f'font-weight="700" fill="{pos_color}">P{i+1}</text>')
        s.append(f'<text x="{x+46}" y="{ry+row_h/2+8:.1f}" font-family="{FONT_DISPLAY}" font-size="15" '
                  f'font-weight="700" fill="{COLOR["text"]}">{esc(proj["title"])}</text>')
        s.append(f'<text x="{x+46}" y="{ry+row_h-12:.1f}" font-family="{FONT_MONO}" font-size="10.5" '
                  f'fill="{COLOR["text_dim"]}">{esc(proj["stack"])} — {esc(proj["detail"])}</text>')
        s.append(f'<text x="{x+w-40}" y="{ry+row_h/2:.1f}" font-family="{FONT_MONO}" font-size="24" '
                  f'font-weight="700" fill="{pos_color}" text-anchor="end">{esc(proj["stat_value"])}</text>')
        s.append(f'<text x="{x+w-40}" y="{ry+row_h/2+20:.1f}" font-family="{FONT_MONO}" font-size="9.5" '
                  f'fill="{COLOR["text_dim"]}" text-anchor="end">{esc(proj["stat_label"])}</text>')
    return "".join(s)


def draw_podium(stats, x, y, w, h):
    s = [panel(x, y, w, h), panel_title(x + 25, y + 35, "PODIUM PROGRESS")]

    tiers = [
        ("BRONZE", COLOR["bronze"]),
        ("SILVER", COLOR["silver"]),
        ("GOLD", COLOR["gold"]),
        ("PLATINUM", COLOR["platinum"]),
    ]

    achievements = [
        ("COMMITS", stats["commits"], [100, 750, 1500, GOAL]),
        ("BEST STREAK", stats["longest_streak"], [3, 7, 14, 30]),
        ("REPOSITORIES", stats["repos"], [5, 10, 20, 40]),
        ("FASTEST LAP", stats["fastest_lap"], [5, 10, 20, 40]),
        ("ACTIVE DAYS", stats["active_days"], [30, 90, 180, 300]),
    ]

    aw = (w - 50 - 12 * (len(achievements) - 1)) / len(achievements)
    card_h = h - 68
    for i, (title, value, thresholds) in enumerate(achievements):
        ax = x + 25 + i * (aw + 12)
        ay = y + 52
        reached_idx = -1
        for ti, t in enumerate(thresholds):
            if value >= t:
                reached_idx = ti
        has_tier = reached_idx >= 0
        tier_label, tier_color = (tiers[reached_idx] if has_tier else ("UNRANKED", COLOR["text_faint"]))
        next_target = thresholds[reached_idx + 1] if reached_idx + 1 < len(thresholds) else None

        s.append(f'<rect x="{ax:.1f}" y="{ay}" width="{aw:.1f}" height="{card_h}" rx="10" '
                  f'fill="{COLOR["panel_alt"]}" stroke="{tier_color}" stroke-width="1.5" '
                  f'opacity="{1.0 if has_tier else 0.55}"/>')
        s.append(f'<circle cx="{ax+26:.1f}" cy="{ay+26}" r="14" fill="{tier_color}" fill-opacity="0.18" stroke="{tier_color}" stroke-width="2"/>')
        s.append(f'<circle cx="{ax+26:.1f}" cy="{ay+26}" r="5.5" fill="{tier_color}"/>')
        s.append(f'<text x="{ax+50:.1f}" y="{ay+18}" font-family="{FONT_MONO}" font-size="9.5" '
                  f'font-weight="700" fill="{tier_color}">{esc(tier_label)}</text>')
        s.append(f'<text x="{ax+50:.1f}" y="{ay+34}" font-family="{FONT_DISPLAY}" font-size="12" '
                  f'font-weight="700" fill="{COLOR["text"]}">{esc(title)}</text>')

        # progress bar toward next tier (or full if maxed)
        bar_x, bar_y, bar_w, bar_h = ax + 14, ay + 46, aw - 28, 7
        s.append(f'<rect x="{bar_x:.1f}" y="{bar_y}" width="{bar_w:.1f}" height="{bar_h}" rx="3.5" fill="{COLOR["grid"]}"/>')
        if next_target:
            lo = thresholds[reached_idx] if reached_idx >= 0 else 0
            frac = min(max((value - lo) / (next_target - lo), 0), 1)
        else:
            frac = 1.0
        s.append(f'<rect x="{bar_x:.1f}" y="{bar_y}" width="{bar_w*frac:.1f}" height="{bar_h}" rx="3.5" fill="{tier_color}"/>')
        caption = f"{value} / {next_target}" if next_target else f"{value} — MAXED"
        s.append(f'<text x="{bar_x:.1f}" y="{bar_y+19}" font-family="{FONT_MONO}" font-size="9.5" '
                  f'fill="{COLOR["text_dim"]}">{esc(caption)}</text>')
    return "".join(s)


def draw_quote(x, y, w, h):
    s = [panel(x, y, w, h)]
    s.append(f'<text x="{x+30}" y="{y+55}" font-family="{FONT_DISPLAY}" font-size="46" '
              f'fill="{COLOR["red"]}" font-weight="800">&quot;</text>')
    s.append(f'<text x="{x+70}" y="{y+70}" font-family="{FONT_DISPLAY}" font-size="16" '
              f'font-style="italic" fill="{COLOR["text"]}">You need to keep pushing,</text>')
    s.append(f'<text x="{x+70}" y="{y+95}" font-family="{FONT_DISPLAY}" font-size="16" '
              f'font-style="italic" fill="{COLOR["text"]}">never give up. Smooth Operator.</text>')
    s.append(f'<text x="{x+w-30}" y="{y+130}" font-family="{FONT_MONO}" font-size="13" '
              f'fill="{COLOR["red"]}" text-anchor="end">— CARLOS SAINZ</text>')
    return "".join(s)


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------

def render(stats):
    parts = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
             f'xmlns="http://www.w3.org/2000/svg" font-family="{FONT_DISPLAY}">']
    parts.append('<defs>')
    parts.append(f'<linearGradient id="edge" x1="0" x2="1">'
                  f'<stop offset="0%" stop-color="{COLOR["red"]}"/>'
                  f'<stop offset="100%" stop-color="{COLOR["red_dark"]}"/></linearGradient>')
    parts.append('</defs>')
    parts.append(f'<rect width="{W}" height="{H}" fill="{COLOR["bg"]}"/>')
    parts.append(f'<rect x="0" y="0" width="{W}" height="4" fill="url(#edge)"/>')

    parts.append(draw_header(stats))
    parts.append(draw_pace_strip(stats, 20, 100, 1620, 66))

    parts.append(draw_gauge_panel(stats, 20, 182, 560, 300))
    parts.append(draw_quick_stats(stats, 600, 182, 1040, 300))

    parts.append(draw_sector_map(stats, 20, 498, 545, 365))
    parts.append(draw_pace_chart(stats, 580, 498, 510, 365))
    parts.append(draw_compound_board(stats, 1105, 498, 535, 365))

    parts.append(draw_garage(20, 883, 700, 300))
    parts.append(draw_highlights(740, 883, 900, 300))

    parts.append(draw_podium(stats, 20, 1203, 1190, 150))
    parts.append(draw_quote(1225, 1203, 415, 150))

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    user = fetch_user()
    stats = compute_stats(user)
    svg = render(stats)

    os.makedirs("assets", exist_ok=True)
    out_path = os.path.join("assets", "f1-dashboard.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print("Dashboard generated successfully!")
    print(f"  Commits: {stats['commits']} | Repos: {stats['repos']} | Followers: {stats['followers']}")
    print(f"  Progress: {int(stats['progress']*100)}% | Streak: {stats['longest_streak']} "
          f"(live {stats['current_streak']}) | Top lang: {stats['top_language']}")
    print(f"  Fastest lap: {stats['fastest_lap']} | {stats['current_month_name']} commits: {stats['current_month_commits']}")


if __name__ == "__main__":
    main()
