import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

data = np.genfromtxt(
    "results/convergence.csv",
    delimiter=",",
    names=True
)

N = data["N"]
h = 1.0 / N
err_inf = data["err_inf"]
err_l2 = data["err_l2"]

order_inf = np.polyfit(np.log(h), np.log(err_inf), 1)[0]
order_l2 = np.polyfit(np.log(h), np.log(err_l2), 1)[0]

plt.figure(figsize=(8, 5))
plt.loglog(h, err_inf, "o-", label=f"Linf (order {order_inf:.3f})")
plt.loglog(h, err_l2, "s-", label=f"L2 (order {order_l2:.3f})")
plt.loglog(
    h, err_inf[0] * (h / h[0])**2,
    "--", label="Reference O(h^2)"
)

plt.xlabel("Grid spacing h")
plt.ylabel("Numerical error")
plt.title("Convergence study - 2D Heat Equation")
plt.legend()
plt.grid(True, which="both")
plt.tight_layout()

plt.savefig("plots/convergence.png", dpi=200)

print(f"Observed Linf order: {order_inf:.4f}")
print(f"Observed L2 order:   {order_l2:.4f}")
print("Saved: plots/convergence.png")
