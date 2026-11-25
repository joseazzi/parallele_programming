"""Task 8.1 - Why not update in place?  (numerical demonstration)

Background PDF, Section 8.2, Task 8.1 (PDF page 28, printed page 24).

Same scheme as src/heat_serial.cpp (Case V, r = 0.2, T = 0.05, steps = N^2/4),
implemented four ways in pure Python:

  two_arrays      : u_new from u_old, then swap          (what heat_serial does)
  inplace_forward : one array, j = 1..N-1 outer, i = 1..N-1 inner (row by row)
  inplace_reverse : one array, j = N-1..1 outer, i = N-1..1 inner
  inplace_colmajor: one array, i outer, j inner

Reports the error against the exact solution, the effective decay rate,
and the differences between the variants.  Writes results/background/task_8_1.csv.
Standard library only:  python3 scripts/background/task_8_1.py
"""

import csv
import math
from pathlib import Path

R = 0.2
T = 0.05
PI = math.pi


def init(N):
    W = N + 1
    u = [0.0] * (W * W)
    h = 1.0 / N
    for j in range(1, N):
        for i in range(1, N):
            u[j * W + i] = math.sin(PI * i * h) * math.sin(PI * j * h)
    return u


def two_arrays(N, steps):
    W = N + 1
    u = init(N)
    nxt = u[:]
    c0 = 1.0 - 4.0 * R
    for _ in range(steps):
        for j in range(1, N):
            for i in range(1, N):
                k = j * W + i
                nxt[k] = c0 * u[k] + R * (u[k + 1] + u[k - 1] + u[k + W] + u[k - W])
        u, nxt = nxt, u
    return u


def inplace(N, steps, order):
    W = N + 1
    u = init(N)
    c0 = 1.0 - 4.0 * R
    fw = range(1, N)
    bw = range(N - 1, 0, -1)
    if order == "forward":
        sweep = [(i, j) for j in fw for i in fw]
    elif order == "reverse":
        sweep = [(i, j) for j in bw for i in bw]
    else:  # column-major
        sweep = [(i, j) for i in fw for j in fw]
    for _ in range(steps):
        for i, j in sweep:
            k = j * W + i
            u[k] = c0 * u[k] + R * (u[k + 1] + u[k - 1] + u[k + W] + u[k - W])
    return u


def errors(N, u):
    W = N + 1
    h = 1.0 / N
    f = math.exp(-2 * PI ** 2 * T)
    einf = s = 0.0
    for j in range(W):
        for i in range(W):
            e = abs(u[j * W + i] - math.sin(PI * i * h) * math.sin(PI * j * h) * f)
            einf = max(einf, e)
            s += e * e
    return einf, h * math.sqrt(s)


def centre(N, u):
    return u[(N // 2) * (N + 1) + N // 2]


rows = []
exact_centre = math.exp(-2 * PI ** 2 * T)
print(f"exact u(1/2,1/2,T=0.05) = {exact_centre:.6f};  "
      f"heat equation with alpha_eff = 1/(1-2r) = {1/(1-2*R):.4f} would give "
      f"{math.exp(-2*PI**2*T/(1-2*R)):.6f}")
print(f"{'N':>4} {'variant':>17} {'u(centre)':>10} {'err_inf':>11} {'err_l2':>11} "
      f"{'alpha_eff':>9} {'max|u-two_arrays|':>18}")
for N in (16, 32, 64):
    steps = N * N // 4
    ref = two_arrays(N, steps)
    variants = {"two_arrays": ref,
                "inplace_forward": inplace(N, steps, "forward"),
                "inplace_reverse": inplace(N, steps, "reverse"),
                "inplace_colmajor": inplace(N, steps, "colmajor")}
    for name, u in variants.items():
        einf, el2 = errors(N, u)
        uc = centre(N, u)
        alpha_eff = -math.log(uc) / (2 * PI ** 2 * T)
        diff = max(abs(a - b) for a, b in zip(u, ref))
        rows.append([N, steps, name, uc, einf, el2, alpha_eff, diff])
        print(f"{N:4d} {name:>17} {uc:10.6f} {einf:11.4e} {el2:11.4e} {alpha_eff:9.4f} {diff:18.4e}")
    fwd, rev = variants["inplace_forward"], variants["inplace_reverse"]
    W = N + 1
    # asymmetry: compare u(i,j) with its mirror image u(N-i, N-j); exact solution is symmetric
    asym = max(abs(fwd[j * W + i] - fwd[(N - j) * W + (N - i)]) for j in range(W) for i in range(W))
    print(f"      max|forward - reverse| = {max(abs(a-b) for a,b in zip(fwd, rev)):.4e};  "
          f"forward-sweep asymmetry max|u(i,j)-u(N-i,N-j)| = {asym:.4e}")
    rows.append([N, steps, "forward_vs_reverse_maxdiff", "", "", "", "",
                 max(abs(a - b) for a, b in zip(fwd, rev))])
    rows.append([N, steps, "forward_point_symmetry_defect", "", "", "", "", asym])

out = Path("results/background/task_8_1.csv")
with out.open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["N", "steps", "variant", "u_centre", "err_inf", "err_l2", "alpha_eff",
                "max_abs_diff_vs_two_arrays"])
    w.writerows(rows)
print(f"Saved {out}")
