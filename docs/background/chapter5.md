# Chapter 5 - Putting Space and Time Together

Reference: `heat_numerics_background.pdf`, Chapter 5, PDF pages 19-21,
printed pages 15-17.

The scheme derived here is the one already implemented in
`src/heat_serial.cpp` and summarised in `docs/PART1_SERIAL.md`
(Sections 3.1-3.4). This chapter gives the complete derivations the
background notes ask for. The solver code is unchanged.

Notation: $D_2$ is the second difference of Task 3.2 and $\nabla_h^2$ is
the discrete Laplacian of Task 3.4.

---

## Task 5.1 - Warm-up: one dimension

Problem: $u_t=\alpha u_{xx}$ on $[0,L]$, with Dirichlet values $u(0,t)$ and
$u(L,t)$ prescribed. Grid: $x_i=i\Delta x$, $\Delta x=L/N$.

### (a) Semi-discretization

At an interior node $x_i$ ($1\le i\le N-1$), replace $u_{xx}$ by the
three-point formula of Task 3.2 and keep $t$ continuous:

$$
\frac{\mathrm{d}u_i}{\mathrm{d}t}
=\alpha\,\frac{u_{i+1}(t)-2u_i(t)+u_{i-1}(t)}{\Delta x^2},
\qquad i=1,\dots,N-1 .
$$

This is a system of $N-1$ ODEs. The boundary values $u_0(t)$ and $u_N(t)$
are known data that enter the equations for $i=1$ and $i=N-1$.

### (b) Forward Euler

Apply $u^{n+1}=u^n+\Delta t\,f(u^n)$ (Worked Example 4.1) to each ODE:

$$
u_i^{n+1}=u_i^n+\frac{\alpha\Delta t}{\Delta x^2}\left(u_{i+1}^n-2u_i^n+u_{i-1}^n\right).
$$

With $s=\alpha\Delta t/\Delta x^2$:

$$
\boxed{\,u_i^{n+1}=(1-2s)\,u_i^n+s\,(u_{i+1}^n+u_{i-1}^n)\,}
$$

### (c) The dimensionless combination

The only combination of $\alpha$, $\Delta t$ and $\Delta x$ in the update is

$$
s=\frac{\alpha\,\Delta t}{\Delta x^2}.
$$

Dimension check: $[\alpha]=\mathrm{m^2/s}$, so
$[s]=\mathrm{(m^2/s)\cdot s/m^2}=1$.

This is exactly the combination $\alpha t/L^2$ of Task 1.2(a), with the
time $t$ replaced by the time step $\Delta t$ and the length $L$ replaced
by the cell size $\Delta x$. In the language of Task 1.2(b), $\Delta x^2/\alpha$
is the time heat needs to diffuse across one grid cell. So $s$ is the time
step measured in units of that cell diffusion time. Chapter 6 shows that
the scheme is stable only if this number is at most $1/2$.

---

## Task 5.2 - The 2D update rule

### (a) General $\Delta x$, $\Delta y$

Semi-discretize $u_t=\alpha\nabla^2u$ with the discrete Laplacian of Task 3.4:

$$
\frac{\mathrm{d}u_{i,j}}{\mathrm{d}t}
=\alpha\left[\frac{u_{i+1,j}-2u_{i,j}+u_{i-1,j}}{\Delta x^2}
+\frac{u_{i,j+1}-2u_{i,j}+u_{i,j-1}}{\Delta y^2}\right].
$$

Apply forward Euler and solve for the new value:

$$
u_{i,j}^{n+1}=u_{i,j}^n
+\frac{\alpha\Delta t}{\Delta x^2}\left(u_{i+1,j}^n-2u_{i,j}^n+u_{i-1,j}^n\right)
+\frac{\alpha\Delta t}{\Delta y^2}\left(u_{i,j+1}^n-2u_{i,j}^n+u_{i,j-1}^n\right).
$$

With $r_x=\alpha\Delta t/\Delta x^2$ and $r_y=\alpha\Delta t/\Delta y^2$:

$$
\boxed{\,u_{i,j}^{n+1}=(1-2r_x-2r_y)\,u_{i,j}^n
+r_x\left(u_{i+1,j}^n+u_{i-1,j}^n\right)
+r_y\left(u_{i,j+1}^n+u_{i,j-1}^n\right)\,}
$$

for $1\le i\le N_x-1$ and $1\le j\le N_y-1$. Only level-$n$ values appear
on the right, so the scheme is **explicit** (Definition 5.1).

### (b) Equal spacing $\Delta x=\Delta y=h$

Then $r_x=r_y=r$ with

$$
r=\frac{\alpha\,\Delta t}{h^2},
$$

and

$$
\boxed{\,u_{i,j}^{n+1}=(1-4r)\,u_{i,j}^n
+r\left(u_{i+1,j}^n+u_{i-1,j}^n+u_{i,j+1}^n+u_{i,j-1}^n\right)\,}
$$

This is line for line the expression in `src/heat_serial.cpp`:

```cpp
next[index(i, j)] =
    (1.0 - 4.0 * r) * u[index(i, j)]
    + r * (u[index(i + 1, j)] + u[index(i - 1, j)] +
           u[index(i, j + 1)] + u[index(i, j - 1)]);
```

The project runs with $\alpha=1$ on the unit square, $h=1/N$, and
$\Delta t=r h^2$.

### (c) Space-time stencil

```
  level n+1:                    (i,j)
                                  ^
                                  |   one new value
              . . . . . . . . . . | . . . . . . . . . .
  level n:            (i,j+1)     |
                         |        |
               (i-1,j)--(i,j)--(i+1,j)
                         |
                      (i,j-1)

  weights at level n:          r
                          r  1-4r  r
                               r
```

Computing one value at level $n+1$ needs **five** values at level $n$: the
node itself and its four nearest neighbours (east, west, north, south). No
diagonal neighbours and no other time levels are used. For general
spacing, the east and west weights are $r_x$, the north and south weights
are $r_y$, and the centre weight is $1-2r_x-2r_y$.

### (d) Cost of one update

**Floating-point operations**, for the form used in the code, with the
loop-invariant constant $c_0=1-4r$ computed once outside the loop:

| operation | count |
|---|---:|
| sum of the four neighbours $a+b+c+d$ | 3 additions |
| $r\times(\text{sum})$ | 1 multiplication |
| $c_0\times u_{i,j}$ | 1 multiplication |
| add the two parts | 1 addition |
| **total** | **6 flops** (4 add + 2 mul) |

The equivalent form $u+r\,(a+b+c+d-4u)$ costs 7 flops (3 adds, $4u$, 1
subtraction, 1 multiplication, 1 addition). For general $\Delta x\ne\Delta y$,
the form $c_0u+r_x(a+b)+r_y(c+d)$ costs 2 + 3 + 2 = **7 flops**.

**Memory:**

- Logically, each update **reads 5 values** (centre + 4 neighbours) from
  `u_old` and **writes 1 value** to `u_new`. That is 6 doubles = 48 bytes.
- When the grid is swept row by row, each value is used by up to five
  different updates. If three consecutive rows stay in cache, each old
  value is loaded from main memory only once per sweep. The real traffic is
  then about **1 read + 1 write = 16 bytes** per update (plus a possible
  write-allocate read).
- The arithmetic intensity is therefore about $6/16\approx0.4$ flop/byte
  (as low as $6/48=0.125$ without cache reuse). This is far below what a
  CPU can sustain: the update is **memory-bandwidth bound**, not flop bound.
  This matters when interpreting the run times in Task 6.6 and in Part 4.

---

## Task 5.3 - Interpreting the update

From Task 5.2(b):

$$
u_{i,j}^{n+1}=\underbrace{(1-4r)}_{w_0}\,u_{i,j}^n
+\underbrace{r}_{w_E}u_{i+1,j}^n+\underbrace{r}_{w_W}u_{i-1,j}^n
+\underbrace{r}_{w_N}u_{i,j+1}^n+\underbrace{r}_{w_S}u_{i,j-1}^n .
$$

### (a) The weights sum to one

$$
w_0+w_E+w_W+w_N+w_S=(1-4r)+4r=1 .
$$

For general spacing, $(1-2r_x-2r_y)+2r_x+2r_y=1$.

**Uniform plate.** If $u_{k}^n=C$ at all five stencil nodes:

$$
u_{i,j}^{n+1}=C\,(w_0+w_E+w_W+w_N+w_S)=C .
$$

A uniform temperature stays exactly uniform, as it must physically: there
is no temperature difference, so no heat flows ($\nabla^2C=0$). The
weights summing to one is the time-stepping counterpart of Task 3.3(b),
where the coefficients of $D_2$ summed to zero. Indeed,
$u^{n+1}=u^n+\alpha\Delta t\,\nabla_h^2u^n$ and $\nabla_h^2$ annihilates
constants.

### (b) Interpretation in words

Let $A_{i,j}=\tfrac14(u_{i+1,j}+u_{i-1,j}+u_{i,j+1}+u_{i,j-1})$ be the
average of the four neighbours. Then

$$
u_{i,j}^{n+1}=u_{i,j}^n+4r\,\big(A_{i,j}^n-u_{i,j}^n\big)
=(1-4r)\,u_{i,j}^n+4r\,A_{i,j}^n .
$$

In each time step, every node moves towards the average of its neighbours,
by the fraction $4r$ of the gap.

- If the surroundings are on average warmer ($A>u$, i.e.
  $\nabla_h^2u>0$), the node heats up.
- If they are colder, it cools down.

This is exactly the reading of the Laplacian in Section 1.4 and formula
(1.2): $\nabla^2u$ measures how much the average of the surroundings
exceeds the value at the point.

When $0\le4r\le1$, the new value is a convex combination of the old value
and the neighbour average, so it lies between them. The extreme case
$4r=1$ replaces $u$ by $A$ completely. If $4r>1$, the node overshoots the
neighbour average, which is the seed of the instability studied in
Section 6.4 and Task 6.4.

---

## Task 5.4 - Insulated edges in 2D

The grid has $(N_x+1)\times(N_y+1)$ nodes. The left edge is $x=0$
($i=0$). Insulated means $\partial u/\partial n=0$; on the left edge the
outward normal is $-x$, so the condition is $u_x(0,y,t)=0$.

### (a) Left edge insulated, other three edges Dirichlet

**Unknowns.** The nodes on the left edge, $(0,j)$ for $1\le j\le N_y-1$,
are no longer prescribed. They become unknowns updated every step. The
unknowns are now $0\le i\le N_x-1$, $1\le j\le N_y-1$: that is
$N_x(N_y-1)$ nodes instead of $(N_x-1)(N_y-1)$.

**Ghost nodes.** Add one ghost column $i=-1$ at $x_{-1}=-\Delta x$, with
values $u_{-1,j}$ for $1\le j\le N_y-1$.

**Filling.** Impose $u_x=0$ with the second-order central difference of
Example 3.5, centred at the wall:

$$
\frac{u_{1,j}^n-u_{-1,j}^n}{2\Delta x}=0
\;\Longrightarrow\;
u_{-1,j}^n=u_{1,j}^n .
$$

Refresh the ghost column at the beginning of every step, before the update
that reads it. Then apply the standard update at $i=0$:

$$
u_{0,j}^{n+1}=(1-2r_x-2r_y)u_{0,j}^n+r_x\left(u_{1,j}^n+u_{-1,j}^n\right)+r_y\left(u_{0,j+1}^n+u_{0,j-1}^n\right).
$$

Eliminating the ghost value gives an equivalent boundary update that needs
no extra storage:

$$
u_{0,j}^{n+1}=(1-2r_x-2r_y)u_{0,j}^n+2r_x\,u_{1,j}^n+r_y\left(u_{0,j+1}^n+u_{0,j-1}^n\right).
$$

The weights still sum to 1, and are non-negative under the same condition
as in the interior. The plate is mirrored across the wall: no heat crosses
it, so the wall node only exchanges heat with its interior neighbour (with
double weight) and its two neighbours along the wall.

### (b) Corners

**Insulated edge meets a Dirichlet edge**, e.g. corner $(0,0)$ between the
insulated left edge and the Dirichlet bottom edge.

- A Dirichlet condition fixes the value, while a Neumann condition only
  fixes a derivative. At the corner node, the prescribed temperature wins:
  $u_{0,0}=g(0,0)$ is set and never updated. A single node cannot satisfy
  both independently, and fixing the value is the stronger condition.
- No ghost value is needed at $(0,0)$ because it is not updated. The
  nearest unknown, $(0,1)$, uses the Dirichlet value $u_{0,0}$ as its south
  neighbour and the ghost $u_{-1,1}=u_{1,1}$ as its west neighbour.
- If the Dirichlet data along the bottom edge is not flat near $x=0$, the
  two conditions are slightly incompatible at the corner. That produces a
  local singularity in the exact solution, but it does not change the
  algorithm.

**Two insulated edges meet**, e.g. left ($x=0$) and bottom ($y=0$) both
insulated.

- The corner $(0,0)$ is now an unknown.
- Its stencil needs a west ghost $u_{-1,0}$ and a south ghost $u_{0,-1}$.
  From $u_x=0$ and $u_y=0$: $u_{-1,0}=u_{1,0}$ and $u_{0,-1}=u_{0,1}$.
- The bottom edge needs a ghost row $u_{i,-1}=u_{i,1}$ just as the left
  edge needs a ghost column.
- The diagonal ghost $u_{-1,-1}$ is never needed, because the five-point
  stencil has no diagonal entries.

The corner update is

$$
u_{0,0}^{n+1}=(1-2r_x-2r_y)u_{0,0}^n+2r_x\,u_{1,0}^n+2r_y\,u_{0,1}^n .
$$

The plate is mirrored in both directions at once. The weights still sum to
1.

### (c) Non-zero flux $u_x(0,t)=h(t)$

The PDF calls the prescribed boundary derivative $h(t)$. Below it is
written $g(t)$ to avoid confusion with the grid spacing $h$.

Use the same central difference, now equal to $g$:

$$
\frac{u_1^n-u_{-1}^n}{2\Delta x}=g(t_n)
\;\Longrightarrow\;
\boxed{\,u_{-1}^n=u_1^n-2\Delta x\,g(t_n)\,}
$$

Substituting into the 1D update of Task 5.1 at $i=0$:

$$
u_0^{n+1}=(1-2s)u_0^n+s\left(u_1^n+u_{-1}^n\right)
=(1-2s)u_0^n+2s\,u_1^n-2s\,\Delta x\,g(t_n).
$$

The 2D version for the left edge is

$$
u_{-1,j}^n=u_{1,j}^n-2\Delta x\,g_j(t_n),
\qquad
u_{0,j}^{n+1}=(1-2r_x-2r_y)u_{0,j}^n+2r_xu_{1,j}^n+r_y(u_{0,j+1}^n+u_{0,j-1}^n)-2r_x\Delta x\,g_j(t_n).
$$

**Physical check.** Fourier's law gives the heat flux $q=-k\,u_x=-k\,g$.
If $g>0$, then $q<0$: heat flows in the $-x$ direction, out of the plate
through the wall. The extra term $-2r_x\Delta x\,g$ indeed lowers the wall
temperature. The insulated case is recovered with $g=0$.

**Accuracy.** The central difference is second order, consistent with the
interior scheme. Example 5.2 is the special case $g\equiv0$. As in that
example, the ghost value must be refreshed with $g(t_n)$ at every step
before the update.

---

## Task 5.5 - Accuracy of the scheme

**Scheme in "time difference − space difference = 0" form (Definition 5.3):**

$$
\frac{u_{i,j}^{n+1}-u_{i,j}^n}{\Delta t}-\alpha\,\nabla_h^2u_{i,j}^n=0 .
$$

**Local truncation error.** Insert the exact solution $u=u(x_i,y_j,t_n)$:

$$
\tau_{i,j}^n=\frac{u(x_i,y_j,t_{n+1})-u(x_i,y_j,t_n)}{\Delta t}-\alpha\,\nabla_h^2u(x_i,y_j,t_n).
$$

**Time part.** Taylor in $t$ (Theorem 2.2), the forward-difference
analysis of Example 3.3:

$$
\frac{u(t_{n+1})-u(t_n)}{\Delta t}=u_t+\frac{\Delta t}{2}u_{tt}+\frac{\Delta t^2}{6}u_{ttt}+\dots
$$

**Space part.** From Tasks 3.2 and 3.4:

$$
\nabla_h^2u=u_{xx}+u_{yy}
+\frac{\Delta x^2}{12}u_{xxxx}+\frac{\Delta y^2}{12}u_{yyyy}
+O(\Delta x^4+\Delta y^4).
$$

**Combine.** The exact solution satisfies $u_t=\alpha(u_{xx}+u_{yy})$, so
the leading terms cancel:

$$
\tau_{i,j}^n
=\frac{\Delta t}{2}u_{tt}
-\frac{\alpha\Delta x^2}{12}u_{xxxx}
-\frac{\alpha\Delta y^2}{12}u_{yyyy}
+O(\Delta t^2)+O(\Delta x^4)+O(\Delta y^4).
$$

Hence

$$
\boxed{\,\tau=O(\Delta t^{1})+O(\Delta x^{2})+O(\Delta y^{2}),\qquad p=1,\quad q=2\,}
$$

- First order in time comes from forward Euler.
- Second order in space comes from the central second differences.

**Consistency.** Each term tends to zero when $\Delta t,\Delta x,\Delta y\to0$,
independently and with no relation required between them. So
$\tau\to0$ and the scheme **is consistent**. By the Lax theorem
(Theorem 6.2), it converges if it is also stable (Chapter 6).

**With the time step tied to the grid.** In the project $\Delta t=rh^2/\alpha$
with $r$ fixed, so $O(\Delta t)=O(h^2)$ and $\tau=O(h^2)$ overall. Using
$u_{tt}=\alpha^2\nabla^4u$ (differentiate the PDE in time), the leading
term can be written in space derivatives only:

$$
\tau=\alpha h^2\left[\frac{r}{2}\left(u_{xxxx}+2u_{xxyy}+u_{yyyy}\right)
-\frac{1}{12}\left(u_{xxxx}+u_{yyyy}\right)\right]+O(h^4).
$$

**Application to the verification problem** $u=\sin(\pi x)\sin(\pi y)e^{-2\pi^2t}$
with $\alpha=1$: every fourth derivative equals $\pi^4u$, so

$$
\tau=h^2\pi^4\,u\left(\frac{r}{2}\cdot4-\frac{2}{12}\right)
=h^2\pi^4\left(2r-\frac16\right)u .
$$

For the project value $r=0.2$:

$$
\tau=0.2333\,\pi^4h^2u=22.73\,h^2\,u .
$$

The error is $O(h^2)$, with a computable constant. Chapter 7 uses this
expression to predict the actual error values of the convergence study.
