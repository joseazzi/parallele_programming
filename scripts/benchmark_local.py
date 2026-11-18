import csv
import statistics
import subprocess
from pathlib import Path

Path("results/performance").mkdir(parents=True, exist_ok=True)

N_VALUES = [512, 1024, 2048]
STEPS = 100
REPEATS = 3

results = []

for N in N_VALUES:
    for mode in ["serial", "strips", "blocks"]:
        for P in ([1] if mode == "serial" else [1, 2]):

            if mode == "serial":
                command = ["./heat"]
            else:
                executable = (
                    "./heat_strips" if mode == "strips"
                    else "./heat_blocks"
                )
                command = ["mpirun", "-np", str(P), executable]

            command += [
                "--case", "1",
                "--N", str(N),
                "--r", "0.2",
                "--steps", str(STEPS)
            ]

            measurements = []

            for repeat in range(REPEATS):
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True
                )

                values = {}

                for item in completed.stdout.split():
                    if "=" in item:
                        key, value = item.split("=", 1)
                        values[key] = value

                measurements.append({
                    "total": float(values["t_total"]),
                    "comp": float(values["t_comp"]),
                    "comm": float(values["t_comm"])
                })

            median_total = statistics.median(
                m["total"] for m in measurements
            )

            median_comp = statistics.median(
                m["comp"] for m in measurements
            )

            median_comm = statistics.median(
                m["comm"] for m in measurements
            )

            comm_fraction = (
                median_comm / median_total
                if median_total > 0 else 0.0
            )

            results.append({
                "N": N,
                "mode": mode,
                "P": P,
                "median_seconds": median_total,
                "median_comp": median_comp,
                "median_comm": median_comm,
                "comm_fraction": comm_fraction
            })

            print(
                f"N={N} mode={mode} P={P} "
                f"total={median_total:.6f}s "
                f"comp={median_comp:.6f}s "
                f"comm={median_comm:.6f}s "
                f"comm%={100*comm_fraction:.1f}"
            )

with open(
    "results/performance/local_benchmark_detailed.csv",
    "w",
    newline=""
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "N", "mode", "P",
            "median_seconds",
            "median_comp",
            "median_comm",
            "comm_fraction"
        ]
    )
    writer.writeheader()
    writer.writerows(results)

print("Saved: results/performance/local_benchmark_detailed.csv")
