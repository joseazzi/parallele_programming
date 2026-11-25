"""Task 6.5 (optional) - Eigenvalues of the discrete second derivative.

Background PDF, Section 6.5, Task 6.5 (PDF pages 24-25, printed pages 20-21).

1D, u_0 = u_N = 0, semi-discrete system u' = -A u with
    (A u)_i = (alpha / dx^2) (2 u_i - u_{i+1} - u_{i-1}),  i = 1..N-1.
Claim (Task 6.5a):  v^(m)_i = sin(m pi x_i / L) is an eigenvector with
    mu_m = (4 alpha / dx^2) sin^2(m pi dx / (2 L)) = (4 alpha / dx^2) sin^2(m pi / (2N)).

This script checks the claim numerically (residual ||A v - mu v||_inf for every m),
and tabulates mu_max * dx^2 (part b), the forward-Euler bound 2/mu_max (part c) and
mu_m against the exact decay rate alpha (m pi / L)^2 (part d).
Standard library only:  python3 scripts/background/task_6_5.py
"""

import csv
import math
from pathlib import Path

ALPHA, L = 1.0, 1.0
out = Path("results/background/task_6_5.csv")
out.parent.mkdir(parents=True, exist_ok=True)


def apply_A(v, N, dx):
    w = []
    for i in range(1, N):                       # interior nodes; v[0] = v[N] = 0
        w.append(ALPHA / dx ** 2 * (2 * v[i] - v[i + 1] - v[i - 1]))
    return w


rows = []
print("(a) eigenpair check: max_m ||A v_m - mu_m v_m||_inf / mu_m")
for N in (10, 40, 160):
    dx = L / N
    worst = 0.0
    for m in range(1, N):
        v = [math.sin(m * math.pi * i * dx / L) for i in range(N + 1)]
        mu = 4 * ALPHA / dx ** 2 * math.sin(m * math.pi * dx / (2 * L)) ** 2
        Av = apply_A(v, N, dx)
        res = max(abs(Av[i - 1] - mu * v[i]) for i in range(1, N))
        worst = max(worst, res / mu)
    print(f"   N = {N:4d}: {worst:.3e}   (round-off level -> eigenpairs confirmed for all m = 1..N-1)")

print("\n(b)/(c) largest eigenvalue and forward-Euler bound")
print(f"{'N':>5} {'mu_max':>14} {'mu_max*dx^2':>12} {'2/mu_max':>12} {'dx^2/(2a)':>12} {'s_max':>9}")
for N in (10, 40, 160, 640):
    dx = L / N
    mu_max = 4 * ALPHA / dx ** 2 * math.sin((N - 1) * math.pi / (2 * N)) ** 2
    print(f"{N:5d} {mu_max:14.6e} {mu_max*dx**2:12.6f} {2/mu_max:12.6e} {dx**2/(2*ALPHA):12.6e} "
          f"{(2/mu_max)*ALPHA/dx**2:9.6f}")
    rows.append(["b_c", N, "", mu_max, mu_max * dx ** 2, 2 / mu_max, dx ** 2 / (2 * ALPHA), "", ""])

print("\n(d) mu_m against the exact decay rate alpha (m pi / L)^2, N = 40")
N = 40
dx = L / N
print(f"{'m':>4} {'mu_m':>14} {'exact':>14} {'mu_m/exact':>11} {'1-(m pi dx)^2/12':>17}")
for m in (1, 2, 3, 5, 10, 20, 30, 39):
    mu = 4 * ALPHA / dx ** 2 * math.sin(m * math.pi * dx / (2 * L)) ** 2
    ex = ALPHA * (m * math.pi / L) ** 2
    approx = 1 - (m * math.pi * dx / L) ** 2 / 12
    print(f"{m:4d} {mu:14.6f} {ex:14.6f} {mu/ex:11.6f} {approx:17.6f}")
    rows.append(["d", N, m, mu, "", "", "", ex, mu / ex])

with out.open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["part", "N", "m", "mu", "mu_dx2", "two_over_mu_max", "dx2_over_2alpha",
                "exact_rate", "mu_over_exact"])
    w.writerows(rows)
print(f"\nSaved {out}")
