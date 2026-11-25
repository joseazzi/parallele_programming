"""Part 4 - strong scaling analysis.

Parses every raw log in results/part4/ (lines written by
scripts/part4_strong.sh), takes the median of the repeated runs
for each configuration, and writes:

  results/part4/strong_scaling.csv
  plots/part4_time.png
  plots/part4_speedup.png
  plots/part4_efficiency.png

Usage:  python3 scripts/part4_analyze.py
"""
import csv
import re
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAW_DIR = Path("results/part4")
OUT_CSV = RAW_DIR / "strong_scaling.csv"
PLOT_DIR = Path("plots")

header_re = re.compile(r"placement=(\w+)")
kv_re = re.compile(r"(\w+)=([^\s]+)")

samples = defaultdict(list)

for path in sorted(RAW_DIR.glob("strong_*_raw.txt")):
    placement = "slot"
    for line in path.read_text().splitlines():
        if line.startswith("N=") and "placement=" in line:
            placement = header_re.search(line).group(1)
            continue
        if not line.startswith("decomp=") or "t_total=" not in line:
            continue
        v = dict(kv_re.findall(line))
        key = (int(v["N"]), int(v["steps"]), placement,
               v["decomp"], int(v["P"]))
        samples[key].append((float(v["t_total"]),
                             float(v["t_comp"]),
                             float(v["t_comm"])))

rows = []
for key in sorted(samples):
    N, steps, placement, mode, P = key
    runs = samples[key]
    t_total = statistics.median(r[0] for r in runs)
    t_comp = statistics.median(r[1] for r in runs)
    t_comm = statistics.median(r[2] for r in runs)
    base = samples.get((N, steps, placement, mode, 1))
    t1 = statistics.median(r[0] for r in base) if base else float("nan")
    S = t1 / t_total
    rows.append({
        "N": N, "steps": steps, "placement": placement,
        "mode": mode, "P": P, "runs": len(runs),
        "t_total": f"{t_total:.6f}", "t_comp": f"{t_comp:.6f}",
        "t_comm": f"{t_comm:.6f}",
        "comm_fraction": f"{t_comm / t_total:.4f}",
        "speedup": f"{S:.4f}", "efficiency": f"{S / P:.4f}",
    })

with OUT_CSV.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"Saved {OUT_CSV} ({len(rows)} configurations)")

# Plots: one line per (N, steps, placement, mode), 20-step study only.
groups = defaultdict(list)
for r in rows:
    if r["steps"] == 20:
        groups[(r["N"], r["placement"], r["mode"])].append(r)

for metric, ylabel, fname, log in [
    ("t_total", "Time (s), median of runs", "part4_time.png", True),
    ("speedup", "Speedup S(P) = T(1)/T(P)", "part4_speedup.png", True),
    ("efficiency", "Efficiency E(P) = S(P)/P", "part4_efficiency.png", True),
]:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for (N, placement, mode), rs in sorted(groups.items()):
        rs.sort(key=lambda r: r["P"])
        ax.plot([r["P"] for r in rs], [float(r[metric]) for r in rs],
                marker="o" if mode == "strips" else "s",
                linestyle="-" if placement == "slot" else "--",
                label=f"N={N} {mode} ({placement})")
    if metric == "speedup":
        ps = range(1, 7)
        ax.plot(ps, ps, color="gray", linestyle=":", label="ideal")
    if metric == "efficiency":
        ax.axhline(1.0, color="gray", linestyle=":", label="ideal")
    if log:
        ax.set_yscale("log")
    ax.set_xlabel("MPI processes P")
    ax.set_ylabel(ylabel)
    ax.set_title(f"Part 4 strong scaling (20 steps): {metric}")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / fname, dpi=150)
    plt.close(fig)
    print(f"Saved {PLOT_DIR / fname}")
