import math, re, sys, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_static as bs  # noqa: E402
import penrose  # noqa: E402
from theme import THEMES  # noqa: E402

import pytest  # noqa: E402

THEME_NAMES = ["dark", "light"]
LINK_NAMES = ["website", "gitlab", "linkedin", "email", "kofi"]


def outputs(theme):
    out = {"banner": bs.render_banner(theme), "skills": bs.render_skills(theme)}
    for n in LINK_NAMES:
        out[f"link-{n}"] = bs.render_link(n, theme)
    return out


ALL = [(t, k) for t in THEME_NAMES for k in outputs(t)]


@pytest.mark.parametrize("theme,key", ALL)
def test_valid_xml_and_clean(theme, key):
    s = outputs(theme)[key]
    ET.fromstring(s)
    assert "<script" not in s
    assert "prefers-color-scheme" not in s
    for m in re.finditer(r"http[^\s\"'<>]*", s):
        assert m.group(0).startswith("http://www.w3.org"), m.group(0)
    assert "var(--" not in s


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_banner_content_and_motion(theme):
    s = outputs(theme)["banner"]
    assert "Andelib Taref Ababa" in s
    assert ">Open source software developer</text>" in s
    assert "hacker" not in s.lower()
    for pill in ("KDE Plasma tools", "Android apps", "Linux fixes &amp; packaging"):
        assert pill in s
    assert 'viewBox="0 0 1200 340"' in s
    assert "crispEdges" in s
    assert "@keyframes" in s
    m = re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{(.*?)\}\s*\}", s, re.S)
    assert m and "animation:none" in m.group(1).replace(" ", "")
    # banner must be deterministic
    assert s == bs.render_banner(theme)


CELL_PATH_RE = re.compile(r'<path class="(c [^"]+)"(?: opacity="[\d.]+")? d="([^"]+)"/>')


def _cells_by_class(svg):
    """cell -> class string, from the merged cell paths (each square is 'Mx yh8v8h-8z')."""
    out = {}
    for cls, d in CELL_PATH_RE.findall(svg):
        for x, y in re.findall(r"M(\d+) (\d+)h8v8h-8z", d):
            cell = ((int(x) - 1) // bs.CELL, (int(y) - 1) // bs.CELL)
            assert cell not in out, cell
            out[cell] = cls
        assert re.fullmatch(r"(M\d+ \d+h8v8h-8z)+", d), d
    return out


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_banner_has_no_mascot(theme):
    s = outputs(theme)["banner"]
    assert "frog-bob" not in s and "<image" not in s
    assert s.count("<svg") == 1


def test_banner_loop_seamless():
    frames = bs.banner_frames()
    assert len(frames) == penrose.FRAMES + 1
    assert frames[0] == frames[-1]


def test_banner_cells_avoid_text():
    m = 8
    for f in bs.banner_frames():
        for cx, cy in f:
            x0, y0 = cx * bs.CELL, cy * bs.CELL
            x1, y1 = x0 + bs.CELL, y0 + bs.CELL
            assert 0 <= x0 and x1 <= 1200 and 0 <= y0 and y1 <= 340, (cx, cy)
            for bx0, by0, bx1, by1 in bs.TEXT_BOXES:
                assert x1 <= bx0 - m or x0 >= bx1 + m or y1 <= by0 - m or y0 >= by1 + m, ((cx, cy), (bx0, by0, bx1, by1))


def test_text_boxes_cover_pills():
    assert len(bs.TEXT_BOXES) == 5  # name, tagline, three pills
    assert bs.TEXT_BOXES[2][0] == bs.PILL_X0 and bs.TEXT_BOXES[2][1] == 226


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_banner_draws_every_live_cell(theme):
    s = outputs(theme)["banner"]
    cells = _cells_by_class(s)
    frames = bs.banner_frames()
    assert set(cells) == set().union(*frames)
    # without animation (reduced motion) the drawn cells and their shapes are exactly frame 0
    base = {c: int(cls.split()[1][1]) for c, cls in cells.items() if cls.split()[1] in ("s0", "s1")}
    assert base == frames[0] and len(base) > 200


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_banner_size_budget(theme):
    assert len(outputs(theme)["banner"].encode()) <= 135_000


def test_themes_differ_in_background():
    assert THEMES["dark"]["bg"] != THEMES["light"]["bg"]
    assert THEMES["dark"]["bg"] in outputs("dark")["banner"] or THEMES["dark"]["pond_a"] in outputs("dark")["banner"]
    d, l = outputs("dark"), outputs("light")
    assert d["banner"] != l["banner"]
    assert THEMES["dark"]["surface"] in d["skills"]
    assert THEMES["light"]["surface"] in l["skills"]
    assert THEMES["dark"]["surface"] not in l["skills"]


def test_theme_keys():
    keys = "bg surface surface2 border fg muted frog frog_deep lily kde link pond_a grid g0 g1 g2 g3 g4".split()
    for t in THEME_NAMES:
        for k in keys:
            assert re.fullmatch(r"#[0-9a-fA-F]{6}", THEMES[t][k]), (t, k)


def test_icon_files_exist():
    names = set()
    for _, items in bs.GROUPS:
        names.update(slug for _, slug, _ in items)
    for slug in names:
        p = ROOT / "assets/icons/skills" / f"{slug}.svg"
        assert p.exists() and p.stat().st_size > 100, p
    for slug in ("gitlab", "kofi"):
        p = ROOT / "assets/icons/links" / f"{slug}.svg"
        assert p.exists() and p.stat().st_size > 300, p


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_group_order(theme):
    s = outputs(theme)["skills"]
    pos = [s.index(f">{g.replace('&', '&amp;')}<") for g, _ in bs.GROUPS]
    assert pos == sorted(pos)
    assert [g for g, _ in bs.GROUPS] == ["Languages", "Desktop & Linux", "Mobile & games", "Tooling"]
    for _, items in bs.GROUPS:
        for name, _, _ in items:
            assert name.replace("&", "&amp;") in s


def _brand(slug):
    svg = (ROOT / "assets/icons/skills" / f"{slug}.svg").read_text()
    return re.search(r'fill="(#[0-9A-Fa-f]+)"', svg).group(1).lower()


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_skills_width_fits_content(theme):
    s = outputs(theme)["skills"]
    vb = float(re.search(r'viewBox="0 0 ([\d.]+) ', s).group(1))
    right = max(float(m.group(1)) + float(m.group(2)) for m in re.finditer(r'<rect x="([\d.]+)" y="[\d.]+" width="([\d.]+)"', s))
    assert 0 <= vb - right <= 8 and vb <= 1200


def test_mono_handling():
    # Java: mono, fg colour in both themes, brand colour never used
    for t in THEME_NAMES:
        s = outputs(t)["skills"].lower()
        assert _brand("openjdk") not in s
    # C++ / CMake: brand colour in light, fg in dark
    assert _brand("cplusplus") in outputs("light")["skills"].lower()
    assert _brand("cplusplus") not in outputs("dark")["skills"].lower()
    assert _brand("cmake") not in outputs("dark")["skills"].lower()


def test_main_writes_files(tmp_path, monkeypatch):
    monkeypatch.setattr(bs, "OUT", tmp_path)
    assert bs.main() == 0
    for t in THEME_NAMES:
        assert (tmp_path / "banner" / f"{bs.BANNER_NAME}-{t}.svg").exists()
        assert (tmp_path / "skills" / f"skills-{t}.svg").exists()
        for n in LINK_NAMES:
            assert (tmp_path / "links" / f"{n}-{t}.svg").exists()


def _css_state(svg, frame, theme):
    """Cell -> shape the CSS shows during `frame` (evaluates our step-end fill keyframes)."""
    fills = bs.shape_fills(theme)
    shape_of = {fills[0]: 0, fills[1]: 1, "#0000": None}
    kfs = {name: [(float(p), shape_of[f]) for p, f in re.findall(r"([\d.]+)%\{fill:(#\w+)\}", body)]
           for name, body in re.findall(r"@keyframes (k\d+)\{(.*?)\}\n", svg)}
    dur = float(re.search(r"\.c\{animation:([\d.]+)s step-end infinite", svg).group(1))
    delays = {d: float(v) for d, v in re.findall(r"\.(d\d+)\{animation-delay:(-?[\d.]+)s\}", svg)}
    shown = {}
    for cell, cls in _cells_by_class(svg).items():
        parts = cls.split()
        name = next((c for c in parts if c.startswith("k")), None)
        if not name:
            shape = None if "off" in parts else int(parts[1][1])
        else:
            delay = delays[next(c for c in parts if c.startswith("d"))]
            t = (((frame + 0.5) * bs.FRAME_S - delay) % dur) / dur * 100  # mid-frame
            shape = [v for p, v in kfs[name] if p <= t][-1]
        if shape is not None:
            shown[cell] = shape
    return shown


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_banner_css_matches_frames(theme):
    s = outputs(theme)["banner"]
    for i, frame in enumerate(bs.banner_frames()):
        assert _css_state(s, i, theme) == frame, i


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_banner_shapes_distinct(theme):
    f = bs.shape_fills(theme)
    assert f[0] != f[1]
    assert _contrast(f[0], f[1]) >= 1.5


def _contrast(a, b):
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    hi, lo = sorted([lum(a), lum(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("theme,minimum", [("dark", 1.08), ("light", 1.12)])
def test_banner_grid_visible(theme, minimum):
    t = THEMES[theme]
    assert _contrast(t["grid"], t["pond_a"]) >= minimum
    s = outputs(theme)["banner"]
    assert f".bn-grid{{fill:{t['grid']}}}" in s


RAD_RE = re.compile(r'<use href="#t(\d+)" class="rad (r\1)" x="(\d+)" y="(\d+)" '
                    r'style="animation-duration:([\d.]+)s;animation-delay:(-?[\d.]+)s"/>')


def _radiation(svg):
    """Particles as dicts, with their direction's keyframes: start cell, step vector (cells), steps, flight share."""
    kf = {}
    for name, flight, ax, ay in re.findall(
            r"@keyframes (r\d+)\{0%\{transform:translate\(0,0\);opacity:[\d.]+\}([\d.]+)%\{transform:translate\((-?\d+)px,(-?\d+)px\);opacity:0\}", svg):
        kf[name] = (float(flight) / 100, int(ax), int(ay))
    steps = dict(re.findall(r"\.(r\d+)\{animation-name:\1;animation-timing-function:steps\((\d+)\)\}", svg))
    out = []
    for _, name, x, y, dur, delay in RAD_RE.findall(svg):
        flight, ax, ay = kf[name]
        k = int(steps[name])
        assert ax % (k * bs.CELL) == 0 and ay % (k * bs.CELL) == 0, name  # every step lands on the grid
        out.append(dict(cell=((int(x) - 1) // bs.CELL, (int(y) - 1) // bs.CELL), step=(ax // k // bs.CELL, ay // k // bs.CELL),
                        steps=k, flight=flight, dur=float(dur), delay=float(delay)))
    return out


def _mask_rects(svg):
    m = re.search(r'<mask id="nt"[^>]*>(.*?)</mask>', svg, re.S)
    return [tuple(map(int, r)) for r in re.findall(r'<rect x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)" fill="#444"/>', m.group(1))]


def _flying(parts, t, masks):
    """Heads of particles visibly in flight at time t (inside the banner, still bright enough to see)."""
    out = []
    for p in parts:
        phase = ((t - p["delay"]) % p["dur"]) / p["dur"]
        if phase >= p["flight"]:
            continue
        k = int(phase / p["flight"] * p["steps"])  # steps(): holds each step until the next
        x, y = p["cell"][0] + k * p["step"][0], p["cell"][1] + k * p["step"][1]
        px, py = x * bs.CELL, y * bs.CELL
        if 0 <= px < 1200 and 0 <= py < 340 and 1 - k / p["steps"] > 0.15:
            out.append((x, y))
    return out


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_radiation_flows_out_of_the_window(theme):
    parts = _radiation(outputs(theme)["banner"])
    cx, cy, r = penrose.WINDOW
    assert 30 <= len(parts) <= 60
    for p in parts:
        sx, sy = (p["cell"][0] + 0.5) * bs.CELL - cx, (p["cell"][1] + 0.5) * bs.CELL - cy
        assert r + 8 <= abs(complex(sx, sy)) <= r + 40  # born just outside the rim
        radial = math.atan2(sy, sx)
        heading = math.atan2(p["step"][1], p["step"][0])
        assert abs((heading - radial + math.pi) % (2 * math.pi) - math.pi) < math.radians(15)  # heading outward
        assert max(abs(p["step"][0]), abs(p["step"][1])) <= 3


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_radiation_random_and_not_crowded(theme):
    s = outputs(theme)["banner"]
    parts, masks = _radiation(s), _mask_rects(s)
    assert len({p["dur"] for p in parts}) >= 0.8 * len(parts)  # own cycles: emission never visibly repeats
    assert len({p["step"] for p in parts}) >= 8  # many directions, not a few beams
    counts = [len(_flying(parts, t / 2, masks)) for t in range(600)]  # 5 minutes, every 0.5 s
    assert max(counts) <= 18 and 5 <= sum(counts) / len(counts) <= 11
    left = sum(1 for p in parts if p["step"][0] < 0)
    assert 0.25 <= left / len(parts) <= 0.6  # emitted all around, not mostly to the right


def test_window_leaves_room_on_the_left():
    # radiation needs space to travel on every side of the window, not just the right
    cx, cy, r = penrose.WINDOW
    assert cx - r >= 70
    assert min(x0 for x0, _, _, _ in bs.TEXT_BOXES) - (cx + r) >= 40  # and a clear gap before the text


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_radiation_dims_behind_text(theme):
    # particles keep flowing behind the text but at ~27% (mask #444), so the text stays easy to read
    s = outputs(theme)["banner"]
    assert '<g mask="url(#nt)"' in s
    masks = _mask_rects(s)
    for bx0, by0, bx1, by1 in bs.TEXT_BOXES:
        assert any(mx <= bx0 - 12 and my <= by0 - 12 and mx + mw >= bx1 + 12 and my + mh >= by1 + 12
                   for mx, my, mw, mh in masks), (bx0, by0)
    assert all(v % bs.CELL == 0 for m in masks for v in m)  # whole cells only: no half-hidden squares


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_radiation_has_fading_trail(theme):
    s = outputs(theme)["banner"]
    steps = dict(re.findall(r"\.(r\d+)\{animation-name:\1;animation-timing-function:steps\((\d+)\)\}", s))
    ends = {n: (int(ax), int(ay)) for n, ax, ay in re.findall(r"@keyframes (r\d+)\{0%\{[^}]*\}[\d.]+%\{transform:translate\((-?\d+)px,(-?\d+)px\)", s)}
    trails = re.findall(r'<g id="t(\d+)">(.*?)</g>', s)
    assert trails
    for n, body in trails:
        hop = (ends[f"r{n}"][0] // int(steps[f"r{n}"]), ends[f"r{n}"][1] // int(steps[f"r{n}"]))
        rects = re.findall(r'<rect x="(-?\d+)" y="(-?\d+)" width="8" height="8"(?: opacity="([\d.]+)")?/>', body)
        assert len(rects) == 3
        ops = [float(o or 1) for _, _, o in rects]
        assert ops[0] > ops[1] > ops[2] > 0  # head, then two fading ghosts
        pos = [(int(x), int(y)) for x, y, _ in rects]
        assert pos[0] == (0, 0)
        assert pos[1] == (-hop[0], -hop[1]) and pos[2] == (-2 * hop[0], -2 * hop[1])  # one hop back each


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_radiation_hidden_under_reduced_motion(theme):
    s = outputs(theme)["banner"]
    assert re.search(r"\.rad\{[^}]*opacity:0[;}]", s)
    m = re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{(.*?)\}\s*\}", s, re.S)
    assert ".rad" in m.group(1)


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_tiles_stand_out_from_grid(theme):
    # both rhomb shapes must be clearly distinct from an empty grid square
    grid = THEMES[theme]["grid"]
    for shape, fill in bs.shape_fills(theme).items():
        assert _contrast(fill, grid) >= 1.8, (shape, fill)


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_animation_rules_cascade_in_order(theme):
    # the .c shorthand must come before the .kN / .dN longhands, or browsers show a frozen frame 0
    s = outputs(theme)["banner"]
    assert s.index(".c{animation:") < s.index(".k0{animation-name:k0}") < s.index(".d1{animation-delay:")
    for k in re.findall(r"\.(k\d+)\{animation-name:(k\d+)\}", s):
        assert k[0] == k[1]
    names = set(re.findall(r"\.(k\d+)\{animation-name", s))
    assert names == set(re.findall(r"@keyframes (k\d+)", s))


def test_readme_uses_current_banner_files():
    # the banner file name changes when the art changes, so no browser or CDN can show a stale copy
    readme = (ROOT / "README.md").read_text()
    for t in THEME_NAMES:
        assert f"assets/banner/{bs.BANNER_NAME}-{t}.svg" in readme
        assert (ROOT / "assets/banner" / f"{bs.BANNER_NAME}-{t}.svg").read_text() == bs.render_banner(t)
    assert sorted(p.name for p in (ROOT / "assets/banner").iterdir()) == sorted(f"{bs.BANNER_NAME}-{t}.svg" for t in THEME_NAMES)


def test_no_github_link_button():
    # the README is shown on the GitHub profile itself, so a GitHub button would point back to the same page
    assert "github" not in bs.LINKS
    assert not list((ROOT / "assets/links").glob("github-*.svg"))
