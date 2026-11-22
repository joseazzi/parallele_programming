### Why corner ghost cells are not required

The explicit finite-difference scheme for the 2D heat equation uses a **5-point stencil**.

To update the temperature at grid point \((i,j)\), the solver uses five values: the current point, its left and right neighbors, and its upper and lower neighbors.

Diagonal neighbors are not used in the calculation. Therefore, each MPI process only needs to exchange ghost rows and columns with its four neighboring processes.

**Corner ghost cells are unnecessary because the 5-point stencil does not access diagonal values.**

However, a **9-point stencil** would also use the four diagonal neighbors. In that case, corner ghost cells would be necessary, and diagonal temperature data would need to be communicated.

## Strips versus blocks: theoretical prediction

The communication model from Part 0 is:

    t_msg(m) = ts + m * tw

Using the mean of the three inter-laptop measurements:

- ts = 0.0350035 seconds
- tw = 1.331733e-6 seconds/byte

Assume double-precision values (8 bytes), a balanced 2x2 block
grid for P=4, and a balanced 2x4 block grid for P=8.

Approximate critical-rank halo communication costs:

- Strips: 2*ts + 16*N*tw
- Blocks, P=4: 2*ts + 8*N*tw
- Blocks, P=8: 3*ts + 10*N*tw

| P | N | Strips (ms) | Blocks (ms) | Prediction |
|---|---|---|---|---|
| 4 | 512 | 80.92 | 75.46 | Blocks |
| 4 | 2048 | 113.65 | 91.83 | Blocks |
| 4 | 8192 | 244.56 | 157.28 | Blocks |
| 8 | 512 | 80.92 | 111.83 | Strips |
| 8 | 2048 | 113.65 | 132.28 | Strips |
| 8 | 8192 | 244.56 | 214.11 | Blocks |

These are simplified network communication estimates per
iteration, not measured total solver runtimes. Real performance
also depends on process placement, local communication, and
computation. For P=8, the estimated crossover is N=4381.

## Strips versus blocks: measured performance

Measurements used Case 2, r=0.2, 100 time steps,
and local MPI processes on Jose's Ubuntu VM.

Open MPI --oversubscribe was required because the VM
has fewer available CPU slots than the requested ranks.

| P | N | Strips total (s) | Blocks total (s) | Faster |
|---|---|---|---|---|
| 4 | 512 | 0.010307134 | 0.010095719 | Blocks |
| 4 | 2048 | 0.168625020 | 0.174521872 | Strips |
| 4 | 8192 | 3.393911816 | 3.374511735 | Blocks |
| 8 | 512 | 0.014791231 | 0.019996555 | Strips |
| 8 | 2048 | 0.192629507 | 0.281884974 | Strips |
| 8 | 8192 | 3.394111979 | 3.513385919 | Strips |

Strips was faster in four of six configurations.

These measurements do not directly validate the Part 0
inter-laptop communication model because the benchmark
ran locally. Oversubscription introduces CPU scheduling
contention, and each configuration was measured once.

The theoretical model captures communication volume and
message startup costs but does not fully capture local
computation, scheduling, or synchronization overhead.
