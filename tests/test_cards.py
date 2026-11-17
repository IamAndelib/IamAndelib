import json, re, sys, xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_cards as bc  # noqa: E402

PROJECTS = json.loads((ROOT / "data/projects.json").read_text())
BASE = dict(PROJECTS[0])


def proj(**kw):
    return {**BASE, **kw}


@pytest.mark.parametrize("theme", ["dark", "light"])
@pytest.mark.parametrize("p", PROJECTS, ids=[p["slug"] for p in PROJECTS])
def test_card_is_valid_xml(p, theme):
    ET.fromstring(bc.render_card(p, theme))


def test_escapes_special_chars():
    s = bc.render_card(proj(pitch="Fast & <safe>"), "dark")
    assert "Fast &amp; &lt;safe&gt;" in s
    ET.fromstring(s)


def test_long_pitch_wraps_to_two_lines():
    pitch = " ".join(["wordy"] * 18)[:90]
    root = ET.fromstring(bc.render_card(proj(pitch=pitch), "dark"))
    ns = "{http://www.w3.org/2000/svg}"
    text = [t for t in root.iter(ns + "text") if t.get("class") == "c-text"][0]
    spans = list(text.iter(ns + "tspan"))
    assert len(spans) == 2
    assert all(len("".join(t.itertext())) <= 55 for t in spans)


def test_zero_stars_hidden():
    assert "★" not in bc.render_card(proj(stars=0), "dark")
    assert "★ 33" in bc.render_card(proj(stars=33), "dark")


def test_in_development_badge_and_credit():
    s = bc.render_card(proj(status="in-development", credit="Juxtopposed"), "light")
    assert "In development" in s and "design by Juxtopposed" in s


def test_no_external_refs():
    for p in PROJECTS:
        for t in ("dark", "light"):
            s = bc.render_card(p, t)
            assert "http" not in s.replace("http://www.w3.org/2000/svg", "")
            assert "prefers-color-scheme" not in s


def test_fetch_failure_keeps_last_values(tmp_path, monkeypatch):
    def boom(repo, token=None):
        raise bc.StatsError("nope")
    monkeypatch.setattr(bc, "fetch_stats", boom)
    data = tmp_path / "p.json"
    data.write_text(json.dumps(PROJECTS))
    out = tmp_path / "out"
    assert bc.main(["--data", str(data), "--out", str(out)]) == 0
    new = json.loads(data.read_text())
    assert [(p["stars"], p["downloads"]) for p in new] == [(p["stars"], p["downloads"]) for p in PROJECTS]
    assert len(list(out.glob("*.svg"))) == 14


@pytest.mark.parametrize("payload", [{}, {"stargazers_count": None}, [], "x"])
def test_unexpected_api_shape_maps_to_stats_error(monkeypatch, payload):
    monkeypatch.setattr(bc, "_get", lambda url, token=None: payload)
    with pytest.raises(bc.StatsError):
        bc.fetch_stats("Tally-android")
