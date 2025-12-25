import numpy as np
from numba import njit, float32, int32

# Optional CUDA imports (guarded to avoid driver init failures)
try:
    from numba import cuda
    try:
        _CUDA_OK = bool(cuda.is_available())
    except Exception:
        _CUDA_OK = False

    if _CUDA_OK:
        from numba.cuda.libdevice import atanf
    else:
        atanf = None
except Exception:
    cuda = None
    atanf = None
    _CUDA_OK = False


@njit
def track_reconstruction(hits: np.ndarray):
    """
    CPU straight-line fit through hits:

    hits : (N, 3) array [x, y, z]
    returns:
        c_x, c_y, theta_x, theta_y
    """
    x = hits[:, 0]
    y = hits[:, 1]
    z = hits[:, 2]

    mean_x = np.mean(x)
    mean_y = np.mean(y)
    mean_z = np.mean(z)

    sum_zz = np.sum((z - mean_z) ** 2)
    sum_zx = np.sum((z - mean_z) * (x - mean_x))
    sum_zy = np.sum((z - mean_z) * (y - mean_y))

    if sum_zz != 0.0:
        m_x = sum_zx / sum_zz
        m_y = sum_zy / sum_zz
    else:
        m_x = 0.0
        m_y = 0.0

    c_x = mean_x - m_x * mean_z
    c_y = mean_y - m_y * mean_z

    return c_x, c_y, np.arctan(m_x), np.arctan(m_y)


if _CUDA_OK:
    @cuda.jit(
        "void(float32[:, :], int32, float32[:])",
        device=True,
        inline=True,
        fastmath=True,
    )
    def track_reconstruction_device(hits, n_hits, out):
        """
        GPU device version:

        hits   : (n_hits, 3) float32 array [x, y, z]
        n_hits : number of valid rows
        out    : length-4 float32 array:
                 out[0] = c_x
                 out[1] = c_y
                 out[2] = atan(m_x)
                 out[3] = atan(m_y)
        """
        # first pass: means
        sum_x = float32(0.0)
        sum_y = float32(0.0)
        sum_z = float32(0.0)

        for i in range(n_hits):
            sum_x += hits[i, 0]
            sum_y += hits[i, 1]
            sum_z += hits[i, 2]

        if n_hits > 0:
            inv_n = float32(1.0) / float32(n_hits)
            mean_x = sum_x * inv_n
            mean_y = sum_y * inv_n
            mean_z = sum_z * inv_n
        else:
            mean_x = float32(0.0)
            mean_y = float32(0.0)
            mean_z = float32(0.0)

        # second pass: sums for slopes
        sum_zz = float32(0.0)
        sum_zx = float32(0.0)
        sum_zy = float32(0.0)

        for i in range(n_hits):
            dz = hits[i, 2] - mean_z
            dx = hits[i, 0] - mean_x
            dy = hits[i, 1] - mean_y

            sum_zz += dz * dz
            sum_zx += dz * dx
            sum_zy += dz * dy

        if sum_zz != 0.0:
            m_x = sum_zx / sum_zz
            m_y = sum_zy / sum_zz
        else:
            m_x = float32(0.0)
            m_y = float32(0.0)

        c_x = mean_x - m_x * mean_z
        c_y = mean_y - m_y * mean_z

        out[0] = c_x
        out[1] = c_y
        out[2] = atanf(m_x)
        out[3] = atanf(m_y)
