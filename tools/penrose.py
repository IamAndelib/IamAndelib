"""Penrose P3 (rhomb) tiling via Robinson triangles, rasterised onto the banner's cell grid as an endless zoom.

A triangle is (shape, a, b, c) with complex vertices; shape 0 = half a thin rhomb, 1 = half a thick rhomb.
Two mirrored triangles sharing edge b-c make one rhomb, so only edges a-b and a-c are tile outlines.
Zooming by phi^2 maps the tiling onto itself turned 36 degrees, which makes the loop seamless.

To feel perpetual (no moment where every tile splits at once), the subdivision level is fixed in *world*
space by distance from the centre: one level finer per factor phi closer in. Zooming then carries tiles
outward, growing, while finer tiles emerge from the centre; a ring of tiles never changes level.
"""
import cmath
import functools
import math

PHI = (1 + 5 ** 0.5) / 2
CELL = 10                      # px; same grid as the banner
COLS, ROWS = 42, 34            # area scanned for the window (px 0..420 x 0..340)
WINDOW = (230, 170, 150)       # round window: centre x, centre y, radius (px); 80 px clear on the left
SCALE = 190                    # px per wheel unit at the start of the loop
BASE_LEVEL = 2                 # level at world radius ~1, i.e. the window's rim at loop start (tile edge ~72 px)
CORE = 34                      # px; empty centre, where tiles would be too small for the grid
EDGE = 0.55 * CELL             # cells this close to a tile outline stay empty, so the grid draws the outline
FRAMES = 40                    # frames per loop
TURN = math.radians(36)        # rotation per loop that goes with the phi^2 zoom


def wheel():
    tris = []
    for i in range(10):
        b = cmath.rect(1, (2 * i - 1) * math.pi / 10)
        c = cmath.rect(1, (2 * i + 1) * math.pi / 10)
        if i % 2 == 0:
            b, c = c, b
        tris.append((0, 0j, b, c))
    return tris


def subdivide(tris):
    out = []
    for shape, a, b, c in tris:
        if shape == 0:
            p = a + (b - a) / PHI
            out += [(0, c, p, b), (1, p, c, a)]
        else:
            q = b + (a - b) / PHI
            r = b + (c - b) / PHI
            out += [(1, r, c, a), (1, q, r, b), (0, r, q, a)]
    return out


@functools.lru_cache(maxsize=None)
def level(n):
    return tuple(wheel()) if n == 0 else tuple(subdivide(level(n - 1)))


def _seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, ((p - a) * ab.conjugate()).real / abs(ab) ** 2))
    return abs(p - (a + t * ab))


def level_for(r):
    """Subdivision level for world radius r (wheel units): one finer per factor phi toward the centre."""
    return BASE_LEVEL + max(0, math.floor(math.log(1 / r, PHI)))


@functools.lru_cache(maxsize=None)
def _band(m):
    """Triangles of level m that can lie where level_for gives m (with margin)."""
    lo, hi = PHI ** (BASE_LEVEL - m - 1), (PHI ** (BASE_LEVEL - m) if m > BASE_LEVEL else 2.0)
    pad = 2 * PHI ** -m
    return tuple(t for t in level(m)
                 if min(abs(z) for z in t[1:]) - pad <= hi and max(abs(z) for z in t[1:]) + pad >= lo)


def _inside(p, a, b, c):
    d1 = ((b - a) * (p - a).conjugate()).imag
    d2 = ((c - b) * (p - b).conjugate()).imag
    d3 = ((a - c) * (p - c).conjugate()).imag
    return (d1 >= 0 and d2 >= 0 and d3 >= 0) or (d1 <= 0 and d2 <= 0 and d3 <= 0)


def raster(scale, rot=1):
    """Cells inside the window ring -> rhomb shape (0 thin, 1 thick); outline cells are left out."""
    cx, cy, radius = WINDOW
    centre = complex(cx, cy)
    out = {}
    for y in range(ROWS):
        for x in range(COLS):
            p = complex((x + 0.5) * CELL, (y + 0.5) * CELL)
            if not CORE <= abs(p - centre) <= radius:
                continue
            w = (p - centre) / (scale * rot)          # world point
            m = level_for(abs(w))
            edge_world = EDGE / scale
            for shape, a, b, c in _band(m):
                if _inside(w, a, b, c):
                    if min(_seg_dist(w, a, b), _seg_dist(w, a, c)) >= edge_world:
                        out[(x, y)] = shape
                    break
    return out


@functools.lru_cache(maxsize=None)
def zoom_frames():
    """FRAMES + 1 rasters over one loop (zoom phi^2, turn 36 degrees); the last equals the first."""
    return tuple(raster(SCALE * PHI ** (2 * i / FRAMES), cmath.rect(1, TURN * i / FRAMES))
                 for i in range(FRAMES + 1))
