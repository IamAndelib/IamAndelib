"""Tiny Conway's Game of Life (B3/S23) engine for the animated banner. Cells are (x, y), y grows downward."""
from collections import Counter

# Gosper glider gun in its 36x9 box; period 30, fires gliders toward +x, +y.
GOSPER_GUN = frozenset({
    (0, 4), (0, 5), (1, 4), (1, 5),
    (10, 4), (10, 5), (10, 6), (11, 3), (11, 7), (12, 2), (12, 8), (13, 2), (13, 8), (14, 5),
    (15, 3), (15, 7), (16, 4), (16, 5), (16, 6), (17, 5),
    (20, 2), (20, 3), (20, 4), (21, 2), (21, 3), (21, 4), (22, 1), (22, 5), (24, 0), (24, 1), (24, 5), (24, 6),
    (34, 2), (34, 3), (35, 2), (35, 3),
})

FAR = 400  # cells this far out are dropped so departing gliders don't grow the simulation forever


def step(cells):
    counts = Counter((x + dx, y + dy) for x, y in cells
                     for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
    return frozenset(c for c, n in counts.items() if n == 3 or (n == 2 and c in cells))


def steady_cycle(seed, warmup, period, keep):
    """Run `warmup` generations, then return period + 1 consecutive frames filtered by keep(x, y)."""
    cells = frozenset(seed)
    frames = []
    for gen in range(warmup + period + 1):
        if gen >= warmup:
            frames.append(frozenset(c for c in cells if keep(*c)))
        cells = frozenset(c for c in step(cells) if abs(c[0]) < FAR and abs(c[1]) < FAR)
    return frames
