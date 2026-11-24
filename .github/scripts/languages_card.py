"""Render a "Most Used Languages" SVG card from public repositories only.

Usage: GH_TOKEN=<token> python3 languages_card.py <out.svg>
The token only needs read access to the repositories (fine-grained: Metadata read-only).
Repository names are never printed, because Actions logs of a public repository are public.
"""
import html
import json
import os
import sys
import urllib.request

API = "https://api.github.com"
LIMIT = 8
# shortcut: fixed GitHub linguist colors for common languages, others are gray; add an entry when a new language shows up.
COLORS = {
    "Python": "#3572A5", "C++": "#f34b7d", "C": "#555555", "C#": "#178600", "Java": "#b07219",
    "Kotlin": "#A97BFF", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "HTML": "#e34c26",
    "CSS": "#663399", "SCSS": "#c6538c", "Vue": "#41b883", "Jupyter Notebook": "#DA5B0B",
    "Shell": "#89e051", "Dockerfile": "#384d54", "Go": "#00ADD8", "Rust": "#dea584",
    "Swift": "#F05138", "Dart": "#00B4AB", "PHP": "#4F5D95", "Ruby": "#701516",
}


def get(url, token):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def language_bytes(token):
    totals, counted, page = {}, 0, 1
    while True:
        repos = get(f"{API}/user/repos?affiliation=owner&visibility=public&per_page=100&page={page}", token)
        for repo in repos:
            if repo["fork"]:
                continue
            counted += 1
            for lang, size in get(repo["languages_url"], token).items():
                totals[lang] = totals.get(lang, 0) + size
        if len(repos) < 100:
            break
        page += 1
    print(f"repositories counted: {counted}")
    return totals


def render(totals):
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:LIMIT]
    shown = sum(size for _, size in top)
    height = 85 + (len(top) + 1) // 2 * 25
    bar, legend, x = [], [], 0.0
    for i, (lang, size) in enumerate(top):
        color = COLORS.get(lang, "#858585")
        width = 250 * size / shown
        bar.append(f'<rect x="{x:.2f}" width="{width:.2f}" height="8" fill="{color}"/>')
        x += width
        legend.append(
            f'<g transform="translate({i % 2 * 150},{i // 2 * 25})">'
            f'<circle cx="5" cy="6" r="5" fill="{color}"/>'
            f'<text x="15" y="10" class="lang">{html.escape(lang)} {size / shown * 100:.2f}%</text></g>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="{height}" '
        f'viewBox="0 0 300 {height}" role="img" aria-labelledby="title">'
        '<title id="title">Most Used Languages</title>'
        "<style>.header{font:600 18px 'Segoe UI',Ubuntu,Sans-Serif;fill:#70a5fd}"
        ".lang{font:400 11px 'Segoe UI',Ubuntu,Sans-Serif;fill:#38bdae}</style>"
        f'<rect width="300" height="{height}" rx="4.5" fill="#1a1b27"/>'
        '<text x="25" y="35" class="header">Most Used Languages</text>'
        '<g transform="translate(25,55)"><clipPath id="bar"><rect width="250" height="8" rx="4"/></clipPath>'
        f'<g clip-path="url(#bar)">{"".join(bar)}</g></g>'
        f'<g transform="translate(25,80)">{"".join(legend)}</g></svg>'
    )


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: languages_card.py <out.svg>")
    totals = language_bytes(os.environ["GH_TOKEN"])
    if not totals:
        sys.exit("no language data: check that the token can read the repositories")
    out = sys.argv[1]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(totals))


if __name__ == "__main__":
    main()
