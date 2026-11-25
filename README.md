
# Parallel 2D Heat Diffusion with MPI

## Project Overview

This project implements and evaluates a parallel
solver for the two-dimensional heat diffusion
equation using C++ and Open MPI.

The project is developed by:
- Jose Azzi
- Dia Hajjar
- Theresa Kozah

The objective is to study numerical correctness,
distributed-memory parallelism, communication
overhead, and parallel performance.

The cluster consists of three Ubuntu virtual
machines communicating through Tailscale.

## 1. Project Objectives

The main objectives are:

1. Build a three-machine MPI cluster.
2. Measure network latency and bandwidth.
3. Implement a serial 2D heat diffusion solver.
4. Implement MPI parallelization using 1D strips.
5. Implement MPI parallelization using 2D blocks.
6. Verify numerical correctness.
7. Measure speedup, efficiency, and communication
   overhead.

## 2. Cluster Configuration

| Machine | Architecture | vCPUs | RAM | Tailscale IP |
|---|---|---|---|---|
| heat-jose | ARM64 | 2 | 3.8 GiB | 100.125.52.39 |
| heat-dia-1 | x86-64 | 2 | 1.9 GiB | 100.115.31.27 |
| heat-theresa | x86-64 | 2 | 3.8 GiB | 100.100.103.111 |

All VMs use:
- Ubuntu 24.04.5 LTS
- Open MPI 4.1.6
- Tailscale
- SSH
- C++17

The cluster uses mixed CPU architectures.
Each computer must compile its own binaries
from the same source code.

For full cluster setup and network configuration,
see:

[Part 0 Cluster Documentation](docs/PART0_CLUSTER.md)

## 3. Requirements

Install the required development tools on
each Ubuntu VM:

    sudo apt update

    sudo apt install -y \
      build-essential \
      make \
      cmake \
      git \
      openmpi-bin \
      libopenmpi-dev \
      python3-numpy \
      python3-pandas \
      python3-matplotlib

Tailscale and passwordless SSH must also be
configured before distributed MPI execution.

## 4. Clone the Repository

    git clone https://github.com/joseazzi/parallele_programming.git heat-mpi

    cd heat-mpi

For distributed MPI execution, the repository
and executable paths must be consistent across
the participating VMs.

The project was developed under:

    /home/ubuntu/heat-mpi

## 5. Compilation

Compile all five main programs using:

    make

This builds:

- heat_serial
- heat_strips
- heat_blocks
- pingpong
- hello_mpi

To force recompilation:

    make -B

To remove compiled executables:

    make clean

Compiler options:

    -O2 -std=c++17 -ffp-contract=off

The final option disables floating-point
contraction to improve reproducibility across
ARM64 and x86-64 architectures.

## 6. MPI Hello World

For a local two-process test:

    mpirun -np 2 ./hello_mpi

For an example distributed MPI launch:

    mpirun \
      --mca btl_tcp_if_include tailscale0 \
      --mca oob_tcp_if_include tailscale0 \
      --mca btl tcp,self \
      --host 100.125.52.39,100.115.31.27 \
      -np 2 \
      /home/ubuntu/heat-mpi/hello_mpi

Distributed execution requires passwordless
SSH and locally compiled executables on the
participating computers.

## 7. Ping-Pong Communication Benchmark

The ping-pong program measures round-trip
communication time between two MPI ranks.

The message sizes range from 8 bytes to
16 MiB, increasing by powers of two.

Example local benchmark:

    mpirun -np 2 ./pingpong

Example distributed benchmark:

    mpirun \
      --mca btl_tcp_if_include tailscale0 \
      --mca oob_tcp_if_include tailscale0 \
      --mca btl tcp,self \
      --host 100.125.52.39,100.100.103.111 \
      -np 2 \
      /home/ubuntu/heat-mpi/pingpong

Raw benchmark data is stored in CSV files.

Six configurations were measured:
- Jose local
- Dia local
- Theresa local
- Jose - Dia
- Jose - Theresa
- Dia - Theresa

Additional historical measurements are
preserved for comparison.

## 8. Communication Model

Communication time is approximated by:

    t_msg(m) = ts + m * tw

Where:
- m: message size in bytes
- ts: startup communication latency
- tw: incremental transfer time per byte

The estimated bandwidth is:

    bandwidth = 1 / tw

The original and refined calculations are
implemented in:

    scripts/fit_pingpong_model.py

Run the analysis using:

    python3 scripts/fit_pingpong_model.py

The refined method estimates startup time
from small messages and fits transfer cost
using large messages.

The original full-range regression is also
preserved for comparison.

Results:

    results/pingpong/

Generated files include:
- communication_model.csv
- communication_model.png
- communication_model_refined.csv
- communication_model_refined.png

These values represent empirical MPI
application-level communication performance,
not physical network link capacity.

## 9. Serial Heat Diffusion Solver

The serial solver uses an explicit finite-
difference method for the 2D heat equation.

The numerical method uses a five-point stencil
and two arrays for consecutive time steps.

The explicit stability condition is:

    0 < r <= 0.25

Example:

    ./heat_serial --N 100 --r 0.2 --T 0.01 --case V

Case V compares the numerical solution against
an analytical solution.

The numerical convergence study produced
observed orders close to 2.

## 10. Parallel MPI Implementations

Two parallel implementations are included.

### 1D Strip Decomposition

Source:

    src/parallel/heat_strips.cpp

The grid is divided into horizontal strips.
Neighboring MPI ranks exchange ghost rows
using MPI_Sendrecv.

Example local execution:

    mpirun -np 2 ./heat_strips \
      --N 100 --r 0.2 --T 0.01 --case V

### 2D Block Decomposition

Source:

    src/parallel/heat_blocks.cpp

The grid is divided into two-dimensional blocks.
MPI communication exchanges boundary information
between neighboring blocks.

Both parallel implementations require numerical
correctness validation against the serial solver
before their final performance results are accepted.

## 11. Results and Graphs

The repository contains numerical and
performance analysis files under:

    results/
    plots/
    scripts/

Available results include:
- Serial convergence data
- Numerical solution outputs
- Initial performance measurements
- Ping-pong communication benchmarks
- Latency and bandwidth graphs
- Communication model fitting results

The numerical and parallel performance studies
will be documented further as the project
progresses.

## 12. Project Documentation

Detailed cluster documentation:

    docs/PART0_CLUSTER.md

This includes:
- Hardware and software specifications
- Tailscale networking
- SSH configuration
- MPI launching
- Ping-pong methodology
- Communication-model results
- Known limitations

Additional project reports and experimental
documentation will be added as the remaining
assignment parts are completed.

## 13. Known Limitations

- The cluster uses mixed ARM64 and x86-64
  architectures.
- Dia's current VM RAM allocation is below
  the assignment's 4 GB minimum.
- Tailscale connections can switch between
  direct communication and DERP relaying.
- The simple linear communication model may
  not accurately represent every message size.
- Parallel MPI correctness and performance
  experiments require further validation.

## 14. Project Status

- Part 0: Cluster and benchmarks completed;
  final checks and documentation in progress.
- Part 1: Serial solver implemented and
  numerical convergence verified.
- Part 2: MPI strip solver implemented;
  final validation in progress.
- Part 3: MPI block solver implemented;
  final validation pending.
- Part 4: Strong-scaling study completed
  (see docs/PART4_PERFORMANCE.md); P=6 not
  measurable over Tailscale.

The repository will continue to be updated
as experiments and verification are completed.
