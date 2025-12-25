import numpy as np
from numba import njit, float32

# Optional CUDA imports (guarded to avoid driver init failures)
try:
    from numba import cuda
    # Probe for a usable CUDA environment; this can raise if the driver is missing.
    try:
        _CUDA_OK = bool(cuda.is_available())
    except Exception:
        _CUDA_OK = False

    if _CUDA_OK:
        from numba.cuda.libdevice import sqrtf, sinf, cosf, atan2f, acosf, tanf
    else:
        sqrtf = sinf = cosf = atan2f = acosf = tanf = None
except Exception:
    cuda = None
    sqrtf = sinf = cosf = atan2f = acosf = tanf = None
    _CUDA_OK = False

EPS = 1e-8


# =========================
# CPU (Numba) versions
# =========================

@njit(cache=True)
def cart2projection(x, y, z):
    r = np.sqrt(x**2 + y**2 + z**2)
    theta_x_rad = np.arctan2(x, z)
    theta_y_rad = np.arctan2(y, z)
    return r, theta_x_rad, theta_y_rad


@njit(cache=True)
def projection2cart(r, theta_x_rad, theta_y_rad):
    """
    Works for both scalar and array inputs in nopython mode.

    r, theta_x_rad, theta_y_rad can be scalars or arrays (same shape).
    We avoid `if denom < EPS` on arrays by using np.where instead.
    """
    tx = np.tan(theta_x_rad)
    ty = np.tan(theta_y_rad)

    denom = np.sqrt(1.0 + tx * tx + ty * ty)

    # Avoid scalar `if` on potentially array-valued denom.
    # First build a safe denom (never < EPS), then zero out c where denom<EPS.
    denom_safe = np.where(denom < EPS, 1.0, denom)
    c = r / denom_safe
    c = np.where(denom < EPS, 0.0, c)

    x = tx * c
    y = ty * c
    z = c

    return x, y, z



@njit(cache=True)
def cart2spherical(x, y, z):
    """
    Works for both scalar and array inputs.

    x, y, z can be scalars or arrays (same shape).
    We avoid scalar 'if r < EPS' by using np.where.
    """
    r = np.sqrt(x * x + y * y + z * z)

    # mask where r is "too small"
    mask = r < EPS

    # Avoid division by zero: use r_safe in the acos
    r_safe = np.where(mask, 1.0, r)

    theta = np.arccos(z / r_safe)
    phi   = np.arctan2(-x, y)

    # For very small r, set angles to 0
    theta = np.where(mask, 0.0, theta)
    phi   = np.where(mask, 0.0, phi)

    return r, theta, phi



@njit(cache=True)
def spherical2cart(r, theta_rad, phi_rad):
    st = np.sin(theta_rad)
    ct = np.cos(theta_rad)
    sp = np.sin(phi_rad)
    cp = np.cos(phi_rad)

    x = -r * st * sp
    y =  r * st * cp
    z =  r * ct

    return x, y, z


@njit(cache=True)
def projection2spherical(r, theta_x_rad, theta_y_rad):
    x, y, z = projection2cart(r, theta_x_rad, theta_y_rad)
    return cart2spherical(x, y, z)


@njit(cache=True)
def spherical2projection(r, theta_rad, phi_rad):
    x, y, z = spherical2cart(r, theta_rad, phi_rad)
    return cart2projection(x, y, z)

@njit(cache=True)
def det2earth(x, y, z, zenith_rad, azimuth_rad):
    """
    Rotate from detector frame -> Earth frame.
    This is left as a plain Python function (no njit) like your original.
    """
    cz = np.cos(zenith_rad)
    sz = np.sin(zenith_rad)
    ca = np.cos(azimuth_rad)
    sa = np.sin(azimuth_rad)

    x_ = ca * x - sa * cz * y - sa * sz * z
    y_ = sa * x + ca * cz * y + ca * sz * z
    z_ =         -sz * y      + cz * z

    return x_, y_, z_


@njit(cache=True)
def earth2det(x, y, z, zenith_rad, azimuth_rad):
    """
    Inverse rotation: Earth -> detector.
    """
    cz = np.cos(zenith_rad)
    sz = np.sin(zenith_rad)
    ca = np.cos(azimuth_rad)
    sa = np.sin(azimuth_rad)

    x_ = ca * x + sa * y
    y_ = -sa * cz * x + ca * cz * y - sz * z
    z_ = -sa * sz * x + ca * sz * y + cz * z

    return x_, y_, z_


@njit(cache=True)
def det2zenith(theta_x_mrad, theta_y_mrad, zenith_rad, azimuth_rad):
    """
    Detector small angles (mrad) -> Earth-frame zenith angle.
    """
    thx = theta_x_mrad * 0.001
    thy = theta_y_mrad * 0.001

    x, y, z = projection2cart(1.0, thx, thy)
    xe, ye, ze = det2earth(x, y, z, zenith_rad, azimuth_rad)
    _, theta, _ = cart2spherical(xe, ye, ze)
    return theta


def mrad2zenith(angle_deg, theta_rad, phi_rad):
    """
    Build a map of zenith angles for a square window in detector-mrad space.

    angle_deg  : half-window size in *degrees* (converted to mrad internally)
    theta_rad  : detector zenith in Earth frame
    phi_rad    : detector azimuth in Earth frame

    Returns:
        zenith_angle[ny, nx]
    """
    mrad = int(np.radians(angle_deg) * 1000.0)

    xs = np.arange(-mrad, mrad + 1)
    ys = np.arange(-mrad, mrad + 1)

    X, Y = np.meshgrid(xs, ys)
    zenith_angle = np.zeros_like(X, dtype=np.float64)

    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            zenith_angle[i, j] = det2zenith(
                float(X[i, j]),
                float(Y[i, j]),
                theta_rad,
                phi_rad,
            )

    return zenith_angle


# =========================
# GPU device versions
# =========================


if _CUDA_OK:
    @cuda.jit("void(float32, float32, float32, float32[:])",
              device=True, inline=True, fastmath=True)
    def cart2projection_device(x, y, z, out):
        r = sqrtf(x * x + y * y + z * z)
        theta_x = atan2f(x, z)
        theta_y = atan2f(y, z)

        out[0] = r
        out[1] = theta_x
        out[2] = theta_y

    @cuda.jit("void(float32, float32, float32, float32[:])",
              device=True, inline=True, fastmath=True)
    def projection2cart_device(r, theta_x_rad, theta_y_rad, out):
        tx = tanf(theta_x_rad)
        ty = tanf(theta_y_rad)

        denom = sqrtf(1.0 + tx * tx + ty * ty)
        if denom < float32(EPS):
            c = float32(0.0)
        else:
            c = r / denom

        out[0] = tx * c
        out[1] = ty * c
        out[2] = c

    @cuda.jit("void(float32, float32, float32, float32[:])",
              device=True, inline=True, fastmath=True)
    def cart2spherical_device(x, y, z, out):
        r = sqrtf(x * x + y * y + z * z)
        if r < float32(EPS):
            out[0] = float32(0.0)
            out[1] = float32(0.0)
            out[2] = float32(0.0)
            return

        theta = acosf(z / r)
        phi = atan2f(-x, y)

        out[0] = r
        out[1] = theta
        out[2] = phi

    @cuda.jit("void(float32, float32, float32, float32[:])",
              device=True, inline=True, fastmath=True)
    def spherical2cart_device(r, theta_rad, phi_rad, out):
        st = sinf(theta_rad)
        ct = cosf(theta_rad)
        sp = sinf(phi_rad)
        cp = cosf(phi_rad)

        x = -r * st * sp
        y =  r * st * cp
        z =  r * ct

        out[0] = x
        out[1] = y
        out[2] = z

    @cuda.jit("void(float32, float32, float32, float32[:])",
              device=True, inline=True, fastmath=True)
    def projection2spherical_device(r, theta_x_rad, theta_y_rad, out):
        tmp_cart = cuda.local.array(3, dtype=float32)
        cart2projection_device(r, theta_x_rad, theta_y_rad, tmp_cart)
        cart2spherical_device(tmp_cart[0], tmp_cart[1], tmp_cart[2], out)

    @cuda.jit("void(float32, float32, float32, float32[:])",
              device=True, inline=True, fastmath=True)
    def spherical2projection_device(r, theta_rad, phi_rad, out):
        tmp_cart = cuda.local.array(3, dtype=float32)
        cart2spherical_device(r, theta_rad, phi_rad, tmp_cart)
        cart2projection_device(tmp_cart[0], tmp_cart[1], tmp_cart[2], out)

    @cuda.jit("void(float32, float32, float32, float32, float32, float32[:])",
              device=True, inline=True, fastmath=True)
    def det2earth_device(x, y, z, zenith_rad, azimuth_rad, out):
        cz = cosf(zenith_rad)
        sz = sinf(zenith_rad)
        ca = cosf(azimuth_rad)
        sa = sinf(azimuth_rad)

        x_ = ca * x - sa * cz * y - sa * sz * z
        y_ = sa * x + ca * cz * y + ca * sz * z
        z_ =      - sz * y          + cz * z

        out[0] = x_
        out[1] = y_
        out[2] = z_

    @cuda.jit("void(float32, float32, float32, float32, float32, float32[:])",
              device=True, inline=True, fastmath=True)
    def earth2det_device(x, y, z, zenith_rad, azimuth_rad, out):
        cz = cosf(zenith_rad)
        sz = sinf(zenith_rad)
        ca = cosf(azimuth_rad)
        sa = sinf(azimuth_rad)

        x_ = ca * x + sa * y
        y_ = -sa * cz * x + ca * cz * y - sz * z
        z_ = -sa * sz * x + ca * sz * y + cz * z

        out[0] = x_
        out[1] = y_
        out[2] = z_

    @cuda.jit("float32(float32, float32, float32, float32)",
              device=True, inline=True, fastmath=True)
    def det2zenith_device(theta_x_mrad, theta_y_mrad, zenith_rad, azimuth_rad):
        thx = theta_x_mrad * 0.001
        thy = theta_y_mrad * 0.001

        tmp_cart = cuda.local.array(3, dtype=float32)
        tmp_earth = cuda.local.array(3, dtype=float32)
        tmp_sph = cuda.local.array(3, dtype=float32)

        projection2cart_device(float32(1.0), thx, thy, tmp_cart)
        det2earth_device(tmp_cart[0], tmp_cart[1], tmp_cart[2],
                         zenith_rad, azimuth_rad, tmp_earth)
        cart2spherical_device(tmp_earth[0], tmp_earth[1], tmp_earth[2], tmp_sph)

        # theta (zenith) is out[1]
        return tmp_sph[1]
