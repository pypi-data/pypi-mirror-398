"""
2D Tikhonov smoothing on a regular grid with Neumann boundary conditions.

Main public API:
    - neumann_laplacian_apply(u, hx, hy)
    - tikhonov_smooth_neumann(f, lam, hx, hy, ...)
    - tikhonov_smooth_neumann_sparse(f, lam, hx, hy, ...)

The Numba path solves (I - lam * L) u = f by a simple
Jacobi-like fixed-point iteration, where L is the 2D Laplacian
with mirrored-neighbour (Neumann) boundaries.

The SciPy path matches your current sparse-CG-based implementation.
"""

import numpy as np

# Optional: Numba support
try:
    from numba import njit
    _HAVE_NUMBA = True
except Exception:       # pragma: no cover
    _HAVE_NUMBA = False
    def njit(*args, **kwargs):   # dummy decorator
        def wrap(fn):
            return fn
        return wrap

# Optional: SciPy support
try:
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    _HAVE_SCIPY = True
except Exception:       # pragma: no cover
    _HAVE_SCIPY = False


# ---------------------------------------------------------------------------
# 1) Low-level Numba kernels
# ---------------------------------------------------------------------------

@njit(cache=True)
def _laplacian_neumann_2d(u, hx, hy, out):
    """
    Apply 2D Laplacian with Neumann BC (mirrored neighbour) to u.

    Parameters
    ----------
    u : 2D array (ny, nx)
    hx, hy : float
        Grid spacing in x and y.
    out : 2D array (ny, nx)
        Output buffer (must be pre-allocated).
    """
    ny, nx = u.shape
    inv_hx2 = 1.0 / (hx * hx) if hx != 0.0 else 0.0
    inv_hy2 = 1.0 / (hy * hy) if hy != 0.0 else 0.0

    for iy in range(ny):
        # y neighbours (with mirror)
        if ny > 1:
            iy_m = iy - 1 if iy > 0     else 1
            iy_p = iy + 1 if iy < ny-1 else ny-2
        else:
            iy_m = 0
            iy_p = 0

        for ix in range(nx):
            # x neighbours (with mirror)
            if nx > 1:
                ix_m = ix - 1 if ix > 0     else 1
                ix_p = ix + 1 if ix < nx-1 else nx-2
            else:
                ix_m = 0
                ix_p = 0

            c = u[iy, ix]
            lap_x = (u[iy, ix_m] + u[iy, ix_p] - 2.0 * c) * inv_hx2
            lap_y = (u[iy_m, ix] + u[iy_p, ix] - 2.0 * c) * inv_hy2
            out[iy, ix] = lap_x + lap_y


@njit(cache=True)
def _tikhonov_neumann_jacobi(f, lam, hx, hy, n_iter, omega):
    """
    Numba-compiled Jacobi-like solver for (I - lam * L) u = f.

    Parameters
    ----------
    f : 2D array (ny, nx)
        RHS (input field to be smoothed).
    lam : float
        Regularization strength (lambda).
    hx, hy : float
        Grid spacings in x, y.
    n_iter : int
        Number of iterations.
    omega : float
        Relaxation parameter (0 < omega <= 1).

    Returns
    -------
    u : 2D array (ny, nx)
        Approximate solution of (I - lam L) u = f.
    """
    ny, nx = f.shape
    u = f.copy()
    tmp = np.empty_like(f)

    # For this Laplacian with Neumann BC, the diagonal of L is constant:
    # L_ii = -2 * (1/hx^2 + 1/hy^2)  (if nx, ny > 1)
    # So diag(A) = 1 - lam * L_ii = 1 + 2*lam*(1/hx^2 + 1/hy^2)
    inv_diagA = 1.0
    if nx > 1 and ny > 1:
        inv_diagA = 1.0 / (1.0 + 2.0 * lam * ((1.0 / (hx * hx)) + (1.0 / (hy * hy))))

    for it in range(n_iter):
        # tmp <- L u
        _laplacian_neumann_2d(u, hx, hy, tmp)

        # A u = u - lam * L u
        # Jacobi-like step: u <- u + omega * D^{-1} (f - A u)
        for iy in range(ny):
            for ix in range(nx):
                Au = u[iy, ix] - lam * tmp[iy, ix]
                r = f[iy, ix] - Au
                u[iy, ix] += omega * inv_diagA * r

    return u


# ---------------------------------------------------------------------------
# 2) Public Numba-accelerated interface
# ---------------------------------------------------------------------------

def neumann_laplacian_apply(u, hx, hy):
    """
    Convenience wrapper to apply the 2D Neumann Laplacian.

    Parameters
    ----------
    u : 2D ndarray
    hx, hy : float

    Returns
    -------
    Lu : 2D ndarray
    """
    u = np.asarray(u, dtype=np.float64)
    out = np.empty_like(u)
    _laplacian_neumann_2d(u, float(hx), float(hy), out)
    return out


def tikhonov_smooth_neumann(
    f,
    lam,
    hx,
    hy,
    n_iter=100,
    omega=0.8,
    use_numba=True,
):
    """
    Tikhonov smoothing with 2D Neumann Laplacian via Numba-accelerated iteration.

    Solves approximately:
        (I - lam * L) u = f

    Parameters
    ----------
    f : 2D ndarray
        Input field.
    lam : float
        Regularization strength (lambda).
    hx, hy : float
        Grid spacings.
    n_iter : int, optional
        Number of iterations (default: 100).
    omega : float, optional
        Relaxation parameter (0 < omega <= 1) (default: 0.8).
    use_numba : bool, optional
        If False, a pure-NumPy fallback of the same algorithm is used
        (slower, but avoids Numba dependency).

    Returns
    -------
    u : 2D ndarray
        Smoothed array.
    """
    f = np.asarray(f, dtype=np.float64)
    lam = float(lam)
    hx = float(hx)
    hy = float(hy)

    if use_numba and _HAVE_NUMBA:
        u = _tikhonov_neumann_jacobi(f, lam, hx, hy, int(n_iter), float(omega))
        return u.astype(f.dtype)

    # --- pure NumPy fallback implementing the same iteration ---
    ny, nx = f.shape
    u = f.copy()
    tmp = np.empty_like(f)
    inv_diagA = 1.0
    if nx > 1 and ny > 1:
        inv_diagA = 1.0 / (1.0 + 2.0 * lam * ((1.0 / (hx * hx)) + (1.0 / (hy * hy))))

    def laplacian_np(arr, _hx, _hy, out_arr):
        ny2, nx2 = arr.shape
        inv_hx2 = 1.0 / (_hx * _hx) if _hx != 0.0 else 0.0
        inv_hy2 = 1.0 / (_hy * _hy) if _hy != 0.0 else 0.0
        for iy in range(ny2):
            if ny2 > 1:
                iy_m = iy - 1 if iy > 0     else 1
                iy_p = iy + 1 if iy < ny2-1 else ny2-2
            else:
                iy_m = 0
                iy_p = 0
            for ix in range(nx2):
                if nx2 > 1:
                    ix_m = ix - 1 if ix > 0     else 1
                    ix_p = ix + 1 if ix < nx2-1 else nx2-2
                else:
                    ix_m = 0
                    ix_p = 0
                c = arr[iy, ix]
                lap_x = (arr[iy, ix_m] + arr[iy, ix_p] - 2.0 * c) * inv_hx2
                lap_y = (arr[iy_m, ix] + arr[iy_p, ix] - 2.0 * c) * inv_hy2
                out_arr[iy, ix] = lap_x + lap_y

    for it in range(int(n_iter)):
        laplacian_np(u, hx, hy, tmp)
        for iy in range(ny):
            for ix in range(nx):
                Au = u[iy, ix] - lam * tmp[iy, ix]
                r = f[iy, ix] - Au
                u[iy, ix] += omega * inv_diagA * r

    return u.astype(f.dtype)


# ---------------------------------------------------------------------------
# 3) SciPy-based sparse solver (your original approach)
# ---------------------------------------------------------------------------

def _build_laplacian_neumann_sparse(nx, ny, dx, dy):
    """
    2D Laplacian with Neumann BC in CSR format.

    This is essentially your original build_laplacian_neumann_sparse().
    """
    if not _HAVE_SCIPY:
        raise RuntimeError("SciPy is required for the sparse Laplacian path.")

    N = nx * ny
    rows = []
    cols = []
    data = []

    def add(k, j, val):
        rows.append(k)
        cols.append(j)
        data.append(val)

    for iy in range(ny):
        for ix in range(nx):
            k = iy * nx + ix
            center = 0.0

            # x-direction
            if ix > 0:
                jL = iy * nx + (ix - 1)
                add(k, jL, 1.0 / (dx * dx))
                center -= 1.0 / (dx * dx)
            else:
                jR = iy * nx + min(ix + 1, nx - 1)
                add(k, jR, 1.0 / (dx * dx))
                center -= 1.0 / (dx * dx)

            if ix < nx - 1:
                jR = iy * nx + (ix + 1)
                add(k, jR, 1.0 / (dx * dx))
                center -= 1.0 / (dx * dx)
            else:
                jL = iy * nx + max(ix - 1, 0)
                add(k, jL, 1.0 / (dx * dx))
                center -= 1.0 / (dx * dx)

            # y-direction
            if iy > 0:
                jD = (iy - 1) * nx + ix
                add(k, jD, 1.0 / (dy * dy))
                center -= 1.0 / (dy * dy)
            else:
                jU = min(iy + 1, ny - 1) * nx + ix
                add(k, jU, 1.0 / (dy * dy))
                center -= 1.0 / (dy * dy)

            if iy < ny - 1:
                jU = (iy + 1) * nx + ix
                add(k, jU, 1.0 / (dy * dy))
                center -= 1.0 / (dy * dy)
            else:
                jD = max(iy - 1, 0) * nx + ix
                add(k, jD, 1.0 / (dy * dy))
                center -= 1.0 / (dy * dy)

            add(k, k, center)

    L = sp.csr_matrix((data, (rows, cols)), shape=(N, N))
    return L


def tikhonov_smooth_neumann_sparse(
    f,
    lam,
    hx,
    hy,
    use_cg=True,
    tol=1e-6,
    maxiter=None,
):
    """
    SciPy sparse-based solver for (I - lam * L) u = f,
    with L the 2D Neumann Laplacian.

    Parameters
    ----------
    f : 2D ndarray
    lam : float
    hx, hy : float
    use_cg : bool, optional
        If True, use CG; otherwise, spsolve.
    tol, maxiter : CG controls.

    Returns
    -------
    u : 2D ndarray
    """
    if not _HAVE_SCIPY:
        raise RuntimeError("SciPy is required for tikhonov_smooth_neumann_sparse.")

    f = np.asarray(f, dtype=np.float64)
    ny, nx = f.shape
    N = nx * ny
    f_flat = f.ravel()

    L = _build_laplacian_neumann_sparse(nx, ny, hx, hy)
    A = sp.eye(N, format="csr") - lam * L

    if use_cg:
        u_flat, info = spla.cg(A, f_flat, tol=tol, maxiter=maxiter)
        if info != 0:
            print(f"[tikhonov_smooth_neumann_sparse] CG info = {info} (0 = converged)")
    else:
        u_flat = spla.spsolve(A, f_flat)

    u = u_flat.reshape((ny, nx))
    return u.astype(f.dtype)
