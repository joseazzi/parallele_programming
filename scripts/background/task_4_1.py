"""Task 4.1 - Experiments with forward Euler (and backward Euler).

Background PDF, Section 4.5, Task 4.1 (PDF page 18, printed page 14).

Test problem:  u' = -lambda u,  u(0) = 1,  lambda = 50,  t in [0, 1].
Exact solution: u(t) = exp(-lambda t).

    forward Euler : u^{n+1} = (1 - lambda dt) u^n      g_FE = 1 - lambda dt
    backward Euler: u^{n+1} = u^n / (1 + lambda dt)    g_BE = 1 / (1 + lambda dt)

Outputs (standard library only, run from the repository root):
    results/background/task_4_1_stability_scan.csv   parts (b) and (d)
    results/background/task_4_1_convergence.csv      part (c) (+ BE for comparison)
    results/background/task_4_1_trajectories.csv     data for the plot

    python3 scripts/background/task_4_1.py
"""

import csv
import math
from pathlib import Path

LAM = 50.0
T = 1.0
OUT = Path("results/background")
OUT.mkdir(parents=True, exist_ok=True)


def forward_euler(dt, nsteps):
    u = 1.0
    hist = [u]
    for _ in range(nsteps):
        u = u - LAM * dt * u
        hist.append(u)
    return hist


def backward_euler(dt, nsteps):
    u = 1.0
    hist = [u]
    for _ in range(nsteps):
        u = u / (1.0 + LAM * dt)
        hist.append(u)
    return hist


# ---------------------------------------------------------------- (b), (d)
# Scan dt and classify each run. Two criteria:
#   * on [0, 1]: |u| at the last step with t <= 1 compared with |u(0)| = 1
#   * long run of 2000 steps: does |u| grow without bound?
print("=== (b)/(d) stability scan, lambda = 50, theory: FE stable iff dt <= 2/lambda = 0.04 ===")
print(f"{'dt':>8} {'lam*dt':>7} {'g_FE':>9} {'FE |u(t<=1)|':>13} {'FE |u_2000|':>12} "
      f"{'FE':>9} {'BE |u(t<=1)|':>13} {'BE':>7}")
scan_rows = []
dts = [round(0.030 + 0.0005 * k, 4) for k in range(0, 41)]   # 0.030 ... 0.050
dts += [0.06, 0.08, 0.1, 0.2, 0.5, 1.0]
for dt in dts:
    n1 = int(math.floor(T / dt + 1e-12))          # steps with t_n <= 1
    fe = forward_euler(dt, 2000)
    be = backward_euler(dt, 2000)
    g = 1.0 - LAM * dt
    fe_t1, fe_long = abs(fe[n1]), abs(fe[-1])
    be_t1, be_long = abs(be[n1]), abs(be[-1])
    fe_status = "bounded" if fe_long <= 1.0 else "BLOWS UP"
    be_status = "bounded" if be_long <= 1.0 else "BLOWS UP"
    scan_rows.append([dt, LAM * dt, g, n1, fe_t1, fe_long, fe_status,
                      1.0 / (1.0 + LAM * dt), be_t1, be_long, be_status])
    print(f"{dt:8.4f} {LAM*dt:7.3f} {g:9.4f} {fe_t1:13.4e} {fe_long:12.4e} "
          f"{fe_status:>9} {be_t1:13.4e} {be_status:>7}")

with (OUT / "task_4_1_stability_scan.csv").open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["dt", "lambda_dt", "g_FE", "steps_to_t_le_1", "FE_abs_u_at_t_le_1",
                "FE_abs_u_after_2000_steps", "FE_status", "g_BE",
                "BE_abs_u_at_t_le_1", "BE_abs_u_after_2000_steps", "BE_status"])
    w.writerows(scan_rows)

fe_ok = [r[0] for r in scan_rows if r[6] == "bounded"]
print(f"\nLargest scanned dt with bounded forward Euler: {max(fe_ok):.4f}  (theory 2/lambda = {2/LAM:.4f})")
print(f"Backward Euler bounded for all {len(scan_rows)} scanned dt up to {max(dts)}: "
      f"{all(r[10] == 'bounded' for r in scan_rows)}")

# ---------------------------------------------------------------- (c)
print("\n=== (c) error at t = 1, dt = 1/n ===")
exact = math.exp(-LAM * T)
print(f"exact u(1) = exp(-50) = {exact:.6e}")
print(f"{'n':>7} {'dt':>11} {'FE u(1)':>13} {'FE abs err':>12} {'FE rel err':>11} {'ratio':>7} {'p_obs':>7}"
      f" {'BE abs err':>12} {'BE rel err':>11} {'p_obs':>7}")
conv_rows = []
prev_fe = prev_be = None
for k in range(0, 11):
    n = 100 * 2 ** k
    dt = T / n
    fe = forward_euler(dt, n)[-1]
    be = backward_euler(dt, n)[-1]
    efe, ebe = abs(fe - exact), abs(be - exact)
    rfe = rbe = pfe = pbe = float("nan")
    if prev_fe is not None:
        rfe, rbe = prev_fe / efe, prev_be / ebe
        pfe, pbe = math.log2(rfe), math.log2(rbe)
    conv_rows.append([n, dt, fe, efe, efe / exact, rfe, pfe, be, ebe, ebe / exact, rbe, pbe])
    print(f"{n:7d} {dt:11.4e} {fe:13.6e} {efe:12.4e} {efe/exact:11.4e} {rfe:7.3f} {pfe:7.3f}"
          f" {ebe:12.4e} {ebe/exact:11.4e} {pbe:7.3f}")
    prev_fe, prev_be = efe, ebe

with (OUT / "task_4_1_convergence.csv").open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["n", "dt", "FE_u1", "FE_abs_error", "FE_rel_error", "FE_ratio", "FE_p_obs",
                "BE_u1", "BE_abs_error", "BE_rel_error", "BE_ratio", "BE_p_obs"])
    for r in conv_rows:
        w.writerow([r[0], f"{r[1]:.10e}"] + [f"{v:.10e}" for v in r[2:]])

# ---------------------------------------------------------------- trajectories for plot
traj = [("FE", 0.01), ("FE", 0.03), ("FE", 0.04), ("FE", 0.042), ("BE", 0.042), ("BE", 0.1)]
with (OUT / "task_4_1_trajectories.csv").open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["method", "dt", "n", "t", "u"])
    for method, dt in traj:
        n1 = int(math.floor(T / dt + 1e-12))
        hist = (forward_euler if method == "FE" else backward_euler)(dt, n1)
        for i, u in enumerate(hist):
            w.writerow([method, dt, i, i * dt, f"{u:.15e}"])

print("\nSaved results/background/task_4_1_{stability_scan,convergence,trajectories}.csv")
