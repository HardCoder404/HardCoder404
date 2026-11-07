"""Render stats/stats.svg and stats/langs.svg from the GitHub GraphQL API.

Runs in a weekly GitHub Action with the built-in GITHUB_TOKEN, so the cards never
depend on a third-party service. Styling matches the profile's dark pink theme.
"""
import json
import os
import sys
import urllib.request
from collections import Counter

LOGIN = os.environ.get("GH_LOGIN", "HardCoder404")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
BG, TITLE, ICON, TEXT, MUTED, RING, BORDER = "#0b0810", "#ff6ab5", "#ff2d8d", "#cdbfcb", "#8e7f8c", "#ff2d8d", "#1c1522"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif"

QUERY = """
query($login:String!){ user(login:$login){
  repositories(first:100, ownerAffiliations:OWNER, isFork:false){ totalCount nodes{ stargazerCount
    languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name color } } } } }
  contributionsCollection{ totalCommitContributions restrictedContributionsCount totalRepositoriesWithContributedCommits }
  pullRequests{ totalCount } issues{ totalCount } } }"""


def gql():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-cards"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"graphql: {data['errors']}")
    return data["data"]["user"]


def fmt(n: int) -> str:
    return f"{n:,}"


def stats_svg(u) -> str:
    repos = u["repositories"]
    stars = sum(r["stargazerCount"] for r in repos["nodes"])
    cc = u["contributionsCollection"]
    commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    rows = [
        ("star", "Total stars", stars),
        ("commit", "Commits (past year)", commits),
        ("pr", "Pull requests", u["pullRequests"]["totalCount"]),
        ("issue", "Issues", u["issues"]["totalCount"]),
        ("repo", "Contributed to (past year)", cc["totalRepositoriesWithContributedCommits"]),
    ]
    icons = {
        "star": "M8 .25a.75.75 0 01.67.41l1.98 4.01 4.43.64a.75.75 0 01.42 1.28l-3.2 3.12.75 4.41a.75.75 0 01-1.09.79L8 12.8l-3.96 2.08a.75.75 0 01-1.09-.79l.75-4.41-3.2-3.12a.75.75 0 01.42-1.28l4.43-.64L7.33.66A.75.75 0 018 .25z",
        "commit": "M10.5 7.75a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm1.43.75a4.002 4.002 0 01-7.86 0H.75a.75.75 0 110-1.5h3.32a4.001 4.001 0 017.86 0h3.32a.75.75 0 110 1.5h-3.32z",
        "pr": "M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z",
        "issue": "M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.25a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5z",
        "repo": "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z",
    }
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="440" height="170" viewBox="0 0 440 170" font-family="{FONT}">',
           f'<rect width="440" height="170" rx="16" fill="{BG}" stroke="{BORDER}"/>',
           f'<text x="25" y="35" font-size="18" font-weight="600" fill="{TITLE}">Prince Raj\'s GitHub stats</text>']
    y = 62
    for key, label, val in rows:
        out.append(f'<g transform="translate(25,{y - 12})"><path fill="{ICON}" d="{icons[key]}"/></g>')
        out.append(f'<text x="50" y="{y}" font-size="14" fill="{TEXT}">{label}:</text>')
        out.append(f'<text x="285" y="{y}" font-size="14" font-weight="700" fill="{TEXT}" text-anchor="end">{fmt(val)}</text>')
        y += 24
    # right ring: public repos
    out.append(f'<circle cx="370" cy="100" r="40" fill="none" stroke="{BORDER}" stroke-width="6"/>')
    out.append(f'<circle cx="370" cy="100" r="40" fill="none" stroke="{RING}" stroke-width="6" stroke-linecap="round" stroke-dasharray="188 251" transform="rotate(-90 370 100)"/>')
    out.append(f'<text x="370" y="98" font-size="24" font-weight="700" fill="{TEXT}" text-anchor="middle">{repos["totalCount"]}</text>')
    out.append(f'<text x="370" y="116" font-size="11" fill="{MUTED}" text-anchor="middle">public repos</text>')
    out.append("</svg>")
    return "\n".join(out)


def langs_svg(u, top=6) -> str:
    size, color = Counter(), {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            size[name] += e["size"]
            color[name] = e["node"]["color"] or "#888"
    total = sum(size.values()) or 1
    langs = [(n, s * 100 / total) for n, s in size.most_common(top)]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="440" height="150" viewBox="0 0 440 150" font-family="{FONT}">',
           f'<rect width="440" height="150" rx="16" fill="{BG}" stroke="{BORDER}"/>',
           f'<text x="25" y="35" font-size="18" font-weight="600" fill="{TITLE}">Most used languages</text>',
           '<defs><clipPath id="bar"><rect x="25" y="50" width="390" height="8" rx="4"/></clipPath></defs>']
    x = 25.0
    for n, pct in langs:
        w = 390 * pct / 100
        out.append(f'<rect x="{x:.1f}" y="50" width="{w:.1f}" height="8" fill="{color[n]}" clip-path="url(#bar)"/>')
        x += w
    for i, (n, pct) in enumerate(langs):
        cx = 25 + (i % 2) * 200
        cy = 84 + (i // 2) * 22
        out.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{color[n]}"/>')
        out.append(f'<text x="{cx + 18}" y="{cy}" font-size="13" fill="{TEXT}">{n} <tspan fill="{MUTED}">{pct:.1f}%</tspan></text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    if not TOKEN:
        sys.exit("set GITHUB_TOKEN")
    user = gql()
    os.makedirs("stats", exist_ok=True)
    open("stats/stats.svg", "w").write(stats_svg(user))
    open("stats/langs.svg", "w").write(langs_svg(user))
    print("wrote stats/stats.svg and stats/langs.svg")
