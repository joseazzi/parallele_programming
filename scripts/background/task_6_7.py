"""Task 6.7 - Breaking it on purpose.

Background PDF, Section 6.6, Task 6.7 (PDF page 25, printed page 21).

Runs ./heat_unstable with a time step 5% above the stability bound,
    r = 1.05 * 1/4 = 0.2625,
on an N = 40 grid (same N as the existing r = 0.3 experiment in
docs/PART1_SERIAL.md, Section 9), for
    Case 1 (four hot edges, discontinuous at the corners/edges), and
    Case V (smooth single Fourier mode sin(pi x) sin(pi y)),
and the stable reference r = 0.2 (Case 1).  Each snapshot is a separate run
from t = 0 (the solver only writes the final field).

For every snapshot it measures
    max |u|                                   overall size
    c_ij = (4 u_ij - sum of 4 neighbours)/8   "checkerboard amplitude":
           equals +-A for a pure (-1)^(i+j) pattern of amplitude A and is
           ~ -h^2 lap(u)/8 (tiny) for a smooth field
    max |c|, its location (i, j) and its distance from the nearest edge
    ratio of max|c| between consecutive snapshots -> growth per step

Writes results/background/task_6_7_metrics.csv and keeps a few snapshot
fields in results/background/task_6_7/ for the plot.  Standard library only.
Run from the repository root after `make heat_unstable`:
    python3 scripts/background/task_6_7.py
"""

import csv
import math
import subprocess
from array import array
from pathlib import Path

N = 40
W = N + 1
SNAP_DIR = Path("results/background/task_6_7")
SNAP_DIR.mkdir(parents=True, exist_ok=True)
OUT = Path("results/background/task_6_7_metrics.csv")

RUNS = [
    ("1", 0.2625, list(range(0, 401, 10))),
    ("V", 0.2625, list(range(0, 701, 10))),
    ("1", 0.2, list(range(0, 401, 50))),
]
KEEP = {("1", 0.2625, s) for s in (10, 40, 100, 200, 300)} | \
       {("V", 0.2625, s) for s in (200, 400, 600)} | {("1", 0.2, 200)}


def load(path):
    a = array("d")
    with open(path, "rb") as fh:
        a.frombytes(fh.read())
    assert len(a) == W * W
    return a


rows = []
for case, r, steps_list in RUNS:
    prev = None
    for steps in steps_list:
        tag = f"case{case}_r{r}_s{steps}"
        path = SNAP_DIR / f"{tag}.bin"
        cmd = ["./heat_unstable", "--N", str(N), "--r", str(r), "--steps", str(steps),
               "--case", case, "--out", str(path)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        u = load(path)
        umax = max(abs(v) for v in u)
        cmax, ci, cj = -1.0, -1, -1
        for j in range(1, N):
            for i in range(1, N):
                k = j * W + i
                c = (4 * u[k] - u[k + 1] - u[k - 1] - u[k + W] - u[k - W]) / 8.0
                if abs(c) > cmax:
                    cmax, ci, cj = abs(c), i, j
        dist = min(ci, cj, N - ci, N - cj)
        growth = ""
        if prev is not None and prev[1] > 0:
            growth = (cmax / prev[1]) ** (1.0 / (steps - prev[0]))
        rows.append([case, r, steps, umax, cmax, ci, cj, dist, growth])
        prev = (steps, cmax)
        if (case, r, steps) not in KEEP:
            path.unlink()

with OUT.open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["case", "r", "steps", "max_abs_u", "max_abs_checker", "i_at_max",
                "j_at_max", "dist_to_edge", "checker_growth_per_step"])
    w.writerows(rows)

g_theory = abs(1 - 8 * 0.2625 * math.cos(math.pi / (2 * N)) ** 2)
print(f"theoretical |G| of the worst grid mode (m=n=N-1): {g_theory:.6f}")
print(f"{'case':>4} {'r':>7} {'steps':>5} {'max|u|':>12} {'max|c|':>12} {'(i,j)':>9} {'edge':>4} {'growth':>9}")
for row in rows:
    g = f"{row[8]:.5f}" if row[8] != "" else "-"
    print(f"{row[0]:>4} {row[1]:7.4f} {row[2]:5d} {row[3]:12.4e} {row[4]:12.4e} "
          f"{'(%d,%d)' % (row[5], row[6]):>9} {row[7]:4d} {g:>9}")
print(f"Saved {OUT}")
