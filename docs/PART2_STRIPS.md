
# Part 2 — Parallel 2D Heat Diffusion Using MPI Strip Decomposition

## 1. Objective

The objective of Part 2 is to implement and verify a parallel version of the two-dimensional heat equation solver using MPI (Message Passing Interface) and one-dimensional strip decomposition.

The parallel solver must reproduce the numerical solution obtained by the serial solver developed and verified in Part 1.

The implementation is evaluated through:

1. Correct execution with different numbers of MPI processes.
2. Correct handling of boundary conditions.
3. Correct communication between neighboring processes.
4. Correct handling of equal and unequal strip sizes.
5. Bit-for-bit comparisons against the serial solver.
6. Verification using the analytical solution (Case V).
7. Distributed execution across the three Ubuntu virtual machines.

Local correctness tests have been completed. Distributed execution across the three machines remains pending.

---

## 2. Implementation

### 2.1 Source code

The existing MPI strip implementation is located at:

`src/parallel/heat_strips.cpp`

The compiled executable is:

`heat_strips`

The serial reference implementation is:

`src/heat_serial.cpp`

The corresponding executable is:

`heat_serial`

Both implementations solve the same two-dimensional heat diffusion problem using an explicit finite-difference method.

### 2.2 Numerical model

The heat equation is:

du/dt = d²u/dx² + d²u/dy²

The computational domain is the unit square:

0 <= x <= 1

0 <= y <= 1

With a uniform grid:

h = 1/N

The explicit five-point finite-difference update is:

u(i,j,n+1) = u(i,j,n)
           + r * (
               u(i+1,j,n)
             + u(i-1,j,n)
             + u(i,j+1,n)
             + u(i,j-1,n)
             - 4*u(i,j,n)
           )

where:

r = dt/h²

Therefore:

dt = r/N²

For the two-dimensional explicit scheme, the standard stability condition is:

0 < r <= 1/4

All Part 2 correctness tests reported here use:

r = 0.2

This satisfies the stability condition.

### 2.3 Strip decomposition

In one-dimensional strip decomposition, the computational domain is divided into horizontal strips.

Each MPI process is responsible for a subset of the grid rows.

The number of interior rows is:

N - 1

These rows are distributed among the participating MPI processes.

For P processes, the implementation must correctly handle both:

- Equal distribution of rows.
- Unequal distribution when (N - 1) is not divisible by P.

Neighboring MPI processes exchange boundary information, commonly called halo or ghost-row data, so that each process can apply the five-point finite-difference stencil correctly.

The global temperature field is written to a binary output file and compared against the serial implementation.

### 2.4 Binary output

The resulting temperature field is stored as a two-dimensional grid of double-precision values.

The expected grid dimensions are:

(N + 1) x (N + 1)

The serial and parallel output files are compared using the Linux `cmp` utility.

When `cmp` reports no differences, the two binary files are identical byte for byte.

This provides a stronger check than merely comparing rounded error values.

---

## 3. Testing Environment

The local correctness tests were performed on Jose's Ubuntu virtual machine.

Machine:

heat-jose

Operating system:

Ubuntu 24.04.5 LTS

Architecture:

ARM64

Allocated virtual CPUs:

2

MPI implementation:

Open MPI 4.1.6

For P = 1 and P = 2, MPI was executed normally.

For P = 3 and P = 4, the option:

`--oversubscribe`

was used because the VM has only two allocated virtual CPUs.

Oversubscription was used exclusively for functional correctness tests.

Consequently, the timings obtained from oversubscribed executions must not be used to draw performance or scalability conclusions.

Distributed execution across Jose, Dia, and Theresa will be evaluated separately.

---

## 4. Verification Methodology

Each correctness test follows the same procedure:

1. Execute the MPI strip solver with selected parameters.
2. Execute the serial solver with identical numerical parameters, unless a matching serial reference already exists.
3. Save the two outputs to separate binary files.
4. Compare the files with `cmp`.
5. Record whether the outputs are bit-for-bit identical.

The numerical parameters must match exactly:

- Case.
- Grid size N.
- Stability parameter r.
- Number of time steps.
- Final simulation time.

MPI process counts are varied independently.

The principal comparison criterion is:

MPI output == serial output

The equality is checked at the binary-file level.

---

## 5. Test 1 — One MPI Process

### 5.1 Parameters

Case: 2

N: 8

P: 1

r: 0.2

Steps: 1

Final time:

T = 0.003125

### 5.2 MPI command

```bash
mpirun -np 1 ./heat_strips \
  --case 2 \
  --N 8 \
  --r 0.2 \
  --steps 1 \
  --decomp strips \
  --out /tmp/strips_p1.bin
```

### 5.3 MPI output

```text
decomp=strips case=2 P=1 N=8 steps=1 r=0.2 T=0.003125 t_total=0.000556336 t_comp=1.66e-07 t_comm=0.000555794
```

### 5.4 Serial reference

```bash
./heat_serial \
  --case 2 \
  --N 8 \
  --r 0.2 \
  --steps 1 \
  --decomp serial \
  --out /tmp/serial_p1.bin
```

### 5.5 Binary comparison

```bash
cmp /tmp/serial_p1.bin /tmp/strips_p1.bin
```

Result:

PASS — Bit-for-bit identical.

### 5.6 Interpretation

The MPI strip implementation produces the same numerical solution as the serial solver when executed with one process.

The reported communication time is nonzero even with P = 1. This may reflect MPI-related overhead, synchronization, or collective operations; its exact source requires code-level timing inspection.

It should not be interpreted as evidence of interprocess halo exchange when only one process is used.

---

## 6. Test 2 — Two MPI Processes, One Time Step

### 6.1 Parameters

Case: 2

N: 8

P: 2

r: 0.2

Steps: 1

T: 0.003125

### 6.2 Command

```bash
mpirun -np 2 ./heat_strips \
  --case 2 \
  --N 8 \
  --r 0.2 \
  --steps 1 \
  --decomp strips \
  --out /tmp/strips_p2.bin
```

### 6.3 MPI output

```text
decomp=strips case=2 P=2 N=8 steps=1 r=0.2 T=0.003125 t_total=1.1042e-05 t_comp=2.08e-07 t_comm=1.075e-05
```

### 6.4 Binary comparison

Serial reference:

`/tmp/serial_p1.bin`

MPI result:

`/tmp/strips_p2.bin`

Command:

```bash
cmp /tmp/serial_p1.bin /tmp/strips_p2.bin
```

Result:

PASS — Bit-for-bit identical.

### 6.5 Interpretation

The two-process implementation successfully reproduces the serial temperature field after one time step.

---

## 7. Test 3 — Two Processes, 100 Time Steps

### 7.1 Parameters

Case: 2

N: 40

P: 2

r: 0.2

Steps: 100

T: 0.0125

### 7.2 MPI command

```bash
mpirun -np 2 ./heat_strips \
  --case 2 \
  --N 40 \
  --r 0.2 \
  --steps 100 \
  --decomp strips \
  --out /tmp/strips_p2_100.bin
```

### 7.3 MPI output

```text
decomp=strips case=2 P=2 N=40 steps=100 r=0.2 T=0.0125 t_total=0.000193455 t_comp=8.3708e-05 t_comm=0.000114326
```

### 7.4 Binary comparison

Serial reference:

`/tmp/heat_case2_part1.bin`

Command:

```bash
cmp /tmp/heat_case2_part1.bin /tmp/strips_p2_100.bin
```

Result:

PASS — Bit-for-bit identical.

### 7.5 Interpretation

The parallel implementation reproduces the serial solution after 100 iterations.

This verifies the numerical result across repeated updates involving communication between neighboring strips.

---

## 8. Test 4 — Three Processes, Equal Strip Sizes

### 8.1 Parameters

Case: 2

N: 40

P: 3

r: 0.2

Steps: 100

T: 0.0125

Number of interior rows:

N - 1 = 39

Distribution:

39 / 3 = 13 rows per process.

### 8.2 MPI command

```bash
mpirun --oversubscribe -np 3 ./heat_strips \
  --case 2 \
  --N 40 \
  --r 0.2 \
  --steps 100 \
  --decomp strips \
  --out /tmp/strips_p3_100.bin
```

### 8.3 MPI output

```text
decomp=strips case=2 P=3 N=40 steps=100 r=0.2 T=0.0125 t_total=0.000541195 t_comp=3.9094e-05 t_comm=0.000495767
```

### 8.4 Binary comparison

```bash
cmp /tmp/heat_case2_part1.bin /tmp/strips_p3_100.bin
```

Result:

PASS — Bit-for-bit identical.

### 8.5 Interpretation

The three-process MPI implementation correctly reproduces the serial result with an equal distribution of interior rows.

---

## 9. Test 5 — Three Processes, Unequal Strip Sizes

### 9.1 Parameters

Case: 2

N: 41

P: 3

r: 0.2

Steps: 100

Final simulation time:

T = 0.0118976799524

Number of interior rows:

N - 1 = 40

Expected row distribution:

- Process 0: 14 rows.
- Process 1: 13 rows.
- Process 2: 13 rows.

### 9.2 MPI command

```bash
mpirun --oversubscribe -np 3 ./heat_strips \
  --case 2 \
  --N 41 \
  --r 0.2 \
  --steps 100 \
  --decomp strips \
  --out /tmp/strips_p3_uneven.bin
```

### 9.3 MPI output

```text
decomp=strips case=2 P=3 N=41 steps=100 r=0.2 T=0.0118976799524 t_total=0.000508128 t_comp=4.2281e-05 t_comm=0.000462018
```

### 9.4 Serial reference

```bash
./heat_serial \
  --case 2 \
  --N 41 \
  --r 0.2 \
  --steps 100 \
  --decomp serial \
  --out /tmp/serial_p3_uneven.bin
```

### 9.5 Binary comparison

```bash
cmp /tmp/serial_p3_uneven.bin /tmp/strips_p3_uneven.bin
```

Result:

PASS — Bit-for-bit identical.

### 9.6 Interpretation

The MPI solver produces the correct temperature field when the number of interior rows is not divisible by the process count.

This verifies the numerical behavior for uneven strip decomposition.

---

## 10. Test 6 — Four MPI Processes

### 10.1 Parameters

Case: 2

N: 41

P: 4

r: 0.2

Steps: 100

T: 0.0118976799524

Number of interior rows:

40

Expected distribution:

10 rows per process.

### 10.2 MPI command

```bash
mpirun --oversubscribe -np 4 ./heat_strips \
  --case 2 \
  --N 41 \
  --r 0.2 \
  --steps 100 \
  --decomp strips \
  --out /tmp/strips_p4.bin
```

### 10.3 MPI output

```text
decomp=strips case=2 P=4 N=41 steps=100 r=0.2 T=0.0118976799524 t_total=0.001764312 t_comp=3.7622e-05 t_comm=0.001721233
```

### 10.4 Binary comparison

```bash
cmp /tmp/serial_p3_uneven.bin /tmp/strips_p4.bin
```

Result:

PASS — Bit-for-bit identical.

### 10.5 Interpretation

The four-process parallel solver reproduces the serial result correctly.

Because the execution was oversubscribed, this test is used for correctness verification only.

---

## 11. Test 7 — Case 1 Boundary Conditions

### 11.1 Objective

Verify the parallel implementation for Case 1, in which all four boundaries are held at temperature 1.

### 11.2 Parameters

Case: 1

N: 40

P: 2

r: 0.2

Steps: 100

T: 0.0125

### 11.3 MPI command

```bash
mpirun -np 2 ./heat_strips \
  --case 1 \
  --N 40 \
  --r 0.2 \
  --steps 100 \
  --decomp strips \
  --out /tmp/strips_case1_p2.bin
```

### 11.4 MPI output

```text
decomp=strips case=1 P=2 N=40 steps=100 r=0.2 T=0.0125 t_total=0.000133026 t_comp=5.5738e-05 t_comm=7.374e-05
```

### 11.5 Binary comparison

Serial reference:

`/tmp/heat_case1_part1.bin`

Command:

```bash
cmp /tmp/heat_case1_part1.bin /tmp/strips_case1_p2.bin
```

Result:

PASS — Bit-for-bit identical.

### 11.6 Interpretation

The MPI strip implementation correctly reproduces the serial solution for Case 1.

This complements the previously completed verification of Case 2.

---

## 12. Test 8 — Analytical Verification, Case V

### 12.1 Analytical solution

Case V uses the analytical solution:

u(x,y,t) = sin(pi*x) * sin(pi*y) * exp(-2*pi²*t)

This provides an independent mathematical reference for the numerical approximation.

The maximum absolute error is:

err_inf = max |u_numerical - u_exact|

The L2 error is also computed by the program.

### 12.2 Parameters

Case: V

N: 40

P: 2

r: 0.2

Steps: 80

T: 0.01

### 12.3 MPI command

```bash
mpirun -np 2 ./heat_strips \
  --case V \
  --N 40 \
  --r 0.2 \
  --steps 80 \
  --decomp strips \
  --out /tmp/strips_caseV_p2.bin
```

### 12.4 MPI output

```text
decomp=strips case=V P=2 N=40 steps=80 r=0.2 T=0.01 t_total=0.000115987 t_comp=4.5244e-05 t_comm=6.8326e-05 err_inf=0.000116740771181 err_l2=5.83703855906e-05
```

### 12.5 Serial command

```bash
./heat_serial \
  --case V \
  --N 40 \
  --r 0.2 \
  --steps 80 \
  --decomp serial \
  --out /tmp/serial_caseV_p2.bin
```

### 12.6 Serial output

```text
decomp=serial case=V P=1 N=40 steps=80 r=0.2 T=0.01 t_total=0.000286011 t_comp=0.000286011 t_comm=0 err_inf=0.000116740771181 err_l2=5.83703855906e-05
```

### 12.7 Error comparison

| Measurement | Serial | MPI strips |
|---|---:|---:|
| Maximum error | 0.000116740771181 | 0.000116740771181 |
| L2 error | 0.0000583703855906 | 0.0000583703855906 |

The reported errors are identical.

### 12.8 Binary comparison

```bash
cmp /tmp/serial_caseV_p2.bin /tmp/strips_caseV_p2.bin
```

Result:

PASS — Bit-for-bit identical.

### 12.9 Interpretation

The parallel and serial solvers produce identical numerical fields for Case V.

Both also report the same numerical errors relative to the analytical solution.

Therefore, the MPI strip implementation preserves the verified numerical accuracy of the serial implementation for this test.

---

## 13. Test 9 — Small-Grid Uneven Decomposition

### 13.1 Objective

Test the solver when certain MPI processes are assigned only one interior row.

### 13.2 Parameters

Case: 2

N: 5

P: 3

r: 0.2

Steps: 10

T: 0.08

Number of interior rows:

N - 1 = 4

Expected distribution:

- Process 0: 2 rows.
- Process 1: 1 row.
- Process 2: 1 row.

### 13.3 MPI command

```bash
mpirun --oversubscribe -np 3 ./heat_strips \
  --case 2 \
  --N 5 \
  --r 0.2 \
  --steps 10 \
  --decomp strips \
  --out /tmp/strips_small_p3.bin
```

### 13.4 MPI output

```text
decomp=strips case=2 P=3 N=5 steps=10 r=0.2 T=0.08 t_total=6.5493e-05 t_comp=4.15e-07 t_comm=6.4325e-05
```

### 13.5 Serial reference

```bash
./heat_serial \
  --case 2 \
  --N 5 \
  --r 0.2 \
  --steps 10 \
  --decomp serial \
  --out /tmp/serial_small_p3.bin
```

Serial output:

```text
decomp=serial case=2 P=1 N=5 steps=10 r=0.2 T=0.08 t_total=6.66e-07 t_comp=6.66e-07 t_comm=0
```

### 13.6 Binary comparison

```bash
cmp /tmp/serial_small_p3.bin /tmp/strips_small_p3.bin
```

Result:

PASS — Bit-for-bit identical.

### 13.7 Interpretation

The MPI strip solver correctly reproduces the serial solution on a small grid with only four interior rows distributed among three processes.

This provides additional evidence that the implementation handles narrow subdomains correctly.

---

## 14. Summary of Local Correctness Tests

| Test | Case | N | P | Steps | Distribution | Result |
|---|---|---:|---:|---:|---|---|
| 1 | 2 | 8 | 1 | 1 | Single process | PASS |
| 2 | 2 | 8 | 2 | 1 | Equal | PASS |
| 3 | 2 | 40 | 2 | 100 | Unequal | PASS |
| 4 | 2 | 40 | 3 | 100 | Equal | PASS |
| 5 | 2 | 41 | 3 | 100 | Unequal | PASS |
| 6 | 2 | 41 | 4 | 100 | Equal | PASS |
| 7 | 1 | 40 | 2 | 100 | Unequal | PASS |
| 8 | V | 40 | 2 | 80 | Unequal | PASS |
| 9 | 2 | 5 | 3 | 10 | Unequal | PASS |

All nine local correctness comparisons passed.

Every tested MPI output file was bit-for-bit identical to its corresponding serial reference.

---

## 15. Timing Observations

The recorded local timings are summarized below.

All times are expressed in seconds.

| Test | P | Total time | Computation time | Communication time |
|---|---:|---:|---:|---:|
| Case 2, N=8, 1 step | 1 | 0.000556336 | 0.000000166 | 0.000555794 |
| Case 2, N=8, 1 step | 2 | 0.000011042 | 0.000000208 | 0.000010750 |
| Case 2, N=40, 100 steps | 2 | 0.000193455 | 0.000083708 | 0.000114326 |
| Case 2, N=40, 100 steps | 3 | 0.000541195 | 0.000039094 | 0.000495767 |
| Case 2, N=41, 100 steps | 3 | 0.000508128 | 0.000042281 | 0.000462018 |
| Case 2, N=41, 100 steps | 4 | 0.001764312 | 0.000037622 | 0.001721233 |
| Case 1, N=40, 100 steps | 2 | 0.000133026 | 0.000055738 | 0.000073740 |
| Case V, N=40, 80 steps | 2 | 0.000115987 | 0.000045244 | 0.000068326 |
| Case 2, N=5, 10 steps | 3 | 0.000065493 | 0.000000415 | 0.000064325 |

### 15.1 Interpretation

These timings demonstrate successful execution but are not sufficient for reliable scalability analysis.

Important limitations include:

- Several workloads are extremely small.
- The measurements come from individual executions rather than repeated statistical benchmarks.
- Tests with P = 3 and P = 4 used CPU oversubscription.
- The reported communication category may include additional MPI overhead.
- Distributed network communication has not yet been evaluated in Part 2.

Therefore, no quantitative speedup or parallel efficiency claims are made from these measurements.

A dedicated performance study will be conducted separately.

---

## 16. Distributed MPI Testing — Pending

The project uses three Ubuntu virtual machines connected through Tailscale.

The participating machines are:

| Machine | Role | Architecture |
|---|---|---|
| heat-jose | Jose's VM | ARM64 |
| heat-dia | Dia's VM | x86_64 |
| heat-theresa | Theresa's VM | x86_64 |

The network and preliminary MPI configuration were investigated during Part 0.

However, the Part 2 strip solver has not yet been validated using MPI processes distributed across these three machines.

This test is postponed until all three laptops are available.

### 16.1 Planned distributed validation

The remaining work includes:

1. Confirm that all three Ubuntu VMs are reachable through Tailscale.
2. Verify that the required MPI executable is available and compatible on each machine.
3. Confirm the hostfile and remote execution configuration.
4. Execute the MPI strip solver across multiple VMs.
5. Compare the distributed temperature field against the serial result.
6. Verify Cases 1, 2, and V where appropriate.
7. Test suitable process allocations across the machines.
8. Record distributed computation and communication timings.
9. Document any failures, corrections, and final successful tests.

### 16.2 Important note

The Part 0 communication benchmarks do not need to be repeated solely for this validation.

Distributed Part 2 tests will focus on the actual heat-equation solver.

The current Part 2 status is:

LOCAL CORRECTNESS: VERIFIED

DISTRIBUTED CORRECTNESS: PENDING

---

## 17. Files and Artifacts

### 17.1 Source code

`src/parallel/heat_strips.cpp`

`src/heat_serial.cpp`

### 17.2 Executables

`heat_strips`

`heat_serial`

### 17.3 Documentation

`docs/PART0_CLUSTER.md`

`docs/PART1_SERIAL.md`

`docs/PART2_STRIPS.md`

### 17.4 Temporary correctness-test files

The local test binary outputs were written under `/tmp`.

These files provide immediate testing references but should not be assumed to persist indefinitely.

The documented commands can be rerun to regenerate them when needed.

---

## 18. Conclusion

The local verification phase of MPI strip decomposition was successful.

Nine correctness comparisons were performed using one, two, three, and four MPI processes.

The tests covered:

- All three numerical cases: 1, 2, and V.
- Equal and unequal strip decomposition.
- Multiple time steps.
- Small grids containing subdomains with only one interior row.
- Binary comparisons against the serial solver.
- Comparison of analytical-solution error values.

All nine binary comparisons passed.

For Case V, the serial and parallel implementations reported:

Maximum error:

0.000116740771181

L2 error:

0.0000583703855906

The results demonstrate that the MPI strip implementation reproduces the verified serial numerical solution for all tested local configurations.

The distributed validation was subsequently completed successfully.
See Section 19 for the results.

---

## 19. Distributed validation across three Ubuntu VMs

Distributed validation was successfully completed using three
Ubuntu virtual machines connected through Tailscale:

- heat-jose
- heat-dia
- heat-theresa

All machines used the same Git commit:

`35c4b7e Add MPI strip ghost row debugging`

### 19.1 MPI connectivity

Open MPI successfully launched processes across all three machines.

Both process-management and data communication were explicitly
restricted to the Tailscale interface:

- `oob_tcp_if_include tailscale0`
- `btl_tcp_if_include tailscale0`

### 19.2 Distributed heat simulation

The strip decomposition solver successfully executed with:

- Grid size: N=8
- Test case: 2
- Time steps: 1
- Stability parameter: r=0.2
- MPI processes: P=3
- Decomposition: strips

The distributed simulation completed successfully.

### 19.3 Ghost-row debugging: P=2

The debugging output was inspected across Jose and Dia.

The output confirmed:

- Rank 0 owned global rows 1 to 4.
- Rank 1 owned global rows 5 to 7.
- Physical boundary ghost rows contained the expected value 1.00.
- Internal ghost rows were exchanged between neighboring ranks.

The distributed binary output was compared against the serial reference.

Result:

`PASS: P=2 ghost-debug output matches serial exactly`

### 19.4 Ghost-row debugging: P=3

The debugging output was inspected across Jose, Dia and Theresa.

The output confirmed:

- Rank 0 owned global rows 1 to 3.
- Rank 1 owned global rows 4 to 5.
- Rank 2 owned global rows 6 to 7.
- Internal ghost rows were exchanged between neighboring ranks.
- Physical boundary ghost rows contained the expected value 1.00.

The distributed binary output was compared against the serial reference.

Result:

`PASS: P=3 ghost-debug output matches serial exactly`

### 19.5 Distributed validation conclusion

Both P=2 and P=3 ghost-row debugging tests completed successfully.

Both distributed output files were byte-for-byte identical to the
serial reference for the same numerical parameters.

The three-machine MPI execution was also successfully verified.

The distributed validation requirement for Part 2 has therefore
been completed.
