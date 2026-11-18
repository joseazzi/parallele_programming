import csv

with open("results/performance/local_benchmark.csv") as f:
    rows = list(csv.DictReader(f))

baselines = {
    int(row["N"]): float(row["median_seconds"])
    for row in rows
    if row["mode"] == "serial"
}

print("N,mode,P,speedup,efficiency")

with open(
    "results/performance/speedup.csv",
    "w",
    newline=""
) as f:
    writer = csv.writer(f)
    writer.writerow(["N", "mode", "P", "speedup", "efficiency"])

    for row in rows:
        N = int(row["N"])
        P = int(row["P"])

        if row["mode"] == "serial":
            continue

        time_parallel = float(row["median_seconds"])
        speedup = baselines[N] / time_parallel
        efficiency = speedup / P

        writer.writerow([
            N, row["mode"], P,
            round(speedup, 4),
            round(efficiency, 4)
        ])

        print(
            f"{N},{row['mode']},{P},"
            f"{speedup:.4f},{efficiency:.4f}"
        )
