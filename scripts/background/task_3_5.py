"""Task 3.5 - Where does round-off take over?

Background PDF, Section 3.8 (PDF page 15, printed page 11).

Repeats the experiment of Task 3.2(c): the central second difference
    D2 f(x) = (f(x+h) - 2 f(x) + f(x-h)) / h^2
for f(x) = sin(x) at x = 1, now for h = 10^-1, ..., 10^-10, and records
the measured absolute error together with the two theoretical error scales:

    truncation scale  : |f''''(x)| h^2 / 12        (leading Taylor term)
    round-off scale   : 4 eps |f(x)| / h^2          (model bound, NOT measured)

The factor 4 = |1| + |-2| + |1| is the sum of the absolute stencil weights:
each of the three function values carries a relative rounding error of at
most about eps, so the numerator can be wrong by about 4 eps |f(x)|.

Run from the repository root:
    python3 scripts/background/task_3_5.py
"""

import csv
import math
import sys
from pathlib import Path

x = 1.0
exact = -math.sin(x)              # f''(x) for f = sin
f_abs = abs(math.sin(x))          # |f(x)|
f4_abs = abs(math.sin(x))         # |f''''(x)| = |sin x|
eps = sys.float_info.epsilon      # 2^-52 for IEEE double precision

results_dir = Path("results/background")
results_dir.mkdir(parents=True, exist_ok=True)
output = results_dir / "task_3_5.csv"

rows = []

print(f"Exact second derivative f''(1) = -sin(1) = {exact:.15f}")
print(f"Machine epsilon eps = {eps:.6e}")
print()
print(f"{'h':>8} {'D2 f(1)':>22} {'abs error':>14} "
      f"{'trunc scale':>12} {'round scale':>12}")
print("-" * 74)

for k in range(1, 11):
    h = 10.0 ** (-k)
    approximation = (math.sin(x + h) - 2.0 * math.sin(x) + math.sin(x - h)) / (h * h)
    error = abs(approximation - exact)
    truncation = f4_abs * h ** 2 / 12.0
    roundoff = 4.0 * eps * f_abs / h ** 2
    rows.append([h, approximation, error, truncation, roundoff])
    print(f"{h:8.0e} {approximation:22.15f} {error:14.6e} "
          f"{truncation:12.4e} {roundoff:12.4e}")

with output.open("w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["h", "approximation", "absolute_error",
                     "truncation_scale", "roundoff_scale"])
    for row in rows:
        writer.writerow([f"{row[0]:.0e}"] + [f"{v:.15e}" for v in row[1:]])

best = min(rows, key=lambda r: r[2])

# Theoretical optimum of E(h) = a h^2 + b / h^2 with
# a = |f''''|/12 and b = 4 eps |f|:  h* = (b/a)^(1/4), E* = 2 sqrt(a b)
a = f4_abs / 12.0
b = 4.0 * eps * f_abs
h_star = (b / a) ** 0.25
e_star = 2.0 * math.sqrt(a * b)

print()
print(f"Measured optimal h       : {best[0]:.0e}")
print(f"Measured minimum error   : {best[2]:.6e}")
print(f"Model optimum h* = (48 eps)^(1/4) : {h_star:.4e}")
print(f"Model minimum error E*            : {e_star:.4e}")
print(f"Crude scale eps^(1/4)             : {eps ** 0.25:.4e}")
print(f"Results saved to: {output}")
