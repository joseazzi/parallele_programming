# Chapter 1 - The Physical Model

## Task 1.1 - Checking the mean-value formula

### Objective

Prove the mean-value formula using a two-variable
Taylor expansion.

### Mathematical derivation

Let:

$$
a=r\cos\phi,\qquad b=r\sin\phi
$$

The Taylor expansion of u around (x,y) is:

$$
u(x+a,y+b)=u+a u_x+b u_y+
\frac{a^2}{2}u_{xx}+ab u_{xy}
+\frac{b^2}{2}u_{yy}+O(r^3)
$$

Substituting a and b gives:

$$
u(x+a,y+b)=u+r\cos\phi\,u_x
+r\sin\phi\,u_y
+\frac{r^2\cos^2\phi}{2}u_{xx}
+r^2\cos\phi\sin\phi\,u_{xy}
+\frac{r^2\sin^2\phi}{2}u_{yy}
+O(r^3)
$$

The required integrals over [0, 2pi] are:

- Integral of 1 = 2pi
- Integral of cos(phi) = 0
- Integral of sin(phi) = 0
- Integral of cos(phi)sin(phi) = 0
- Integral of cos(phi) = pi
- Integral of sin(phi) = pi

For a sufficiently smooth function, all third-order
Taylor terms also integrate to zero by symmetry.
The remaining error is therefore O(r^4).

Integrating and dividing by 2pi gives:

$$
\frac{1}{2\pi}\int_0^{2\pi}
u(x+r\cos\phi,y+r\sin\phi)d\phi
=u+\frac{r^2}{4}(u_{xx}+u_{yy})+O(r^4)
$$

### Final result

Since the Laplacian is:

$$
\nabla^2u=u_{xx}+u_{yy}
$$

we obtain:

$$
\boxed{
\frac{1}{2\pi}\int_0^{2\pi}
u(x+r\cos\phi,y+r\sin\phi)d\phi
=u+\frac{r^2}{4}\nabla^2u+O(r^4)
}
$$

### Physical interpretation

- A positive Laplacian means that the surroundings
  are warmer on average, so the point heats up.
- A negative Laplacian means that the surroundings
  are colder on average, so the point cools down.
- A zero Laplacian means that the instantaneous
  local temperature change is zero.

This explains the physical meaning of the Laplacian
in the heat equation.

## Task 1.2 - Dimensional analysis

### (a) Dimensionless combination

The units of thermal diffusivity, time and length are:

$$
[\alpha]=m^2/s,\qquad [t]=s,\qquad [L]=m
$$

Therefore:

$$
\left[\frac{\alpha t}{L^2}\right]
=\frac{(m^2/s)s}{m^2}=1
$$

The combination is dimensionless.

### (b) Characteristic diffusion time

Let the characteristic time have the form:

$$
\tau=\alpha^a L^b
$$

Its dimensions are:

$$
[\tau]=m^{2a+b}s^{-a}
$$

To obtain units of time:

$$
-a=1,\qquad 2a+b=0
$$

Solving gives:

$$
a=-1,\qquad b=2
$$

Therefore:

$$
\boxed{\tau=\frac{L^2}{\alpha}}
$$

Any characteristic diffusion time determined only
by L and alpha must be proportional to this quantity.

For both plates:

$$
L=10\,cm=0.1\,m
$$

#### Copper plate

Thermal diffusivity:

$$
\alpha=1.1\times10^{-4}\,m^2/s
$$

Calculation:

$$
\tau=\frac{0.1^2}{1.1\times10^{-4}}
=90.91\,s
$$

#### Carbon steel plate

Thermal diffusivity:

$$
\alpha=1.3\times10^{-5}\,m^2/s
$$

Calculation:

$$
\tau=\frac{0.1^2}{1.3\times10^{-5}}
=769.23\,s
$$

### Numerical results

| Material | Diffusivity (m^2/s) | Time (s) | Time (min) |
|---|---:|---:|---:|
| Copper | 1.1e-4 | 90.91 | 1.52 |
| Carbon steel | 1.3e-5 | 769.23 | 12.82 |

The ratio of characteristic diffusion times is:

$$
\frac{\tau_{steel}}{\tau_{copper}}
=\frac{769.23}{90.91}
\approx8.46
$$

Copper has a characteristic heat diffusion time
approximately 8.46 times shorter than carbon steel.

This agrees with physical intuition because copper
has a higher thermal diffusivity.

These are characteristic time scales, not exact
times required to reach thermal equilibrium.

### (c) Dimensionless heat equation

The original heat equation is:

$$
u_t=\alpha(u_{xx}+u_{yy})
$$

Introduce dimensionless variables:

$$
\hat{x}=\frac{x}{L},\qquad
\hat{y}=\frac{y}{L},\qquad
\hat{t}=\frac{\alpha t}{L^2}
$$

Using the chain rule:

$$
u_t=\frac{\alpha}{L^2}u_{\hat{t}}
$$

$$
u_{xx}=\frac{1}{L^2}u_{\hat{x}\hat{x}}
$$

$$
u_{yy}=\frac{1}{L^2}u_{\hat{y}\hat{y}}
$$

Substituting into the original heat equation:

$$
\frac{\alpha}{L^2}u_{\hat{t}}
=\frac{\alpha}{L^2}
(u_{\hat{x}\hat{x}}+u_{\hat{y}\hat{y}})
$$

Canceling the common factor gives:

$$
\boxed{
u_{\hat{t}}=
u_{\hat{x}\hat{x}}+u_{\hat{y}\hat{y}}
}
$$

Neither alpha nor L appears in the dimensionless
equation.

Therefore, a solver with alpha=1 on a unit square
can represent square plates of different sizes
and materials by rescaling space and time and
using the corresponding initial and boundary
conditions.

This justifies the dimensionless parameters
used in our serial, strips and blocks solvers.

## Task 1.3 - Fourier modes

### Objective

Show that the general Fourier mode satisfies
the 2D heat equation and the zero Dirichlet
boundary conditions, and determine its initial
condition.

### Given solution

For positive integers m and n, define:

$$
u_{mn}(x,y,t)=
\sin\left(\frac{m\pi x}{L_x}\right)
\sin\left(\frac{n\pi y}{L_y}\right)
\exp\left[
-\alpha\pi^2
\left(\frac{m^2}{L_x^2}+
\frac{n^2}{L_y^2}\right)t
\right]
$$

### (a) Verification of the heat equation

The heat equation is:

$$
u_t=\alpha(u_{xx}+u_{yy})
$$

Differentiating with respect to time gives:

$$
u_t=-\alpha\pi^2
\left(\frac{m^2}{L_x^2}+
\frac{n^2}{L_y^2}\right)u_{mn}
$$

Differentiating twice with respect to x gives:

$$
u_{xx}=-\frac{m^2\pi^2}{L_x^2}u_{mn}
$$

Differentiating twice with respect to y gives:

$$
u_{yy}=-\frac{n^2\pi^2}{L_y^2}u_{mn}
$$

Adding the spatial derivatives:

$$
u_{xx}+u_{yy}
=-\pi^2
\left(\frac{m^2}{L_x^2}+
\frac{n^2}{L_y^2}\right)u_{mn}
$$

Multiplying by alpha gives exactly the time
derivative.

Therefore:

$$
\boxed{u_t=\alpha(u_{xx}+u_{yy})}
$$

The proposed Fourier mode satisfies the heat
equation.

### (b) Boundary conditions

At x=0:

$$
\sin(0)=0
$$

At x=L_x:

$$
\sin(m\pi)=0
$$

At y=0:

$$
\sin(0)=0
$$

At y=L_y:

$$
\sin(n\pi)=0
$$

Since m and n are integers, the solution is
zero on all four edges.

Therefore, all homogeneous Dirichlet boundary
conditions are satisfied.

### (c) Initial condition

At t=0, the exponential factor equals 1.

Therefore:

$$
\boxed{
u_{mn}(x,y,0)=
\sin\left(\frac{m\pi x}{L_x}\right)
\sin\left(\frac{n\pi y}{L_y}\right)
}
$$

### Application to our project

For the verification Case V, we use:

$$
L_x=L_y=1,\qquad
\alpha=1,\qquad m=n=1
$$

The general solution reduces to:

$$
u_{\mathrm{exact}}(x,y,t)
=\sin(\pi x)\sin(\pi y)e^{-2\pi^2t}
$$

This is the analytical solution already implemented
and documented in the serial solver.

Existing repository references:

- docs/PART1_SERIAL.md
- src/heat_serial.cpp
- results/convergence.csv

The existing numerical verification results are
preserved. This task adds the missing mathematical
proof of the general Fourier solution.
