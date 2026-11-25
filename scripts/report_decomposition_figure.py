"""Figure for the report: 1D strips vs 2D blocks with ghost layers.

Usage: python3 scripts/report_decomposition_figure.py
Output: plots/decomposition.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

fig, axes = plt.subplots(1, 2, figsize=(9, 4.2))
colors = ["#dbe5f1", "#dcefe3", "#fdf0d9", "#eadcf0"]
ghost = dict(facecolor="none", edgecolor="#2a9d2a", hatch="////", lw=0)

# --- strips: 4 ranks stacked, ghost rows between neighbours
ax = axes[0]
for r in range(4):
    ax.add_patch(Rectangle((0, r), 4, 1, facecolor=colors[r], edgecolor="k"))
    ax.text(4.15, r + 0.5, f"rank {r}", va="center", fontsize=9)
for r in range(1, 4):
    ax.add_patch(Rectangle((0, r - 0.08), 4, 0.16, **ghost))
ax.annotate("ghost rows\n(MPI_Sendrecv,\nN+1 doubles each)", xy=(2, 2), xytext=(-2.6, 2.6),
            fontsize=8, arrowprops=dict(arrowstyle="->"))
ax.set_title("(a) 1D strips: 2 messages per step")
ax.set_xlim(-2.8, 5.2); ax.set_ylim(-0.3, 4.3); ax.axis("off")

# --- blocks: 2x2 Cartesian grid, ghost rows and columns
ax = axes[1]
k = 0
for j in range(2):
    for i in range(2):
        ax.add_patch(Rectangle((2 * i, 2 * j), 2, 2, facecolor=colors[k], edgecolor="k"))
        ax.text(2 * i + 1, 2 * j + 1, f"rank {k}\n({i},{j})", ha="center", va="center", fontsize=9)
        k += 1
ax.add_patch(Rectangle((0, 1.92), 4, 0.16, **ghost))
ax.add_patch(Rectangle((1.92, 0), 0.16, 4, **ghost))
ax.annotate("rows: contiguous", xy=(3, 2), xytext=(4.3, 3.0), fontsize=8,
            arrowprops=dict(arrowstyle="->"))
ax.annotate("columns: MPI_Type_vector", xy=(2, 0.6), xytext=(4.3, 0.6), fontsize=8,
            arrowprops=dict(arrowstyle="->"))
ax.set_title("(b) 2D blocks (MPI_Cart_create): up to 4 messages")
ax.set_xlim(-0.3, 7.6); ax.set_ylim(-0.3, 4.3); ax.axis("off")

fig.tight_layout()
fig.savefig("plots/decomposition.png", dpi=170)
print("Saved plots/decomposition.png")
