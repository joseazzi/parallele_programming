"""Task 7.2 - Convergence study of the serial solver (Case V).

Background PDF, Section 7.4, Task 7.2 (PDF page 27, printed page 23).

Runs ./heat_serial on the verification problem u = sin(pi x) sin(pi y) e^{-2 pi^2 t}
to T = 0.05 for N = 16, 32, 64, 128, 256 with the dimensionless parameter
fixed at r = alpha dt / h^2 = 0.2 (<= 1/4, stable).  Then
    dt = r h^2 = 0.2 / N^2,   steps = T / dt = T N^2 / r = N^2 / 4   (an integer).
The step count is passed explicitly with --steps so that r stays exactly 0.2.

Writes results/background/task_7_2.csv.  Standard library only.
Run from the repository root after `make heat_serial`:
    python3 scripts/background/task_7_2.py
"""

import csv
import math
import subprocess
from fractions import Fraction
from pathlib import Path

T = Fraction(1, 20)        # 0.05
R = Fraction(1, 5)         # 0.2
NS = [16, 32, 64, 128, 256]
out = Path("results/background/task_7_2.csv")
out.parent.mkdir(parents=True, exist_ok=True)

# Theoretical prediction (Chapter 5, Task 5.5 + Chapter 7):
#   e(T) ~ -K h^2 T u(T),  K = pi^4 (2r - 1/6)  for the (1,1) mode, alpha = 1
K = math.pi ** 4 * (2 * float(R) - 1.0 / 6.0)
decay = math.exp(-2 * math.pi ** 2 * float(T))
C_inf = K * float(T) * decay          # max |sin sin| = 1
C_l2 = C_inf * 0.5                    # L2 norm of sin(pi x) sin(pi y) on unit square = 1/2

rows = []
for N in NS:
    steps = T * N * N / R
    assert steps.denominator == 1, f"T/dt not an integer for N={N}"
    steps = int(steps)
    cmd = ["./heat_serial", "--N", str(N), "--r", "0.2", "--steps", str(steps), "--case", "V"]
    line = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()
    kv = dict(item.split("=", 1) for item in line.split())
    h = 1.0 / N
    rows.append({
        "N": N, "h": h, "dt": float(R) * h * h, "steps": steps,
        "T_reported": float(kv["T"]), "r_reported": float(kv["r"]),
        "err_inf": float(kv["err_inf"]), "err_l2": float(kv["err_l2"]),
        "pred_inf": C_inf * h * h, "pred_l2": C_l2 * h * h,
        "t_total_s": float(kv["t_total"]),
    })
    print(line)

for k, row in enumerate(rows):
    if k == 0:
        row["ratio_inf"] = row["p_inf"] = row["ratio_l2"] = row["p_l2"] = ""
    else:
        prev = rows[k - 1]
        row["ratio_inf"] = prev["err_inf"] / row["err_inf"]
        row["ratio_l2"] = prev["err_l2"] / row["err_l2"]
        row["p_inf"] = math.log2(row["ratio_inf"])
        row["p_l2"] = math.log2(row["ratio_l2"])

fields = ["N", "h", "dt", "steps", "T_reported", "r_reported", "err_inf", "err_l2",
          "ratio_inf", "p_inf", "ratio_l2", "p_l2", "pred_inf", "pred_l2", "t_total_s"]
with out.open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print()
print(f"Prediction: ||e||_inf ~ {C_inf:.5f} h^2, ||e||_2,h ~ {C_l2:.5f} h^2  (K = {K:.4f})")
print(f"{'N':>4} {'h':>10} {'steps':>6} {'err_inf':>12} {'err_l2':>12} {'p_inf':>7} {'p_l2':>7} "
      f"{'inf/pred':>9}")
for row in rows:
    p1 = f"{row['p_inf']:.4f}" if row["p_inf"] != "" else "-"
    p2 = f"{row['p_l2']:.4f}" if row["p_l2"] != "" else "-"
    print(f"{row['N']:4d} {row['h']:10.6f} {row['steps']:6d} {row['err_inf']:12.5e} "
          f"{row['err_l2']:12.5e} {p1:>7} {p2:>7} {row['err_inf']/row['pred_inf']:9.4f}")
print(f"Saved {out}")
