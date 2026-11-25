"""Task 7.2 - log-log plot of the discrete L2 error against h (needs matplotlib, no numpy).

    python3 scripts/background/task_7_2_plot.py
reads results/background/task_7_2.csv, writes plots/background/task_7_2_convergence.png
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("results/background/task_7_2.csv")))
h = [float(r["h"]) for r in rows]
e2 = [float(r["err_l2"]) for r in rows]
ei = [float(r["err_inf"]) for r in rows]
p2 = [float(r["pred_l2"]) for r in rows]

out = Path("plots/background/task_7_2_convergence.png")
out.parent.mkdir(parents=True, exist_ok=True)
fig, ax = plt.subplots(figsize=(7.5, 5.3))
ax.loglog(h, e2, "o-", color="#1f4e9c", lw=2, ms=7, label=r"measured $\|e\|_{2,h}$")
ax.loglog(h, ei, "s-", color="#c0392b", lw=1.2, ms=5, alpha=0.8, label=r"measured $\|e\|_\infty$")
ax.loglog(h, p2, "k--", lw=1,
          label=r"theory $\|e\|_{2,h}\approx\frac{1}{2}\pi^4(2r-\frac{1}{6})\,T e^{-2\pi^2T}h^2=0.2118\,h^2$")
x0, y0 = h[0], e2[0] * 3
ax.loglog([x0, h[-1]], [y0, y0 * (h[-1] / x0) ** 2], ":", color="gray", label="slope 2 reference")
for N, x, y in zip([r["N"] for r in rows], h, e2):
    ax.annotate(f"N={N}", (x, y), textcoords="offset points", xytext=(6, -12), fontsize=8)
ax.set_xlabel("h = 1/N")
ax.set_ylabel("error at T = 0.05")
ax.set_title("Task 7.2: convergence of the serial solver (Case V, r = 0.2, T = 0.05)")
ax.grid(True, which="both", ls=":", alpha=0.6)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(out, dpi=150)
print(f"Saved {out}")
