"""Build the standalone banner, skills strip and link-button SVGs (dark + light)."""
import functools
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import FONT, THEMES  # noqa: E402
import life  # noqa: E402

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

TERMINAL = ('<path fill-rule="evenodd" d="M3 4h18a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Zm1 2v12h16V6Zm2.3 2.6 1.4-1.4 4.4 4.4-4.4 4.4-1.4-1.4 3-3ZM12.5 15h5.5v2h-5.5Z"/>')

# name -> (label, icon file slug or None, inline path, brand colour or None for fg)
LINKS = {
    "website": ("Website", None, TERMINAL, "#3fb950"),
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


CELL = 10  # banner Life cell pitch in px (8 px square + 2 px gap)
GUN_AT = (1, 7)  # gun box top-left, in cells; stream leaves through the bottom edge left of the pills
GEN_S = 0.25  # seconds per generation
PILLS = [("KDE Plasma tools", "kde"), ("Android apps", "frog"), ("Linux fixes & packaging", None)]
PILL_X0, PILL_Y, PILL_H = 412, 226, 36


def _pill_layout():
    x, out = PILL_X0, []
    for text, key in PILLS:
        w = round(len(text) * 8.4 + 34)
        out.append((x, w, text, key))
        x += w + 10
    return out


# Generous text extents (px): name 54px/800 at baseline 148, tagline 22px at baseline 192, then the pills.
TEXT_BOXES = [(410, 100, 1050, 162), (412, 172, 905, 198)] + [
    (x, PILL_Y, x + w, PILL_Y + PILL_H) for x, w, _, _ in _pill_layout()]


@functools.lru_cache(maxsize=None)
def banner_frames():
    """One loop of the glider gun in banner cell coordinates: 31 frames, frame 0 == frame 30."""
    gx, gy = GUN_AT
    cols, rows = 1200 // CELL, 340 // CELL
    seed = frozenset((x + gx, y + gy) for x, y in life.GOSPER_GUN)
    return tuple(life.steady_cycle(seed, warmup=300, period=30,
                                   keep=lambda x, y: 0 <= x < cols and 0 <= y < rows))


def _life_cells(t):
    frames = banner_frames()[:-1]
    n = len(frames)
    canon, rects = {}, []  # canonical timeline -> keyframes name
    for cx, cy in sorted(set().union(*frames), key=lambda c: (c[1], c[0])):
        tl = tuple((cx, cy) in f for f in frames)
        cls = "c" if tl[0] else "c off"
        style = ""
        if not all(tl):
            # share one @keyframes between timelines that are time-shifts of each other
            rots = [tl[s:] + tl[:s] for s in range(n)]
            key = min(rots)
            shift = rots.index(key)
            if key not in canon:
                canon[key] = f"k{len(canon)}"
            style = f' style="animation:{canon[key]} {n * GEN_S:g}s step-end infinite;animation-delay:{-((n - shift) % n) * GEN_S:g}s"'
        rects.append(f'<rect class="{cls}" x="{cx * CELL + 1}" y="{cy * CELL + 1}" width="{CELL - 2}" height="{CELL - 2}"{style}/>')
    kf = ""
    for key, name in canon.items():
        stops = [f"{i * 100 / n:.3f}".rstrip("0").rstrip(".") + f"%{{opacity:{int(v)}}}"
                 for i, v in enumerate(key) if i == 0 or v != key[i - 1]]
        kf += f"@keyframes {name}{{{''.join(stops)}100%{{opacity:{int(key[0])}}}}}\n"
    return "".join(rects), kf


def render_banner(theme: str) -> str:
    t = THEMES[theme]
    pill_svg = ""
    for px, w, text, key in _pill_layout():
        color = t[key] if key else "#d29922"
        pill_svg += (f'<rect class="bn-pill" x="{px}" y="{PILL_Y}" width="{w}" height="{PILL_H}" rx="18" style="stroke:{color}"/>'
                     f'<circle cx="{px+17}" cy="244" r="4" style="fill:{color}"/>'
                     f'<text class="bn-pilltext" x="{px+28}" y="249">{esc(text)}</text>')
    cells, keyframes = _life_cells(t)
    css = f"""
.bn-bg{{fill:{t['pond_a']}}} .bn-grid{{fill:{t['grid']}}}
.c{{fill:{t['g3']}}} .off{{opacity:0}}
.bn-name{{fill:{t['fg']};font:800 54px {FONT};letter-spacing:-.5px}}
.bn-tag{{fill:{t['muted']};font:500 22px {FONT}}}
.bn-pill{{fill:{t['bg']};stroke-width:1.5}}
.bn-pilltext{{font:600 15px {FONT};fill:{t['fg']}}}
{keyframes}@media (prefers-reduced-motion: reduce){{.c{{animation:none!important}}}}
"""
    return (_head(1200, 340, "Andelib Taref Ababa, Linux desktop hacker and Android developer", t) + "\n"
            f"<style>{css}</style>\n"
            f'<defs><pattern id="grid" width="{CELL}" height="{CELL}" patternUnits="userSpaceOnUse">'
            f'<rect class="bn-grid" x="1" y="1" width="{CELL - 2}" height="{CELL - 2}" rx="1.5"/></pattern></defs>\n'
            f'<rect class="bn-bg" width="1200" height="340"/>\n'
            '<rect width="1200" height="340" fill="url(#grid)"/>\n'
            f'<g shape-rendering="crispEdges">{cells}</g>\n'
            '<text class="bn-name" x="410" y="148">Andelib Taref Ababa</text>\n'
            '<text class="bn-tag" x="412" y="192">Linux desktop hacker · Android developer</text>\n'
            f"{pill_svg}\n</svg>\n")


def render_skills(theme: str) -> str:
    t = THEMES[theme]
    MAXW, X0, TILE_H, GAP, ROW_GAP = 1200, 170, 36, 8, 18
    body, y, max_right = "", 4, 0
    for title, items in GROUPS:
        x, row_y, rows = X0, y, 1
        tiles = ""
        for name, slug, mode in items:
            tw = round(len(name) * 7.4 + 48)
            if x + tw > MAXW - 4 and x > X0:
                x, row_y, rows = X0, row_y + TILE_H + GAP, rows + 1
            paths, brand = _icon("skills", slug)
            fill = t["fg"] if mode == "mono" or (mode == "monodark" and theme == "dark") else (brand or t["fg"])
            tiles += (f'<rect x="{x}" y="{row_y}" width="{tw}" height="{TILE_H}" rx="8" fill="{t["surface"]}" stroke="{t["border"]}"/>'
                      f'<svg x="{x+8}" y="{row_y+8}" width="20" height="20" viewBox="0 0 24 24" fill="{fill}">{paths}</svg>'
                      f'<text x="{x+36}" y="{row_y+23}" class="nm">{esc(name)}</text>')
            max_right = max(max_right, x + tw)
            x += tw + GAP
        gh = rows * TILE_H + (rows - 1) * GAP
        body += f'<text x="0" y="{y + gh/2 + 4:.1f}" class="lb">{esc(title)}</text>{tiles}\n'
        y += gh + ROW_GAP
    H = y - ROW_GAP + 4
    W = max_right + 4
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
    for d in ("banner", "skills", "links"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (OUT / "banner" / f"banner-{theme}.svg").write_text(render_banner(theme))
        (OUT / "skills" / f"skills-{theme}.svg").write_text(render_skills(theme))
        for n in LINKS:
            (OUT / "links" / f"{n}-{theme}.svg").write_text(render_link(n, theme))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
