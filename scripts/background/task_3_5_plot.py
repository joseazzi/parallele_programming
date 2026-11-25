"""Task 3.5 - log-log plot of the second-difference error versus h.

Reads results/background/task_3_5.csv (written by task_3_5.py) and writes
plots/background/task_3_5_roundoff.png.

Only the measured curve is experimental data. The two dashed lines are the
theoretical error SCALES of the model E(h) ~ |f''''| h^2/12 + 4 eps |f| / h^2;
the round-off line is an estimate, not a measured round-off error.

Run from the repository root (needs matplotlib, no numpy):
    python3 scripts/background/task_3_5_plot.py
"""

import csv
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

src = Path("results/background/task_3_5.csv")
out = Path("plots/background/task_3_5_roundoff.png")
out.parent.mkdir(parents=True, exist_ok=True)

h, err, trunc, rnd = [], [], [], []
with src.open() as fh:
    for row in csv.DictReader(fh):
        h.append(float(row["h"]))
        err.append(float(row["absolute_error"]))
        trunc.append(float(row["truncation_scale"]))
        rnd.append(float(row["roundoff_scale"]))

eps = sys.float_info.epsilon
s1 = math.sin(1.0)
h_star = (48.0 * eps) ** 0.25
best = min(range(len(h)), key=lambda i: err[i])

fig, ax = plt.subplots(figsize=(7.5, 5.2))
ax.loglog(h, err, "o-", color="#1f4e9c", lw=2, ms=6,
          label="measured |D2 f(1) - f''(1)|")
ax.loglog(h, trunc, "--", color="#2a9d4b", lw=1.5,
          label=r"theoretical truncation scale $|f''''|\,h^2/12$")
ax.loglog(h, rnd, "--", color="#c0392b", lw=1.5,
          label=r"theoretical round-off scale $4\varepsilon|f|/h^2$ (model)")
ax.axvline(h_star, color="gray", ls=":", lw=1.2,
           label=rf"model optimum $h^*=(48\varepsilon)^{{1/4}}\approx{h_star:.1e}$")
ax.annotate(f"measured minimum\nh = {h[best]:.0e}, error = {err[best]:.2e}",
            xy=(h[best], err[best]), xytext=(1e-8, 1e-10),
            arrowprops=dict(arrowstyle="->", color="black"), fontsize=9)

ax.set_xlabel("h")
ax.set_ylabel("absolute error")
ax.set_title(r"Task 3.5: second difference of $\sin x$ at $x=1$ (double precision)")
ax.set_ylim(1e-11, 1e4)
ax.grid(True, which="both", ls=":", lw=0.5, alpha=0.6)
ax.legend(fontsize=8.5, loc="upper right")
fig.tight_layout()
fig.savefig(out, dpi=150)
print(f"Saved {out}")
