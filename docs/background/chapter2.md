# Chapter 2 - Mathematical Toolbox

## Task 2.1 - Expansions you will need

### General Taylor expansion

For a sufficiently smooth function f, Taylor's
theorem around x gives:

$$
f(x+a)=f(x)+af'(x)
+\frac{a^2}{2!}f''(x)
+\frac{a^3}{3!}f'''(x)
+\frac{a^4}{4!}f^{(4)}(x)
+O(a^5)
$$

### (a) Expansion of f(x+h)

Substituting a=h gives:

$$
\boxed{
f(x+h)=f(x)+hf'(x)
+\frac{h^2}{2}f''(x)
+\frac{h^3}{6}f'''(x)
+\frac{h^4}{24}f^{(4)}(x)
+O(h^5)
}
$$

### (b) Expansion of f(x-h)

Substituting a=-h gives:

$$
f(x-h)=f(x)-hf'(x)
+\frac{(-h)^2}{2}f''(x)
+\frac{(-h)^3}{6}f'''(x)
+\frac{(-h)^4}{24}f^{(4)}(x)
+O(h^5)
$$

Since:

$$
(-h)^2=h^2,\qquad
(-h)^3=-h^3,\qquad
(-h)^4=h^4
$$

the final result is:

$$
\boxed{
f(x-h)=f(x)-hf'(x)
+\frac{h^2}{2}f''(x)
-\frac{h^3}{6}f'''(x)
+\frac{h^4}{24}f^{(4)}(x)
+O(h^5)
}
$$

The odd-order terms change sign because odd
powers of -h are negative.

The even-order terms remain unchanged because
even powers of -h are positive.

### (c) Expansion of f(x+2h)

Substituting a=2h gives:

$$
f(x+2h)=f(x)+2hf'(x)
+\frac{(2h)^2}{2}f''(x)
+\frac{(2h)^3}{6}f'''(x)
+\frac{(2h)^4}{24}f^{(4)}(x)
+O(h^5)
$$

Simplifying the coefficients:

$$
\frac{4}{2}=2,\qquad
\frac{8}{6}=\frac{4}{3},\qquad
\frac{16}{24}=\frac{2}{3}
$$

Therefore:

$$
\boxed{
f(x+2h)=f(x)+2hf'(x)
+2h^2f''(x)
+\frac{4h^3}{3}f'''(x)
+\frac{2h^4}{3}f^{(4)}(x)
+O(h^5)
}
$$

### Summary of coefficients

| Term | f(x+h) | f(x-h) | f(x+2h) |
|---|---:|---:|---:|
| f(x) | 1 | 1 | 1 |
| h f'(x) | 1 | -1 | 2 |
| h^2 f''(x) | 1/2 | 1/2 | 2 |
| h^3 f'''(x) | 1/6 | -1/6 | 4/3 |
| h^4 f^(4)(x) | 1/24 | 1/24 | 2/3 |

### Application to the project

These expansions are the mathematical foundation
of the finite-difference approximations used
in our heat diffusion solver.

Adding the expansions of f(x+h) and f(x-h)
cancels the odd-order terms.

Subtracting them cancels the even-order terms
shown above.

These properties will be used in Chapter 3
to derive approximations of spatial derivatives
and their truncation errors.
