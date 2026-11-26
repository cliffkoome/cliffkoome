"""Render the animated profile sections in assets/profile/.

Each section is written twice, as <name>-dark.svg and <name>-light.svg, and the
README picks one with <picture>. Everything is plain SVG + CSS animation, so it
renders inside GitHub's image proxy with no scripts. Motion stops for people
who ask for reduced motion: every element's resting state is its final state,
and animations only run "from" an earlier state.

Needs GITHUB_TOKEN (GraphQL requires auth). Standard library only; the
portrait is drawn once by portrait.py and read from assets/profile/portrait.svg.
"""

import json
import os
import urllib.request
from datetime import date, datetime
from html import escape

import languages  # same folder: reuse the language totals and colours

USER = "cliffkoome"
NAME = "Clifford Karani"
ROLE = "Full-stack software engineer"
TAGS = ["IoT", "Embedded systems", "Systems architecture"]
LOCATION = "Nairobi, Kenya"

# Featured repos, with a one-line note on the architecture worth a look.
PROJECTS = [
    ("MatConnect", "Live GPS kept apart from the Postgres system of record; a leased ETA job safe on VM, cron or many instances."),
    ("InstaScreen", "Checksummed wire format chunked through Firebase to fit ~320 KB of SRAM; ETag compare-and-set, no backend."),
    ("typeghast", "Tails coding-agent logs live; a local Gemma model writes the text to type. Nothing leaves the machine."),
]

W = 860
FONT = "ui-monospace, 'JetBrains Mono', SFMono-Regular, Menlo, Consolas, monospace"
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

THEMES = {
    "dark": {
        "bg": "#0a0e16", "panel": "#0f1520", "line": "#1e2a3a", "text": "#e6edf3",
        "muted": "#7d8a9c", "dim": "#3a4658", "a1": "#2dd4bf", "a2": "#818cf8", "a3": "#38bdf8",
        "cell": ["#141c28", "#0e4a48", "#13756e", "#1fa597", "#2dd4bf"],
    },
    "light": {
        "bg": "#fbfcfe", "panel": "#f2f5f9", "line": "#dbe2ea", "text": "#14202e",
        "muted": "#5b6878", "dim": "#b6c0cc", "a1": "#0d9488", "a2": "#6366f1", "a3": "#0284c7",
        "cell": ["#e8edf3", "#a7e3db", "#5cc4b6", "#1d9f90", "#0b7a6e"],
    },
}

# Neofetch-style card (after Andrew Grant's profile). Static lines; the
# languages and GitHub stats are filled in from live data.
HANDLE = "clifford@karani"
CARD_ABOUT = [
    ("Role", "Full-stack software engineer"),
    ("Focus", "IoT, embedded, systems architecture"),
    ("Location", "Nairobi, Kenya (UTC+3)"),
    ("Open.To", "Senior full-stack, IoT, platform"),
]
CARD_STACK = [
    ("Hardware", "ESP32, Arduino, PlatformIO"),
    ("Cloud", "Next.js, Postgres, Firebase, Prisma"),
]
CARD_WORK = [
    ("MatConnect", "live matatu ETAs from GPS"),
    ("InstaScreen", "cloud-synced ESP32 photo frame"),
    ("typeghast", "typing game vs your agent"),
]
CARD_CONTACT = [
    ("Email", "koomekoome902@gmail.com"),
    ("LinkedIn", "cliffkoome"),
    ("DEV", "megalodon"),
]
PORTRAIT_FILE = "assets/profile/portrait-{theme}.svg"  # written by portrait.py

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


# ---------------------------------------------------------------- data

def graphql(query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
    )
    with urllib.request.urlopen(req) as resp:
        body = json.load(resp)
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


def fetch():
    names = " ".join(
        f'p{i}: repository(name: "{n}") {{ name url description pushedAt primaryLanguage {{ name color }} '
        f'repositoryTopics(first: 4) {{ nodes {{ topic {{ name }} }} }} }}'
        for i, (n, _) in enumerate(PROJECTS)
    )
    data = graphql(f"""{{ user(login: "{USER}") {{
        createdAt
        repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {{ totalCount }}
        contributionsCollection {{ contributionCalendar {{ totalContributions
            weeks {{ contributionDays {{ date contributionCount contributionLevel }} }} }} }}
        {names}
    }} }}""")["user"]
    weeks = [
        [(d["date"], d["contributionCount"], LEVELS[d["contributionLevel"]]) for d in w["contributionDays"]]
        for w in data["contributionsCollection"]["contributionCalendar"]["weeks"]
    ]
    days = [d for w in weeks for d in w]
    longest = run = 0
    for _, n, _ in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    active = sum(1 for _, n, _ in days if n)
    return {
        "since": datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")).year,
        "repos": data["repositories"]["totalCount"],
        "total": data["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "weeks": weeks,
        "longest": longest,
        "active": active,
        "projects": [(data[f"p{i}"], note) for i, (_, note) in enumerate(PROJECTS)],
    }


# ---------------------------------------------------------------- svg helpers

def svg(name, height, t, body, css="", title=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<defs>
<linearGradient id="g-{name}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t['a1']}"/><stop offset="1" stop-color="{t['a2']}"/></linearGradient>
</defs>
<style>
.m {{ font-family: {FONT}; }}
.s {{ font-family: {SANS}; }}
.lab {{ font-family: {FONT}; font-size: 11px; letter-spacing: 2.5px; fill: {t['muted']}; }}
.up {{ animation: up .9s cubic-bezier(.2,.7,.2,1) backwards; }}
@keyframes up {{ from {{ opacity: 0; transform: translateY(8px); }} }}
@keyframes fade {{ from {{ opacity: 0; }} }}
@keyframes blink {{ 50% {{ opacity: .25; }} }}
{css}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="14" fill="{t['bg']}" stroke="{t['line']}"/>
{body}
</svg>
"""


def label(x, y, text, t, anchor="start"):
    return f'<text x="{x}" y="{y}" class="lab" text-anchor="{anchor}">{escape(text.upper())}</text>'


# ---------------------------------------------------------------- sections

def card(d, langs, portrait, t, name):
    """Portrait on the left, neofetch-style key: value lines on the right."""
    pad = 24
    px, py, pw = pad, pad, 336                      # portrait box (matches portrait.py)
    x0, fs, lh = px + pw + 28, 14, 18.6
    cw = fs * .6
    cols = int((W - x0 - pad) / (fs * .6))          # characters per line

    def kv(key, value):
        dots = max(2, cols - len(key) - len(value) - 4)
        return [(". ", "dim"), (key, "key"), (": ", "dim"), ("." * dots + " ", "dot"), (value, "val")]

    def head(text):
        return [("- " + text + " ", "hd"), ("─" * (cols - len(text) - 3), "rule")]

    stats = [
        ("Repos", f"{d['repos']}"), ("Contributions", f"{d['total']:,}"),
        ("Active.Days", f"{d['active']}"), ("Longest.Streak", f"{d['longest']}d"),
    ]
    half = (cols - 3) // 2

    def pair(a, b):
        left = kv(*a)
        dots = max(2, half - len(a[0]) - len(a[1]) - 4)
        left[3] = ("." * dots + " ", "dot")
        right = kv(*b)
        dots = max(2, cols - half - 3 - len(b[0]) - len(b[1]) - 4)
        right[3] = ("." * dots + " ", "dot")
        return left + [(" | ", "dim")] + right[1:]

    lines = [[(HANDLE + " ", "handle"), ("─" * (cols - len(HANDLE) - 1), "rule")]]
    lines += [kv(k, v) for k, v in CARD_ABOUT]
    lines += [[]]
    room = cols - len("Languages.Code") - 6
    shown = []
    for lang in langs:  # as many top languages as fit on the line
        if len(", ".join(shown + [lang])) > room:
            break
        shown.append(lang)
    lines += [kv("Languages.Code", ", ".join(shown))] + [kv(k, v) for k, v in CARD_STACK]
    lines += [[]] + [head("Selected work")] + [kv(k, v) for k, v in CARD_WORK]
    lines += [[]] + [head("Contact")] + [kv(k, v) for k, v in CARD_CONTACT]
    lines += [[]] + [head("GitHub stats")] + [pair(stats[0], stats[1]), pair(stats[2], stats[3])]
    lines += [kv("On.GitHub.Since", str(d["since"]))]

    h = round(py + 14 + (len(lines) - 1) * lh + pad + 6)
    rows = []
    for i, parts in enumerate(lines):
        # Every part gets its own x, so no renderer can collapse the spacing.
        spans, at = [], 0
        for txt, c in parts:
            lead = len(txt) - len(txt.lstrip(" "))
            if txt.strip():
                spans.append(f'<tspan x="{x0 + (at + lead) * cw:.1f}" class="{c}">{escape(txt.strip())}</tspan>')
            at += len(txt)
        rows.append(f'<text y="{py + 14 + i * lh:.1f}" class="ln" style="animation-delay:{.4 + i * .07:.2f}s">{"".join(spans)}</text>')
    cur_y = py + 14 + (len(lines) - 1) * lh
    cur_x = x0 + sum(len(txt) for txt, _ in lines[-1]) * cw + 4

    css = f"""
.ln {{ font-family: {FONT}; font-size: {fs}px; animation: type .35s steps(4) backwards; }}
@keyframes type {{ from {{ opacity: 0; transform: translateX(-4px); }} }}
.handle {{ fill: url(#g-card); font-weight: 700; }}
.key {{ fill: {t['a1']}; }}
.val {{ fill: {t['text']}; }}
.dot, .rule {{ fill: {t['dim']}; }}
.dim {{ fill: {t['muted']}; }}
.hd {{ fill: {t['a2']}; }}
.cur {{ animation: blink 1.1s steps(1) infinite; }}
.frame {{ animation: fade 1.2s ease-out backwards; }}
"""
    body = f"""
<defs><linearGradient id="ink" x1="0" y1="0" x2=".3" y2="1"><stop offset="0" stop-color="{t['a1']}"/><stop offset=".6" stop-color="{t['a3']}"/><stop offset="1" stop-color="{t['a2']}"/></linearGradient></defs>
<rect class="frame" x="{px}" y="{py}" width="{pw}" height="{h - 2 * pad}" rx="10" fill="{t['panel']}" stroke="{t['line']}"/>
<svg x="{px}" y="{py}" width="{pw}" height="{h - 2 * pad}" viewBox="0 0 {pw} 420" preserveAspectRatio="xMidYMax meet" overflow="hidden">{portrait[name]}</svg>
{''.join(rows)}
<rect class="cur" x="{cur_x:.1f}" y="{cur_y - 12:.1f}" width="8" height="15" fill="{t['a1']}"/>
"""
    return svg("card", h, t, body, css, f"{NAME}: {ROLE}. {', '.join(TAGS)}. {LOCATION}.")


def stack(totals, t):
    top = totals.most_common(7)
    total = sum(totals.values())
    h = 82 + len(top) * 32
    rows = []
    for i, (lang, n) in enumerate(top):
        y = 74 + i * 32
        pct = 100 * n / total
        bw = (W - 330) * pct / (100 * top[0][1] / total)
        col = languages.COLOURS.get(lang, "#8b949e")
        rows.append(
            f'<g class="up" style="animation-delay:{.1 + i * .08:.2f}s">'
            f'<text x="48" y="{y + 4}" class="m" font-size="13" fill="{t["text"]}">{escape(lang)}</text>'
            f'<rect x="190" y="{y - 6}" width="{W - 330}" height="10" rx="5" fill="{t["panel"]}"/>'
            f'<rect class="bar" style="animation-delay:{.3 + i * .08:.2f}s" x="190" y="{y - 6}" width="{bw:.1f}" height="10" rx="5" fill="{col}"/>'
            f'<text x="{W - 48}" y="{y + 4}" class="m" font-size="13" text-anchor="end" fill="{t["muted"]}">{pct:.1f}%</text></g>'
        )
    css = ".bar { transform-box: fill-box; transform-origin: left; animation: grow 1.2s cubic-bezier(.2,.7,.2,1) backwards; }\n@keyframes grow { from { transform: scaleX(0); } }"
    body = f'{label(48, 38, "stack / share of code in public repos", t)}{"".join(rows)}'
    return svg("stack", h, t, body, css, "Languages: " + ", ".join(f"{l} {100 * n / total:.0f}%" for l, n in top))


def projects(d, t):
    h = 122 + len(d["projects"]) * 96
    rows = []
    for i, (p, note) in enumerate(d["projects"]):
        y = 60 + i * 96
        lang = p["primaryLanguage"] or {"name": "", "color": t["muted"]}
        topics = [n["topic"]["name"] for n in p["repositoryTopics"]["nodes"]][:3]
        pushed = datetime.fromisoformat(p["pushedAt"].replace("Z", "+00:00")).strftime("%b %Y")
        meta = f"{lang['name']}   ·   {'  '.join('#' + x for x in topics)}" if topics else lang["name"]
        rows.append(
            f'<g class="up" style="animation-delay:{.15 + i * .2:.2f}s">'
            f'<circle cx="64" cy="{y + 26}" r="7" fill="{t["bg"]}" stroke="{lang["color"] or t["a1"]}" stroke-width="2"/>'
            f'<circle cx="64" cy="{y + 26}" r="3" fill="{lang["color"] or t["a1"]}" class="node" style="animation-delay:{i * .6:.1f}s"/>'
            f'<rect x="92" y="{y}" width="{W - 140}" height="80" rx="10" fill="{t["panel"]}" stroke="{t["line"]}"/>'
            f'<text x="112" y="{y + 30}" class="s" font-size="17" font-weight="650" fill="{t["text"]}">{escape(p["name"])}</text>'
            f'<text x="{W - 68}" y="{y + 30}" class="m" font-size="11" text-anchor="end" fill="{t["muted"]}">updated {pushed}</text>'
            f'<text x="112" y="{y + 52}" class="s" font-size="12.5" fill="{t["muted"]}">{escape(note)}</text>'
            f'<text x="112" y="{y + 70}" class="m" font-size="11" fill="{t["a1"]}">{escape(meta)}</text></g>'
        )
    line_end = 60 + (len(d["projects"]) - 1) * 96 + 26
    css = f""".trace {{ stroke-dasharray: 4 6; animation: flow 1.6s linear infinite; }}
@keyframes flow {{ to {{ stroke-dashoffset: -20; }} }}
.node {{ animation: blink 2.4s ease-in-out infinite; }}"""
    body = (
        f'{label(48, 38, "selected work / project constellation", t)}'
        f'<line class="trace" x1="64" y1="86" x2="64" y2="{line_end}" stroke="{t["dim"]}" stroke-width="1.5"/>'
        + "".join(rows)
        + f'<text x="{W - 48}" y="{h - 26}" class="m" font-size="11" text-anchor="end" fill="{t["muted"]}">architecture notes and ADRs in each repo →</text>'
    )
    return svg("projects", h, t, body, css, "Selected work: " + ", ".join(p["name"] for p, _ in d["projects"]))


def activity(d, t):
    weeks = d["weeks"]
    size, gap = 12, 3
    gx = (W - len(weeks) * (size + gap) + gap) / 2
    gy = 64
    h = gy + 7 * (size + gap) + 70
    cols = []
    for wi, week in enumerate(weeks):
        cells = "".join(
            f'<rect x="{gx + wi * (size + gap):.1f}" y="{gy + date.fromisoformat(day).isoweekday() % 7 * (size + gap)}" '
            f'width="{size}" height="{size}" rx="2.5" fill="{t["cell"][lvl]}"><title>{day}: {n}</title></rect>'
            for day, n, lvl in week
        )
        cols.append(f'<g class="col" style="animation-delay:{wi * .045:.2f}s">{cells}</g>')
    css = """.col { animation: wave 4.8s ease-in-out infinite; }
@keyframes wave { 0%, 100% { opacity: 1; } 12% { opacity: .35; } 24% { opacity: 1; } }"""
    y = h - 30
    body = (
        f'{label(48, 38, "activity / contribution field, last 12 months", t)}'
        + "".join(cols)
        + f'<text x="48" y="{y}" class="m" font-size="13" fill="{t["text"]}">{d["total"]:,} <tspan fill="{t["muted"]}">contributions</tspan>'
        f'   ·   {d["active"]} <tspan fill="{t["muted"]}">active days</tspan>'
        f'   ·   {d["longest"]} <tspan fill="{t["muted"]}">day longest streak</tspan></text>'
        + "".join(f'<rect x="{W - 48 - (5 - i) * 16}" y="{y - 10}" width="11" height="11" rx="2" fill="{c}"/>' for i, c in enumerate(t["cell"]))
    )
    return svg("activity", h, t, body, css, f"{d['total']} contributions in the last year, {d['active']} active days, longest streak {d['longest']} days")


def main():
    d = fetch()
    portrait = {}
    for theme in THEMES:
        with open(PORTRAIT_FILE.format(theme=theme)) as f:
            portrait[theme] = f.read()
    totals = languages.language_totals()
    langs = [l for l, _ in totals.most_common(8)]
    os.makedirs("assets/profile", exist_ok=True)
    for name, t in THEMES.items():
        out = {
            "card": card(d, langs, portrait, t, name),
            "stack": stack(totals, t),
            "projects": projects(d, t),
            "activity": activity(d, t),
        }
        for section, content in out.items():
            with open(f"assets/profile/{section}-{name}.svg", "w") as f:
                f.write(content)


if __name__ == "__main__":
    main()
