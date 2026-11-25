
# Part 1 — Serial 2D Heat Diffusion Solver

## 1. Objective

The objective of Part 1 is to implement and verify a serial C++ solver for the two-dimensional heat equation.

This serial implementation serves as the reference solution for the parallel MPI implementations developed in Parts 2 and 3.

The solver must:

- Implement the explicit finite-difference method.
- Simulate the two prescribed heating configurations.
- Support verification against an exact analytical solution.
- Enforce the numerical stability condition.
- Measure computation time.
- Produce a binary temperature field.
- Demonstrate second-order convergence.
- Illustrate the effects of violating the stability limit.

## 2. Mathematical Model

The two-dimensional heat equation is:

\[
\frac{\partial u}{\partial t}
=
\alpha\left(
\frac{\partial^2u}{\partial x^2}
+
\frac{\partial^2u}{\partial y^2}
\right)
\]

where:

- \(u(x,y,t)\) is the temperature.
- \(\alpha\) is the thermal diffusivity.
- \(x,y\) are spatial coordinates.
- \(t\) is time.

The computational domain is the unit square:

\[
\Omega=[0,1]\times[0,1]
\]

The assignment specifies:

\[
\alpha=1
\]

The uniform grid contains \(N\) intervals in each direction, corresponding to \((N+1)^2\) grid points.

The spatial step is:

\[
h=\frac{1}{N}
\]

The time-step parameter is defined as:

\[
r=\frac{\alpha\Delta t}{h^2}
\]

For this project, \(\alpha=1\), so:

\[
\Delta t=rh^2=\frac{r}{N^2}
\]

## 3. Numerical Method

### 3.1 Spatial discretization

The second derivative in the x-direction is approximated using central differences:

\[
\frac{\partial^2u}{\partial x^2}
\approx
\frac{u_{i+1,j}-2u_{i,j}+u_{i-1,j}}{h^2}
\]

Similarly, for the y-direction:

\[
\frac{\partial^2u}{\partial y^2}
\approx
\frac{u_{i,j+1}-2u_{i,j}+u_{i,j-1}}{h^2}
\]

Combining them gives the five-point discrete Laplacian:

\[
\nabla_h^2u_{i,j}
=
\frac{
u_{i+1,j}+u_{i-1,j}
+u_{i,j+1}+u_{i,j-1}
-4u_{i,j}
}{h^2}
\]

### 3.2 Temporal discretization

Forward Euler is used for the time derivative:

\[
\frac{\partial u}{\partial t}
\approx
\frac{u_{i,j}^{n+1}-u_{i,j}^{n}}{\Delta t}
\]

Substituting the finite-difference approximations gives:

\[
u_{i,j}^{n+1}
=
u_{i,j}^{n}
+
r\left(
u_{i+1,j}^{n}
+
u_{i-1,j}^{n}
+
u_{i,j+1}^{n}
+
u_{i,j-1}^{n}
-
4u_{i,j}^{n}
\right)
\]

Equivalently:

\[
u_{i,j}^{n+1}
=
(1-4r)u_{i,j}^{n}
+
r\left(
u_{i+1,j}^{n}
+
u_{i-1,j}^{n}
+
u_{i,j+1}^{n}
+
u_{i,j-1}^{n}
\right)
\]

This explicit update is applied to every interior grid point at every time step.

Boundary values remain fixed according to the selected simulation case.

### 3.3 Stability condition

For the explicit two-dimensional heat scheme on a uniform square grid, the stability requirement is:

\[
0<r\leq\frac14
\]

Therefore:

\[
\Delta t\leq\frac{h^2}{4\alpha}
\]

For \(\alpha=1\):

\[
\Delta t\leq\frac{1}{4N^2}
\]

The normal serial solver rejects an unstable choice such as \(r=0.3\).

A separate experimental program is retained to demonstrate numerical instability when this limit is deliberately exceeded.

### 3.4 Accuracy

Central differences give second-order spatial accuracy, while Forward Euler gives first-order temporal accuracy.

The expected global accuracy for a sufficiently smooth solution is:

\[
O(\Delta t+h^2)
\]

Because the experiments keep \(r\) fixed, the time step satisfies:

\[
\Delta t=O(h^2)
\]

Consequently, the overall error is expected to decrease approximately as:

\[
O(h^2)
\]

This prediction is verified through the convergence study.

## 4. Serial Implementation

### 4.1 Source code

The serial solver is implemented in:

`src/heat_serial.cpp`

The executable is:

`heat_serial`

The program is written in C++17 and compiled with the repository Makefile.

Compiler options include:

```text
-O2 -std=c++17 -ffp-contract=off
```

The `-O2` option enables compiler optimization.

The `-ffp-contract=off` option reduces differences caused by fused floating-point operations, helping comparisons between the serial and parallel versions.

### 4.2 Grid representation

The two-dimensional temperature field is stored in a contiguous one-dimensional array.

For a grid of \((N+1)\times(N+1)\) nodes, row-major indexing is:

\[
\operatorname{index}(i,j)=j(N+1)+i
\]

The index \(i\) varies fastest.

Two arrays store the current and next time levels.

After each iteration, the arrays are swapped instead of copying the complete temperature field.

### 4.3 Program interface

The serial solver supports command-line arguments for:

- `--case`: simulation case (1, 2 or V).
- `--N`: number of intervals in each direction.
- `--r`: dimensionless time-step parameter.
- `--steps`: number of time steps.
- `--T`: requested final simulation time.
- `--out`: output binary file.
- `--decomp`: decomposition selection, using `serial` for this version.

Example:

```bash
./heat_serial --case 1 --N 40 --r 0.2 \
  --steps 100 --decomp serial --out case1.bin
```

The program prints a summary line containing simulation parameters and timing measurements.

### 4.4 Output format

The temperature field is stored as:

- Raw binary data.
- Little-endian double-precision values.
- Row-major ordering.
- \((N+1)^2\) total values.
- Boundary nodes included.
- No file header.

For \(N=40\), the output contains:

\[
41\times41=1681
\]

double-precision values, corresponding to 13,448 bytes.

### 4.5 Timing

The solver reports computation time using a steady timing mechanism.

Only the time-stepping computation is measured, excluding initialization and binary output.

Because this is the serial implementation, the communication time is zero.

## 5. Case 1 — Four Hot Edges

### 5.1 Initial and boundary conditions

For Case 1, the interior of the plate initially has temperature:

\[
u(x,y,0)=0
\]

All four boundaries are maintained at:

\[
u=1
\]

Heat enters the plate from every edge.

As the simulation progresses, the interior temperature increases toward the hot boundary temperature.

### 5.2 Verification experiment

The following parameters were tested:

| Parameter | Value |
|---|---|
| Case | 1 |
| Grid intervals | 40 |
| Stability parameter | 0.2 |
| Number of steps | 100 |
| Final simulation time | 0.0125 |
| MPI processes | 1 |
| Decomposition | Serial |

The final time follows from:

\[
T=100\times\frac{0.2}{40^2}=0.0125
\]

Recorded program output:

```text
decomp=serial case=1 P=1 N=40 steps=100 r=0.2 T=0.0125 t_total=0.000519476 t_comp=0.000519476 t_comm=0
```

### 5.3 Boundary verification

The saved binary field was inspected using NumPy.

| Check | Recorded result |
|---|---|
| Grid shape | (41, 41) |
| Bottom boundary | 1.0 |
| Top boundary | 1.0 |
| Left boundary | 1.0 |
| Right boundary | 1.0 |
| Interior minimum | 0.006295574205116837 |
| Interior maximum | 0.984338939215897 |
| All values finite | True |

All four boundaries remained exactly at temperature 1.

All interior temperatures were finite and between 0 and 1.

The numerical field is therefore consistent with the expected physical behavior of Case 1 for the tested parameters.

## 6. Case 2 — Hot Top and Bottom

### 6.1 Initial and boundary conditions

For Case 2, the interior initially has:

\[
u(x,y,0)=0
\]

The top and bottom boundaries are maintained at:

\[
u=1
\]

The left and right boundaries are maintained at:

\[
u=0
\]

The four corner nodes are assigned temperature 1, as specified by the project.

The simulation models heat flowing from the hot top and bottom edges toward the colder side edges.

### 6.2 Verification experiment

The following parameters were tested:

| Parameter | Value |
|---|---|
| Case | 2 |
| Grid intervals | 40 |
| Stability parameter | 0.2 |
| Number of steps | 100 |
| Final simulation time | 0.0125 |
| MPI processes | 1 |
| Decomposition | Serial |

Recorded program output:

```text
decomp=serial case=2 P=1 N=40 steps=100 r=0.2 T=0.0125 t_total=0.000404693 t_comp=0.000404693 t_comm=0
```

### 6.3 Boundary and corner verification

The binary field was loaded using NumPy.

| Check | Recorded result |
|---|---|
| Grid shape | (41, 41) |
| Bottom boundary | 1.0 |
| Top boundary | 1.0 |
| Left boundary excluding corners | 0.0 |
| Right boundary excluding corners | 0.0 |
| Four corners | 1.0 |
| Interior minimum | 0.0004414112361914415 |
| Interior maximum | 0.8746669919129538 |
| All values finite | True |

The top and bottom boundaries correctly remained at 1.

The left and right boundaries remained at 0 except at the four corners.

All corner values were exactly 1.

The interior temperatures remained finite and within the expected physical range.

These results verify the boundary conditions and numerical bounds of Case 2 for the tested configuration.

## 7. Case V — Verification Against an Exact Solution

### 7.1 Analytical solution

Case V is used to verify the numerical solver against a known exact solution.

The initial condition is:

\[
u(x,y,0)=\sin(\pi x)\sin(\pi y)
\]

All four boundaries are maintained at:

\[
u=0
\]

The analytical solution is:

\[
u_{\mathrm{exact}}(x,y,t)
=
\sin(\pi x)\sin(\pi y)e^{-2\pi^2t}
\]

The numerical result is compared with this exact solution at the final simulation time.

### 7.2 Error measurements

The maximum absolute error is:

\[
\|e\|_{\infty}
=
\max_{i,j}
|u_{i,j}^{\mathrm{numerical}}-u_{i,j}^{\mathrm{exact}}|
\]

The discrete L2 error is:

\[
\|e\|_{2,h}
=
\sqrt{
h^2\sum_{i,j}
\left(
u_{i,j}^{\mathrm{numerical}}
-
u_{i,j}^{\mathrm{exact}}
\right)^2
}
\]

Both error norms are calculated to evaluate numerical accuracy.

## 8. Convergence Study

### 8.1 Objective

The purpose of the convergence study is to verify that the numerical error decreases at the expected second-order rate as the spatial grid is refined.

The study uses Case V and compares numerical results against the analytical solution.

Run parameters (identified later by reproducing the CSV bit for bit): r = 0.2, final time T = 0.01, i.e. 0.05 N^2 time steps. The background Task 7.2 study (N = 16..256, T = 0.05) is in `docs/background/chapter7.md`.

### 8.2 Recorded convergence results

The project contains the numerical results in:

`results/convergence.csv`

The measured errors are:

| N | Maximum error | Discrete L2 error |
|---|---:|---:|
| 20 | 4.6856e-4 | 2.3428e-4 |
| 40 | 1.1674e-4 | 5.8370e-5 |
| 80 | 2.9160e-5 | 1.4580e-5 |
| 160 | 7.2885e-6 | 3.6443e-6 |
| 320 | 1.8220e-6 | 9.1102e-7 |

As N doubles, the grid spacing is halved.

The measured errors decrease by approximately a factor of four, consistent with second-order convergence.

### 8.3 Observed convergence order

The observed convergence order is calculated using:

\[
p=
\frac{\log(E_h/E_{h/2})}{\log(2)}
\]

where \(E_h\) represents an error norm computed using grid spacing \(h\).

The overall observed convergence order from the recorded results is approximately:

\[
p_{\infty}=2.00146
\]

\[
p_{2,h}=2.00146
\]

These results are very close to the theoretical value:

\[
p=2
\]

Therefore, the convergence experiment supports the expected second-order accuracy of the numerical method.

### 8.4 Convergence figure

The existing convergence graph is stored in:

`plots/convergence.png`

The plot-generation script is:

`plots/convergence.py`

The convergence figure should be included in the final project report.

## 9. Numerical Stability Experiment

### 9.1 Objective

The objective is to demonstrate the difference between stable and unstable time-step choices.

The explicit two-dimensional heat scheme is stable when:

\[
r\leq0.25
\]

Two parameter choices were compared:

- Stable configuration: \(r=0.2\).
- Unstable configuration: \(r=0.3\).

The unstable experiment intentionally exceeds the theoretical stability limit.

### 9.2 Experimental files

The experiment uses:

- `src/heat_unstable.cpp`
- `results/stable.bin`
- `results/unstable.bin`
- `plots/stability.py`
- `plots/stability.png`

The plotting script reads the binary fields using a grid size of \(N=40\).

The normal serial solver rejects invalid unstable time-step parameters.

The separate experimental solver is used to demonstrate the consequences of exceeding the stability limit.

### 9.3 Recorded results

The existing simulation outputs were analyzed using:

```bash
python3 plots/stability.py
```

The recorded values were:

| Configuration | Maximum absolute temperature |
|---|---:|
| Stable, r = 0.2 | 0.6102809917525998 |
| Unstable, r = 0.3 | 658118062191.4608 |

For the stable configuration, the numerical values remain bounded.

For the unstable configuration, the maximum absolute temperature grows to approximately:

\[
6.58\times10^{11}
\]

This extremely large magnitude illustrates numerical instability when the explicit stability restriction is violated.

### 9.4 Stability figure

The comparison figure is stored in:

`plots/stability.png`

The script `plots/stability.py` generates two panels:

- Stable solution for \(r=0.2\).
- Unstable solution for \(r=0.3\).

The figure visually illustrates the difference between bounded and unstable numerical behavior.

The result is consistent with the stability condition derived for the explicit two-dimensional scheme.

## 10. Results and Repository Files

### 10.1 Source code

- `src/heat_serial.cpp`
- `src/heat_unstable.cpp`

### 10.2 Build configuration

- `Makefile`

### 10.3 Convergence results

- `results/convergence.csv`
- `plots/convergence.py`
- `plots/convergence.png`

### 10.4 Stability results

- `results/stable.bin`
- `results/unstable.bin`
- `plots/stability.py`
- `plots/stability.png`

### 10.5 Project repository

The complete project is maintained at:

https://github.com/joseazzi/parallele_programming

The serial implementation provides the reference output used to verify the later MPI strip and block decompositions.

## 11. Conclusion

Part 1 implements the explicit finite-difference method for the two-dimensional heat equation using C++17.

The serial implementation supports the two required heating configurations and an analytical verification case.

Case 1 was tested with four hot edges and produced a finite temperature field with the correct boundary values.

Case 2 was tested with hot top and bottom boundaries, cold side boundaries and hot corners. All prescribed boundary conditions were verified.

Case V was used to measure the numerical error against an exact analytical solution.

The convergence study produced an observed convergence order of approximately 2.0015, in agreement with the expected second-order accuracy.

The stability experiment demonstrated that the numerical method remains bounded for \(r=0.2\), while deliberately using \(r=0.3\) resulted in rapidly growing numerical values.

The serial solver therefore provides a verified numerical reference for developing and testing the distributed MPI implementations.

The convergence and stability figures, numerical data, source code and analysis scripts are preserved in the project repository.
