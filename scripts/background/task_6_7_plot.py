"""Task 6.7 - figures from task_6_7.py output (needs numpy + matplotlib).

    python3 scripts/background/task_6_7_plot.py
writes plots/background/task_6_7_snapshots.png and plots/background/task_6_7_growth.png
"""

import csv
import math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm

N = 40
D = Path("results/background/task_6_7")
P = Path("plots/background")
P.mkdir(parents=True, exist_ok=True)


def field(case, r, s):
    return np.fromfile(D / f"case{case}_r{r}_s{s}.bin", dtype="<f8").reshape(N + 1, N + 1)


def checker(u):
    """c = (4u - neighbours)/8 on interior nodes, 0 on the boundary."""
    c = np.zeros_like(u)
    c[1:-1, 1:-1] = (4 * u[1:-1, 1:-1] - u[2:, 1:-1] - u[:-2, 1:-1]
                     - u[1:-1, 2:] - u[1:-1, :-2]) / 8
    return c


# ------------------------------------------------------------ snapshots
panels = [("1", 0.2, 200, "Case 1, r=0.2 (stable), 200 steps"),
          ("1", 0.2625, 100, "Case 1, r=0.2625, 100 steps"),
          ("1", 0.2625, 200, "Case 1, r=0.2625, 200 steps"),
          ("1", 0.2625, 300, "Case 1, r=0.2625, 300 steps"),
          ("V", 0.2625, 200, "Case V, r=0.2625, 200 steps"),
          ("V", 0.2625, 400, "Case V, r=0.2625, 400 steps"),
          ("V", 0.2625, 600, "Case V, r=0.2625, 600 steps")]
# portrait 4x4 layout (fits an A4 page): rows 1-2 = Case 1 (u, c), rows 3-4 = Case V (u, c)
fig, grid = plt.subplots(4, 4, figsize=(15, 15.5))
slots = [(0, 0), (0, 1), (0, 2), (0, 3), (2, 0), (2, 1), (2, 2)]
grid[2, 3].axis("off")
grid[3, 3].axis("off")
for k, (case, r, s, title) in enumerate(panels):
    u = field(case, r, s)
    c = checker(u)
    row, col = slots[k]
    axes = {(0, k): grid[row, col], (1, k): grid[row + 1, col]}
    a = axes[0, k]
    m = max(abs(u).max(), 1e-12)
    im = a.imshow(u, origin="lower", cmap="RdBu_r", vmin=-m, vmax=m)
    a.set_title(f"{title}\nu,  max|u| = {abs(u).max():.3g}", fontsize=8.5)
    fig.colorbar(im, ax=a, fraction=0.046)
    # zoom inset of the 8x8 block around the max of |c| to show the sign pattern
    a = axes[1, k]
    j0, i0 = np.unravel_index(np.argmax(abs(c)), c.shape)
    mc = abs(c).max()
    im = a.imshow(c, origin="lower", cmap="RdBu_r",
                  norm=SymLogNorm(linthresh=max(mc * 1e-3, 1e-12), vmin=-mc, vmax=mc))
    a.plot(i0, j0, "k+", ms=10)
    a.set_title(f"checkerboard indicator c = (4u - nbrs)/8\nmax|c| = {mc:.3g} at (i,j)=({i0},{j0})",
                fontsize=8.5)
    fig.colorbar(im, ax=a, fraction=0.046)
for a in grid.ravel():
    a.set_xlabel("i", fontsize=8)
    a.set_ylabel("j", fontsize=8)
fig.suptitle("Task 6.7: explicit scheme on N = 40 with r = 0.2625 (5% above 1/4)\n"
             "Red/blue = sign; the unstable field alternates sign from node to node", fontsize=13)
fig.tight_layout()
fig.savefig(P / "task_6_7_snapshots.png", dpi=110)

# zoom figure: raw node values in a 9x9 window, Case 1 r=0.2625 at 200 steps
u = field("1", 0.2625, 200)
c = checker(u)
j0, i0 = np.unravel_index(np.argmax(abs(c)), c.shape)

# ------------------------------------------------------------ growth curve
rows = list(csv.DictReader(open("results/background/task_6_7_metrics.csv")))
fig, ax = plt.subplots(figsize=(8, 5.2))
style = {("1", "0.2625"): ("#c0392b", "Case 1, r = 0.2625"),
         ("V", "0.2625"): ("#1f4e9c", "Case V, r = 0.2625"),
         ("1", "0.2"): ("#2a9d4b", "Case 1, r = 0.2 (stable)")}
for (case, r), (col, lab) in style.items():
    sel = [x for x in rows if x["case"] == case and x["r"] == r]
    ax.semilogy([int(x["steps"]) for x in sel], [float(x["max_abs_checker"]) for x in sel],
                "o-", ms=3, color=col, label=f"measured max|c|, {lab}")
G = abs(1 - 8 * 0.2625 * math.cos(math.pi / (2 * N)) ** 2)
s = np.arange(300, 701)
ax.semilogy(s, 1.9936e11 * G ** (s - 700), "k--", lw=1,
            label=f"theory: |G| = {G:.5f} per step (mode m=n=N-1)")
ax.set_xlabel("time step n")
ax.set_ylabel("max |c|  (checkerboard amplitude)")
ax.set_title("Task 6.7: growth of the sawtooth mode, N = 40")
ax.grid(True, which="both", ls=":", alpha=0.6)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(P / "task_6_7_growth.png", dpi=150)

print("Saved plots/background/task_6_7_snapshots.png and task_6_7_growth.png")
print(f"Case 1 r=0.2625 s=200: 5x5 raw values around max|c| at (i,j)=({i0},{j0}):")
print(np.array2string(u[j0 - 2:j0 + 3, i0 - 2:i0 + 3], precision=2, suppress_small=False))
