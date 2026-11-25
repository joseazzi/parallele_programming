"""Task 4.1 - plots from the CSVs written by task_4_1.py (needs matplotlib, no numpy).

    python3 scripts/background/task_4_1_plot.py
writes plots/background/task_4_1_euler.png
"""

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = Path("results/background")
out = Path("plots/background/task_4_1_euler.png")
out.parent.mkdir(parents=True, exist_ok=True)

traj = defaultdict(lambda: ([], []))
with (R / "task_4_1_trajectories.csv").open() as fh:
    for row in csv.DictReader(fh):
        key = (row["method"], float(row["dt"]))
        traj[key][0].append(float(row["t"]))
        traj[key][1].append(float(row["u"]))

conv = list(csv.DictReader((R / "task_4_1_convergence.csv").open()))
dt = [float(r["dt"]) for r in conv]
efe = [float(r["FE_abs_error"]) for r in conv]
ebe = [float(r["BE_abs_error"]) for r in conv]

fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))

ts = [i / 1000 for i in range(1001)]
a1.plot(ts, [math.exp(-50 * t) for t in ts], "k-", lw=2, label="exact $e^{-50t}$")
styles = {("FE", 0.01): ("#2a9d4b", "o"), ("FE", 0.03): ("#e9a23b", "s"),
          ("FE", 0.04): ("#7b3fa0", "^"), ("FE", 0.042): ("#c0392b", "v"),
          ("BE", 0.042): ("#1f4e9c", "D"), ("BE", 0.1): ("#4aa3df", "x")}
for key, (c, m) in styles.items():
    t, u = traj[key]
    lam_dt = 50 * key[1]
    a1.plot(t, u, "-", color=c, marker=m, ms=3.5, lw=1,
            label=f"{'forward' if key[0]=='FE' else 'backward'} Euler, $\\Delta t$={key[1]} ($\\lambda\\Delta t$={lam_dt:.2f})")
a1.set_yscale("symlog", linthresh=1e-2)
a1.set_xlabel("t")
a1.set_ylabel("u  (symlog scale)")
a1.set_title(r"$u'=-50u$, $u(0)=1$: forward Euler unstable for $\Delta t>2/\lambda=0.04$")
a1.legend(fontsize=7.5, loc="lower left")
a1.grid(True, ls=":", alpha=0.6)

a2.loglog(dt, efe, "o-", color="#c0392b", label="forward Euler (measured)")
a2.loglog(dt, ebe, "s-", color="#1f4e9c", label="backward Euler (measured)")
a2.loglog(dt, [math.exp(-50) * 1250 * d for d in dt], "k--", lw=1,
          label=r"first-order prediction $e^{-50}\,\lambda^2 T\,\Delta t/2$")
a2.set_xlabel(r"$\Delta t$")
a2.set_ylabel(r"$|u^n - u(1)|$ at $t=1$")
a2.set_title("Error at t = 1 (slope 1 once $\\lambda^2\\Delta t/2 \\ll 1$)")
a2.legend(fontsize=8)
a2.grid(True, which="both", ls=":", alpha=0.6)

fig.tight_layout()
fig.savefig(out, dpi=150)
print(f"Saved {out}")
