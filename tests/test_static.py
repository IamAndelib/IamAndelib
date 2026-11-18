import re, sys, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_static as bs  # noqa: E402
import penrose  # noqa: E402
from theme import THEMES  # noqa: E402

import pytest  # noqa: E402

THEME_NAMES = ["dark", "light"]
LINK_NAMES = ["github", "gitlab", "linkedin", "email", "kofi"]


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
    assert bs.TEXT_BOXES[2][0] == 412 and bs.TEXT_BOXES[2][1] == 226


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
    for slug in ("github", "gitlab", "kofi"):
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
        assert (tmp_path / "banner" / f"banner-{t}.svg").exists()
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


STAR_RE = re.compile(r'<path class="st( halo)?" style="animation-duration:([\d.]+)s;animation-delay:(-?[\d.]+)s" d="([^"]+)"/>')


def _stars(svg):
    """[(is_halo, duration, delay, [cells])] from the star paths."""
    out = []
    for halo, dur, delay, d in STAR_RE.findall(svg):
        assert re.fullmatch(r"(M\d+ \d+h8v8h-8z)+", d), d
        cells = [((int(x) - 1) // bs.CELL, (int(y) - 1) // bs.CELL) for x, y in re.findall(r"M(\d+) (\d+)", d)]
        out.append((bool(halo), float(dur), float(delay), cells))
    return out


def _lit(stars, t):
    """Core stars lit at time t (s): the pop keyframes light a star during 1-9% of its own cycle."""
    return {tuple(c[0]) for halo, dur, delay, c in stars if not halo
            for phase in [((t - delay) % dur) / dur] if 0.01 < phase < 0.09} if stars else set()


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_stars_appear_at_random_places_not_crowded(theme):
    stars = _stars(outputs(theme)["banner"])
    cores = [st for st in stars if not st[0]]
    assert 40 <= len(cores) <= 80
    counts = [len(_lit(stars, t / 2)) for t in range(0, 600)]  # 5 minutes, every 0.5 s
    assert max(counts) <= 10 and 2 <= sum(counts) / len(counts) <= 8  # a handful at a time
    assert min(counts) >= 0
    # where they show up keeps changing: lit sets 10 s apart rarely share a star
    overlap = [len(_lit(stars, t) & _lit(stars, t + 10)) for t in range(0, 300, 5)]
    assert sum(overlap) / len(overlap) < 1
    xs = [c[3][0][0] for c in cores]
    assert min(xs) * bs.CELL < 400 and max(xs) * bs.CELL > 1000  # spread across the banner


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_star_timing_never_lines_up(theme):
    stars = _stars(outputs(theme)["banner"])
    durs = [d for halo, d, _, _ in stars if not halo]
    assert len(set(durs)) >= 0.8 * len(durs)  # distinct cycles: the overall pattern doesn't visibly repeat
    assert min(durs) >= 8 and max(durs) <= 30
    s = outputs(theme)["banner"]
    assert "@keyframes pop" in s and "ease-in-out" in s


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_stars_avoid_text_and_window(theme):
    s = outputs(theme)["banner"]
    cx, cy, r = penrose.WINDOW
    cells = [c for *_, cs in _stars(s) for c in cs]
    assert len(cells) == len(set(cells))  # no overlapping squares
    for x, y in cells:
        x0, y0 = x * bs.CELL, y * bs.CELL
        x1, y1 = x0 + bs.CELL, y0 + bs.CELL
        assert 0 <= x0 and x1 <= 1200 and 0 <= y0 and y1 <= 340
        for bx0, by0, bx1, by1 in bs.TEXT_BOXES:
            assert x1 <= bx0 - 12 or x0 >= bx1 + 12 or y1 <= by0 - 12 or y0 >= by1 + 12, (x, y)
        assert abs(complex(x0 + 5 - cx, y0 + 5 - cy)) >= r + 12, (x, y)


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_stars_hidden_under_reduced_motion(theme):
    s = outputs(theme)["banner"]
    assert re.search(r"\.st\{[^}]*opacity:0[;}]", s)  # base state: dark, so a static banner shows no stars
    m = re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{(.*?)\}\s*\}", s, re.S)
    assert ".st" in m.group(1)


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
