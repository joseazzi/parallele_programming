"""Heat map of a field file: ASCII art in the terminal + PNG.

Usage: python3 scripts/demo_heatmap.py <field.bin> <N> <title> <out.png>
The field file is the raw (N+1)x(N+1) little-endian double grid,
row j = line y_j (row 0 = bottom edge).
"""
import sys

import numpy as np

path, N, title, png = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
u = np.fromfile(path, dtype="<f8").reshape(N + 1, N + 1)

# --- terminal heat map (top of the plate printed first)
shades = " .:-=+*#%@"
cols = 48
rows = 22
ys = np.linspace(N, 0, rows).round().astype(int)
xs = np.linspace(0, N, cols).round().astype(int)
print(f"\n{title}   (cold ' ' ... '@' hot)")
print("+" + "-" * cols + "+")
for j in ys:
    line = "".join(shades[min(9, int(u[j, i] * 9.999))] for i in xs)
    print("|" + line + "|")
print("+" + "-" * cols + "+")
print(f"min={u.min():.3f}  max={u.max():.3f}  mean={u.mean():.3f}")

# --- PNG
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(5.5, 4.6))
im = ax.imshow(u, origin="lower", extent=[0, 1, 0, 1], cmap="hot",
               vmin=0, vmax=1, interpolation="bilinear")
fig.colorbar(im, label="temperature u")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_title(title)
fig.tight_layout()
fig.savefig(png, dpi=150)
print(f"Saved {png}")
