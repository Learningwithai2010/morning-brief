#!/usr/bin/env python3
"""
Reads brief_data.json, renders it into the HTML template, writes docs/YYYY-MM-DD.html,
updates docs/index.html, then commits and pushes via git.
"""

import html
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR  = REPO_ROOT / "docs"
TEMPLATE  = REPO_ROOT / "templates" / "brief_template.html"
DATA_FILE = REPO_ROOT / "brief_data.json"


def get_github_pages_url() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        return ""
    # repo is "owner/name"
    parts = repo.split("/")
    if len(parts) != 2:
        return ""
    owner, name = parts
    return f"https://{owner}.github.io/{name}"


def render_stories(stories: list) -> str:
    parts = []
    for story in stories:
        title   = html.escape(story.get("title", ""))
        summary = html.escape(story.get("summary", ""))
        source  = html.escape(story.get("source", ""))
        url     = html.escape(story.get("url", "#"))
        parts.append(f"""      <div class="story">
        <p class="story-title">{title}</p>
        <p class="story-summary">{summary}</p>
        <p class="story-source"><a href="{url}" target="_blank" rel="noopener">{source}</a></p>
      </div>""")
    return "\n".join(parts)


def render_brief(data: dict) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")

    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_display = dt.strftime("%A, %B %-d, %Y")
    except ValueError:
        date_display = date_str

    sections = data.get("sections", {})

    def sec(key):
        return sections.get(key, {})

    replacements = {
        "{{DATE_DISPLAY}}":       date_display,
        "{{HOLISTIC_SUMMARY}}":   html.escape(data.get("holistic_summary", "")),
        "{{POLITICS_HEADLINE}}":  html.escape(sec("politics").get("headline", "")),
        "{{POLITICS_STORIES}}":   render_stories(sec("politics").get("stories", [])),
        "{{TECH_HEADLINE}}":      html.escape(sec("tech_and_ai").get("headline", "")),
        "{{TECH_STORIES}}":       render_stories(sec("tech_and_ai").get("stories", [])),
        "{{SOCCER_HEADLINE}}":    html.escape(sec("soccer").get("headline", "")),
        "{{SOCCER_STORIES}}":     render_stories(sec("soccer").get("stories", [])),
        "{{BASKETBALL_HEADLINE}}": html.escape(sec("basketball").get("headline", "")),
        "{{BASKETBALL_STORIES}}": render_stories(sec("basketball").get("stories", [])),
    }

    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)

    return template


def update_index(date_str: str, date_display: str, pages_url: str):
    index_path = DOCS_DIR / "index.html"

    # Collect all existing brief dates from docs/
    existing = sorted(
        [f.stem for f in DOCS_DIR.glob("????-??-??.html")],
        reverse=True
    )

    # Ensure today is included
    if date_str not in existing:
        existing.insert(0, date_str)

    rows = []
    for d in existing:
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
            label = dt.strftime("%A, %B %-d, %Y")
        except ValueError:
            label = d
        href = f"{d}.html"
        rows.append(f'      <li><a href="{href}">{label}</a></li>')

    list_html = "\n".join(rows)

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Maxi's Morning Brief — Archive</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #0f1117; color: #e8eaf0;
      font-family: 'DM Sans', sans-serif;
      padding: 0 16px 48px;
    }}
    .page {{ max-width: 680px; margin: 0 auto; }}
    .masthead {{
      text-align: center; padding: 40px 0 32px;
      border-bottom: 1px solid #252a3a; margin-bottom: 32px;
    }}
    .masthead-eyebrow {{
      font-size: 11px; font-weight: 600; letter-spacing: 0.18em;
      text-transform: uppercase; color: #7a8099; margin-bottom: 8px;
    }}
    h1 {{
      font-family: 'Playfair Display', serif;
      font-size: clamp(28px, 8vw, 48px); font-weight: 900;
      color: #fff; letter-spacing: -0.02em; line-height: 1.1;
    }}
    h2 {{
      font-family: 'Playfair Display', serif;
      font-size: 20px; color: #fff; margin-bottom: 16px;
    }}
    ul {{ list-style: none; }}
    li {{ border-bottom: 1px solid #252a3a; }}
    li a {{
      display: block; padding: 16px 0;
      font-size: 15px; font-weight: 500;
      color: #b0b8cc; text-decoration: none;
      transition: color 0.15s;
    }}
    li a:hover {{ color: #f0b429; }}
    .footer {{
      text-align: center; padding-top: 32px;
      font-size: 12px; color: #7a8099;
    }}
  </style>
</head>
<body>
<div class="page">
  <header class="masthead">
    <p class="masthead-eyebrow">Archive</p>
    <h1>Maxi's Morning Brief</h1>
  </header>
  <h2>Past Editions</h2>
  <ul>
{list_html}
  </ul>
  <footer class="footer">Generated by Claude &middot; Maxi's Morning Brief</footer>
</div>
</body>
</html>"""

    index_path.write_text(index_html, encoding="utf-8")
    print(f"Updated docs/index.html ({len(existing)} entries)")


def git_push(date_str: str):
    cmds = [
        ["git", "config", "user.name", "Morning Brief Bot"],
        ["git", "config", "user.email", "bot@morning-brief"],
        ["git", "add", "docs/"],
        ["git", "commit", "-m", f"Morning Brief: {date_str}"],
        ["git", "push"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        if result.returncode != 0:
            # "nothing to commit" is fine
            if "nothing to commit" in result.stdout + result.stderr:
                print("git: nothing new to commit, skipping push")
                return
            print(f"git error ({' '.join(cmd)}): {result.stderr}", file=sys.stderr)
            sys.exit(1)
        if result.stdout.strip():
            print(result.stdout.strip())


def main():
    if not DATA_FILE.exists():
        print("ERROR: brief_data.json not found — run generate_brief.py first", file=sys.stderr)
        sys.exit(1)

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_display = dt.strftime("%A, %B %-d, %Y")
    except ValueError:
        date_display = date_str

    DOCS_DIR.mkdir(exist_ok=True)

    # Ensure .nojekyll exists (prevents GitHub Pages from running Jekyll)
    nojekyll = DOCS_DIR / ".nojekyll"
    if not nojekyll.exists():
        nojekyll.touch()

    # Render and write the daily brief HTML
    rendered = render_brief(data)
    out_path = DOCS_DIR / f"{date_str}.html"
    out_path.write_text(rendered, encoding="utf-8")
    print(f"Written: {out_path}")

    pages_url = get_github_pages_url()
    update_index(date_str, date_display, pages_url)

    git_push(date_str)
    print(f"Published: {pages_url}/{date_str}.html")


if __name__ == "__main__":
    main()
