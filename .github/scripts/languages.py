"""Render a "most used languages" card from my public repositories.

Writes assets/languages-light.svg and assets/languages-dark.svg. Only public,
non-fork repositories are counted, plus the repos in EXTRA_REPOS that I
contribute to under someone else's account.
"""

import json
import os
import urllib.request
from collections import Counter
from html import escape

USER = "cliffkoome"
EXTRA_REPOS = ["davidongora/Agenti"]
# Course and workshop repos: the code in them isn't mine.
SKIP_REPOS = {"cliffkoome", "Kubernetes-Course-Labs", "react-workshop"}
SKIP_LANGUAGES = {"Tape", "Dockerfile", "Makefile", "Procfile", "Batchfile"}
TOP = 8

# Colours from GitHub Linguist, so the card matches the repo language bars.
COLOURS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5",
    "Dart": "#00B4AB", "Kotlin": "#A97BFF", "Go": "#00ADD8", "CSS": "#663399",
    "HTML": "#e34c26", "PHP": "#4F5D95", "C#": "#178600", "C++": "#f34b7d",
    "C": "#555555", "Java": "#b07219", "Rust": "#dea584", "Shell": "#89e051",
    "Swift": "#F05138", "Vue": "#41b883", "SCSS": "#c6538c",
}

THEMES = {
    "light": {"bg": "#ffffff", "border": "#d0d7de", "title": "#1f2328", "text": "#59636e"},
    "dark": {"bg": "#0d1117", "border": "#30363d", "title": "#f0f6fc", "text": "#9198a1"},
}


def get(path):
    req = urllib.request.Request(f"https://api.github.com/{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if token := os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def language_totals():
    repos = get(f"users/{USER}/repos?per_page=100&type=owner")
    names = [
        r["full_name"] for r in repos
        if not r["private"] and not r["fork"] and r["name"] not in SKIP_REPOS
    ]
    totals = Counter()
    for name in names + EXTRA_REPOS:
        totals.update(get(f"repos/{name}/languages"))
    for lang in SKIP_LANGUAGES:
        totals.pop(lang, None)
    return totals


def render(totals, theme):
    t = THEMES[theme]
    total = sum(totals.values())
    top = totals.most_common(TOP)
    width, bar_w, x0 = 400, 352, 24

    bar, x = [], x0
    for lang, n in top:
        w = bar_w * n / total
        bar.append(f'<rect x="{x:.2f}" y="52" width="{w:.2f}" height="8" fill="{COLOURS.get(lang, "#8b949e")}"/>')
        x += w

    legend = []
    for i, (lang, n) in enumerate(top):
        cx = x0 + (i % 2) * 180
        cy = 88 + (i // 2) * 24
        legend.append(
            f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{COLOURS.get(lang, "#8b949e")}"/>'
            f'<text x="{cx + 16}" y="{cy}" class="t">{escape(lang)} '
            f'<tspan class="p">{100 * n / total:.1f}%</tspan></text>'
        )

    height = 88 + ((len(top) + 1) // 2) * 24
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
<title id="title">Most used languages: {escape(", ".join(f"{l} {100 * n / total:.0f}%" for l, n in top))}</title>
<style>
text {{ font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }}
.h {{ font-size: 16px; font-weight: 600; fill: {t["title"]}; }}
.t {{ font-size: 13px; fill: {t["title"]}; }}
.p {{ fill: {t["text"]}; }}
</style>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" fill="{t["bg"]}" stroke="{t["border"]}"/>
<text x="{x0}" y="34" class="h">Most used languages</text>
<clipPath id="bar"><rect x="{x0}" y="52" width="{bar_w}" height="8" rx="4"/></clipPath>
<g clip-path="url(#bar)">{"".join(bar)}</g>
{"".join(legend)}
</svg>
"""


def main():
    totals = language_totals()
    os.makedirs("assets", exist_ok=True)
    for theme in THEMES:
        with open(f"assets/languages-{theme}.svg", "w") as f:
            f.write(render(totals, theme))


if __name__ == "__main__":
    main()
