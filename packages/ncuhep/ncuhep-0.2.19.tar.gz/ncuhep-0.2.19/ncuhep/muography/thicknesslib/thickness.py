# thicknesslib/thickness.py
import importlib
import time
import logging
import numpy as np
from numba import njit, prange
from math import tan, sqrt, cos, sin, floor, fabs

from ..profiler import Profiler, print_profile

# ---------------- Optional CUDA ----------------
cuda = None
_CUDA_OK = False

if importlib.util.find_spec("numba.cuda") is not None:
    from numba import cuda as _cuda_mod
    from numba.cuda.cudadrv.error import CudaSupportError

    cuda = _cuda_mod
    try:
        _CUDA_OK = cuda.is_available()
    except CudaSupportError:
        _CUDA_OK = False

# ---------------- Optional tqdm ----------------
if importlib.util.find_spec("tqdm.auto") is not None:
    from tqdm.auto import tqdm
else:
    def tqdm(x, **kwargs):
        return x


# ---------------- logging setup ----------------
_LOGGER_NAME = "thickness_map_engine"
_logger = logging.getLogger(_LOGGER_NAME)
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    _logger.addHandler(_h)
    _logger.propagate = False


# ============================================================
# Geometry (detector slopes → Earth ENU → DEM frame)
# ============================================================

@njit(cache=True)
def projection2cart(r, theta_x_rad, theta_y_rad):
    x_ = np.tan(theta_x_rad)
    y_ = np.tan(theta_y_rad)
    c = r / np.sqrt(1.0 + x_ ** 2 + y_ ** 2)
    return x_ * c, y_ * c, c


@njit(cache=True)
def det2earth(x, y, z, zenith_rad, azimuth_rad):
    # azimuth: clockwise from North (0°=North, 90°=East)
    ca = np.cos(azimuth_rad)
    sa = np.sin(azimuth_rad)
    cz = np.cos(zenith_rad)
    sz = np.sin(zenith_rad)
    x_ = ca * x - sa * cz * y + sa * sz * z
    y_ = sa * x + ca * cz * y - ca * sz * z
    z_ = sz * y + cz * z
    return x_, y_, z_


@njit(cache=True, fastmath=True)
def earth_dir_from_detector_angles(theta_x_rad, theta_y_rad, zenith_rad, azimuth_rad):
    xd, yd, zd = projection2cart(1.0, theta_x_rad, theta_y_rad)
    xe, ye, ze = det2earth(xd, yd, zd, zenith_rad, azimuth_rad)
    return xe, ye, ze  # ENU


# ============================================================
# DEM sampling and marching (CPU)
# ============================================================

@njit(cache=True, fastmath=True)
def bilinear_sample(Z, x0, y0, dx, dy, x, y):
    fx = (x - x0) / dx
    fy = (y - y0) / dy
    i = int(floor(fx))
    j = int(floor(fy))
    if i < 0:
        i = 0
    if j < 0:
        j = 0
    nx_ = Z.shape[1]
    ny_ = Z.shape[0]
    if i > nx_ - 2:
        i = nx_ - 2
    if j > ny_ - 2:
        j = ny_ - 2
    tx = fx - i
    ty = fy - j
    z00 = Z[j, i]
    z10 = Z[j, i + 1]
    z01 = Z[j + 1, i]
    z11 = Z[j + 1, i + 1]
    return (
        (1.0 - tx) * (1.0 - ty) * z00
        + tx * (1.0 - ty) * z10
        + (1.0 - tx) * ty * z01
        + tx * ty * z11
    )


@njit(cache=True, fastmath=True)
def cumulative_terrain_length(
    Z, x0, y0, dx, dy,
    x_min, x_max, y_min, y_max,
    x_det, y_det, z_det,
    nx, ny, nz,
    s_max, ds_coarse, eps_bisect, max_bisect
):
    s = 1e-6
    x = x_det + s * nx
    y = y_det + s * ny
    z = z_det + s * nz
    if (x < x_min) or (x > x_max) or (y < y_min) or (y > y_max):
        return 0.0
    h = bilinear_sample(Z, x0, y0, dx, dy, x, y)
    f_prev = z - h
    inside = (f_prev <= 0.0)
    s_entry = s if inside else 0.0
    total = 0.0

    while s < s_max:
        s_next = s + ds_coarse
        if s_next > s_max:
            s_next = s_max
        x = x_det + s_next * nx
        y = y_det + s_next * ny
        z = z_det + s_next * nz

        if (x < x_min) or (x > x_max) or (y < y_min) or (y > y_max):
            if inside:
                total += (s_next - s_entry)
            break

        h = bilinear_sample(Z, x0, y0, dx, dy, x, y)
        f = z - h
        crossed = (f <= 0.0) != inside

        if crossed:
            s_left = s
            s_right = s_next
            for _ in range(max_bisect):
                s_mid = 0.5 * (s_left + s_right)
                xm = x_det + s_mid * nx
                ym = y_det + s_mid * ny
                zm = z_det + s_mid * nz
                hm = bilinear_sample(Z, x0, y0, dx, dy, xm, ym)
                fm = zm - hm
                if (fm <= 0.0) != inside:
                    s_right = s_mid
                else:
                    s_left = s_mid
                if (s_right - s_left) < 1e-4 or fabs(fm) < eps_bisect:
                    break
            s_cross = 0.5 * (s_left + s_right)
            if inside:
                total += (s_cross - s_entry)
                inside = False
            else:
                s_entry = s_cross
                inside = True
            s = s_next
            continue

        s = s_next

    if inside and s >= s_max:
        total += (s_max - s_entry)
    return total


@njit(parallel=True, cache=True, fastmath=True)
def compute_thickness_map_rotated_cpu(
    Z, x0, y0, dx, dy, z_det,
    zenith_rad, det_azimuth_rad,
    dem_cos, dem_sin,
    THX, THY,
    s_max, ds_coarse, eps_bisect, max_bisect,
    x_min, x_max, y_min, y_max
):
    H, W = THX.shape
    L = np.zeros((H, W), dtype=np.float64)
    for j in prange(H):
        for i in range(W):
            thx = THX[j, i]
            thy = THY[j, i]
            nx_e, ny_e, nz = earth_dir_from_detector_angles(thx, thy, zenith_rad, det_azimuth_rad)
            nx = nx_e * dem_cos + ny_e * dem_sin
            ny = -nx_e * dem_sin + ny_e * dem_cos
            L[j, i] = cumulative_terrain_length(
                Z, x0, y0, dx, dy,
                x_min, x_max, y_min, y_max,
                0.0, 0.0, z_det,
                nx, ny, nz,
                s_max, ds_coarse, eps_bisect, max_bisect
            )
    return L


# ============================================================
# CUDA device functions & kernel (GPU)
# ============================================================
if _CUDA_OK:

    @cuda.jit(device=True, inline=True)
    def _bilinear_sample_gpu(Z, x0, y0, dx, dy, x, y):
        fx = (x - x0) / dx
        fy = (y - y0) / dy
        i = int(floor(fx))
        j = int(floor(fy))
        nx_ = Z.shape[1]
        ny_ = Z.shape[0]
        if i < 0:
            i = 0
        if j < 0:
            j = 0
        if i > nx_ - 2:
            i = nx_ - 2
        if j > ny_ - 2:
            j = ny_ - 2
        tx = fx - i
        ty = fy - j
        z00 = Z[j, i]
        z10 = Z[j, i + 1]
        z01 = Z[j + 1, i]
        z11 = Z[j + 1, i + 1]
        return (
            (1.0 - tx) * (1.0 - ty) * z00
            + tx * (1.0 - ty) * z10
            + (1.0 - tx) * ty * z01
            + tx * ty * z11
        )

    @cuda.jit(device=True, inline=True)
    def _projection2cart_gpu(r, tx, ty):
        x_ = tan(tx)
        y_ = tan(ty)
        c = r / sqrt(1.0 + x_ * x_ + y_ * y_)
        return x_ * c, y_ * c, c

    @cuda.jit(device=True, inline=True)
    def _det2earth_gpu(x, y, z, zenith_rad, azimuth_rad):
        ca = cos(azimuth_rad)
        sa = sin(azimuth_rad)
        cz = cos(zenith_rad)
        sz = sin(zenith_rad)
        x_ = ca * x - sa * cz * y + sa * sz * z
        y_ = sa * x + ca * cz * y - ca * sz * z
        z_ = sz * y + cz * z
        return x_, y_, z_

    @cuda.jit(device=True, inline=True)
    def _earth_dir_from_detector_angles_gpu(tx, ty, zenith_rad, azimuth_rad):
        xd, yd, zd = _projection2cart_gpu(1.0, tx, ty)
        xe, ye, ze = _det2earth_gpu(xd, yd, zd, zenith_rad, azimuth_rad)
        return xe, ye, ze

    @cuda.jit(device=True)
    def _ray_length_gpu(
        Z, x0, y0, dx, dy,
        x_min, x_max, y_min, y_max,
        x_det, y_det, z_det,
        nx, ny, nz,
        s_max, ds_coarse, eps_bisect, max_bisect
    ):
        s = 1e-6
        x = x_det + s * nx
        y = y_det + s * ny
        z = z_det + s * nz
        if (x < x_min) or (x > x_max) or (y < y_min) or (y > y_max):
            return 0.0
        h = _bilinear_sample_gpu(Z, x0, y0, dx, dy, x, y)
        f_prev = z - h
        inside = (f_prev <= 0.0)
        s_entry = s if inside else 0.0
        total = 0.0

        while s < s_max:
            s_next = s + ds_coarse
            if s_next > s_max:
                s_next = s_max
            x = x_det + s_next * nx
            y = y_det + s_next * ny
            z = z_det + s_next * nz

            if (x < x_min) or (x > x_max) or (y < y_min) or (y > y_max):
                if inside:
                    total += (s_next - s_entry)
                break

            h = _bilinear_sample_gpu(Z, x0, y0, dx, dy, x, y)
            f = z - h
            crossed = (f <= 0.0) != inside

            if crossed:
                s_left = s
                s_right = s_next
                for _ in range(max_bisect):
                    s_mid = 0.5 * (s_left + s_right)
                    xm = x_det + s_mid * nx
                    ym = y_det + s_mid * ny
                    zm = z_det + s_mid * nz
                    hm = _bilinear_sample_gpu(Z, x0, y0, dx, dy, xm, ym)
                    fm = zm - hm
                    if (fm <= 0.0) != inside:
                        s_right = s_mid
                    else:
                        s_left = s_mid
                    if (s_right - s_left) < 1e-4 or fabs(fm) < eps_bisect:
                        break
                s_cross = 0.5 * (s_left + s_right)
                if inside:
                    total += (s_cross - s_entry)
                    inside = False
                else:
                    s_entry = s_cross
                    inside = True
                s = s_next
                continue

            s = s_next

        if inside and s >= s_max:
            total += (s_max - s_entry)
        return total

    @cuda.jit
    def compute_thickness_map_rotated_gpu(
        Z, x0, y0, dx, dy, z_det,
        zenith_rad, det_azimuth_rad,
        dem_cos, dem_sin,
        THX, THY,
        s_max, ds_coarse, eps_bisect, max_bisect,
        x_min, x_max, y_min, y_max,
        L
    ):
        j, i = cuda.grid(2)
        H = THX.shape[0]
        W = THX.shape[1]
        if j >= H or i >= W:
            return
        thx = THX[j, i]
        thy = THY[j, i]
        nx_e, ny_e, nz = _earth_dir_from_detector_angles_gpu(thx, thy, zenith_rad, det_azimuth_rad)
        nx = nx_e * dem_cos + ny_e * dem_sin
        ny = -nx_e * dem_sin + ny_e * dem_cos
        L[j, i] = _ray_length_gpu(
            Z, x0, y0, dx, dy,
            x_min, x_max, y_min, y_max,
            0.0, 0.0, z_det,
            nx, ny, nz,
            s_max, ds_coarse, eps_bisect, max_bisect
        )


# ============================================================
# Jacobian in slope coordinates (weight)
# ============================================================

@njit(cache=True, fastmath=True)
def jacobian_slope(theta_x, theta_y):
    cx = np.cos(theta_x)
    cy = np.cos(theta_y)
    tx = np.tan(theta_x)
    ty = np.tan(theta_y)
    sec2x = 1.0 / (cx * cx)
    sec2y = 1.0 / (cy * cy)
    return (sec2x * sec2y) / np.power(1.0 + tx * tx + ty * ty, 1.5)


# ============================================================
# Gaussian random field for DEM perturbations (MC; CPU only)
# ============================================================

def _gaussian_random_field(shape, dx, dy, sigma, corr_len_m, rng):
    """
    Generate a Gaussian random field with optional Gaussian correlation.
    Falls back to white noise (no FFT) if corr_len_m is 0, None, or so small
    that the frequency response is ~1 over the entire resolvable band.
    """
    H, W = shape

    if sigma <= 0.0:
        return np.zeros(shape, dtype=float)

    if corr_len_m is None or corr_len_m <= 0.0:
        return rng.normal(0.0, sigma, size=shape)

    l2 = float(corr_len_m) ** 2
    kx_max = np.pi / float(dx)
    ky_max = np.pi / float(dy)
    Kmax2 = kx_max * kx_max + ky_max * ky_max

    delta = 1.0 - np.exp(-0.5 * l2 * Kmax2)
    if delta < 1e-6:
        return rng.normal(0.0, sigma, size=shape)

    wn = rng.normal(0.0, 1.0, size=shape)
    kx = 2.0 * np.pi * np.fft.fftfreq(W, d=dx)
    ky = 2.0 * np.pi * np.fft.fftfreq(H, d=dy)
    KX, KY = np.meshgrid(kx, ky, indexing="xy")
    K2 = KX * KX + KY * KY
    Hk = np.exp(-0.5 * l2 * K2)

    WN = np.fft.fft2(wn)
    F = WN * Hk
    field = np.fft.ifft2(F).real

    s = field.std()
    if s > 0.0:
        field *= (sigma / s)
    else:
        field = rng.normal(0.0, sigma, size=shape)

    return field


# ============================================================
# Binning utils
# ============================================================

def _jacobian_array(THX, THY):
    return jacobian_slope(THX, THY)


def _conservative_rebin_jacobian(THX_f, THY_f, Q_f, fine_step_mrad, coarse_step_mrad):
    r_exact = coarse_step_mrad / fine_step_mrad
    r = int(round(r_exact))
    if r <= 0:
        raise ValueError("coarse_step_mrad must be >= fine_step_mrad.")
    if abs(r_exact - r) > 1e-3:
        return None  # signal to use general path

    Hf, Wf = Q_f.shape
    Hy = (Hf // r) * r
    Wx = (Wf // r) * r

    trim_y = Hf - Hy
    trim_x = Wf - Wx
    top = trim_y // 2
    left = trim_x // 2
    bottom = Hf - (trim_y - top)
    right = Wf - (trim_x - left)

    THX_f_t = THX_f[top:bottom, left:right]
    THY_f_t = THY_f[top:bottom, left:right]
    Q_f_t = Q_f[top:bottom, left:right]
    J_f_t = _jacobian_array(THX_f_t, THY_f_t)

    Ny_c = THX_f_t.shape[0] // r
    Nx_c = THX_f_t.shape[1] // r

    def blockify(A):
        return A.reshape(Ny_c, r, Nx_c, r).transpose(0, 2, 1, 3)

    Q_blk = blockify(Q_f_t)
    J_blk = blockify(J_f_t)

    num = (Q_blk * J_blk).sum(axis=(2, 3))
    den = J_blk.sum(axis=(2, 3))
    Q_c = np.where(den > 0.0, num / den, 0.0)

    theta_x_f = THX_f[0, :]
    theta_y_f = THY_f[:, 0]
    theta_x_f_t = theta_x_f[left:right]
    theta_y_f_t = theta_y_f[top:bottom]
    dxf = (theta_x_f_t[1] - theta_x_f_t[0]) if theta_x_f_t.size > 1 else fine_step_mrad * 1e-3
    dyf = (theta_y_f_t[1] - theta_y_f_t[0]) if theta_y_f_t.size > 1 else fine_step_mrad * 1e-3

    theta_x_c = theta_x_f_t[0] + (np.arange(Nx_c) * r + 0.5 * (r - 1)) * dxf
    theta_y_c = theta_y_f_t[0] + (np.arange(Ny_c) * r + 0.5 * (r - 1)) * dyf
    THX_c, THY_c = np.meshgrid(theta_x_c, theta_y_c, indexing="xy")

    step = float(coarse_step_mrad) * 1e-3
    THX_c = np.round(THX_c / step) * step
    THY_c = np.round(THY_c / step) * step

    return THX_c, THY_c, Q_c


def _bin_results_by_jacobian_general(THX_rad, THY_rad, Q, result_step_mrad):
    step = float(result_step_mrad) * 1e-3  # rad

    x = THX_rad.ravel()
    y = THY_rad.ravel()
    J = _jacobian_array(THX_rad, THY_rad).ravel()
    Qf = Q.ravel()

    x_min, x_max = x.min(), x.max()
    y_min, y_max = y.min(), y.max()

    kx_min = int(np.ceil((x_min - 0.5 * step) / step))
    kx_max = int(np.floor((x_max + 0.5 * step) / step))
    ky_min = int(np.ceil((y_min - 0.5 * step) / step))
    ky_max = int(np.floor((y_max + 0.5 * step) / step))

    x_cent = (np.arange(kx_min, kx_max + 1, dtype=np.int64) * step).astype(np.float64)
    y_cent = (np.arange(ky_min, ky_max + 1, dtype=np.int64) * step).astype(np.float64)

    x_edges = np.concatenate([x_cent - 0.5 * step, [x_cent[-1] + 0.5 * step]])
    y_edges = np.concatenate([y_cent - 0.5 * step, [y_cent[-1] + 0.5 * step]])

    H_w = np.histogram2d(y, x, bins=[y_edges, x_edges], weights=J)[0]
    H_Qw = np.histogram2d(y, x, bins=[y_edges, x_edges], weights=J * Qf)[0]
    tiny = 1e-300
    Q_bin = H_Qw / np.maximum(H_w, tiny)

    THX_c, THY_c = np.meshgrid(x_cent, y_cent, indexing="xy")
    return THX_c, THY_c, Q_bin


def bin_results_jacobian(
    THX_rad, THY_rad, Q, fine_step_mrad, result_step_mrad,
    sigma=None, P=None
):
    """
    Returns coarse (THX, THY, Q, sigma?, P?), all in radians.
    Integer ratio → conservative block rebin; else → histogram2d.
    """
    out = _conservative_rebin_jacobian(THX_rad, THY_rad, Q, fine_step_mrad, result_step_mrad)
    if out is not None:
        THX_c, THY_c, Q_c = out
        sigma_c = None
        P_c = None
        if sigma is not None:
            s_out = _conservative_rebin_jacobian(
                THX_rad, THY_rad, sigma * sigma + Q * Q,
                fine_step_mrad, result_step_mrad
            )
            if s_out is not None:
                _, _, m2 = s_out
                var = np.maximum(m2 - Q_c * Q_c, 0.0)
                sigma_c = np.sqrt(var)
        if P is not None:
            p_out = _conservative_rebin_jacobian(
                THX_rad, THY_rad, P,
                fine_step_mrad, result_step_mrad
            )
            if p_out is not None:
                _, _, P_c = p_out
        return THX_c, THY_c, Q_c, sigma_c, P_c

    THX_c, THY_c, Q_c = _bin_results_by_jacobian_general(THX_rad, THY_rad, Q, result_step_mrad)
    sigma_c = None
    P_c = None
    if sigma is not None:
        _, _, m2 = _bin_results_by_jacobian_general(
            THX_rad, THY_rad, sigma * sigma + Q * Q,
            result_step_mrad
        )
        var = np.maximum(m2 - Q_c * Q_c, 0.0)
        sigma_c = np.sqrt(var)
    if P is not None:
        _, _, P_c = _bin_results_by_jacobian_general(
            THX_rad, THY_rad, P,
            result_step_mrad
        )
    return THX_c, THY_c, Q_c, sigma_c, P_c


# ============================================================
# Class wrapper
# ============================================================

class ThicknessMap:
    """
    Compute thickness maps from a regular DEM, with tilt+azimuths.

    Key idea: fine grid/results are immutable; coarse (binned) results
    are stored separately, so multiple compute_thickness() calls are safe.
    """

    def __init__(
        self,
        dem_path: str,
        angle_deg: float,
        angle_window_deg: float,
        fine_step_mrad: float,
        *,
        det_azimuth_deg: float = 0.0,
        dem_azimuth_deg: float = 0.0,
        flip_x: bool = False,
        flip_y: bool = False,
        s_max: float = 5000.0,
        eps_bisect: float = 0.02,
        max_bisect: int = 96,
        ds_coarse_scale: float = 0.1,
        log_level: int = logging.INFO,
    ):
        self.dem_path = str(dem_path)
        self.angle_deg = float(angle_deg)
        self.angle_window_deg = float(angle_window_deg)
        self.fine_step_mrad = float(fine_step_mrad)
        self.det_azimuth_deg = float(det_azimuth_deg)
        self.dem_azimuth_deg = float(dem_azimuth_deg)
        self.flip_x = bool(flip_x)
        self.flip_y = bool(flip_y)
        self.s_max = float(s_max)
        self.eps_bisect = float(eps_bisect)
        self.max_bisect = int(max_bisect)
        self.ds_coarse_scale = float(ds_coarse_scale)

        # radians/precompute
        self.theta0 = np.deg2rad(self.angle_deg)
        self.det_azimuth = np.deg2rad(self.det_azimuth_deg)
        self.dem_azimuth = np.deg2rad(self.dem_azimuth_deg)
        self._dem_cos = np.cos(self.dem_azimuth)
        self._dem_sin = np.sin(self.dem_azimuth)

        # DEM/grid
        self.Zg = None
        self.x0g = self.x1g = self.y0g = self.y1g = None
        self.dx = self.dy = None
        self.z0 = None
        self.THX_f = self.THY_f = None  # fine slope grid

        # fine results
        self.L = None
        self.sigmaL = None
        self.P = None

        # coarse (binned) results
        self.THX_c = None
        self.THY_c = None
        self.L_c = None
        self.sigmaL_c = None
        self.P_c = None
        self._result_step_mrad = None

        self._warned_cuda = False
        self.logger = logging.getLogger(_LOGGER_NAME)
        self.set_log_level(log_level)
        self._prof: Profiler | None = None

    # ----- logger control / profiler -----
    def set_log_level(self, level: int):
        self.logger.setLevel(level)

    def get_profile(self) -> Profiler | None:
        return self._prof

    def print_profile(self, title: str = "ThicknessMap run"):
        if self._prof is not None:
            print_profile(title, self._prof)

    # ---------------- DEM I/O ----------------
    def load_dem(self):
        t0 = time.perf_counter()
        dem = np.load(self.dem_path)["DEM"]
        Xr = dem[:, 0].copy()
        Yr = dem[:, 1].copy()
        Zr = dem[:, 2].copy()
        if self.flip_x:
            Xr = -Xr
        if self.flip_y:
            Yr = -Yr

        x_unique = np.unique(Xr)
        y_unique = np.unique(Yr)
        nx = x_unique.size
        ny = y_unique.size
        if nx * ny != Zr.size:
            raise ValueError("DEM points do not form a complete regular grid.")

        order = np.lexsort((Xr, Yr))
        Zg = Zr[order].reshape(ny, nx)

        self.x0g, self.y0g = x_unique[0], y_unique[0]
        self.x1g, self.y1g = x_unique[-1], y_unique[-1]
        self.dx = (self.x1g - self.x0g) / (nx - 1) if nx > 1 else 1.0
        self.dy = (self.y1g - self.y0g) / (ny - 1) if ny > 1 else 1.0

        if not (self.x0g <= 0.0 <= self.x1g and self.y0g <= 0.0 <= self.y1g):
            raise ValueError(
                f"Detector (0,0) outside DEM bounds: "
                f"X:[{self.x0g:.2f},{self.x1g:.2f}]  Y:[{self.y0g:.2f},{self.y1g:.2f}]"
            )

        self.z0 = bilinear_sample(Zg, self.x0g, self.y0g, self.dx, self.dy, 0.0, 0.0)
        self.Zg = Zg
        t1 = time.perf_counter()
        self.logger.info(
            f"DEM loaded: shape={Zg.shape}, dx={self.dx:.3f} m, dy={self.dy:.3f} m, "
            f"z0={self.z0:.3f} m ({t1 - t0:.2f}s)"
        )
        return self

    # ---------------- Grids ----------------
    def _make_centered_grid(self, step_mrad: float):
        half = int(np.floor(np.radians(self.angle_window_deg) * 1e3 / step_mrad))
        m = np.arange(-half, half + 1, dtype=np.float64) * step_mrad
        r = m * 1e-3  # radians
        THX, THY = np.meshgrid(r, r, indexing="xy")
        return THX, THY

    def build_fine_grid(self):
        if self.THX_f is not None and self.THY_f is not None:
            return self.THX_f, self.THY_f
        t0 = time.perf_counter()
        self.THX_f, self.THY_f = self._make_centered_grid(self.fine_step_mrad)
        t1 = time.perf_counter()
        self.logger.info(
            f"Slope grid built: shape={self.THX_f.shape}, "
            f"step={self.fine_step_mrad:.3f} mrad ({t1 - t0:.2f}s)"
        )
        return self.THX_f, self.THY_f

    # ---------------- Compute (CPU/GPU + optional MC) ----------------
    def compute_thickness(
        self,
        *,
        calculate_sigma: bool = False,
        accelerator: str = "cpu",
        sigmaZ_m: float = 3.0,
        mc_samples: int = 64,
        mc_corr_len_m: float | None = 40.0,
        mc_corr: float | None = None,
        mc_seed: int | None = 123,
        show_progress: bool = True,
        gpu_block: tuple[int, int] = (16, 16),
        profile: bool = False,
        return_profile: bool = False,
        result_step_mrad: float | None = None,
        profiler: Profiler | None = None,
    ):
        """
        - calculate_sigma=False: computes fine-grid L only
        - calculate_sigma=True:  MC (E[L], σ[L], P(hit)) on fine grid
        - result_step_mrad: optional Jacobian-weighted binning to coarse grid
        - profiler: optional shared Profiler instance; if None, a fresh one is used
        """
        # reset profiler & (coarse) outputs for this run
        self._prof = profiler if profiler is not None else Profiler()
        prof = self._prof
        self.THX_c = self.THY_c = self.L_c = self.sigmaL_c = self.P_c = None
        self._result_step_mrad = None

        with prof.section("io:ensure_dem"):
            if self.Zg is None:
                with prof.section("io:load_dem"):
                    self.load_dem()
        with prof.section("grid:ensure"):
            if self.THX_f is None:
                with prof.section("grid:build_fine"):
                    self.build_fine_grid()

        use_gpu = (accelerator.lower() == "gpu") and _CUDA_OK
        if (accelerator.lower() == "gpu") and not _CUDA_OK and (not self._warned_cuda):
            self.logger.warning("CUDA not available; falling back to CPU.")
            self._warned_cuda = True

        ds_coarse = self.ds_coarse_scale * min(self.dx, self.dy)
        self.logger.debug(f"ds_coarse={ds_coarse:.3f} m, s_max={self.s_max:.1f} m")

        def _compute_L(Z):
            if use_gpu:
                with prof.section("gpu:thickness_kernel"):
                    return self._compute_L_gpu(Z, ds_coarse, gpu_block)
            else:
                with prof.section("cpu:thickness"):
                    return compute_thickness_map_rotated_cpu(
                        Z, self.x0g, self.y0g, self.dx, self.dy, self.z0,
                        self.theta0, self.det_azimuth,
                        self._dem_cos, self._dem_sin,
                        self.THX_f, self.THY_f,
                        self.s_max, ds_coarse, self.eps_bisect, self.max_bisect,
                        self.x0g, self.x1g, self.y0g, self.y1g
                    )

        mode = "GPU (CUDA)" if use_gpu else "CPU"

        if not calculate_sigma:
            self.logger.info(f"Compute L only on {mode} …")
            t0 = time.perf_counter()
            self.L = _compute_L(self.Zg)
            t1 = time.perf_counter()
            self.logger.info(f"Done: L computed in {t1 - t0:.2f}s")
            self.sigmaL = None
            self.P = None
        else:
            corr_len = float(
                mc_corr_len_m if mc_corr_len_m is not None
                else (mc_corr if mc_corr is not None else 0.0)
            )
            self.logger.info(
                f"Compute MC on {mode}: sigmaZ={sigmaZ_m} m, "
                f"samples={mc_samples}, corr_len={corr_len} m"
            )
            rng = np.random.default_rng(mc_seed)
            H, W = self.THX_f.shape
            mean = np.zeros((H, W), dtype=np.float64)
            m2 = np.zeros((H, W), dtype=np.float64)
            hits = np.zeros((H, W), dtype=np.int64)
            iterator = tqdm(
                range(mc_samples),
                desc="Monte-Carlo DEM",
                unit="realization",
            ) if show_progress else range(mc_samples)
            t0_all = time.perf_counter()
            for m in iterator:
                with prof.section("mc:noise_gen"):
                    dZ = _gaussian_random_field(
                        self.Zg.shape, self.dx, self.dy,
                        sigmaZ_m, corr_len, rng
                    )
                    Zm = self.Zg + dZ
                with prof.section("mc:thickness"):
                    Lm = _compute_L(Zm)
                with prof.section("mc:accumulate"):
                    hits += (Lm > 0.0)
                    delta = Lm - mean
                    mean += delta / (m + 1)
                    m2 += delta * (Lm - mean)
            t1_all = time.perf_counter()
            with prof.section("mc:finalize"):
                var = m2 / max(mc_samples - 1, 1)
                std = np.sqrt(np.maximum(var, 0.0))
                p_hit = hits.astype(np.float64) / mc_samples
            self.L = mean
            self.sigmaL = std
            self.P = p_hit
            self.logger.info(f"Done: MC (samples={mc_samples}) in {t1_all - t0_all:.2f}s")

        # ---- Optional: bin fine result to coarse grid (Jacobian-weighted)
        if result_step_mrad is not None and result_step_mrad > 0.0:
            self.logger.info(
                f"Binning fine result → coarse grid: "
                f"step={result_step_mrad:.3f} mrad (Jacobian-weighted)"
            )
            t_bin0 = time.perf_counter()
            THX_c, THY_c, L_c, s_c, P_c = bin_results_jacobian(
                self.THX_f, self.THY_f, self.L,
                self.fine_step_mrad, result_step_mrad,
                sigma=self.sigmaL, P=self.P
            )
            self.THX_c, self.THY_c = THX_c, THY_c
            self.L_c = L_c
            self.sigmaL_c = s_c
            self.P_c = P_c
            self._result_step_mrad = float(result_step_mrad)
            t_bin1 = time.perf_counter()
            if self._prof is not None:
                self._prof.add("post:bin_by_jacobian", (t_bin1 - t_bin0))
            self.logger.info(
                f"Done binning in {t_bin1 - t_bin0:.2f}s; "
                f"coarse shape={self.L_c.shape}"
            )

        if profile:
            self.print_profile("Thickness" + ("" if not calculate_sigma else " (Monte-Carlo)"))
        if return_profile:
            return self, prof
        return self

    def _compute_L_gpu(self, Z_host, ds_coarse, gpu_block):
        if not _CUDA_OK:
            raise RuntimeError("CUDA not available.")
        from numba import cuda
        with self._prof.section("gpu:HtoD"):
            Z_d = cuda.to_device(np.asarray(Z_host, dtype=np.float64))
            THX_d = cuda.to_device(np.asarray(self.THX_f, dtype=np.float64))
            THY_d = cuda.to_device(np.asarray(self.THY_f, dtype=np.float64))
            L_d = cuda.device_array(THX_d.shape, dtype=np.float64)
        H, W = THX_d.shape
        by, bx = gpu_block
        grid = ((H + by - 1) // by, (W + bx - 1) // bx)
        self.logger.info(f"Running on GPU (CUDA): grid={grid}, block={(by, bx)}")
        t0 = time.perf_counter()
        with self._prof.section("gpu:kernel"):
            compute_thickness_map_rotated_gpu[grid, (by, bx)](
                Z_d,
                np.float64(self.x0g), np.float64(self.y0g),
                np.float64(self.dx), np.float64(self.dy),
                np.float64(self.z0),
                np.float64(self.theta0), np.float64(self.det_azimuth),
                np.float64(self._dem_cos), np.float64(self._dem_sin),
                THX_d, THY_d,
                np.float64(self.s_max), np.float64(ds_coarse),
                np.float64(self.eps_bisect), np.int32(self.max_bisect),
                np.float64(self.x0g), np.float64(self.x1g),
                np.float64(self.y0g), np.float64(self.y1g),
                L_d
            )
            cuda.synchronize()
        t1 = time.perf_counter()
        self.logger.info(f"GPU kernel finished in {t1 - t0:.2f}s")
        with self._prof.section("gpu:DtoH"):
            out = L_d.copy_to_host()
        return out

    # ---------------- Orientation helpers ----------------
    @staticmethod
    def orient_xy(THX, THY, Z, *, transpose=False, flip_axis=None):
        X = THX
        Y = THY
        W = Z
        if transpose:
            X = X.T
            Y = Y.T
            W = W.T if W.ndim == 2 else W.transpose(0, 2, 1)
        if flip_axis is not None:
            if flip_axis == 0:
                X = X[::-1, :]
                Y = Y[::-1, :]
                W = W[::-1, :] if W.ndim == 2 else W[:, ::-1, :]
            elif flip_axis == 1:
                X = X[:, ::-1]
                Y = Y[:, ::-1]
                W = W[:, ::-1] if W.ndim == 2 else W[:, :, ::-1]
        return X, Y, W

    # ---------------- Helpers to pick fine/coarse ----------------
    def _current_arrays(self):
        """
        Prefer coarse if available; else fine. Returns (THX, THY, L, sigma?, P?, is_coarse).
        """
        if self.L_c is not None:
            return self.THX_c, self.THY_c, self.L_c, self.sigmaL_c, self.P_c, True
        return self.THX_f, self.THY_f, self.L, self.sigmaL, self.P, False

    # ---------------- Export ----------------
    def export_npz(self, out_path: str, *, export_order: str = "xy", extra_meta: dict | None = None):
        if self.L is None:
            raise RuntimeError("No results to export. Call compute_thickness() first.")
        t0 = time.perf_counter()

        THX_use, THY_use, L_use, s_use, P_use, is_coarse = self._current_arrays()
        THX_o, THY_o, L_o = self.orient_xy(
            THX_use, THY_use, L_use,
            transpose=True, flip_axis=1
        )
        payload = dict(
            THX_rad=THX_o,
            THY_rad=THY_o,
            THX_mrad=(THX_o * 1e3),
            THY_mrad=(THY_o * 1e3),
            L=L_o,
        )
        if s_use is not None:
            _, _, s_o = self.orient_xy(
                THX_use, THY_use, s_use,
                transpose=True, flip_axis=1
            )
            payload["sigmaL"] = s_o
        if P_use is not None:
            _, _, P_o = self.orient_xy(
                THX_use, THY_use, P_use,
                transpose=True, flip_axis=1
            )
            payload["P"] = P_o

        ds_coarse = self.ds_coarse_scale * min(self.dx, self.dy)
        meta = dict(
            angle_deg=float(self.angle_deg),
            det_azimuth_deg=float(self.det_azimuth_deg),
            dem_azimuth_deg=float(self.dem_azimuth_deg),
            window_deg=float(self.angle_window_deg),
            fine_mrad_step=float(self.fine_step_mrad),
            result_mrad_step=(
                None if self._result_step_mrad is None
                else float(self._result_step_mrad)
            ),
            s_max=float(self.s_max),
            ds_coarse=float(ds_coarse),
            eps_bisect=float(self.eps_bisect),
            max_bisect=int(self.max_bisect),
            dem_bounds=(float(self.x0g), float(self.x1g), float(self.y0g), float(self.y1g)),
            z0=float(self.z0),
            export_order=str(export_order),
            flips=dict(flip_x=bool(self.flip_x), flip_y=bool(self.flip_y)),
            downsample=(
                "jacobian_weighted_rebin"
                + (
                    " (integer-block)"
                    if is_coarse
                    and self._result_step_mrad
                    and abs(
                        (self._result_step_mrad / self.fine_step_mrad)
                        - round(self._result_step_mrad / self.fine_step_mrad)
                    ) < 1e-3
                    else " (general or none)"
                )
            ),
        )
        if extra_meta:
            meta.update(extra_meta)
        payload["meta"] = meta

        np.savez(out_path, **payload)
        t1 = time.perf_counter()
        self.logger.info(f"Saved NPZ → {out_path} ({t1 - t0:.2f}s)")
        if self._prof is not None:
            self._prof.add("io:export_npz", (t1 - t0))
        return out_path

    # ---------------- Plot (quick-look) ----------------
    def plot(self, *, show=True):
        if self.L is None:
            raise RuntimeError("Nothing to plot. Call compute_thickness() first.")
        import matplotlib.pyplot as plt
        t0 = time.perf_counter()
        THX_use, THY_use, L_use, s_use, P_use, _ = self._current_arrays()
        THX_o, THY_o, L_o = self.orient_xy(
            THX_use, THY_use, L_use,
            transpose=True, flip_axis=1
        )
        self.logger.info("Plotting results…")
        plt.figure()
        im = plt.imshow(L_o.T, aspect="equal")
        plt.colorbar(im, label="L (m)" if s_use is None else "E[L] (m)")
        plt.xlabel("Theta X (mrad)")
        plt.ylabel("Theta Y (mrad)")
        plt.title("Thickness" + ("" if s_use is None else " (MC mean)"))

        if s_use is not None:
            _, _, sL_o = self.orient_xy(
                THX_use, THY_use, s_use,
                transpose=True, flip_axis=1
            )
            plt.figure()
            im = plt.imshow(sL_o.T, aspect="equal")
            plt.colorbar(im, label="σ_L (m)")
            plt.xlabel("Theta X (mrad)")
            plt.ylabel("Theta Y (mrad)")
            plt.title("Thickness uncertainty (MC)")

        if P_use is not None:
            _, _, P_o = self.orient_xy(
                THX_use, THY_use, P_use,
                transpose=True, flip_axis=1
            )
            plt.figure()
            im = plt.imshow(P_o.T, aspect="equal", vmin=0, vmax=1)
            plt.colorbar(im, label="P(hit)")
            plt.xlabel("Theta X (mrad)")
            plt.ylabel("Theta Y (mrad)")
            plt.title("Hit probability (MC)")

        plt.tight_layout()
        if show:
            plt.show()
        t1 = time.perf_counter()
        if self._prof is not None:
            self._prof.add("viz:plot", (t1 - t0))


