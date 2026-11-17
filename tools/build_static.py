"""Build the standalone banner, skills strip and link-button SVGs (dark + light)."""
import html
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import FONT, THEMES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ASSETS  # output root (tests redirect this)
esc = lambda s: html.escape(s, quote=True)

# (label, icon slug, mode); mode "mono" = fg in both themes, "monodark" = fg in dark only
GROUPS = [
    ("Languages", [("C++", "cplusplus", "monodark"), ("TypeScript", "typescript", ""), ("JavaScript", "javascript", ""), ("Python", "python", ""), ("Kotlin", "kotlin", ""), ("Java", "openjdk", "mono"), ("Bash", "gnubash", ""), ("GDScript", "godotengine", "")]),
    ("Desktop & Linux", [("KDE Plasma", "kdeplasma", ""), ("Qt / QML", "qt", ""), ("Wayland", "wayland", ""), ("Fedora", "fedora", ""), ("Flatpak", "flatpak", ""), ("Linux", "linux", "")]),
    ("Mobile & games", [("Android", "android", ""), ("Capacitor", "capacitor", ""), ("Preact", "preact", ""), ("Godot", "godotengine", "")]),
    ("Tooling", [("Git", "git", ""), ("GitHub Actions", "githubactions", ""), ("CMake", "cmake", "monodark"), ("Podman", "podman", "")]),
]

LINKEDIN = ('<path fill-rule="evenodd" d="M4 2h16a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm2.5 7.5v8h2.6v-8Zm1.3-4.2a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm3.7 4.2v8h2.6v-4.3c0-1.2.5-1.9 1.5-1.9s1.4.7 1.4 1.9v4.3h2.6v-4.9c0-2.4-1.3-3.3-3-3.3-1.2 0-2 .5-2.5 1.2v-1Z"/>')
MAIL = ('<path d="M2 5.5A2.5 2.5 0 0 1 4.5 3h15A2.5 2.5 0 0 1 22 5.5v13a2.5 2.5 0 0 1-2.5 2.5h-15A2.5 2.5 0 0 1 2 18.5Zm2.4-.5L12 10.7 19.6 5Zm15.6 2.2-7.4 5.5a1 1 0 0 1-1.2 0L4 7.2v11.3c0 .3.2.5.5.5h15c.3 0 .5-.2.5-.5Z"/>')

# name -> (label, icon file slug or None, inline path, brand colour or None for fg)
LINKS = {
    "github": ("GitHub", "github", None, None),
    "gitlab": ("GitLab", "gitlab", None, "icon"),
    "linkedin": ("LinkedIn", None, LINKEDIN, "#0A66C2"),
    "email": ("Email", None, MAIL, "#3fb950"),
    "kofi": ("Ko-fi", "kofi", None, "icon"),
}


def _icon(folder: str, slug: str):
    svg = (ASSETS / "icons" / folder / f"{slug}.svg").read_text()
    paths = "".join(re.findall(r"<path[^>]*/>", svg))
    m = re.search(r'fill="(#[0-9A-Fa-f]+)"', svg)
    return paths, (m.group(1) if m else None)


def _head(w, h, label, t):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{esc(label)}">')


def render_banner(theme: str, mascot_svg: str) -> str:
    t = THEMES[theme]
    mascot = re.sub(r"<\?xml[^>]*\?>", "", mascot_svg).strip()
    root = re.match(r"<svg\b[^>]*>", mascot).group(0)
    new_root = re.sub(r'\s(?:width|height|x|y)="[^"]*"', "", root)
    new_root = new_root.replace("<svg", '<svg x="40" y="6" width="300" height="300"', 1)
    mascot = new_root + mascot[len(root):]
    pills = [("KDE Plasma tools", t["kde"]), ("Android apps", t["frog"]), ("Linux fixes & packaging", "#d29922")]
    px, pill_svg = 412, ""
    for text, color in pills:
        w = round(len(text) * 8.4 + 34)
        pill_svg += (f'<rect class="bn-pill" x="{px}" y="226" width="{w}" height="36" rx="18" style="stroke:{color}"/>'
                     f'<circle cx="{px+17}" cy="244" r="4" style="fill:{color}"/>'
                     f'<text class="bn-pilltext" x="{px+28}" y="249">{esc(text)}</text>')
        px += w + 10
    rnd = random.Random(7)
    ff = "".join(
        f'<rect class="ff" x="{rnd.randint(380,1170)}" y="{rnd.choice([rnd.randint(16,80), rnd.randint(282,326)])}" '
        f'width="9" height="9" rx="2" style="animation-delay:{rnd.uniform(0,4):.1f}s"/>' for _ in range(22))
    css = f"""
.bn-bg{{fill:{t['pond_a']}}} .bn-water{{fill:{t['pond_b']}}}
.bn-ripple{{fill:none;stroke:{t['ripple']};stroke-width:2;transform-box:fill-box;transform-origin:center;animation:ripple 6s ease-out infinite}}
.r2{{animation-delay:2s}} .r3{{animation-delay:4s}}
.bn-pad{{fill:{t['pad']}}} .bn-vein{{stroke:{t['pad_vein']};stroke-width:3;fill:none}}
.bn-name{{fill:{t['fg']};font:800 54px {FONT};letter-spacing:-.5px}}
.bn-tag{{fill:{t['muted']};font:500 22px {FONT}}}
.bn-pill{{fill:{t['bg']};stroke-width:1.5}}
.bn-pilltext{{font:600 15px {FONT};fill:{t['fg']}}}
.ff{{fill:{t['g3']};animation:twinkle 4s ease-in-out infinite}}
.frog-bob{{animation:bob 5s ease-in-out infinite;transform-box:fill-box;transform-origin:center bottom}}
@keyframes ripple{{0%{{opacity:.9;transform:scale(.4)}}100%{{opacity:0;transform:scale(1.25)}}}}
@keyframes twinkle{{0%,100%{{opacity:.15}}50%{{opacity:1}}}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-6px)}}}}
@media (prefers-reduced-motion: reduce){{.bn-ripple,.ff,.frog-bob{{animation:none}}}}
"""
    return (_head(1200, 340, "Andelib Taref Ababa, Linux desktop hacker and Android developer", t) + "\n"
            f"<style>{css}</style>\n"
            f'<rect class="bn-bg" width="1200" height="340"/>\n'
            '<path class="bn-water" d="M0 250 C 200 232, 400 268, 600 250 S 1000 232, 1200 250 V340 H0Z"/>\n'
            '<ellipse class="bn-ripple" cx="190" cy="300" rx="190" ry="34"/><ellipse class="bn-ripple r2" cx="190" cy="300" rx="190" ry="34"/><ellipse class="bn-ripple r3" cx="190" cy="300" rx="190" ry="34"/>\n'
            '<path class="bn-pad" d="M190 270 C 300 270, 335 290, 330 304 C 322 324, 250 332, 190 332 C 110 332, 52 322, 50 304 C 48 288, 92 270, 172 270 L 186 298 Z"/>\n'
            '<path class="bn-vein" d="M186 298 L 110 316 M186 298 L 262 318 M186 298 L 300 296 M186 298 L 76 296"/>\n'
            f"{ff}\n"
            f'<g class="frog-bob">{mascot}</g>\n'
            '<text class="bn-name" x="410" y="148">Andelib Taref Ababa</text>\n'
            '<text class="bn-tag" x="412" y="192">Linux desktop hacker · Android developer</text>\n'
            f"{pill_svg}\n</svg>\n")


def render_skills(theme: str) -> str:
    t = THEMES[theme]
    W, LABEL_W, X0, TILE_H, GAP, ROW_GAP = 1200, 150, 170, 36, 8, 18
    body, y = "", 4
    for title, items in GROUPS:
        x, row_y, rows = X0, y, 1
        tiles = ""
        for name, slug, mode in items:
            tw = round(len(name) * 7.4 + 48)
            if x + tw > W - 4 and x > X0:
                x, row_y, rows = X0, row_y + TILE_H + GAP, rows + 1
            paths, brand = _icon("skills", slug)
            fill = t["fg"] if mode == "mono" or (mode == "monodark" and theme == "dark") else (brand or t["fg"])
            tiles += (f'<rect x="{x}" y="{row_y}" width="{tw}" height="{TILE_H}" rx="8" fill="{t["surface"]}" stroke="{t["border"]}"/>'
                      f'<svg x="{x+8}" y="{row_y+8}" width="20" height="20" viewBox="0 0 24 24" fill="{fill}">{paths}</svg>'
                      f'<text x="{x+36}" y="{row_y+23}" class="nm">{esc(name)}</text>')
            x += tw + GAP
        gh = rows * TILE_H + (rows - 1) * GAP
        body += f'<text x="0" y="{y + gh/2 + 4:.1f}" class="lb">{esc(title)}</text>{tiles}\n'
        y += gh + ROW_GAP
    H = y - ROW_GAP + 4
    css = (f".lb{{fill:{t['muted']};font:600 11px {FONT};letter-spacing:.06em;text-transform:uppercase}}"
           f".nm{{fill:{t['fg']};font:500 13px {FONT}}}")
    return _head(W, H, "Skills: languages, desktop and Linux, mobile and games, tooling", t) + f"<style>{css}</style>\n{body}</svg>\n"


def render_link(name: str, theme: str) -> str:
    t = THEMES[theme]
    label, slug, inline, color = LINKS[name]
    if slug:
        paths, brand = _icon("links", slug)
    else:
        paths, brand = inline, None
    fill = t["fg"] if color is None else (brand if color == "icon" else color)
    w, h = round(len(label) * 7.8 + 54), 36
    return (_head(w, h, label, t) +
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="17.5" fill="{t["surface"]}" stroke="{t["border"]}"/>'
            f'<svg x="14" y="10" width="16" height="16" viewBox="0 0 24 24" fill="{fill}">{paths}</svg>'
            f'<text x="38" y="23" fill="{t["fg"]}" style="font:600 13px {FONT}">{esc(label)}</text></svg>\n')


def main() -> int:
    mascot = (ASSETS / "mascot" / "frog.svg").read_text()
    for d in ("banner", "skills", "links"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (OUT / "banner" / f"banner-{theme}.svg").write_text(render_banner(theme, mascot))
        (OUT / "skills" / f"skills-{theme}.svg").write_text(render_skills(theme))
        for n in LINKS:
            (OUT / "links" / f"{n}-{theme}.svg").write_text(render_link(n, theme))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
