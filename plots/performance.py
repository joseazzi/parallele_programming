import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

with open("results/performance/speedup.csv") as f:
    rows = list(csv.DictReader(f))

# Ne garder que les resultats avec 2 processus
strips = sorted(
    [r for r in rows if r["mode"] == "strips" and r["P"] == "2"],
    key=lambda r: int(r["N"])
)

blocks = sorted(
    [r for r in rows if r["mode"] == "blocks" and r["P"] == "2"],
    key=lambda r: int(r["N"])
)

N = [int(r["N"]) for r in strips]

# Graphique 1 : Speed-up
plt.figure(figsize=(8, 5))

plt.plot(N, [float(r["speedup"]) for r in strips],
         "o-", label="Strips P=2")

plt.plot(N, [float(r["speedup"]) for r in blocks],
         "s-", label="Blocks P=2")

plt.axhline(2, linestyle="--", color="gray",
            label="Ideal speed-up")

plt.axhline(1, linestyle=":", color="black",
            label="Serial baseline")

plt.xlabel("Grid size N")
plt.ylabel("Speed-up")
plt.title("Local MPI Speed-up")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("plots/speedup.png", dpi=200)
plt.close()

# Graphique 2 : Efficiency
plt.figure(figsize=(8, 5))

plt.plot(N, [float(r["efficiency"]) for r in strips],
         "o-", label="Strips P=2")

plt.plot(N, [float(r["efficiency"]) for r in blocks],
         "s-", label="Blocks P=2")

plt.axhline(1, linestyle="--", color="gray",
            label="Ideal efficiency")

plt.xlabel("Grid size N")
plt.ylabel("Efficiency")
plt.title("Local MPI Efficiency")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("plots/efficiency.png", dpi=200)
plt.close()

print("Saved: plots/speedup.png")
print("Saved: plots/efficiency.png")
