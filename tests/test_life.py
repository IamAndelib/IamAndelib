import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import life  # noqa: E402

BLINKER = frozenset({(1, 0), (1, 1), (1, 2)})
GLIDER = frozenset({(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)})


def run(cells, n):
    for _ in range(n):
        cells = life.step(cells)
    return cells


def test_blinker_period_2():
    assert life.step(BLINKER) == frozenset({(0, 1), (1, 1), (2, 1)})
    assert run(BLINKER, 2) == BLINKER


def test_glider_moves_1_1_every_4():
    assert run(GLIDER, 4) == frozenset((x + 1, y + 1) for x, y in GLIDER)


def test_gun_emits_and_is_period_30():
    g = run(life.GOSPER_GUN, 120)
    in_box = lambda cs: frozenset(c for c in cs if 0 <= c[0] < 36 and 0 <= c[1] < 9)
    assert in_box(g) == in_box(run(g, 30))
    # it has fired: cells exist beyond the gun's 36x9 box
    assert any(x >= 36 or y >= 9 for x, y in g)


def test_steady_cycle_loops():
    keep = lambda x, y: 0 <= x < 150 and 0 <= y < 42
    frames = life.steady_cycle(life.GOSPER_GUN, warmup=300, period=30, keep=keep)
    assert len(frames) == 31
    assert frames[0] == frames[30]  # each glider steps into its predecessor's place every gun period
    assert len(set(frames[:30])) == 30  # no shorter cycle: every generation in the loop is distinct
    assert all(keep(x, y) for f in frames for x, y in f)
