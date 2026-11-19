from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path.home() / "heat-mpi"
OUTPUT = BASE / "plots"
OUTPUT.mkdir(exist_ok=True)

# Compare the three computer pairs using 1 MiB benchmarks
benchmarks = {
    "Jose - Dia (direct)": "pingpong_jose_dia_direct.csv",
    "Jose - Theresa (direct)": "pingpong_jose_theresa_direct.csv",
    "Dia - Theresa": "pingpong_dia_theresa_1mb.csv",
}

results = []

for name, filename in benchmarks.items():
    df = pd.read_csv(BASE / filename)

    # Keep the common message range: 8 B through 1 MiB
    df = df[(df["bytes"] >= 8) & (df["bytes"] <= 1048576)].copy()

    # RTT/2 is an estimated one-way transfer time
    df["latency_ms"] = df["one_way_seconds"] * 1000

    # Effective bandwidth in decimal megabits per second
    df["bandwidth_mbps"] = (
        df["bytes"] * 8 / df["one_way_seconds"] / 1_000_000
    )

    df["connection"] = name
    results.append(df)

data = pd.concat(results, ignore_index=True)

# Save calculated results
data.to_csv(OUTPUT / "pingpong_analysis.csv", index=False)

# Graph 1: Estimated one-way latency
plt.figure(figsize=(10, 6))

for name, group in data.groupby("connection"):
    plt.plot(
        group["bytes"],
        group["latency_ms"],
        marker="o",
        label=name
    )

plt.xscale("log", base=2)
plt.xlabel("Message size (bytes)")
plt.ylabel("Estimated one-way time (ms)")
plt.title("MPI Ping-Pong: Communication Time")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(OUTPUT / "pingpong_latency.png", dpi=200)
plt.close()

# Graph 2: Effective bandwidth
plt.figure(figsize=(10, 6))

for name, group in data.groupby("connection"):
    plt.plot(
        group["bytes"],
        group["bandwidth_mbps"],
        marker="o",
        label=name
    )

plt.xscale("log", base=2)
plt.xlabel("Message size (bytes)")
plt.ylabel("Effective bandwidth (Mbps)")
plt.title("MPI Ping-Pong: Effective Bandwidth")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(OUTPUT / "pingpong_bandwidth.png", dpi=200)
plt.close()

print("Analysis complete.")
print("Results saved in:", OUTPUT)
print(data[data["bytes"] == 1048576][
    ["connection", "latency_ms", "bandwidth_mbps"]
].to_string(index=False))
