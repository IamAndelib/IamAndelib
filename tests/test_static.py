import re, sys, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_static as bs  # noqa: E402
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
    assert "Linux desktop hacker · Android developer" in s
    for pill in ("KDE Plasma tools", "Android apps", "Linux fixes &amp; packaging"):
        assert pill in s
    assert 'viewBox="0 0 1200 340"' in s
    assert "crispEdges" in s
    assert "@keyframes" in s
    m = re.search(r"@media \(prefers-reduced-motion: reduce\)\s*\{(.*?)\}\s*\}", s, re.S)
    assert m and "animation:none" in m.group(1).replace(" ", "")
    # banner must be deterministic
    assert s == bs.render_banner(theme)


CELL_RE = re.compile(r'<rect class="(c[^"]*)" x="([\d.]+)" y="([\d.]+)" width="(\d+)" height="\4"')


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_banner_has_no_mascot(theme):
    s = outputs(theme)["banner"]
    assert "frog-bob" not in s and "<image" not in s
    assert s.count("<svg") == 1


def test_banner_loop_seamless():
    frames = bs.banner_frames()
    assert len(frames) == 31
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
    cells = {(round((float(x) - 1) / bs.CELL), round((float(y) - 1) / bs.CELL)): cls for cls, x, y, _ in CELL_RE.findall(s)}
    frames = bs.banner_frames()
    assert set(cells) == set().union(*frames)
    # without animation (reduced motion) the visible cells are exactly frame 0: gun plus gliders in flight
    shown = {c for c, cls in cells.items() if "off" not in cls.split()}
    assert shown == frames[0] and len(shown) > 36
    assert THEMES[theme]["g3"] in s


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_banner_size_budget(theme):
    assert len(outputs(theme)["banner"].encode()) <= 80_000


def test_themes_differ_in_background():
    assert THEMES["dark"]["bg"] != THEMES["light"]["bg"]
    assert THEMES["dark"]["bg"] in outputs("dark")["banner"] or THEMES["dark"]["pond_a"] in outputs("dark")["banner"]
    d, l = outputs("dark"), outputs("light")
    assert d["banner"] != l["banner"]
    assert THEMES["dark"]["surface"] in d["skills"]
    assert THEMES["light"]["surface"] in l["skills"]
    assert THEMES["dark"]["surface"] not in l["skills"]


def test_theme_keys():
    keys = "bg surface surface2 border fg muted frog frog_deep lily kde link pond_a g0 g1 g2 g3 g4".split()
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


def _css_state(svg, gen):
    """Which cells the CSS shows during generation `gen` (evaluates our step-end keyframes)."""
    kfs = {}
    for name, body in re.findall(r"@keyframes (k\d+)\{(.*?)\}\n", svg):
        kfs[name] = [(float(p), o == "1") for p, o in re.findall(r"([\d.]+)%\{opacity:(\d)\}", body)]
    shown = set()
    for m in re.finditer(r'<rect class="(c[^"]*)" x="([\d.]+)" y="([\d.]+)"[^>]*?(?:style="animation:(k\d+) ([\d.]+)s step-end infinite;animation-delay:(-?[\d.]+)s")?/>', svg):
        cls, x, y, name, dur, delay = m.groups()
        cell = (round((float(x) - 1) / bs.CELL), round((float(y) - 1) / bs.CELL))
        if not name:
            on = "off" not in cls.split()
        else:
            t = (((gen + 0.5) * bs.GEN_S - float(delay)) % float(dur)) / float(dur) * 100  # mid-generation
            on = [o for p, o in kfs[name] if p <= t][-1]
        if on:
            shown.add(cell)
    return shown


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_banner_css_matches_simulation(theme):
    s = outputs(theme)["banner"]
    for gen, frame in enumerate(bs.banner_frames()):
        assert _css_state(s, gen) == set(frame), gen
