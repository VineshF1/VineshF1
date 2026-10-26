#!/usr/bin/env python3
"""
Build the clickable project cards from projects.json. No packages needed.

Usage (run from the repo root):
    python make_carousel.py
    python make_carousel.py --json projects.json --out-dir assets/cards --readme README.md

What it does:
  1. Reads projects.json (any number of projects, 1 or more).
  2. Writes one animated SVG per project into assets/cards/.
  3. Rewrites the card grid in README.md between these two lines:
         <!-- PROJECT-CARDS:START -->
         <!-- PROJECT-CARDS:END -->

Why one file per project instead of one big carousel SVG:
  GitHub serves README images through <img>, and an SVG loaded as an image is
  non-interactive, so <a> links inside it never fire. A separate SVG per card,
  each wrapped in a real <a href> in the README, is the only way to make each
  card click its own repo while keeping the motion.

Each project in projects.json:
  title         project name                               (required)
  description   one or two sentences, wraps to 3 lines     (required)
  url           repo link used for the click target        (optional)
"""
import argparse, html, json, os, re, sys, textwrap

W, H = 420, 180
SANS = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
GRAD = ('<linearGradient id="ink" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00f5a0"/>'
        '<stop offset=".5" stop-color="#2d9cff"/><stop offset="1" stop-color="#ff4fd8"/></linearGradient>')
WRAP = 46


def esc(s):
    return html.escape(str(s), quote=False)


def slug(title):
    s = re.sub(r"[^a-z0-9]+", "-", str(title).lower()).strip("-")
    return s or "project"


def build_card(p, i):
    n = f"{i:02d}"
    lines = textwrap.wrap(p["description"], WRAP)[:3]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="{esc(p["title"])}: {esc(p["description"])}">',
        f'<defs>{GRAD}'
        f'<filter id="bl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="26"/></filter>'
        f'<clipPath id="cc"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>',
        f'<rect width="{W}" height="{H}" rx="14" fill="#080913"/>',
        '<g clip-path="url(#cc)"><g filter="url(#bl)" opacity=".45">',
        '<circle cx="60" cy="24" r="78" fill="#00f5a0">'
        '<animateTransform attributeName="transform" type="translate" values="0 0;46 16;0 0" dur="14s" repeatCount="indefinite"/></circle>',
        '<circle cx="366" cy="158" r="84" fill="#7c5cff">'
        '<animateTransform attributeName="transform" type="translate" values="0 0;-44 -14;0 0" dur="17s" repeatCount="indefinite"/></circle>',
        '</g></g>',
        f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="13.5" fill="#ffffff" fill-opacity=".04" '
        f'stroke="url(#ink)" stroke-opacity=".55"/>',
        f'<text x="24" y="46" font-family="{SANS}" font-size="24" font-weight="800" fill="#fff">{esc(p["title"])}</text>',
        '<rect x="26" y="58" width="40" height="3" rx="1.5" fill="#00f5a0"/>',
    ]
    for k, line in enumerate(lines):
        out.append(f'<text x="24" y="{88 + k*20}" font-family="{SANS}" font-size="13" fill="#c9cbe8">{esc(line)}</text>')
    out.append(f'<text x="396" y="162" text-anchor="end" font-family="{SANS}" font-size="56" font-weight="800" '
               f'fill="url(#ink)" fill-opacity=".14">{n}</text>')
    out.append('</svg>')
    return "\n".join(out)


def card_grid(projects, out_dir, columns):
    cells = []
    for p in projects:
        src = f"{out_dir}/{slug(p['title'])}.svg"
        img = f'<img src="{src}" width="400" alt="{html.escape(p["title"], quote=True)}" />'
        cells.append(f'<a href="{html.escape(p["url"], quote=True)}">{img}</a>' if p.get("url") else img)
    rows = []
    for i in range(0, len(cells), columns):
        rows.append('<p align="center">\n  ' + "\n  ".join(cells[i:i + columns]) + "\n</p>")
    return "\n\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="projects.json")
    ap.add_argument("--out-dir", default="assets/cards")
    ap.add_argument("--readme", default="README.md")
    ap.add_argument("--columns", type=int, default=2)
    a = ap.parse_args()

    try:
        projects = json.load(open(a.json, encoding="utf-8"))
    except Exception as e:
        sys.exit(f"Cannot read {a.json}: {e}")
    if not isinstance(projects, list) or not projects:
        sys.exit("projects.json must be a non-empty list.")
    for i, p in enumerate(projects, 1):
        miss = [k for k in ("title", "description") if not str(p.get(k, "")).strip()]
        if miss:
            sys.exit(f"Project #{i} is missing: {', '.join(miss)}")
        if len(textwrap.wrap(p["description"], WRAP)) > 3:
            print(f"warning: project #{i} description is longer than 3 lines; the extra text is cut")
        if "REPO_NAME" in p.get("url", ""):
            print(f"warning: project #{i} url still has a REPO_NAME placeholder")

    os.makedirs(a.out_dir, exist_ok=True)
    written = set()
    for i, p in enumerate(projects, 1):
        path = os.path.join(a.out_dir, f"{slug(p['title'])}.svg")
        open(path, "w", encoding="utf-8").write(build_card(p, i))
        written.add(os.path.normpath(path))
        print(f"wrote {path}")

    for f in os.listdir(a.out_dir):
        if f.endswith(".svg") and os.path.normpath(os.path.join(a.out_dir, f)) not in written:
            os.remove(os.path.join(a.out_dir, f))
            print(f"removed stale {a.out_dir}/{f}")

    if os.path.exists(a.readme):
        txt = open(a.readme, encoding="utf-8").read()
        pat = re.compile(r"(<!-- PROJECT-CARDS:START -->).*?(<!-- PROJECT-CARDS:END -->)", re.S)
        if pat.search(txt):
            grid = card_grid(projects, a.out_dir.replace("\\", "/"), a.columns)
            txt = pat.sub(lambda m: f"{m.group(1)}\n{grid}\n{m.group(2)}", txt)
            open(a.readme, "w", encoding="utf-8").write(txt)
            print(f"updated card grid in {a.readme}")
        else:
            print(f"note: no PROJECT-CARDS markers in {a.readme}; grid not updated. Paste this yourself:\n"
                  f"{card_grid(projects, a.out_dir.replace(chr(92), '/'), a.columns)}")


if __name__ == "__main__":
    main()
