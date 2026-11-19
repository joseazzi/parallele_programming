
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path.home() / "heat-mpi"
OUTPUT = BASE / "results" / "pingpong"
OUTPUT.mkdir(parents=True, exist_ok=True)

benchmarks = {
    "Jose local": "pingpong_jose_local.csv",
    "Dia local": "pingpong_dia_local.csv",
    "Theresa local": "pingpong_theresa_local.csv",
    "Jose - Dia": "pingpong_jose_dia.csv",
    "Jose - Theresa": "pingpong_jose_theresa_16mb.csv",
    "Dia - Theresa": "pingpong_dia_theresa_16mb.csv",
}

expected_sizes = [2**k for k in range(3, 25)]

# Small-message region for startup latency estimation
SMALL_MAX = 1024

# Large-message region for bandwidth estimation
LARGE_MIN = 1024 * 1024

results = []

fig, ax = plt.subplots(figsize=(11, 7))

for name, filename in benchmarks.items():
    df = pd.read_csv(BASE / filename)
    df = df.sort_values("bytes")

    if df["bytes"].tolist() != expected_sizes:
        raise ValueError(f"Incomplete benchmark: {filename}")

    values = df[
        ["rtt_seconds", "one_way_seconds"]
    ].to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError(f"Non-finite data: {filename}")

    if (values <= 0).any():
        raise ValueError(f"Non-positive timing: {filename}")

    if not np.allclose(
        df["rtt_seconds"] / 2,
        df["one_way_seconds"],
        rtol=1e-6,
        atol=1e-9,
    ):
        raise ValueError(f"RTT mismatch: {filename}")

    sizes = df["bytes"].to_numpy(dtype=float)
    times = df["one_way_seconds"].to_numpy(dtype=float)

    # 1. Full-range ordinary linear fit (diagnostic)
    full_slope, full_intercept = np.polyfit(
        sizes, times, 1
    )

    # 2. Startup latency estimated from small messages
    small = df[df["bytes"] <= SMALL_MAX]
    startup_s = float(
        small["one_way_seconds"].median()
    )

    # 3. Fit transfer time per byte for large messages,
    # holding startup latency fixed at its small-message estimate
    large = df[df["bytes"] >= LARGE_MIN]

    x = large["bytes"].to_numpy(dtype=float)
    y = large["one_way_seconds"].to_numpy(dtype=float)

    numerator = np.dot(x, y - startup_s)
    denominator = np.dot(x, x)

    tw = numerator / denominator

    if tw <= 0:
        raise ValueError(f"Invalid bandwidth fit: {name}")

    bandwidth_mbps = 8 / (tw * 1_000_000)

    predicted_large = startup_s + x * tw

    ss_res = np.sum((y - predicted_large) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    r_squared = (
        1 - ss_res / ss_tot
        if ss_tot > 0
        else float("nan")
    )

    results.append({
        "connection": name,
        "startup_latency_ms": startup_s * 1000,
        "transfer_seconds_per_byte": tw,
        "bandwidth_mbps": bandwidth_mbps,
        "R_squared_large": r_squared,
        "full_fit_intercept_ms": full_intercept * 1000,
    })

    # Plot measured and model-predicted times
    ax.plot(
        sizes / (1024**2),
        times,
        marker="o",
        markersize=3,
        linestyle="",
        label=f"{name} measured",
    )

    predicted_all = startup_s + sizes * tw

    ax.plot(
        sizes / (1024**2),
        predicted_all,
        linestyle="--",
        linewidth=1,
    )

    print(
        f"{name}: "
        f"startup={startup_s * 1000:.6f} ms, "
        f"bandwidth={bandwidth_mbps:.3f} Mbps, "
        f"R2_large={r_squared:.4f}"
    )

summary = pd.DataFrame(results)

# Preserve the original model output
summary.to_csv(
    OUTPUT / "communication_model_refined.csv",
    index=False,
)

ax.set_xlabel("Message size (MiB)")
ax.set_ylabel("Estimated one-way transfer time (seconds)")
ax.set_title("MPI Ping-Pong: Refined Communication Model")
ax.grid(True, alpha=0.3)
ax.legend(fontsize=7, ncol=2)

fig.tight_layout()
fig.savefig(
    OUTPUT / "communication_model_refined.png",
    dpi=200,
)
plt.close(fig)

print("\nFinal comparison table:")
print(summary.to_string(index=False))

print("\nResults saved in:", OUTPUT)
print(
    "\nMethod: startup latency is the median time for "
    "messages <= 1024 bytes; bandwidth is fitted using "
    "messages >= 1 MiB with that startup estimate fixed."
)
print(
    "These are approximate empirical parameters. "
    "The model may not capture all MPI communication regimes."
)
# Additional plots: separate local and cross-machine communication
plot_groups = {
    "local": {
        "title": "MPI Ping-Pong: Local Communication",
        "connections": [
            "Jose local",
            "Dia local",
            "Theresa local",
        ],
    },
    "cross_machine": {
        "title": "MPI Ping-Pong: Cross-Machine Communication",
        "connections": [
            "Jose - Dia",
            "Jose - Theresa",
            "Dia - Theresa",
        ],
    },
}

for group_name, group in plot_groups.items():
    fig, ax = plt.subplots(figsize=(10, 6))

    for name in group["connections"]:
        df = pd.read_csv(BASE / benchmarks[name])
        df = df.sort_values("bytes")

        sizes = df["bytes"].to_numpy(dtype=float)
        times = df["one_way_seconds"].to_numpy(dtype=float)

        row = summary.loc[summary["connection"] == name].iloc[0]

        startup_s = row["startup_latency_ms"] / 1000
        tw = row["transfer_seconds_per_byte"]

        predicted = startup_s + sizes * tw

        line, = ax.plot(
            sizes / (1024**2),
            times * 1000,
            marker="o",
            markersize=4,
            label=f"{name} measured",
        )

        ax.plot(
            sizes / (1024**2),
            predicted * 1000,
            linestyle="--",
            color=line.get_color(),
            label=f"{name} model",
        )

    ax.set_xlabel("Message size (MiB)")
    ax.set_ylabel("Estimated one-way transfer time (ms)")
    ax.set_title(group["title"])
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(
        OUTPUT / f"communication_model_{group_name}.png",
        dpi=200,
    )
    plt.close(fig)

    print(f"Saved communication_model_{group_name}.png")
