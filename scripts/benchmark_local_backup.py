import csv
import statistics
import subprocess
from pathlib import Path

Path("results/performance").mkdir(parents=True, exist_ok=True)

# Premiers tests locaux, sans depasser les 2 vCPU
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

            times = []

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

                times.append(float(values["t_total"]))

            median = statistics.median(times)

            results.append({
                "N": N,
                "mode": mode,
                "P": P,
                "median_seconds": median,
                "min_seconds": min(times),
                "max_seconds": max(times)
            })

            print(
                f"N={N} mode={mode} P={P} "
                f"median={median:.6f}s"
            )

with open(
    "results/performance/local_benchmark.csv",
    "w",
    newline=""
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "N", "mode", "P", "median_seconds",
            "min_seconds", "max_seconds"
        ]
    )
    writer.writeheader()
    writer.writerows(results)

print("Saved: results/performance/local_benchmark.csv")
