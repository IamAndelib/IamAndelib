import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_readme  # noqa: E402

README = ROOT / "README.md"
ALLOW = {f"profile/{n}-{t}.svg" for n in ("stats", "top-langs", "snake") for t in ("dark", "light")}


def problems():
    return check_readme.check(str(README), str(ROOT), ALLOW)


def only(prefix):
    return [p for p in problems() if p.startswith(prefix)]


def test_readme_has_no_hotlinks():
    assert only("hotlink") == []


def test_all_local_images_exist():
    assert only("missing") == []


def test_every_picture_has_dark_source_and_alt():
    assert only("picture") == []


def test_no_private_repo_links():
    assert only("private") == []


def test_contact_links_present():
    text = README.read_text()
    for u in ("https://iamandelib.github.io", "https://gitlab.com/IamAndelib",
              "https://www.linkedin.com/in/andelibababa/",
              "mailto:andelibtarefsrizon@gmail.com", "https://ko-fi.com/iamandelib"):
        assert u in text, u


def test_no_redundant_contacts():
    text = README.read_text()
    # visitors are already on the GitHub profile, so no button back to it
    assert 'href="https://github.com/IamAndelib"' not in text
    # the Email button carries the address; it isn't repeated as plain text
    assert text.count("andelibtarefsrizon@gmail.com") == 1


def test_checker_flags_bad_input(tmp_path):
    bad = tmp_path / "R.md"
    bad.write_text('<img src="https://x.io/a.png"><img src="nope.svg" alt="a">'
                   '<picture><img src="a.svg"></picture> [x](https://github.com/IamAndelib/secret-project)')
    kinds = {p.split(":")[0] for p in check_readme.check(str(bad), str(tmp_path), set())}
    assert kinds == {"hotlink", "missing", "picture", "private"}
