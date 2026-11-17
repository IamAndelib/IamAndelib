#!/usr/bin/env python3
"""Generate assets/cards/<slug>-{dark,light}.svg from data/projects.json (stdlib only)."""
import argparse, base64, json, mimetypes, os, sys, urllib.request, urllib.error
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import THEMES, FONT  # noqa: E402

OWNER = "IamAndelib"
SKIP_SUFFIXES = (".sha256", ".sha256sum", ".aab", ".asc")
DEV_COLOR = "#d29922"


class StatsError(Exception):
    pass


def _get(url, token):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "profile-cards"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise StatsError(f"{url}: {e}") from e


def fetch_stats(repo, token=None):
    try:
        return _fetch_stats(repo, token)
    except (KeyError, TypeError, AttributeError) as e:
        raise StatsError(f"{repo}: unexpected API response shape: {e!r}") from e


def _fetch_stats(repo, token=None):
    info = _get(f"https://api.github.com/repos/{OWNER}/{repo}", token)
    downloads, page = 0, 1
    while True:
        rels = _get(f"https://api.github.com/repos/{OWNER}/{repo}/releases?per_page=100&page={page}", token)
        for rel in rels:
            for a in rel.get("assets", []):
                if not a["name"].lower().endswith(SKIP_SUFFIXES):
                    downloads += a.get("download_count", 0)
        if len(rels) < 100:
            break
        page += 1
    return {"stars": int(info["stargazers_count"]), "downloads": downloads}


def wrap(text, width=54, lines=2):
    out, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = (cur + " " + w).strip()
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][: width - 1].rstrip() + "…"
    return out


def data_uri(path):
    p = Path(path)
    mime = "image/svg+xml" if p.suffix == ".svg" else mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def render_card(p, theme):
    t = THEMES[theme]
    esc = escape
    logo = data_uri(ROOT / p["logo"])
    lines = "".join(f'<tspan x="20" dy="{0 if i == 0 else 19}">{esc(l)}</tspan>'
                    for i, l in enumerate(wrap(p["pitch"])))
    chips, cx = "", 20
    for s in p["stack"][:4]:
        w = round(len(s) * 7 + 20)
        chips += (f'<rect class="c-chip" x="{cx}" y="128" width="{w}" height="24" rx="12"/>'
                  f'<text class="c-chiptext" x="{cx + w / 2:g}" y="144" text-anchor="middle">{esc(s)}</text>')
        cx += w + 6
    nums = []
    if p.get("stars"):
        nums.append(f"★ {p['stars']}")
    if p.get("downloads"):
        nums.append(f"⬇ {p['downloads']}")
    dev = p.get("status") == "in-development"
    right = (f'<text class="c-foot" x="400" y="40" text-anchor="end">{esc("   ".join(nums))}</text>'
             if nums and not dev else "")
    badge = ""
    if dev:
        badge = ('<rect class="c-dev" x="296" y="24" width="104" height="22" rx="11"/>'
                 '<text class="c-devtext" x="348" y="39" text-anchor="middle">In development</text>')
    sub = esc(p["platform"]) + (f'<tspan class="c-foot"> · design by {esc(p["credit"])}</tspan>'
                                if p.get("credit") else "")
    tcls = "c-title sm" if len(p["name"]) > 17 else "c-title"
    css = (f'text{{font-family:{FONT}}}'
           f'.c-bg{{fill:{t["surface"]};stroke:{t["border"]}}}'
           f'.c-title{{fill:{t["fg"]};font-weight:700;font-size:19px}}.c-title.sm{{font-size:15.5px}}'
           f'.c-text{{fill:{t["muted"]};font-weight:400;font-size:13.5px}}'
           f'.c-chip{{fill:{t["surface2"]};stroke:{t["border"]}}}'
           f'.c-chiptext{{fill:{t["fg"]};font-weight:500;font-size:11.5px}}'
           f'.c-foot{{fill:{t["muted"]};font-weight:500;font-size:12.5px}}'
           f'.c-plat{{fill:{t["kde"]};font-weight:600;font-size:12.5px}}'
           f'.c-dev{{fill:none;stroke:{DEV_COLOR}}}'
           f'.c-devtext{{fill:{DEV_COLOR};font-weight:600;font-size:11.5px}}'
           f'.c-logo-bg{{fill:{t["bg"]};stroke:{t["border"]}}}')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 170" width="420" height="170" role="img" '
            f'aria-label="{esc(p["name"], {chr(34): "&quot;"})}: {esc(p["pitch"], {chr(34): "&quot;"})}">'
            f'<style>{css}</style>'
            f'<rect class="c-bg" x=".5" y=".5" width="419" height="169" rx="12"/>'
            f'<rect class="c-logo-bg" x="20" y="18" width="46" height="46" rx="10"/>'
            f'<image href="{logo}" x="25" y="23" width="36" height="36"/>'
            f'<text class="{tcls}" x="78" y="40">{esc(p["name"])}</text>'
            f'<text class="c-plat" x="78" y="60">{sub}</text>{right}{badge}'
            f'<text class="c-text" x="20" y="96">{lines}</text>{chips}</svg>\n')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--data", default=str(ROOT / "data/projects.json"))
    ap.add_argument("--out", default=str(ROOT / "assets/cards"))
    a = ap.parse_args(argv)
    data_path, out = Path(a.data), Path(a.out)
    projects = json.loads(data_path.read_text())
    token = os.environ.get("GITHUB_TOKEN")
    if not a.offline:
        for p in projects:
            try:
                s = fetch_stats(p["repo"], token)
                p["stars"], p["downloads"] = s["stars"], s["downloads"]
            except StatsError as e:
                print(f"warning: {p['slug']}: keeping last values ({e})", file=sys.stderr)
        data_path.write_text(json.dumps(projects, indent=2, ensure_ascii=False) + "\n")
    out.mkdir(parents=True, exist_ok=True)
    for p in projects:
        for theme in THEMES:
            (out / f"{p['slug']}-{theme}.svg").write_text(render_card(p, theme), encoding="utf-8")
    print(f"wrote {len(projects) * len(THEMES)} cards to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
