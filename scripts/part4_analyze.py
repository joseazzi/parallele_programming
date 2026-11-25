"""Part 4 - analysis and performance model.

Reads the raw logs written by scripts/part4_final.sh
(results/part4/final/*_raw.txt) and the serial baselines
(results/part4/{jose,dia,theresa}_serial_raw.txt), then writes

  results/part4/baseline.csv           serial time per step and per node
  results/part4/strong_scaling.csv     median T, S(P), E(P), comm share, model
  results/part4/weak_scaling.csv       median T per configuration, model
  results/part4/model_predictions.csv  crossover N, Tailscale vs ts = 1 us
  plots/part4_strong_N*.png            time per step, measured vs model
  plots/part4_speedup.png, plots/part4_efficiency.png
  plots/part4_weak.png

Usage:  python3 scripts/part4_analyze.py
"""
import csv
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = Path("results/part4")
RAW = RES / "final"
PLOTS = Path("plots")
KV = re.compile(r"(\w+)=([^\s]+)")

VMS = ["jose", "dia", "theresa"]          # host order in the --host list
SLOTS = 2                                  # slots per VM

# ---------------------------------------------------------------- baseline
# c[vm][N] = serial seconds per step per interior node (compute rate)
c = {}
base_rows = []
for vm in VMS:
    runs = defaultdict(list)
    for line in (RES / f"{vm}_serial_raw.txt").read_text().splitlines():
        if line.startswith("decomp="):
            v = dict(KV.findall(line))
            runs[int(v["N"])].append((float(v["t_total"]), int(v["steps"])))
    c[vm] = {}
    for N, rs in sorted(runs.items()):
        t = statistics.median(r[0] for r in rs)
        steps = rs[0][1]
        per_step = t / steps
        per_node = per_step / (N - 1) ** 2
        c[vm][N] = per_node
        base_rows.append({
            "vm": vm, "N": N, "runs": len(rs),
            "median_total_s": f"{t:.4f}",
            "spread_s": f"{min(r[0] for r in rs):.4f}-{max(r[0] for r in rs):.4f}",
            "time_per_step_ms": f"{per_step * 1e3:.4f}",
            "time_per_node_ns": f"{per_node * 1e9:.4f}",
        })


def rate(vm, N):
    """Compute rate for any N: log-interpolate the measured baselines."""
    Ns = sorted(c[vm])
    if N <= Ns[0]:
        return c[vm][Ns[0]]
    if N >= Ns[-1]:
        return c[vm][Ns[-1]]
    for a, b in zip(Ns, Ns[1:]):
        if a <= N <= b:
            w = (math.log(N) - math.log(a)) / (math.log(b) - math.log(a))
            return math.exp((1 - w) * math.log(c[vm][a]) + w * math.log(c[vm][b]))


# ------------------------------------------------------- communication data
# Part 0 refined fit: startup latency ts (s) and time per byte tw (s/B)
TS, TW = {}, {}
with open("results/pingpong/communication_model_refined.csv") as f:
    for r in csv.DictReader(f):
        TS[r["connection"]] = float(r["startup_latency_ms"]) / 1e3
        TW[r["connection"]] = float(r["transfer_seconds_per_byte"])


def link(a, b, ts_override=None):
    """(ts, tw) between two VMs; same VM -> local values."""
    if a == b:
        key = f"{a.capitalize()} local"
    else:
        x, y = sorted([a, b], key=VMS.index)
        key = f"{x.capitalize()} - {y.capitalize()}"
    ts, tw = TS[key], TW[key]
    if ts_override is not None and a != b:
        ts, tw = ts_override, 1e-10          # "real cluster": 1 us, 10 GB/s
    return ts, tw


# ------------------------------------------------------------------ model
def placement(P, mapping):
    """VM of each rank for Open MPI --map-by slot / node."""
    if mapping == "slot":
        return [VMS[r // SLOTS] for r in range(P)]
    return [VMS[r % len(VMS)] for r in range(P)]


def dims_create(P):
    """MPI_Dims_create(P, 2): two factors as close as possible."""
    a = int(math.isqrt(P))
    while P % a:
        a -= 1
    return P // a, a


def model_step(N, P, mode, mapping, ts_override=None):
    """Predicted seconds per step = slowest rank's compute + halo phases.

    Each Cartesian direction with more than one process costs two
    MPI_Sendrecv phases (up and down). A phase lasts as long as its
    slowest pair: ts + m*tw with that pair's own ts, tw (Task 8.2).
    """
    vm_of = placement(P, mapping)
    d0, d1 = (P, 1) if mode == "strips" else dims_create(P)
    n0, n1 = (N - 1) / d0, (N - 1) / d1        # local interior extents
    comp = max(rate(vm, N) * n0 * n1 for vm in vm_of)
    comm = 0.0
    for dim, d, msg_len in [(0, d0, n1), (1, d1, n0)]:
        if d == 1:
            continue
        pairs = []
        for r in range(P):                       # rank = i0 * d1 + i1
            i0, i1 = divmod(r, d1)
            j0, j1 = (i0 + 1, i1) if dim == 0 else (i0, i1 + 1)
            if j0 < d0 and j1 < d1:
                pairs.append((r, j0 * d1 + j1))
        m = (msg_len + 2) * 8                    # bytes per halo message
        phase = 0.0
        for a, b in pairs:
            ts, tw = link(vm_of[a], vm_of[b], ts_override)
            phase = max(phase, ts + m * tw)
        comm += 2 * phase
    return comp + comm


# ---------------------------------------------------------- measurements
def parse(path):
    samples, failed = defaultdict(list), defaultdict(int)
    cur = None
    for line in path.read_text().splitlines():
        if line.startswith("N=") and "placement=" in line:
            h = dict(KV.findall(line))
            cur = (int(h["N"]), h["placement"], h["mode"], int(h["P"]))
        elif line.startswith("FAILED") and cur:
            failed[cur] += 1
        elif line.startswith("decomp=") and cur:
            v = dict(KV.findall(line))
            samples[cur].append((float(v["t_total"]), float(v["t_comp"]),
                                 float(v["t_comm"]), int(v["steps"])))
    return samples, failed


strong, sfail = defaultdict(list), defaultdict(int)
for p in sorted(RAW.glob("strong_*_raw.txt")):
    s, f = parse(p)
    for k, v in s.items():
        strong[k] += v
    for k, v in f.items():
        sfail[k] += v
# P = 1 is the same run for both placements: reuse the slot runs for node
for (N, pl, mode, P), v in list(strong.items()):
    if pl == "slot" and P == 1:
        strong[(N, "node", mode, 1)] = v

rows = []
for key in sorted(strong):
    N, pl, mode, P = key
    rs = strong[key]
    base = strong.get((N, pl, mode, 1))
    if not base:
        continue
    t = statistics.median(r[0] for r in rs)
    steps = rs[0][3]
    t1 = statistics.median(r[0] for r in base)
    comm = statistics.median(r[2] for r in rs)
    S = t1 / t
    rows.append({
        "N": N, "placement": pl, "mode": mode, "P": P,
        "runs_ok": len(rs), "runs_failed": sfail.get(key, 0),
        "t_total": f"{t:.6f}",
        "spread": f"{min(r[0] for r in rs):.4f}-{max(r[0] for r in rs):.4f}",
        "t_per_step_ms": f"{t / steps * 1e3:.4f}",
        "model_per_step_ms": f"{model_step(N, P, mode, pl) * 1e3:.4f}",
        "comm_share": f"{comm / t:.4f}",
        "speedup": f"{S:.4f}", "efficiency": f"{S / P:.4f}",
    })

weak_rows = []
weak = defaultdict(list)
wpath = RAW / "weak_raw.txt"
if wpath.exists():
    s, wfail = parse(wpath)
    for (N, pl, mode, P), rs in sorted(s.items(), key=lambda kv: kv[0][3]):
        t = statistics.median(r[0] for r in rs)
        steps = rs[0][3]
        comm = statistics.median(r[2] for r in rs)
        mdl = model_step(N, P, mode, "slot")
        weak[mode].append((P, N, t / steps, mdl))
        weak_rows.append({
            "P": P, "N": N, "mode": mode, "runs_ok": len(rs),
            "runs_failed": wfail.get((N, pl, mode, P), 0),
            "t_total": f"{t:.6f}",
            "spread": f"{min(r[0] for r in rs):.4f}-{max(r[0] for r in rs):.4f}",
            "t_per_step_ms": f"{t / steps * 1e3:.4f}",
            "model_per_step_ms": f"{mdl * 1e3:.4f}",
            "comm_share": f"{comm / t:.4f}",
        })


def write(path, data):
    if not data:
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)
    print(f"Saved {path} ({len(data)} rows)")


write(RES / "baseline.csv", base_rows)
write(RES / "strong_scaling.csv", rows)
write(RES / "weak_scaling.csv", weak_rows)

# ------------------------------------------- model predictions (questions)
pred = []
for net, ts in [("tailscale_measured", None), ("real_cluster_ts_1us", 1e-6)]:
    for mode in ["strips", "blocks"]:
        for pl in ["slot", "node"]:
            cross = "none up to 2^20"
            N = 64
            while N <= 2 ** 20:
                if model_step(N, 5, mode, pl, ts) < model_step(N, 1, mode, pl, ts):
                    cross = N
                    break
                N *= 2
            row = {"network": net, "mode": mode, "placement": pl,
                   "crossover_N_P5_faster_than_P1": cross}
            for n in [512, 2048, 8192]:
                row[f"model_S5_N{n}"] = (
                    f"{model_step(n, 1, mode, pl, ts) / model_step(n, 5, mode, pl, ts):.3f}")
            pred.append(row)
write(RES / "model_predictions.csv", pred)

# ------------------------------------------------------------------ plots
STYLE = {("strips", "slot"): ("C0", "o"), ("blocks", "slot"): ("C1", "s"),
         ("strips", "node"): ("C2", "^"), ("blocks", "node"): ("C3", "D")}
Ps = list(range(1, 6))       # P = 6 skipped (see report)

for N in sorted({r["N"] for r in rows}):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for (mode, pl), (col, mk) in STYLE.items():
        rs = sorted((r for r in rows if r["N"] == N and r["mode"] == mode
                     and r["placement"] == pl), key=lambda r: r["P"])
        ax.plot([r["P"] for r in rs], [float(r["t_per_step_ms"]) for r in rs],
                mk, color=col, label=f"{mode}, map-by {pl} (measured)")
        ax.plot(Ps, [model_step(N, P, mode, pl) * 1e3 for P in Ps],
                "-", color=col, alpha=0.6, label=f"{mode}, map-by {pl} (model)")
    ax.set_yscale("log")
    ax.set_xlabel("MPI processes P")
    ax.set_ylabel("time per step (ms)")
    ax.set_title(f"Strong scaling N={N}: measurement vs model")
    ax.grid(True, alpha=0.3, which="both")
    ax.legend(fontsize=6.5, ncol=2)
    fig.tight_layout()
    fig.savefig(PLOTS / f"part4_strong_N{N}.png", dpi=150)
    plt.close(fig)
    print(f"Saved plots/part4_strong_N{N}.png")

for metric, fname, ideal in [("speedup", "part4_speedup.png", Ps),
                             ("efficiency", "part4_efficiency.png", [1] * 5)]:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for N, ls in [(512, ":"), (2048, "-"), (8192, "--")]:
        for (mode, pl), (col, mk) in STYLE.items():
            rs = sorted((r for r in rows if r["N"] == N and r["mode"] == mode
                         and r["placement"] == pl), key=lambda r: r["P"])
            if rs:
                ax.plot([r["P"] for r in rs], [float(r[metric]) for r in rs],
                        marker=mk, linestyle=ls, color=col,
                        label=f"N={N} {mode} {pl}")
    ax.plot(Ps, ideal, color="gray", linestyle="-.", label="ideal")
    ax.set_yscale("log")
    ax.set_xlabel("MPI processes P")
    ax.set_ylabel(metric)
    ax.set_title(f"Strong scaling: {metric}")
    ax.grid(True, alpha=0.3, which="both")
    ax.legend(fontsize=6.5, ncol=2)
    fig.tight_layout()
    fig.savefig(PLOTS / fname, dpi=150)
    plt.close(fig)
    print(f"Saved plots/{fname}")

if weak:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for mode, col in [("strips", "C0"), ("blocks", "C1")]:
        pts = sorted(weak[mode])
        ax.plot([p[0] for p in pts], [p[2] * 1e3 for p in pts], "o",
                color=col, label=f"{mode} (measured)")
        ax.plot([p[0] for p in pts], [p[3] * 1e3 for p in pts], "-",
                color=col, alpha=0.6, label=f"{mode} (model)")
    ax.set_yscale("log")
    ax.set_xlabel("MPI processes P (N = 1024*sqrt(P), map-by slot)")
    ax.set_ylabel("time per step (ms)")
    ax.set_title("Weak scaling: about 1024x1024 nodes per process")
    ax.grid(True, alpha=0.3, which="both")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS / "part4_weak.png", dpi=150)
    plt.close(fig)
    print("Saved plots/part4_weak.png")
