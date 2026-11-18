import cmath
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import penrose  # noqa: E402

PHI = (1 + 5 ** 0.5) / 2


def test_wheel_is_ten_triangles_round_origin():
    w = penrose.wheel()
    assert len(w) == 10 and all(t[1] == 0 for t in w)


def test_subdivide_counts():
    # each thin-half (0) becomes 2 triangles, each thick-half (1) becomes 3
    lv1 = penrose.subdivide(penrose.wheel())
    assert len(lv1) == 20
    lv2 = penrose.subdivide(lv1)
    assert len(lv2) == sum(2 if t[0] == 0 else 3 for t in lv1)


def _edges(tris, scale=1, rot=1, r=0.8):
    out = set()
    for _, a, b, c in tris:
        for p, q in ((a, b), (a, c)):
            p, q = p * scale * rot, q * scale * rot
            if abs(p) < r and abs(q) < r:
                out.add(tuple(sorted([(round(p.real, 4), round(p.imag, 4)), (round(q.real, 4), round(q.imag, 4))])))
    return out


def test_phi_squared_zoom_turned_36_degrees_is_self_similar():
    lv = penrose.level(penrose.BASE_LEVEL)
    lv2 = penrose.level(penrose.BASE_LEVEL + 2)
    assert _edges(lv2, PHI ** 2, cmath.rect(1, math.radians(36))) == _edges(lv)


def test_zoom_loop_is_seamless():
    frames = penrose.zoom_frames()
    assert len(frames) == penrose.FRAMES + 1
    assert frames[0] == frames[-1]
    assert len(set(map(lambda f: tuple(sorted(f.items())), frames[:-1]))) > penrose.FRAMES // 2  # it moves


def test_cells_stay_inside_window():
    cx, cy, r = penrose.WINDOW
    for f in penrose.zoom_frames():
        for (x, y), shape in f.items():
            assert shape in (0, 1)
            assert abs(complex((x + 0.5) * penrose.CELL, (y + 0.5) * penrose.CELL) - complex(cx, cy)) <= r


def test_edges_leave_gaps():
    f = penrose.zoom_frames()[0]
    cx, cy, r = penrose.WINDOW
    inside = sum(1 for x in range(cx // penrose.CELL * 2) for y in range(34)
                 if abs(complex((x + 0.5) * penrose.CELL, (y + 0.5) * penrose.CELL) - complex(cx, cy)) <= r)
    assert 0.4 * inside < len(f) < 0.9 * inside  # outlines take a real share of the window


def _changes(frames):
    return [len(set(a.items()) ^ set(b.items())) for a, b in zip(frames, frames[1:])]


def test_motion_is_steady_no_global_split():
    # perpetual flow: no frame where the whole picture changes at once
    ch = sorted(_changes(penrose.zoom_frames()))
    median = ch[len(ch) // 2]
    assert ch[-1] <= 2 * median, (ch[-1], median)


def test_core_is_empty():
    cx, cy, _ = penrose.WINDOW
    for f in penrose.zoom_frames():
        for x, y in f:
            assert abs(complex((x + 0.5) * penrose.CELL, (y + 0.5) * penrose.CELL) - complex(cx, cy)) >= penrose.CORE
