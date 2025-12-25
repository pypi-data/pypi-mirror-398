# Sparse GSP & SGWT Tools

A highly customizable, sparse-friendly SGWT/GSP module. This package provides tools to design, approximate, and implement a custom SGWT kernel for use over sparse networks.

Intended for GSP of time-vertex signals over static and dynamic sparse graphs.

## Installation

The package can be installed using:

```
python -m pip install scipy
```

The package uses a compiled CHOLMOD `.dll` file. Tests use `scikit-sparse` as a second level of vertification.

## Basic Usage

### Quick Start
For the quick-start example, we will find the response of a low-pass filter $\phi$ scaled by `s` to impulse $\delta$ at node $n$ over the graph `L`. This is mathematically denoted by $\phi_{n,s}=\delta_n*\phi_s$.
```python
import sgwt

# Graph Laplacian
L = sgwt.library.IMPEDANCE_TX

# Impulse at Vertex n
X = sgwt.impulse(L, n=...)

# Discrete Scales
s = np.logspace(...)

# L -> Context of Convolution
with sgwt.Convolve(L) as conv:

    # Apply Low-Pass Filters
    Y = conv.lowpass(X, s)
```

The numpy arrays `Y[i]` correspond to a filtered signal `X` at the `i-th` scale.

The purpose of the context manager is to provide safe re-use of `cholmod` workspace. While inside the context, the convolution procedure optimizes memory usage.

### Underlying Graph

The module has a small repository of built in graph laplacians that are useful for quick start examples. 

```python
L = sgwt.library.LENGTH_TX
L = sgwt.library.IMPEDANCE_HAWAII
L = sgwt.library.STANFARD_BUNNY
```

The user can also load any graph Laplacian so long it is in the `csc_matrix` format.


### Input Signals

A real-valued time-vertex function $X\in\mathbb{R}^{|N|\times|T|}$ stored as a 2D numpy array in column-major ordering (i.e., fortran style) can be used. For example, an empty array meeting these specifications:

```python
X = np.empty(
    shape=(nVert, nTime),
    order = 'F'
)
```

Although, a `(nVert,1)` array can also be used.

### Kernel Functions

There are three convenience analytical filters available.
```python
with Convolve(L) as conv:

    Y = conv.lowpass(X, s)
    Y = conv.bandpass(X, s)
    Y = conv.highpass(X, s)
```

For more advanced functionality, the convolution is generalized using kernel fitting. Single Function kernels include `MEXICAN_HAT`, `MODIFIED_MORLET`, `SHANNON`, and more.

The convolutional kernel `F` can be a vector function, meaning multiple filters can be applied concurrently (i.e., an orthoginal kernel to generate the wavaelet coefficients `SGWT`) This kernel will be available soon.
```python
with Convolve(L) as conv:

    Y = conv(X, F)
```

Same as before, the convolution is simply performed on our signal `X` by first defining L as the convolution context.

## Kernel Fitting

The kernel fitting representation is more generally a vector fitted function, a simple pole expansion of the form:
```math
g_a(\mathbf{\Lambda})\approx 
        d_aI + e_a\mathbf{\Lambda}
        + \sum_{q\in Q}\dfrac{r_{q,a}}{\mathbf{\Lambda}+qI} 
```

An iterative pole realocation procedure is used to converge to a reduced order model. The convolution of some function $\mathbf{f}*g_a$ is computed using the cholesky decomposition and memory efficient re-factors.

An example of an approriate format of the rational expansion:

```json
{
    "nfunc": N,
    "d": [d0, d1, ..., dN],
    "npoles": M,
    "poles": [
        {
            'q': q0, 
            'r':[r0, r1, ..., rN]
        },
        {
            'q': q1, 
            'r':[r0, r1, ..., rN]
        },
        ...
        {
            'q': qM, 
            'r':[r0, r1, ..., rN]
        }
    ]
}
```

## Analytical Filters

### Low-Pass Spectral Graph Filter

The low-pass filter (2) is *refinable*, as it is a self-similar rational function. The refinability of (2) makes it useful for signal smoothing across a range of spatial scales.

```math
\phi(\mathbf{\Lambda}) = \dfrac{I}{\mathbf{\Lambda}+I} 
```


### High-Pass Spectral Graph Filter

The proposed high-pass filter \eqref{eq:highpass} acts as a container for variations over the graph below a given spatial scale.

```math
\mu(\mathbf{\Lambda}) = \dfrac{\mathbf{\Lambda}}{\mathbf{\Lambda}+I}
```


### Band-Pass Spectral Graph Filter


A convenient closed-form wavelet generating kernel was found to be a useful kernel as an alternative to the vector-fitting procedure if a particular filter does not need to be designed. 

```math
\Psi(\mathbf{\Lambda}) = \dfrac{4\mathbf{\Lambda}}{(\mathbf{\Lambda}+I)^2} 
```

This filter qualifies as a wavelet generating kernel for the SGWT, since $\Psi(0)=0$ and the admissibility condition is satisfied. The admissibility constant of this band-pass filter is $C_f=8/3$.

```math
\Psi(0)=0  \qquad\text{and}\quad \int_0^{\infty}\dfrac{\Psi^2(x)}{x}\mathrm{d}x <\infty
```


## Cholesky Implementation

Given a rational approximation of some kernel function, we are able to implement graph convolutions using the Cholesky Decomposition. To ensure scalability to signals of large sparse networks, time-varying graph signals must be as efficient as possible with memory.

The `cholmod_solve2` function is the primary engine behind the fast reusable convolution environment. Access to the `cholmod` functions also means that this module is ideal for GSP of signals on dynamic graphs, using low-rank updates to change the factorization of the graph Laplacian.

