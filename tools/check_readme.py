"""Lint README.md: no hotlinked images, local images exist, pictures well-formed, only allowlisted public repo links."""
import json
import re
import sys
from pathlib import Path

EXTRA_PUBLIC = {
    "linux-suspend-instant-wake-fix", "linux-bluetooth-wake-reconnect",
    "plasma-browser-integration-flatpak-fix", "Frosted-Color-Plasma-Style",
    "alucard-dracula-light-kde", "openbangla-keyboard-flatpak",
}


def public_repos() -> set[str]:
    data = json.loads((Path(__file__).resolve().parent.parent / "data" / "projects.json").read_text())
    return {p["repo"].lower() for p in data} | {r.lower() for r in EXTRA_PUBLIC}


def check(readme_path: str, repo_root: str, allow_missing: set[str]) -> list[str]:
    text = Path(readme_path).read_text()
    problems = []
    for m in re.finditer(r'\b(?:src|srcset)\s*=\s*"([^"]*)"', text):
        ref = m.group(1).strip()
        if ref.startswith("http"):
            problems.append(f"hotlink: {ref}")
        elif ref not in allow_missing and not (Path(repo_root) / ref).exists():
            problems.append(f"missing: {ref}")
    for m in re.finditer(r"<picture>(.*?)</picture>", text, re.S):
        body = m.group(1)
        if not re.search(r'<source[^>]*prefers-color-scheme:\s*dark[^>]*srcset=', body):
            problems.append("picture: no dark <source>")
        if not re.search(r'<img[^>]*\balt="[^"]+"', body):
            problems.append("picture: <img> without alt")
    public = public_repos()
    for m in re.finditer(r"github\.com/IamAndelib/([A-Za-z0-9._-]+)", text, re.I):
        name = m.group(1).removesuffix(".git").rstrip(".")
        if name.lower() not in public:
            problems.append(f"private: {name}")
    return problems


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    allow = {f"profile/{n}-{t}.svg" for n in ("stats", "top-langs", "snake") for t in ("dark", "light")}
    probs = check(str(root / "README.md"), str(root), allow)
    print("\n".join(probs) or "README ok")
    sys.exit(1 if probs else 0)
