# Chapter 8 - From Scheme to Program

Reference: `heat_numerics_background.pdf`, Chapter 8, PDF pages 28-30,
printed pages 24-26.

---

## Task 8.1 - Why not update in place?

Setting: a single array, overwritten as soon as each new value is
computed. The sweep is row by row in the storage order of Section 8.1,
`idx(i,j) = j*(Nx+1) + i`, with $j$ in the outer loop and $i$ in the inner
loop, both increasing.

### (a) Which neighbours already hold level n+1 values?

When node $(i,j)$ is reached, every node earlier in the sweep has already
been overwritten:

- all of row $j-1$ (and earlier rows), and
- nodes $(1,j),\dots,(i-1,j)$ of the current row.

Among the four stencil neighbours:

| neighbour | position in sweep | value it holds |
|---|---|---|
| west $(i-1,j)$ | earlier in the same row | **$u^{n+1}$ (new)** |
| south $(i,j-1)$ | previous row | **$u^{n+1}$ (new)** |
| east $(i+1,j)$ | later in the same row | $u^n$ (old) |
| north $(i,j+1)$ | next row | $u^n$ (old) |

So **the west and south neighbours** already hold level $n+1$ values. The
node itself is still old at the moment it is read.

### (b) Is it still the derived scheme? Is it order-independent?

**No to both.** The in-place loop computes

$$
u_{i,j}^{n+1}=(1-4r)u_{i,j}^n+r\left(u_{i+1,j}^n+u_{i,j+1}^n+u_{i-1,j}^{\,n+1}+u_{i,j-1}^{\,n+1}\right),
$$

which is not the explicit scheme of Task 5.2. It is a Gauss-Seidel-like
mixture of time levels.

**What it actually approximates.** Write
$u_{i-1,j}^{n+1}=u_{i-1,j}^n+(u_{i-1,j}^{n+1}-u_{i-1,j}^n)$, and similarly
for the south neighbour. Each bracket is about $\Delta t\,u_t$. Then

$$
\frac{u_{i,j}^{n+1}-u_{i,j}^n}{\Delta t}
=\alpha\nabla_h^2u_{i,j}^n+\frac{r}{\Delta t}\cdot2\Delta t\,u_t+\dots
\;\Longrightarrow\;
(1-2r)\,u_t\approx\alpha\nabla^2u .
$$

The in-place loop is a consistent scheme for **a different PDE**, the heat
equation with diffusivity

$$
\alpha_{\text{eff}}=\frac{\alpha}{1-2r}.
$$

For $r=0.2$ this is $1.667\,\alpha$: heat spreads 67 % too fast. Refining
the grid at fixed $r$ does not remove this error, so the convergence order
drops to **zero**.

**Order dependence.** The result depends on which neighbours are new,
which depends on the sweep direction. A forward sweep makes west and south
new; a reverse sweep makes east and north new. (A column-major sweep
with both indices increasing happens to make the same west and south
neighbours new, so it gives the same norms in the table below.) Different
orders give different answers, and the forward sweep even breaks the
symmetry of a symmetric problem.

**Numerical demonstration** (`scripts/background/task_8_1.py`, run on
`heat-theresa`, raw values in `results/background/task_8_1.csv`).
Settings: Case V, $r=0.2$, $T=0.05$, $N^2/4$ steps (the Task 7.2 setting).
The exact centre value is $u(\frac12,\frac12,0.05)=e^{-2\pi^2\cdot0.05}=0.372708$.
A heat equation with $\alpha_{\text{eff}}=1/(1-2r)$ would give $0.193025$.

| N | variant | $u$(centre) | $\|e\|_\infty$ | $\alpha_{\text{eff}}$ measured | max\|u − two-array\| |
|---:|---|---:|---:|---:|---:|
| 16 | two arrays (correct) | 0.371044 | 1.6634e-03 | 1.0045 | 0 |
| 16 | in place, row-major forward | 0.193773 | 1.7893e-01 | 1.6627 | 1.7727e-01 |
| 32 | two arrays | 0.372294 | 4.1418e-04 | 1.0011 | 0 |
| 32 | in place, forward | 0.193213 | 1.7949e-01 | 1.6657 | 1.7908e-01 |
| 64 | two arrays | 0.372604 | 1.0344e-04 | 1.0003 | 0 |
| 64 | in place, forward | 0.193072 | 1.7964e-01 | **1.6664** | 1.7953e-01 |

Here $\alpha_{\text{eff}}$ is computed from the centre value as
$-\ln u_c/(2\pi^2T)$.

Observations:

- The two-array version reproduces `heat_serial` exactly
  ($\|e\|_\infty=1.6634\times10^{-3}$ at $N=16$, as in Task 7.2) and
  converges with order 2.
- The in-place version has an error of about $0.18$ that **does not
  decrease** with $N$ (order 0). Its measured $\alpha_{\text{eff}}$ tends
  to $1.6667=1/(1-2r)$, exactly as derived above.
- **Order dependence:** forward and reverse in-place sweeps give different
  fields, with max difference $1.88\times10^{-2}$ ($N=16$),
  $9.46\times10^{-3}$ ($N=32$) and $4.74\times10^{-3}$ ($N=64$). The two
  are mirror images of each other. That is why the centre value and the
  error norms coincide in the table while the fields differ.
- The forward sweep breaks the point symmetry $u(i,j)=u(N-i,N-j)$ of the
  exact solution by the same amount. That violates the symmetry check of
  Section 7.5.

### (c) Why order-independence is essential in parallel

When the grid is split among processes, all processes update their nodes
**at the same time**. There is no global sweep order. A process cannot
know whether its neighbour has already updated the nodes along their
common cut.

- With two time levels, every update reads only level-$n$ values: its own
  nodes, plus ghost copies of the neighbours' level-$n$ edge rows,
  exchanged before the step. The result is the same no matter when or in
  what order the nodes are computed.
- This is why the parallel program can reproduce the serial result **bit
  for bit** (Section 7.5), as verified in Part 3.
- With in-place updates, the answer would depend on the number of
  processes, on the decomposition, and even on timing (a race condition).
  It would also not be a correct heat solver to begin with.

### Connection with the implementation

`src/heat_serial.cpp` follows Section 8.2 exactly:

```cpp
std::vector<double> u(total, 0.0);      // level n
std::vector<double> next(total, 0.0);   // level n+1
...
next = u;                               // boundary values present in both arrays
for (int step = 0; step < steps; ++step) {
    for (int j = 1; j < N; ++j)
        for (int i = 1; i < N; ++i)
            next[index(i, j)] = (1.0 - 4.0 * r) * u[index(i, j)]
                + r * (u[index(i + 1, j)] + u[index(i - 1, j)]
                     + u[index(i, j + 1)] + u[index(i, j - 1)]);
    u.swap(next);                       // O(1): exchanges the internal pointers, no copy
}
```

- All reads are from `u` and all writes go to `next`, so the loop order
  does not affect the result.
- `std::vector::swap` exchanges the internal buffers in constant time:
  this is the "swap the pointers, don't copy" of Section 8.2.
- Boundary nodes are written once into both arrays (`next = u`) and never
  touched again, so the Dirichlet values survive every swap.
- The strips and blocks programs (`src/parallel/`) use the same two-array
  update on each process's subgrid, after refreshing the ghost rows and
  columns with `MPI_Sendrecv`.

---

## Task 8.2 - Surface-to-volume (preview of the parallel project)

Grid of $N\times N$ nodes on $P$ processes. Message model:
$t_{\text{msg}}=t_s+m\,t_w$, with $m$ in **numbers** (doubles) as in the
PDF. (The repository's ping-pong fit gives $t_w$ per **byte**; per double
it is $8\times$ larger.) "Typical process" means one with neighbours on
all sides. Counts are per time step, for the 5-point stencil, which needs
one ghost layer.

### (a) Strips

Each process owns $N/P$ full rows. A typical (interior) strip has two
neighbours, above and below.

- It **sends** its first and last owned rows: $2N$ numbers. It
  **receives** two ghost rows: $2N$ numbers.
- **Messages:** 2 sent and 2 received per step. That is 2 exchanges, and
  `heat_strips.cpp` uses exactly 2 `MPI_Sendrecv` calls per step.
- The first and last strips have only one neighbour: $N$ numbers and 1
  message each way.
- Rows contain $N-1$ interior values (or $N+1$ with boundaries). Taking
  $N$ is the usual approximation.

### (b) Blocks, $\sqrt P\times\sqrt P$

Each process owns an $\frac N{\sqrt P}\times\frac N{\sqrt P}$ block. A
typical (interior) block has four neighbours (west, east, south, north),
and each shared edge has $N/\sqrt P$ nodes.

- It **sends** $4N/\sqrt P$ numbers and **receives** $4N/\sqrt P$ numbers.
- **Messages:** 4 sent and 4 received per step. That is 4 exchanges, and
  `heat_blocks.cpp` uses 4 `MPI_Sendrecv` calls, with an
  `MPI_Type_vector` for the non-contiguous columns.
- No corner (diagonal) exchange is needed, because the 5-point stencil has
  no diagonal neighbours (see `docs/PART3_BLOCKS.md`).
- Edge blocks have 3 neighbours and corner blocks have 2. In a $2\times2$
  grid ($P=4$) **every** block is a corner block, with 2 messages of
  $N/2$.

Volume comparison: blocks move $4N/\sqrt P$ against $2N$ for strips. That
is less data as soon as $\sqrt P>2$, i.e. $P>4$, and the advantage grows
with $P$. Strips use fewer messages (2 against 4).

### (c) Communication time per step

Treat the messages of a process as sequential (no overlap), and count each
exchange once:

$$
T_{\text{strips}}=2\,(t_s+N\,t_w)=2t_s+2N\,t_w,
$$

$$
T_{\text{blocks}}=4\left(t_s+\frac{N}{\sqrt P}t_w\right)=4t_s+\frac{4N}{\sqrt P}t_w .
$$

Blocks are faster when

$$
4t_s+\frac{4N}{\sqrt P}t_w<2t_s+2Nt_w
\iff 2N\,t_w\left(1-\frac{2}{\sqrt P}\right)>2t_s
\iff N>N^*=\frac{t_s}{t_w\,(1-2/\sqrt P)}\quad(P>4).
$$

- **$t_s$ small** (cluster interconnect, about 1 µs): the volume term
  dominates, so **blocks** win, for $P>4$ and every reasonable $N$.
- **$t_s$ very large** (VPN or Tailscale): the message count dominates.
  Blocks pay $2t_s$ more per step, so **strips** win unless $N$ exceeds
  the large threshold $N^*$.

**With the team's measured parameters.** These come from
`results/pingpong/communication_model_refined.csv`. The means over the
three inter-laptop pairs were recomputed here:

$$
t_s=\tfrac13(32.2165+33.0187+39.7753)\ \text{ms}=35.0035\ \text{ms},
$$

$$
t_w=\tfrac13(1.16116+1.25487+1.57917)\times10^{-6}\ \text{s/byte}=1.33173\times10^{-6}\ \text{s/byte}.
$$

That is $t_w=1.0654\times10^{-5}$ s per double. These match the values in
`docs/PART3_BLOCKS.md`.

- For large $P$, e.g. $P=16$: $1-2/\sqrt P=0.5$, so
  $N^*=0.0350035/(1.0654\times10^{-5}\times0.5)\approx6.6\times10^3$.
- For the actual project configurations, the critical rank is not a
  "typical" interior block. `docs/PART3_BLOCKS.md` uses the exact
  critical-rank counts in bytes:
  - strips: $2t_s+16Nt_w^{(B)}$;
  - $2\times2$ blocks: $2t_s+8Nt_w^{(B)}$, so blocks win for every $N$ when
    $P=4$;
  - $2\times4$ blocks: $3t_s+10Nt_w^{(B)}$. The $P=8$ crossover is
    $2t_s+16Nt_w^{(B)}=3t_s+10Nt_w^{(B)}\Rightarrow N=t_s/(6t_w^{(B)})=0.0350035/(6\times1.331733\times10^{-6})=4380.7$,
    which confirms the recorded value $N\approx4381$.

  These existing results were checked and are consistent with the general
  formulas above.

**Local communication** (same VM) has $t_s\approx0.4$ µs and
$t_w\approx2\times10^{-10}$ s/byte. That is the "small $t_s$" regime,
where blocks are favoured for $P>4$.

### (d) Communication-to-computation ratio for strips

Computation per step: a strip has $N\cdot\frac NP$ nodes, each costing
$t_c$ (time per node update; about 6 flops, see Task 5.2(d)):
$T_{\text{comp}}=\frac{N^2}{P}t_c$. Therefore

$$
\boxed{\ \rho_{\text{strips}}=\frac{T_{\text{comm}}}{T_{\text{comp}}}
=\frac{2t_s+2Nt_w}{N^2t_c/P}
=\frac{2P\,t_s}{t_c}\cdot\frac1{N^2}+\frac{2P\,t_w}{t_c}\cdot\frac1N\ }
$$

**As $N$ grows with $P$ fixed,** $\rho\to0$: the latency part decays like
$1/N^2$ and the bandwidth part like $1/N$. Communication scales with the
perimeter ($\propto N$) and computation with the area ($\propto N^2$). The
surface-to-volume ratio of a strip shrinks as the strip grows.

**Numbers for this project** (three laptops over Tailscale, $P=3$,
strips):

- $t_s=0.0350$ s, and $t_w=1.0654\times10^{-5}$ s/double (from above).
- $t_c=9.6\times10^{-10}$ s per node update. This was measured on
  `heat-theresa` (Task 7.2, $N=256$: 1.022 s for $1.065\times10^9$
  updates).

$$
\rho(N)=\frac{2\cdot3\cdot0.035}{9.6\times10^{-10}}\frac1{N^2}+\frac{2\cdot3\cdot1.0654\times10^{-5}}{9.6\times10^{-10}}\frac1N
=\frac{2.19\times10^{8}}{N^2}+\frac{6.66\times10^{4}}{N}.
$$

| N | $\rho$ (communication / computation) |
|---:|---:|
| 512 | 964 |
| 2 048 | 84.7 |
| 8 192 | 11.4 |
| 36 300 | ≈ 2 (break-even for speedup, see below) |
| 69 700 | ≈ 1 |

With no overlap, the parallel time per step is
$T_{\text{comp}}(1+\rho)$ against $P\,T_{\text{comp}}$ serially, so the
speedup is

$$
S=\frac{P}{1+\rho}.
$$

$S>1$ requires $\rho<P-1=2$. Solving
$2N^2-6.66\times10^4N-2.19\times10^8=0$ gives
$N\approx3.6\times10^4$. Even the bandwidth term alone requires
$N>2Pt_w/t_c\approx6.7\times10^4$ for $\rho<1$.

**What this suggests.** Parallelism over a slow network pays off only for
**very large** problems, where each process has enough area to hide its
perimeter traffic. For this project's network, that means $N$ in the tens
of thousands. Such a grid needs $2\times8N^2\approx20$ GB in total at
$N=36\,000$, i.e. about 7 GB per laptop. That is more than each Ubuntu VM
has (about 3 GB of RAM measured on `heat-theresa`).

Practical consequences for Part 4:

- Expect cross-machine runs at $N\le8192$ to be slower than serial.
- Use the largest $N$ that fits in memory.
- Prefer strips (fewer messages) over Tailscale.
- Report the measured times against this model, rather than expecting
  speedup.

All figures above are **model predictions** from the measured ping-pong
parameters and one measured serial update rate. They are not distributed
run measurements.

---

## Summary

| Task | Result |
|---|---|
| 8.1 | In-place sweep uses new west and south values. It solves $u_t=\frac{\alpha}{1-2r}\nabla^2u$ (measured $\alpha_{\text{eff}}=1.6664$ against predicted 1.6667), has order 0, and depends on the sweep order. Two arrays plus a pointer swap are required and are used in `heat_serial.cpp`. |
| 8.2 | Strips: $2N$ numbers, 2 messages. Blocks: $4N/\sqrt P$ numbers, 4 messages. $T_s=2t_s+2Nt_w$, $T_b=4t_s+4Nt_w/\sqrt P$. Blocks win for small $t_s$, strips for large $t_s$. $\rho_{\text{strips}}=2Pt_s/(N^2t_c)+2Pt_w/(Nt_c)\to0$, but over Tailscale $\rho<2$ needs $N\approx3.6\times10^4$. |
