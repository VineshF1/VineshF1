#!/usr/bin/env python3
"""
Build the animated project carousel from projects.json. No packages needed.

Usage (run from the repo root):
    python3 make_carousel.py
    python3 make_carousel.py --seconds 6 --json projects.json --out assets/projects.svg --readme README.md

What it does:
  1. Reads projects.json (any number of projects, 1 or more).
  2. Writes assets/projects.svg (the animated carousel).
  3. Rewrites the link row in README.md between these two lines:
         <!-- PROJECT-LINKS:START -->
         <!-- PROJECT-LINKS:END -->
     (skipped if README.md or the markers are missing).

Each project in projects.json:
  title         project name                               (required)
  description   one or two sentences, wraps to 3 lines     (required)
  url           repo link used in the README link row      (optional)
"""
import argparse, html, json, os, re, sys, textwrap

W, H = 1200, 270
SANS = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
GRAD = ('<linearGradient id="ink" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00f5a0"/>'
        '<stop offset=".5" stop-color="#2d9cff"/><stop offset="1" stop-color="#ff4fd8"/></linearGradient>')


def esc(s):
    return html.escape(str(s), quote=False)


def build_svg(projects, seg):
    n = len(projects)
    total = n * seg
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="Project carousel: {esc(", ".join(p["title"] for p in projects))}">',
        f'<defs>{GRAD}<filter id="bl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="45"/></filter>'
        f'<clipPath id="cc"><rect width="{W}" height="{H}" rx="16"/></clipPath></defs>',
        f'<rect width="{W}" height="{H}" rx="16" fill="#080913"/>',
        '<g clip-path="url(#cc)"><g filter="url(#bl)" opacity=".5">'
        '<circle cx="200" cy="60" r="110" fill="#00f5a0"><animateTransform attributeName="transform" type="translate" values="0 0;120 30;0 0" dur="16s" repeatCount="indefinite"/></circle>'
        '<circle cx="1000" cy="220" r="120" fill="#7c5cff"><animateTransform attributeName="transform" type="translate" values="0 0;-140 -30;0 0" dur="18s" repeatCount="indefinite"/></circle>'
        '</g></g>',
    ]
    fade = min(0.7, seg / 4)
    kt = f"0;{fade/total:.5f};{(seg-fade)/total:.5f};{seg/total:.5f};1"
    for i, p in enumerate(projects):
        if n > 1:
            anim = (f'<g opacity="0">'
                    f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="{kt}" dur="{total}s" begin="{i*seg}s" repeatCount="indefinite"/>'
                    f'<animateTransform attributeName="transform" type="translate" values="40 0;0 0;0 0;-40 0;-40 0" keyTimes="{kt}" dur="{total}s" begin="{i*seg}s" repeatCount="indefinite"/>')
        else:
            anim = '<g>'
        out.append(anim)
        out.append('<rect x="60" y="34" width="1080" height="180" rx="16" fill="#ffffff" fill-opacity=".05" stroke="url(#ink)" stroke-opacity=".7"/>')
        out.append(f'<text x="1104" y="170" text-anchor="end" font-family="{SANS}" font-size="120" font-weight="800" fill="url(#ink)" fill-opacity=".16">{i+1:02d}</text>')
        out.append(f'<text x="96" y="96" font-family="{SANS}" font-size="38" font-weight="800" fill="#fff">{esc(p["title"])}</text>')
        out.append('<rect x="98" y="110" width="56" height="3" rx="1.5" fill="#00f5a0"/>')
        for k, line in enumerate(textwrap.wrap(p["description"], 70)[:3]):
            out.append(f'<text x="96" y="{148 + k*28}" font-family="{SANS}" font-size="20" fill="#c9cbe8">{esc(line)}</text>')
        out.append('</g>')
    if n > 1:
        gap = 26 if n <= 12 else max(10, 300 // n)
        kd = f"0;0.0001;{seg/total:.5f};{seg/total+0.0001:.5f};1"
        for i in range(n):
            x = 600 + (i - (n - 1) / 2) * gap
            out.append(f'<circle cx="{x:.1f}" cy="244" r="4" fill="#ffffff" fill-opacity=".25"/>'
                       f'<circle cx="{x:.1f}" cy="244" r="4" fill="#00f5a0" opacity="0">'
                       f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="{kd}" dur="{total}s" begin="{i*seg}s" repeatCount="indefinite"/></circle>')
    out.append('</svg>')
    return "\n".join(out)


def link_row(projects):
    parts = []
    for p in projects:
        t = esc(p["title"])
        parts.append(f'<a href="{html.escape(p["url"], quote=True)}">{t}</a>' if p.get("url") else t)
    return '<p align="center">\n  ' + " &nbsp;·&nbsp;\n  ".join(parts) + "\n</p>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="projects.json")
    ap.add_argument("--out", default="assets/projects.svg")
    ap.add_argument("--readme", default="README.md")
    ap.add_argument("--seconds", type=float, default=5, help="seconds each card stays on screen")
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
        if len(p["title"]) > 34:
            print(f"warning: project #{i} title is long ({len(p['title'])} chars) and may run into the number on the right")
        if len(textwrap.wrap(p["description"], 70)) > 3:
            print(f"warning: project #{i} description is longer than 3 lines; the extra text is cut")
        if "REPO_NAME" in p.get("url", ""):
            print(f"warning: project #{i} url still has a REPO_NAME placeholder")

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(build_svg(projects, a.seconds))
    print(f"wrote {a.out} with {len(projects)} project(s), {a.seconds}s each")

    if os.path.exists(a.readme):
        txt = open(a.readme, encoding="utf-8").read()
        pat = re.compile(r"(<!-- PROJECT-LINKS:START -->).*?(<!-- PROJECT-LINKS:END -->)", re.S)
        if pat.search(txt):
            txt = pat.sub(lambda m: f"{m.group(1)}\n{link_row(projects)}\n{m.group(2)}", txt)
            open(a.readme, "w", encoding="utf-8").write(txt)
            print(f"updated link row in {a.readme}")
        else:
            print(f"note: no PROJECT-LINKS markers in {a.readme}; link row not updated. Paste this yourself:\n{link_row(projects)}")


if __name__ == "__main__":
    main()
