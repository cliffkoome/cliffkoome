"""Render the animated profile sections in assets/profile/.

Each section is written twice, as <name>-dark.svg and <name>-light.svg, and the
README picks one with <picture>. Everything is plain SVG + CSS animation, so it
renders inside GitHub's image proxy with no scripts. Motion stops for people
who ask for reduced motion: every element's resting state is its final state,
and animations only run "from" an earlier state.

Needs GITHUB_TOKEN (GraphQL requires auth). Standard library only; the
portrait is drawn once by portrait.py and read from assets/profile/portrait-*.svg.
"""

import json
import re
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

FOCUS = [
    ("Devices to cloud", "Hardware, phones and cloud services that agree on what's true."),
    ("Built for failure", "Dropped networks and duplicate events are the normal case."),
    ("Decisions on record", "Trade-offs written down as ADRs, with a scaling plan."),
]

# Selected work: repo, two short lines about it, tags to show (chosen here, not
# taken from repo topics, so they stay accurate).
PROJECTS = [
    ("MatConnect", ["Live matatu ETAs from in-vehicle GPS, with SMS", "alerts. A leased job never counts a trip twice."],
     ["neon-postgres", "prisma", "firebase"]),
    ("InstaScreen", ["Cloud-synced ESP32 photo frame. Checksummed", "chunks fit 320 KB of RAM, with no backend."],
     ["esp32", "platformio", "python"]),
    ("typeghast", ["A terminal typing game haunted by your coding", "agent's context rot. Runs a local Gemma model."],
     ["bubbletea", "ollama", "gemma"]),
    ("haki-afya", ["Checks a hospital bill against SHA tariffs.", "AI reads the bill; plain code decides."],
     ["fastapi", "react", "gemma-4"]),
]

# More I've built: repo, display name, two short lines. Placed on a launch line
# in the order the repos were created.
MORE = [
    ("ds-loadbalancer", "ds-loadbalancer", ["consistent hashing,", "self-healing replicas"]),
    ("chamaconnect-bug-patch", "ChamaConnect fixes", ["15 vulnerabilities", "found, then patched"]),
    ("echo-reach", "Echo Reach", ["climate alerts by", "phone call"]),
    ("zephyr", "Zephyr", ["offline AI tutor", "for 8 GB laptops"]),
    ("hack-mavericks-mtah2027", "Hack Mavericks", ["ball-possession model,", "reproducible to the byte"]),
    ("local-llm-speedtune", "llm-speedtune", ["local LLMs 3.1x", "faster, by measuring"]),
]

# Repos whose docs/adr folders are counted for the "adrs written" stat.
ADR_REPOS = ["MatConnect", "InstaScreen"]
AWARDS = 3  # hackathon awards listed in the README

ICON_FOR = {"TypeScript": "typescript", "Python": "python", "C++": "cplusplus", "Go": "go",
            "JavaScript": "javascript", "Kotlin": "kotlin", "Dart": "dart"}

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

PORTRAIT_FILE = "assets/profile/portrait-{theme}.svg"  # written by portrait.py



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
    fields = ("name createdAt pushedAt primaryLanguage { name color } "
              "languages(first: 1, orderBy: {field: SIZE, direction: DESC}) { totalSize edges { size } }")
    names = " ".join(f'p{i}: repository(name: "{n}") {{ {fields} }}' for i, (n, _, _) in enumerate(PROJECTS))
    names += " " + " ".join(f'm{i}: repository(name: "{n}") {{ {fields} }}' for i, (n, _, _) in enumerate(MORE))
    adrs = " ".join(f'a{i}: repository(name: "{n}") {{ object(expression: "HEAD:docs/adr") {{ ... on Tree {{ entries {{ name }} }} }} }}'
                    for i, n in enumerate(ADR_REPOS))
    data = graphql(f"""{{ user(login: "{USER}") {{
        contributionsCollection {{ contributionCalendar {{ totalContributions }} }}
        {adrs}
        {names}
    }} }}""")["user"]
    adr_count = sum(1 for i in range(len(ADR_REPOS)) for e in (data[f"a{i}"]["object"] or {}).get("entries", [])
                    if re.match(r"\d{4}-.+\.md$", e["name"]))
    return {
        "total": data["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "adrs": adr_count,
        "projects": [(data[f"p{i}"], note, tags) for i, (_, note, tags) in enumerate(PROJECTS)],
        "more": sorted(((data[f"m{i}"], name, note) for i, (_, name, note) in enumerate(MORE)),
                       key=lambda m: m[0]["createdAt"]),
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

def hero(d, portrait, t):
    h = 380
    cx, cy, rr = W - 40 - 133, h / 2, 154      # orbit ring around the portrait
    R = rr - 18                                # everything inside the ring stays within this circle, with a gap
    ph = round(2 * R * 1.03)                   # portrait box; portrait.py draws at 336x420
    pw = round(ph * 336 / 420)
    px, py = cx - pw / 2, cy + R - ph          # shoulders rest on the bottom of the circle

    stats = [
        (f"{d['total']:,}", "contributions"),
        (f"{d['adrs']}", "adrs written"),
        (f"{len(PROJECTS) + len(MORE)}", "projects"),
        (f"{AWARDS}", "awards"),
    ]
    stat_svg = []
    for i, ((v, k), x) in enumerate(zip(stats, (48, 196, 336, 446))):
        stat_svg.append(
            f'<g class="up" style="animation-delay:{1.1 + i * .12:.2f}s">'
            f'<text x="{x}" y="{h - 62}" class="m" font-size="24" font-weight="600" fill="{t["text"]}">{escape(v)}</text>'
            f'<text x="{x}" y="{h - 40}" class="lab" font-size="10" letter-spacing="1.5">{escape(k.upper())}</text></g>'
        )
    stats_end = 516

    tags = []
    x = 48
    for i, tag in enumerate(TAGS):
        w = 18 + len(tag) * 7.6
        tags.append(
            f'<g class="up" style="animation-delay:{.8 + i * .1:.2f}s"><rect x="{x}" y="198" width="{w:.0f}" height="26" rx="13" fill="none" stroke="{t["line"]}"/>'
            f'<text x="{x + w / 2:.0f}" y="215" class="m" font-size="12" text-anchor="middle" fill="{t["text"]}">{escape(tag)}</text></g>'
        )
        x += w + 10

    css = f"""
.scan {{ animation: scan 6s linear infinite; }}
@keyframes scan {{ from {{ transform: translateY(0); }} to {{ transform: translateY({2 * R}px); }} }}
.cur {{ animation: blink 1.1s steps(1) infinite; }}
.live {{ animation: blink 2s ease-in-out infinite; }}
.ring {{ transform-origin: {cx:.0f}px {cy:.0f}px; animation: spin 48s linear infinite; }}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
"""
    body = f"""
<defs>
<linearGradient id="ink" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t['a1']}"/><stop offset=".65" stop-color="{t['a3']}"/><stop offset="1" stop-color="{t['a2']}"/></linearGradient>
<radialGradient id="fadeg"><stop offset=".8" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
<mask id="fade"><circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R}" fill="url(#fadeg)"/></mask>
</defs>
{label(48, 40, "profile / living identity", t)}
<line x1="48" y1="56" x2="{stats_end}" y2="56" stroke="{t['line']}"/>
<g class="up" style="animation-delay:.15s">{label(48, 92, "hello, world. i'm", t)}</g>
<text x="48" y="150" class="s up" style="animation-delay:.3s" font-size="50" font-weight="700" fill="url(#g-hero)">{escape(NAME)}</text>
<text x="48" y="182" class="m up" style="animation-delay:.55s" font-size="16" fill="{t['text']}">{escape(ROLE)}<tspan class="cur" fill="{t['a1']}">_</tspan></text>
{''.join(tags)}
<text x="48" y="254" class="m up" style="animation-delay:1.05s" font-size="12" fill="{t['muted']}">{escape(LOCATION)}  ·  EAT (UTC+3)  ·  @{USER}</text>
<line x1="48" y1="{h - 100}" x2="{stats_end}" y2="{h - 100}" stroke="{t['line']}"/>
{''.join(stat_svg)}
<radialGradient id="halo"><stop offset="0" stop-color="{t['a3']}" stop-opacity=".16"/><stop offset="1" stop-color="{t['a3']}" stop-opacity="0"/></radialGradient>
<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R}" fill="url(#halo)"/>
<g class="ring" fill="none" stroke="url(#g-hero)" stroke-linecap="round">
<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rr}" stroke-width="1.5" stroke-opacity=".6" stroke-dasharray="90 28 0.01 28"/>
<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rr + 9}" stroke-width="1" stroke-opacity=".16"/></g>
<g mask="url(#fade)"><svg x="{px}" y="{py:.0f}" width="{pw}" height="{ph:.0f}" viewBox="0 0 336 420">{portrait}</svg>
<rect class="scan" x="{cx - R:.0f}" y="{cy - R:.0f}" width="{2 * R}" height="2" fill="{t['a1']}" opacity=".45"/></g>
"""
    return svg("hero", h, t, body, css, f"{NAME}: {ROLE}, {', '.join(TAGS)}. {LOCATION}.")


def focus(t):
    h = 170
    colw = (W - 96 - 40) / 3
    cards = []
    for i, (head, line) in enumerate(FOCUS):
        x = 48 + i * (colw + 20)
        words, lines, cur = line.split(), [], ""
        for w_ in words:
            if len(cur) + len(w_) > 34:
                lines.append(cur)
                cur = w_
            else:
                cur = f"{cur} {w_}".strip()
        lines.append(cur)
        tsp = "".join(f'<tspan x="{x + 18:.0f}" dy="{0 if j == 0 else 18}">{escape(l)}</tspan>' for j, l in enumerate(lines))
        cards.append(
            f'<g class="up" style="animation-delay:{.15 + i * .18:.2f}s">'
            f'<rect x="{x:.0f}" y="56" width="{colw:.0f}" height="90" rx="10" fill="{t["panel"]}" stroke="{t["line"]}"/>'
            f'<rect x="{x:.0f}" y="56" width="3" height="90" rx="1.5" fill="url(#g-focus)"/>'
            f'<text x="{x + 18:.0f}" y="84" class="m" font-size="11" fill="{t["a1"]}">0{i + 1}</text>'
            f'<text x="{x + 44:.0f}" y="84" class="s" font-size="15" font-weight="600" fill="{t["text"]}">{escape(head)}</text>'
            f'<text y="110" class="s" font-size="12.5" fill="{t["muted"]}">{tsp}</text></g>'
        )
    body = f'{label(48, 38, "current focus", t)}{"".join(cards)}'
    return svg("focus", h, t, body, title="Current focus: " + "; ".join(f"{a}: {b}" for a, b in FOCUS))


# Toolbox: what I build with, grouped by layer. (slug in icons.json, label)
# Icons are Simple Icons (CC0), vendored in icons.json so nothing loads at view time.
TOOLBOX = [
    ("languages", [("typescript", "TypeScript"), ("python", "Python"), ("cplusplus", "C/C++"),
                   ("go", "Go"), ("kotlin", "Kotlin"), ("dart", "Dart")]),
    ("web + backend", [("nodedotjs", "Node.js"), ("nextdotjs", "Next.js"), ("react", "React"),
                       ("fastapi", "FastAPI"), ("postgresql", "Postgres"), ("prisma", "Prisma")]),
    ("embedded + iot", [("espressif", "ESP32"), ("arduino", "Arduino"), ("platformio", "PlatformIO"),
                        ("bluetooth", "BLE"), ("firebase", "Firebase")]),
    ("mobile", [("flutter", "Flutter"), ("expo", "Expo"), ("android", "Android")]),
    ("data + ai", [("pandas", "pandas"), ("scikitlearn", "sklearn"), ("ollama", "Ollama"),
                   ("googlegemini", "Gemini")]),
    ("ship", [("githubactions", "Actions"), ("docker", "Docker"), ("nginx", "Nginx"),
              ("ubuntu", "Ubuntu"), ("vercel", "Vercel")]),
]


def toolbox(totals, t):
    with open(os.path.join(os.path.dirname(__file__), "icons.json")) as f:
        icons = json.load(f)
    colw, rowh, top = (W - 96 - 40) / 2, 84, 62
    rows_n = (len(TOOLBOX) + 1) // 2
    bar_y = top + rows_n * rowh + 18
    h = bar_y + 62
    parts, k = [], 0
    for gi, (group, items) in enumerate(TOOLBOX):
        gx = 48 + (gi % 2) * (colw + 40)
        gy = top + (gi // 2) * rowh
        parts.append(f'<text x="{gx:.0f}" y="{gy}" class="lab" font-size="10" style="fill:{t['a1']}">{escape(group.upper())}</text>')
        for ii, (slug, name) in enumerate(items):
            x = gx + ii * 62
            sc = 22 / 24
            parts.append(
                f'<g class="up" style="animation-delay:{.1 + k * .035:.2f}s">'
                f'<g transform="translate({x + 20:.0f} {gy + 14}) scale({sc:.3f})"><path d="{icons[slug]["d"]}"/></g>'
                f'<text x="{x + 31:.0f}" y="{gy + 52}" class="m" font-size="9.5" text-anchor="middle" fill="{t["muted"]}">{escape(name)}</text></g>'
            )
            k += 1
    # language share: one thin segmented bar with an inline legend
    langs = [(l, n) for l, n in totals.most_common(6)]
    total = sum(totals.values())
    bw, x = W - 96, 48.0
    segs, legend = [], []
    for i, (lang, n) in enumerate(langs):
        w = bw * n / total
        col = languages.COLOURS.get(lang, "#8b949e")
        segs.append(f'<rect x="{x:.1f}" y="{bar_y + 14}" width="{max(w - 2, 1):.1f}" height="6" rx="3" fill="{col}"/>')
        x += w
    if x < 48 + bw - 1:  # everything else, so the bar spans the full share
        segs.append(f'<rect x="{x:.1f}" y="{bar_y + 14}" width="{48 + bw - x:.1f}" height="6" rx="3" fill="{t["dim"]}"/>')
    lx = 48
    for lang, n in langs:
        txt = f"{lang} {100 * n / total:.0f}%"
        col = languages.COLOURS.get(lang, "#8b949e")
        legend.append(f'<circle cx="{lx + 4}" cy="{bar_y + 39}" r="3.5" fill="{col}"/>'
                      f'<text x="{lx + 12}" y="{bar_y + 43}" class="m" font-size="11" fill="{t["muted"]}">{escape(txt)}</text>')
        lx += 22 + len(txt) * 6.8
    css = ".seg { transform-box: fill-box; transform-origin: left; animation: grow 1.4s cubic-bezier(.2,.7,.2,1) backwards .6s; }\n" \
          "@keyframes grow { from { transform: scaleX(0); } }"
    body = (
        f'{label(48, 38, "toolbox / what I build with", t)}'
        f'<g fill="{t["text"]}" fill-opacity=".88">{"".join(parts)}</g>'
        f'<line x1="48" y1="{bar_y - 8}" x2="{W - 48}" y2="{bar_y - 8}" stroke="{t["line"]}"/>'
        f'{label(48, bar_y + 4, "code in public repos", t)}'
        f'<g class="seg">{"".join(segs)}</g>{"".join(legend)}'
    )
    names = "; ".join(f"{g}: {', '.join(n for _, n in items)}" for g, items in TOOLBOX)
    return svg("toolbox", h, t, body, css, f"Toolbox. {names}. Languages: " + ", ".join(f"{l} {100 * n / total:.0f}%" for l, n in langs))


def ago(iso):
    days = (date.today() - datetime.fromisoformat(iso.replace("Z", "+00:00")).date()).days
    if days < 1:
        return "today"
    if days < 45:
        return f"{days}d ago"
    return f"{round(days / 30)}mo ago"


def lang_share(p):
    l = p["languages"]
    return round(100 * l["edges"][0]["size"] / l["totalSize"]) if l["totalSize"] else 0


def projects(d, t):
    """Selected work as a 2x2 grid of terminal-style cards with a language gauge."""
    cw, ch, gap, top = (W - 96 - 20) / 2, 158, 20, 66
    rows = (len(d["projects"]) + 1) // 2
    h = top + rows * ch + (rows - 1) * gap + 40
    cards = []
    for i, (p, note, tags) in enumerate(d["projects"]):
        x = 48 + (i % 2) * (cw + gap)
        y = top + (i // 2) * (ch + gap)
        lang = p["primaryLanguage"] or {"name": "", "color": t["muted"]}
        col = lang["color"] or t["a1"]
        pct = lang_share(p)
        r = 24
        circ = 2 * 3.14159 * r
        gx, gy = x + cw - 46, y + 82
        chips, cx = [], x + 18
        for tag in tags:
            w = 16 + len(tag) * 6.1
            chips.append(f'<rect x="{cx:.0f}" y="{y + 112}" width="{w:.0f}" height="20" rx="10" fill="none" stroke="{t["line"]}"/>'
                         f'<text x="{cx + w / 2:.0f}" y="{y + 126}" class="m" font-size="10" text-anchor="middle" fill="{t["muted"]}">{escape(tag)}</text>')
            cx += w + 6
        desc = "".join(f'<tspan x="{x + 18:.0f}" dy="{0 if k == 0 else 17}">{escape(line)}</tspan>' for k, line in enumerate(note))
        cards.append(f"""<g class="up" style="animation-delay:{.15 + i * .15:.2f}s">
<rect x="{x:.0f}" y="{y}" width="{cw:.0f}" height="{ch}" rx="10" fill="{t['panel']}" stroke="{t['line']}"/>
<line x1="{x:.0f}" y1="{y + 26}" x2="{x + cw:.0f}" y2="{y + 26}" stroke="{t['line']}"/>
<text x="{x + 16:.0f}" y="{y + 17}" class="m" font-size="10" fill="{t['muted']}">· {escape(p['name'])}</text>
<circle cx="{x + cw - 16:.0f}" cy="{y + 13}" r="3" fill="{t['a1']}" class="live"/>
<text x="{x + 18:.0f}" y="{y + 52}" class="m" font-size="16" font-weight="700" fill="{t['text']}">{escape(p['name'])}<tspan class="cur" fill="{t['a1']}"> _</tspan></text>
<text y="{y + 74}" class="s" font-size="12" fill="{t['muted']}">{desc}</text>
<circle cx="{gx:.0f}" cy="{gy - 28}" r="{r}" fill="none" stroke="{t['line']}" stroke-width="5"/>
<circle cx="{gx:.0f}" cy="{gy - 28}" r="{r}" fill="none" stroke="{col}" stroke-width="5" stroke-linecap="round"
  stroke-dasharray="{circ * pct / 100:.1f} {circ:.1f}" transform="rotate(-90 {gx:.0f} {gy - 28})" class="gauge" style="--c:{circ:.1f}"/>
<text x="{gx:.0f}" y="{gy - 24}" class="m" font-size="11" font-weight="600" text-anchor="middle" fill="{t['text']}">{pct}%</text>
<text x="{gx:.0f}" y="{gy + 10}" class="m" font-size="9.5" text-anchor="middle" fill="{t['muted']}">{escape(lang['name'])}</text>
{''.join(chips)}
<text x="{x + cw - 18:.0f}" y="{y + 126}" class="m" font-size="10" text-anchor="end" fill="{t['dim']}">updated {ago(p['pushedAt'])}</text>
</g>""")
    css = """.gauge { animation: gauge 1.4s cubic-bezier(.2,.7,.2,1) backwards .5s; }
@keyframes gauge { from { stroke-dasharray: 0 var(--c); } }
.live { animation: blink 2.4s ease-in-out infinite; }
.cur { animation: blink 1.1s steps(1) infinite; }"""
    body = (f'{label(48, 38, "selected work / projects.list", t)}'
            f'<text x="{W - 48}" y="38" class="lab" text-anchor="end">{len(d["projects"])} projects</text>'
            f'<line x1="48" y1="48" x2="{W - 48}" y2="48" stroke="{t["line"]}"/>'
            + "".join(cards))
    return svg("projects", h, t, body, css, "Selected work: " + ", ".join(p["name"] for p, _, _ in d["projects"]))


def more(d, t):
    """More I've built: repos on a dated launch line, labels alternating above and below."""
    with open(os.path.join(os.path.dirname(__file__), "icons.json")) as f:
        icons = json.load(f)
    items = d["more"]
    h, ly = 330, 168
    x0, x1 = 90, W - 90
    step = (x1 - x0) / (len(items) - 1)
    nodes = []
    for i, (p, name, note) in enumerate(items):
        x = x0 + i * step
        lang = p["primaryLanguage"] or {"name": "", "color": t["muted"]}
        col = lang["color"] or t["a1"]
        slug = ICON_FOR.get(lang["name"])
        icon = (f'<g transform="translate({x - 9:.1f} {ly - 9}) scale(.75)" fill="{col}"><path d="{icons[slug]["d"]}"/></g>'
                if slug else "")
        when = datetime.fromisoformat(p["createdAt"].replace("Z", "+00:00")).strftime("%b %Y")
        above = i % 2 == 0
        ty = ly - 92 if above else ly + 48
        lines = "".join(f'<tspan x="{x:.1f}" dy="{0 if k == 0 else 14}">{escape(l)}</tspan>' for k, l in enumerate(note))
        nodes.append(f"""<g class="up" style="animation-delay:{.3 + i * .18:.2f}s">
<line x1="{x:.1f}" y1="{ly - 28 if above else ly + 28}" x2="{x:.1f}" y2="{ly - 40 if above else ly + 40}" stroke="{t['line']}"/>
<g class="orb" style="transform-origin:{x:.1f}px {ly}px;animation-duration:{18 + i * 3}s"><circle cx="{x:.1f}" cy="{ly}" r="25" fill="none" stroke="{col}" stroke-opacity=".55" stroke-dasharray="8 6"/></g>
<circle cx="{x:.1f}" cy="{ly}" r="18" fill="{t['bg']}" stroke="{col}" stroke-width="1.5"/>
{icon}
<text x="{x:.1f}" y="{ty}" class="m" font-size="9.5" text-anchor="middle" fill="{t['dim']}">{when}</text>
<text x="{x:.1f}" y="{ty + 18}" class="s" font-size="13" font-weight="650" text-anchor="middle" fill="{t['text']}">{escape(name)}</text>
<text y="{ty + 35}" class="s" font-size="10.5" text-anchor="middle" fill="{t['muted']}">{lines}</text>
</g>""")
    css = f""".orb {{ animation: spin 20s linear infinite; }}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
.flow {{ stroke-dasharray: 5 7; animation: flow 1.4s linear infinite; }}
@keyframes flow {{ to {{ stroke-dashoffset: -24; }} }}
.pulse {{ animation: travel 7s cubic-bezier(.45,0,.55,1) infinite; }}
@keyframes travel {{ from {{ transform: translateX(0); opacity: 0; }} 8% {{ opacity: 1; }} 92% {{ opacity: 1; }} to {{ transform: translateX({x1 - x0:.0f}px); opacity: 0; }} }}"""
    first = datetime.fromisoformat(items[0][0]["createdAt"].replace("Z", "+00:00")).strftime("%b %Y")
    body = (f'{label(48, 38, "more i have built / launch sequence", t)}'
            f'<text x="{W - 48}" y="38" class="lab" text-anchor="end">{len(items)} repos since {first.lower()}</text>'
            f'<line x1="48" y1="48" x2="{W - 48}" y2="48" stroke="{t["line"]}"/>'
            f'<line class="flow" x1="{x0 - 30}" y1="{ly}" x2="{x1 + 30}" y2="{ly}" stroke="{t["dim"]}" stroke-width="1.5"/>'
            f'<circle class="pulse" cx="{x0}" cy="{ly}" r="3.5" fill="{t["a1"]}"/>'
            + "".join(nodes))
    return svg("more", h, t, body, css, "More I've built: " + ", ".join(n for _, n, _ in items))


def main():
    d = fetch()
    portrait = {}
    for theme in THEMES:
        with open(PORTRAIT_FILE.format(theme=theme)) as f:
            portrait[theme] = f.read()
    totals = languages.language_totals()
    os.makedirs("assets/profile", exist_ok=True)
    for name, t in THEMES.items():
        out = {
            "hero": hero(d, portrait[name], t),
            "focus": focus(t),
            "toolbox": toolbox(totals, t),
            "projects": projects(d, t),
            "more": more(d, t),
        }
        for section, content in out.items():
            with open(f"assets/profile/{section}-{name}.svg", "w") as f:
                f.write(content)


if __name__ == "__main__":
    main()
