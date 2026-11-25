"""Make the demo video: heat spreading in Case 1 and Case 2.

Frames are field files written by the solver at increasing step counts:
  for c in 1 2; for k in 0..90: ./heat_serial --case $c --N 48 --r 0.25
      --steps max(1, 10k) --out frames/c${c}_$(printf %03d $k).bin
(The parallel run on the three VMs gives bit-for-bit the same fields,
see scripts/demo.sh.)

Usage: python3 scripts/demo_animation.py <frames_dir> <out.mp4>
Needs ffmpeg.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter

frames_dir, out = Path(sys.argv[1]), sys.argv[2]
N, r = 48, 0.25
dt = r / N ** 2
K = len(list(frames_dir.glob("c1_*.bin")))


def load(c, k):
    return np.fromfile(frames_dir / f"c{c}_{k:03d}.bin", dtype="<f8").reshape(N + 1, N + 1)


fig, axes = plt.subplots(1, 2, figsize=(10, 5.2))
ims = []
for ax, c, name in [(axes[0], 1, "Case 1: four hot edges"),
                    (axes[1], 2, "Case 2: hot top and bottom")]:
    im = ax.imshow(load(c, 0), origin="lower", extent=[0, 1, 0, 1], cmap="hot",
                   vmin=0, vmax=1, interpolation="bilinear")
    ax.set_title(name)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ims.append(im)
fig.colorbar(ims[1], ax=axes, shrink=0.8, label="temperature u")
label = fig.suptitle("")
fig.text(0.5, 0.02,
         f"Explicit 5-point scheme, N={N}, r={r}. The MPI run on heat-jose + "
         "heat-dia + heat-theresa gives the same field bit-for-bit (cmp, t = 0.05).",
         ha="center", fontsize=8)

writer = FFMpegWriter(fps=12, bitrate=2400)
with writer.saving(fig, out, dpi=120):
    for k in range(K):
        steps = max(1, 10 * k)
        ims[0].set_data(load(1, k))
        ims[1].set_data(load(2, k))
        label.set_text(f"2D heat diffusion   t = {steps * dt:.4f}   (step {steps})")
        writer.grab_frame()
    for _ in range(24):          # hold the last frame for 2 s
        writer.grab_frame()
print(f"Saved {out}")
