import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

N = 100

u = np.fromfile(
    "results/heat_case1.bin",
    dtype="<f8"
).reshape((N + 1, N + 1))

plt.figure(figsize=(7, 6))
plt.imshow(
    u,
    origin="lower",
    extent=[0, 1, 0, 1],
    cmap="hot",
    vmin=0,
    vmax=1
)

plt.colorbar(label="Temperature")
plt.xlabel("x")
plt.ylabel("y")
plt.title("2D Heat Diffusion - Case 1")
plt.tight_layout()

plt.savefig("plots/heat_case1.png", dpi=200)
print("Saved: plots/heat_case1.png")
