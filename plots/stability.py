import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

N = 40

stable = np.fromfile(
    "results/stable.bin", dtype="<f8"
).reshape((N + 1, N + 1))

unstable = np.fromfile(
    "results/unstable.bin", dtype="<f8"
).reshape((N + 1, N + 1))

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

im1 = axes[0].imshow(
    stable,
    origin="lower",
    cmap="coolwarm",
    vmin=-1,
    vmax=1
)

axes[0].set_title("Stable: r = 0.2")
fig.colorbar(im1, ax=axes[0])

im2 = axes[1].imshow(
    unstable,
    origin="lower",
    cmap="coolwarm"
)

axes[1].set_title("Unstable: r = 0.3")
fig.colorbar(im2, ax=axes[1])

for ax in axes:
    ax.set_xlabel("Grid index i")
    ax.set_ylabel("Grid index j")

plt.tight_layout()
plt.savefig("plots/stability.png", dpi=200)

print("Stable max:", np.max(np.abs(stable)))
print("Unstable max:", np.max(np.abs(unstable)))
print("Saved: plots/stability.png")
