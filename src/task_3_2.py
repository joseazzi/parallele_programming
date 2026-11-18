import math

x = 1.0
exact = -math.sin(x)

print("h,approximation,error")

for h in [0.2, 0.1, 0.05, 0.025]:
    approximation = (
        math.sin(x + h)
        - 2 * math.sin(x)
        + math.sin(x - h)
    ) / (h * h)

    error = abs(approximation - exact)

    print(f"{h},{approximation:.12f},{error:.12e}")
