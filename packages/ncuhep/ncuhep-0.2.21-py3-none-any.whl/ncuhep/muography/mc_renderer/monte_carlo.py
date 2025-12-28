"""
Monte Carlo basis generator for a planar muon telescope.

This module lives under ``muography.mc_renderer`` and provides a
``MonteCarloRenderer`` class that can drive either a CPU or multi-GPU
simulation, using the detector geometry from :class:`PlaneDetector`
and the profiling helpers in :mod:`muography.profiler`.
"""

import importlib
import math
import numpy as np

from numba import njit, prange
from numba import cuda, float32  # type: ignore
from numba.cuda.cudadrv.error import CudaSupportError

_CUPY_SPEC = importlib.util.find_spec("cupy")
if _CUPY_SPEC is not None:  # optional: only needed for GPU mode
    import cupy as cp  # type: ignore
else:  # pragma: no cover
    cp = None  # type: ignore

from ..classes import PlaneDetector
from ..utils.coordinates import det2earth, earth2det, cart2projection
from ..utils.tracking import track_reconstruction
from ..utils.flux import geometric_factor
from ..profiler import Profiler, print_profile, time_block


def _cuda_is_available() -> bool:
    try:
        return cuda.is_available()
    except CudaSupportError:
        return False


# ---------------------------------------------------------------------------
# GPU helpers (simulation)
# ---------------------------------------------------------------------------

MAX_LAYERS = 8  # must be >= number of detector layers


@cuda.jit(device=True)
def det2earth_device(x, y, z, zenith_rad, azimuth_rad):
    """
    Device version of :func:`det2earth`.

    Parameters
    ----------
    x, y, z : float32
        Coordinates in the detector frame (mm).
    zenith_rad, azimuth_rad : float32
        Boresight orientation in radians.

    Returns
    -------
    x_e, y_e, z_e : float32
        Coordinates in the Earth frame (mm).
    """
    ca = math.cos(azimuth_rad)
    sa = math.sin(azimuth_rad)
    cz = math.cos(zenith_rad)
    sz = math.sin(zenith_rad)

    x_e = ca * x - sa * cz * y - sa * sz * z
    y_e = sa * x + ca * cz * y + ca * sz * z
    z_e = -sz * y + cz * z
    return x_e, y_e, z_e


@cuda.jit(fastmath=True)
def simulate_events_kernel(
    layer_z,
    layer_half_length_x,
    layer_half_length_y,
    pixel_length_x,
    pixel_length_y,
    zenith_boresight_rad,
    azimuth_boresight_rad,
    x_pp_arr,
    y_pp_arr,
    cos_theta_arr,
    phi_arr,
    all_hits,
    valid_flags,
):
    """
    One thread = one Monte Carlo event.

    Writes, for event ``i``:

    * all_hits[i, 0] = incident theta_x (Earth frame, radians)
    * all_hits[i, 1] = incident theta_y (Earth frame, radians)
    * all_hits[i, 2] = reconstructed theta_x (detector frame)
    * all_hits[i, 3] = reconstructed theta_y (detector frame)
    * valid_flags[i] = 1 if the track hits all layers, else 0

    This version:
      - avoids early return inside the layer loop
      - avoids per-layer local arrays
      - computes LSQ slopes in one pass
    """
    i = cuda.grid(1)
    n_events = cos_theta_arr.shape[0]
    if i >= n_events:
        return

    # default: invalid
    valid_flags[i] = 0
    hit_all_layers = 1  # 1 = valid, 0 = missed at least one layer

    # --- direction sampling (already randomised on host / CuPy) ---
    cos_theta = cos_theta_arr[i]
    if cos_theta > 1.0:
        cos_theta = 1.0
    if cos_theta < -1.0:
        cos_theta = -1.0

    theta = math.acos(cos_theta)
    phi = phi_arr[i]

    s_t = math.sin(theta)
    c_t = math.cos(theta)
    s_p = math.sin(phi)
    c_p = math.cos(phi)

    # Direction in detector frame
    x_dir_det = s_t * -s_p
    y_dir_det = s_t * c_p
    z_dir_det = c_t

    # Start position in detector frame
    x_pos_det = x_pp_arr[i]
    y_pos_det = y_pp_arr[i]
    z_pos_det = 0.0

    # ---- propagate through layers in detector frame ----
    n_layers = layer_z.shape[0]
    if n_layers > MAX_LAYERS:
        # Safety guard; uniform bailout
        return

    theta_x = math.atan2(x_dir_det, z_dir_det)
    theta_y = math.atan2(y_dir_det, z_dir_det)
    tan_tx = math.tan(theta_x)
    tan_ty = math.tan(theta_y)

    inv_pixel_length_x = 1.0 / pixel_length_x
    inv_pixel_length_y = 1.0 / pixel_length_y

    # LSQ accumulators in pixelised coordinates
    sum_x = 0.0
    sum_y = 0.0
    sum_z = 0.0
    sum_zz = 0.0
    sum_zx = 0.0
    sum_zy = 0.0

    for k in range(n_layers):
        layerz = layer_z[k]

        dz = layerz - z_pos_det
        x_hit = x_pos_det + dz * tan_tx
        y_hit = y_pos_det + dz * tan_ty

        # geometric bounds check
        if (
            math.fabs(x_hit) > layer_half_length_x[k]
            or math.fabs(y_hit) > layer_half_length_y[k]
        ):
            hit_all_layers = 0

        # Pixelisation (still done; invalid events are masked later)
        ix = math.floor(x_hit * inv_pixel_length_x)
        iy = math.floor(y_hit * inv_pixel_length_y)

        x_hit_pix = (ix + 0.5) * pixel_length_x
        y_hit_pix = (iy + 0.5) * pixel_length_y

        # accumulate for LSQ
        sum_x += x_hit_pix
        sum_y += y_hit_pix
        sum_z += layerz
        sum_zz += layerz * layerz
        sum_zx += layerz * x_hit_pix
        sum_zy += layerz * y_hit_pix

    # ---- straight-line reconstruction in detector frame ----
    invN = 1.0 / n_layers
    mean_z = sum_z * invN
    mean_x = sum_x * invN
    mean_y = sum_y * invN

    # N * Var(z) = Σz^2 - N*mean_z^2 = Σz^2 - sum_z*mean_z
    denom = sum_zz - sum_z * mean_z
    if denom != 0.0:
        # N * Cov(z,x) = Σ(zx) - N*mean_z*mean_x = Σ(zx) - sum_z*mean_x
        num_x = sum_zx - sum_z * mean_x
        num_y = sum_zy - sum_z * mean_y
        m_x = num_x / denom
        m_y = num_y / denom
    else:
        m_x = 0.0
        m_y = 0.0

    theta_x_rec = math.atan(m_x)
    theta_y_rec = math.atan(m_y)

    # ---- incident angles in Earth frame ----
    x_dir_earth, y_dir_earth, z_dir_earth = det2earth_device(
        x_dir_det, y_dir_det, z_dir_det,
        zenith_boresight_rad, azimuth_boresight_rad
    )

    theta_x_inc = math.atan2(x_dir_earth, z_dir_earth)
    theta_y_inc = math.atan2(y_dir_earth, z_dir_earth)

    # ---- store results only if the track hit all layers ----
    if hit_all_layers == 1:
        all_hits[i, 0] = theta_x_inc
        all_hits[i, 1] = theta_y_inc
        all_hits[i, 2] = theta_x_rec
        all_hits[i, 3] = theta_y_rec
        valid_flags[i] = 1


def _run_simulation_gpu(
    n_events,
    layer_z,
    pixel_length_x,
    pixel_length_y,
    layer_half_length_x,
    layer_half_length_y,
    zenith_boresight_deg,
    azimuth_boresight_deg,
    theta_max_deg,
    simulation_half_length_x,
    simulation_half_length_y,
    device_ids,
):
    """
    Multi-GPU implementation of the track simulation.

    Parameters
    ----------
    n_events : int
        Total number of generated events across all GPUs.
    device_ids : list of int or None
        List of CUDA device IDs to use. If ``None`` or empty, defaults
        to ``[0]``.

    Returns
    -------
    hits : ndarray, shape (N_valid, 4)
        For each accepted event:
        (theta_x_incident, theta_y_incident,
         theta_x_reco, theta_y_reco), in radians.
    """
    if cp is None:
        raise RuntimeError(
            "CuPy is not available. Install cupy or run with use_gpu=False."
        )
    if not _cuda_is_available():
        raise RuntimeError(
            "Numba CUDA is not available. Set use_gpu=False to run on CPU."
        )

    if device_ids is None or len(device_ids) == 0:
        device_ids = [0]

    # Host-side static geometry as float32
    layer_z_f32_host = layer_z.astype(np.float32)
    layer_half_x_f32_host = layer_half_length_x.astype(np.float32)
    layer_half_y_f32_host = layer_half_length_y.astype(np.float32)

    theta_max_rad = np.float32(np.radians(theta_max_deg))
    cos_min = float(np.cos(theta_max_rad))
    pixel_length_x_f32 = np.float32(pixel_length_x)
    pixel_length_y_f32 = np.float32(pixel_length_y)
    zenith_boresight_rad = np.float32(np.radians(zenith_boresight_deg))
    azimuth_boresight_rad = np.float32(np.radians(azimuth_boresight_deg))

    # Split events evenly across GPUs
    n_dev = len(device_ids)
    base = n_events // n_dev
    rem = n_events % n_dev

    tasks = []  # (dev_id, all_hits_dev, valid_flags_dev)

    # Launch kernels on all GPUs (asynchronously)
    for idx, dev_id in enumerate(device_ids):
        n_i = base + (1 if idx < rem else 0)
        if n_i <= 0:
            continue

        with cp.cuda.Device(dev_id):
            cuda.select_device(dev_id)

            layer_z_f32 = cp.asarray(layer_z_f32_host)
            layer_half_x_f32 = cp.asarray(layer_half_x_f32_host)
            layer_half_y_f32 = cp.asarray(layer_half_y_f32_host)

            cos_theta = cp.random.uniform(
                low=cos_min,
                high=1.0,
                size=n_i,
                dtype=cp.float32,
            )
            phi = cp.random.uniform(
                low=0.0,
                high=2.0 * np.pi,
                size=n_i,
                dtype=cp.float32,
            )
            x_pp = cp.random.uniform(
                low=-simulation_half_length_x,
                high=simulation_half_length_x,
                size=n_i,
                dtype=cp.float32,
            )
            y_pp = cp.random.uniform(
                low=-simulation_half_length_y,
                high=simulation_half_length_y,
                size=n_i,
                dtype=cp.float32,
            )

            all_hits_dev = cp.empty((n_i, 4), dtype=cp.float32)
            valid_flags_dev = cp.empty(n_i, dtype=cp.int8)

            threads_per_block = 128
            blocks_per_grid = (n_i + threads_per_block - 1) // threads_per_block

            simulate_events_kernel[blocks_per_grid, threads_per_block](
                layer_z_f32,
                layer_half_x_f32,
                layer_half_y_f32,
                pixel_length_x_f32,
                pixel_length_y_f32,
                zenith_boresight_rad,
                azimuth_boresight_rad,
                x_pp,
                y_pp,
                cos_theta,
                phi,
                all_hits_dev,
                valid_flags_dev,
            )

            tasks.append((dev_id, all_hits_dev, valid_flags_dev))

    # Gather results back to host (synchronising per device)
    hits_list = []
    for dev_id, all_hits_dev, valid_flags_dev in tasks:
        with cp.cuda.Device(dev_id):
            cuda.select_device(dev_id)
            cuda.synchronize()
            all_hits = cp.asnumpy(all_hits_dev)
            valid_flags = cp.asnumpy(valid_flags_dev).astype(bool)

        hits_list.append(all_hits[valid_flags].astype(np.float64))

    if len(hits_list) == 0:
        return np.empty((0, 4), dtype=np.float64)

    return np.vstack(hits_list)


# ---------------------------------------------------------------------------
# CPU simulation (Numba)
# ---------------------------------------------------------------------------

@njit(fastmath=True)
def _homogenous_generator(theta_max_rad,
                          zenith_boresight_rad,
                          azimuth_boresight_rad,
                          simulation_half_length_x,
                          simulation_half_length_y):
    theta = np.arccos(
        np.random.uniform(np.cos(theta_max_rad), 1.0)
    )
    phi = np.random.uniform(0.0, 2.0 * np.pi)

    x_pp = np.random.uniform(-simulation_half_length_x, simulation_half_length_x)
    y_pp = np.random.uniform(-simulation_half_length_y, simulation_half_length_y)
    z_pp = 0.0

    x_dir_det = np.sin(theta) * -np.sin(phi)
    y_dir_det = np.sin(theta) * np.cos(phi)
    z_dir_det = np.cos(theta)

    x_pos_det = 0.0
    y_pos_det = 0.0
    z_pos_det = 0.0

    x_pp, y_pp, z_pp = det2earth(
        x_pp,
        y_pp,
        z_pp,
        zenith_boresight_rad,
        azimuth_boresight_rad,
    )

    x_pos_det += x_pp
    y_pos_det += y_pp
    z_pos_det += z_pp

    x_dir_earth, y_dir_earth, z_dir_earth = det2earth(
        x_dir_det,
        y_dir_det,
        z_dir_det,
        zenith_boresight_rad,
        azimuth_boresight_rad,
    )
    x_pos_earth, y_pos_earth, z_pos_earth = det2earth(
        x_pos_det,
        y_pos_det,
        z_pos_det,
        zenith_boresight_rad,
        azimuth_boresight_rad,
    )

    return x_pos_earth, y_pos_earth, z_pos_earth, x_dir_earth, y_dir_earth, z_dir_earth


@njit(fastmath=True)
def _detection_simulation(layer_z,
                          pixel_length_x,
                          pixel_length_y,
                          layer_half_length_x,
                          layer_half_length_y,
                          zenith_boresight_rad,
                          azimuth_boresight_rad,
                          x_pos_earth,
                          y_pos_earth,
                          z_pos_earth,
                          x_dir_earth,
                          y_dir_earth,
                          z_dir_earth,
                          mode=0):

    hits = np.zeros((len(layer_z), 3), dtype=np.float64)

    particle_dir_det = earth2det(
        x_dir_earth,
        y_dir_earth,
        z_dir_earth,
        zenith_boresight_rad,
        azimuth_boresight_rad,
    )
    particle_pos_det = earth2det(
        x_pos_earth,
        y_pos_earth,
        z_pos_earth,
        zenith_boresight_rad,
        azimuth_boresight_rad,
    )

    theta_x = np.arctan2(particle_dir_det[0], particle_dir_det[2])
    theta_y = np.arctan2(particle_dir_det[1], particle_dir_det[2])

    tan_theta_x = np.tan(theta_x)
    tan_theta_y = np.tan(theta_y)

    for i in range(len(layer_z)):
        hits[i, 0] = particle_pos_det[0] + (layer_z[i] - particle_pos_det[2]) * tan_theta_x
        hits[i, 1] = particle_pos_det[1] + (layer_z[i] - particle_pos_det[2]) * tan_theta_y
        hits[i, 2] = layer_z[i]

        if (np.abs(hits[i, 0]) > layer_half_length_x[i] or
                np.abs(hits[i, 1]) > layer_half_length_y[i]):
            return hits, False

        hits[i, 0] = (
            np.floor(hits[i, 0] / pixel_length_x)
            * pixel_length_x + pixel_length_x / 2.0
        )
        hits[i, 1] = (
            np.floor(hits[i, 1] / pixel_length_y)
            * pixel_length_y + pixel_length_y / 2.0
        )

    if mode == 0:
        pass
    elif mode == 1:
        hits[:, 0] += pixel_length_x / 2.0
        hits[:, 1] += pixel_length_y / 2.0
    else:
        raise ValueError("mode must be 0 or 1")

    return hits, True


@njit(parallel=True, fastmath=True)
def _run_simulation_cpu(n_events,
                        layer_z,
                        pixel_length_x,
                        pixel_length_y,
                        layer_half_length_x,
                        layer_half_length_y,
                        zenith_boresight_rad,
                        azimuth_boresight_rad,
                        theta_max_rad,
                        simulation_half_length_x,
                        simulation_half_length_y):
    all_hits = np.empty((n_events, 4), dtype=np.float64)
    valid_hits = np.zeros(n_events, dtype=np.bool_)

    for i in prange(n_events):
        (
            x_pos_earth, y_pos_earth, z_pos_earth,
            x_dir_earth, y_dir_earth, z_dir_earth,
        ) = _homogenous_generator(
            theta_max_rad,
            zenith_boresight_rad,
            azimuth_boresight_rad,
            simulation_half_length_x,
            simulation_half_length_y,
        )
        hits, ok = _detection_simulation(
            layer_z,
            pixel_length_x,
            pixel_length_y,
            layer_half_length_x,
            layer_half_length_y,
            zenith_boresight_rad,
            azimuth_boresight_rad,
            x_pos_earth,
            y_pos_earth,
            z_pos_earth,
            x_dir_earth,
            y_dir_earth,
            z_dir_earth,
            mode=1,
        )

        if ok:
            c_x, c_y, theta_x, theta_y = track_reconstruction(hits)
            _, theta_x_incident, theta_y_incident = cart2projection(
                x_dir_earth, y_dir_earth, z_dir_earth,
            )
            all_hits[i, 0] = theta_x_incident
            all_hits[i, 1] = theta_y_incident
            all_hits[i, 2] = theta_x
            all_hits[i, 3] = theta_y
            valid_hits[i] = True

    return all_hits[valid_hits]


# ---------------------------------------------------------------------------
# Basis construction (CPU, Numba)
# ---------------------------------------------------------------------------

@njit(cache=True, fastmath=True)
def _chunked_unique_rounded(arr, resolution_mrad, chunk_size=10000):
    """
    Compute unique rounded values in chunks, to reduce peak memory.

    Parameters
    ----------
    arr : ndarray
        Input array of angles (radians).
    resolution_mrad : float
        Target rounding resolution in mrad (e.g. 0.1, 0.2, 0.5, 1.0).
    chunk_size : int
        Chunk size for processing.

    Returns
    -------
    unique : ndarray
        Sorted unique values after rounding (in mrad, not radians).
    """
    # Clamp to something reasonable
    if resolution_mrad <= 0.0:
        resolution_mrad = 0.1

    # Integer factor: how many bins per mrad
    factor_int = int(np.round(1.0 / resolution_mrad))
    if factor_int < 1:
        factor_int = 1
    inv_res = float(factor_int)  # bins per mrad
    res_mrad_effective = 1.0 / inv_res

    n = arr.shape[0]
    total_uniques = np.empty(n, dtype=np.float64)
    total_count = 0

    for i in range(0, n, chunk_size):
        chunk = arr[i:i + chunk_size]
        # Convert radians -> mrad
        chunk_mrad = chunk * 1000.0

        # Quantise to multiples of res_mrad_effective
        # q = round(mrad / res) * res
        q = np.round(chunk_mrad * inv_res) / inv_res

        uniques = np.unique(q)
        count = uniques.shape[0]
        total_uniques[total_count:total_count + count] = uniques
        total_count += count

    all_uniques = total_uniques[:total_count]
    final_unique = np.unique(all_uniques)
    return final_unique


def _init_basis_from_hits(hits,
                          angle_deg=25.0,
                          resolution_mrad=1.0,
                          measured_resolution_mrad=0.1):
    """
    One-time initialisation of the basis grids and lookup tables.

    Parameters
    ----------
    hits : ndarray, shape (N, 4)
        First batch of Monte Carlo hits.
    angle_deg : float
        Half-width of the incident-angle grid (in degrees).
        The grid is constructed in mrad: [-mrad_max, +mrad_max]
        in steps of ``resolution_mrad``.
    resolution_mrad : float
        Incident-angle bin size for the basis (in mrad).
    measured_resolution_mrad : float
        Rounding / bin size for measured angles (in mrad).

    Returns
    -------
    basis : ndarray (Nx, Ny, Nthx, Nthy)
    unique_theta_x, unique_theta_y : 1D ndarrays (measured angles, mrad)
    theta_x_mrad, theta_y_mrad : 1D int32 ndarrays (incident angles, mrad)
    ref_x, ref_y : 1D int32 lookup arrays
    """
    # Clamp resolutions to sane values
    if resolution_mrad <= 0.0:
        resolution_mrad = 1.0
    if measured_resolution_mrad <= 0.0:
        measured_resolution_mrad = 0.1

    # -- measured angles: unique values at measured_resolution_mrad --
    unique_theta_x = _chunked_unique_rounded(
        hits[:, 2],
        measured_resolution_mrad,
        chunk_size=10000,
    )
    unique_theta_y = _chunked_unique_rounded(
        hits[:, 3],
        measured_resolution_mrad,
        chunk_size=10000,
    )

    # -- incident angle grid in mrad --
    angle_max_mrad = np.radians(angle_deg) * 1000.0
    mrad_max_int = int(np.round(angle_max_mrad))

    # Incident resolution in integer mrad (>= 1)
    step_inc_int = int(np.round(resolution_mrad))
    if step_inc_int < 1:
        step_inc_int = 1

    theta_x_mrad = np.arange(-mrad_max_int, mrad_max_int + 1,
                             step_inc_int, dtype=np.int32)
    theta_y_mrad = np.arange(-mrad_max_int, mrad_max_int + 1,
                             step_inc_int, dtype=np.int32)

    # Measured-angle indexing factor (how many bins per mrad)
    meas_factor_int = int(np.round(1.0 / measured_resolution_mrad))
    if meas_factor_int < 1:
        meas_factor_int = 1

    # Lookup tables index range for measured angles
    # coverage: [-mrad_max_int, +mrad_max_int] in steps of measured_resolution_mrad
    Lx = 2 * mrad_max_int * meas_factor_int + 1
    Ly = 2 * mrad_max_int * meas_factor_int + 1
    ref_x = np.full(Lx, -1, dtype=np.int32)
    ref_y = np.full(Ly, -1, dtype=np.int32)

    # Build lookup: int(val * meas_factor_int) -> index in unique_theta_*
    for idx, val in enumerate(unique_theta_x):
        raw = int(val * meas_factor_int)
        if raw < 0:
            raw += Lx
        if 0 <= raw < Lx:
            ref_x[raw] = idx

    for idx, val in enumerate(unique_theta_y):
        raw = int(val * meas_factor_int)
        if raw < 0:
            raw += Ly
        if 0 <= raw < Ly:
            ref_y[raw] = idx

    basis = np.zeros(
        (
            unique_theta_x.shape[0],
            unique_theta_y.shape[0],
            theta_x_mrad.shape[0],
            theta_y_mrad.shape[0],
        ),
        dtype=np.int32,
    )

    return basis, unique_theta_x, unique_theta_y, theta_x_mrad, theta_y_mrad, ref_x, ref_y


@njit(parallel=True, fastmath=True)
def _update_basis(hits,
                  basis,
                  theta_x_mrad,
                  theta_y_mrad,
                  ref_x,
                  ref_y,
                  measured_resolution_mrad):
    """
    Update the 4D basis histogram with a batch of hits.

    Parameters
    ----------
    hits : ndarray, shape (N, 4)
        (theta_x_inc, theta_y_inc, theta_x_meas, theta_y_meas), all in radians.
    basis : ndarray
        4D histogram to be updated in-place.
    theta_x_mrad, theta_y_mrad : ndarray of int32
        Incident-angle grids in mrad (physical mrad values).
    ref_x, ref_y : ndarray of int32
        Lookup tables mapping rounded measured angles to the index in
        ``unique_theta_x`` and ``unique_theta_y``.
    measured_resolution_mrad : float
        Rounding / binning resolution for measured angles (mrad).
    """
    if measured_resolution_mrad <= 0.0:
        measured_resolution_mrad = 0.1

    # Measured-angle integer factor (bins per mrad)
    meas_factor_int = int(np.round(1.0 / measured_resolution_mrad))
    if meas_factor_int < 1:
        meas_factor_int = 1
    meas_factor = float(meas_factor_int)
    meas_res_effective = 1.0 / meas_factor  # actual mrad step

    # Incident grid parameters
    cx = float(theta_x_mrad[0])  # leftmost incident angle in mrad
    cy = float(theta_y_mrad[0])
    nx_inc = theta_x_mrad.shape[0]
    ny_inc = theta_y_mrad.shape[0]

    # Incident resolution (inferred from grid)
    if nx_inc > 1:
        inc_step_x = float(theta_x_mrad[1] - theta_x_mrad[0])
    else:
        inc_step_x = 1.0
    if ny_inc > 1:
        inc_step_y = float(theta_y_mrad[1] - theta_y_mrad[0])
    else:
        inc_step_y = 1.0

    Lx = ref_x.shape[0]
    Ly = ref_y.shape[0]

    # Precompute measured and incident angles in mrad
    # Measured: quantised to measured_resolution_mrad
    theta_x_measured = (
        np.round(hits[:, 2] * 1000.0 * meas_factor) / meas_factor
    )
    theta_y_measured = (
        np.round(hits[:, 3] * 1000.0 * meas_factor) / meas_factor
    )

    # Incident: quantised to nearest incident grid step (inferred from theta_*_mrad)
    theta_x_incident = np.round(
        (hits[:, 0] * 1000.0 - cx) / inc_step_x
    ) * inc_step_x + cx
    theta_y_incident = np.round(
        (hits[:, 1] * 1000.0 - cy) / inc_step_y
    ) * inc_step_y + cy

    for i in prange(hits.shape[0]):
        mx = theta_x_measured[i]
        my = theta_y_measured[i]
        ix = theta_x_incident[i]
        iy = theta_y_incident[i]

        # 8-fold symmetry
        for sym in range(8):
            mxx = mx
            myy = my
            ixx = ix
            iyy = iy

            if sym == 1:
                mxx = -mx
                myy = my
                ixx = -ix
                iyy = iy
            elif sym == 2:
                mxx = mx
                myy = -my
                ixx = ix
                iyy = -iy
            elif sym == 3:
                mxx = -mx
                myy = -my
                ixx = -ix
                iyy = -iy
            elif sym == 4:
                mxx = my
                myy = mx
                ixx = iy
                iyy = ix
            elif sym == 5:
                mxx = -my
                myy = mx
                ixx = -iy
                iyy = ix
            elif sym == 6:
                mxx = my
                myy = -mx
                ixx = iy
                iyy = -ix
            elif sym == 7:
                mxx = -my
                myy = -mx
                ixx = -iy
                iyy = -ix

            # Measured -> lookup index (emulate Python negative indexing)
            idx_mx = int(mxx * meas_factor)
            idx_my = int(myy * meas_factor)
            if idx_mx < 0:
                idx_mx += Lx
            if idx_my < 0:
                idx_my += Ly
            if idx_mx < 0 or idx_mx >= Lx or idx_my < 0 or idx_my >= Ly:
                continue

            meas_ix = ref_x[idx_mx]
            meas_iy = ref_y[idx_my]
            if meas_ix < 0 or meas_ix >= basis.shape[0]:
                continue
            if meas_iy < 0 or meas_iy >= basis.shape[1]:
                continue

            # Incident indices in mrad grid:
            # index = (angle_mrad - left_edge_mrad) / step
            inc_x_idx = int((ixx - cx) / inc_step_x)
            inc_y_idx = int((iyy - cy) / inc_step_y)
            if inc_x_idx < 0 or inc_x_idx >= nx_inc:
                continue
            if inc_y_idx < 0 or inc_y_idx >= ny_inc:
                continue

            basis[meas_ix, meas_iy, inc_x_idx, inc_y_idx] += 1

    return basis


# ---------------------------------------------------------------------------
# MonteCarloRenderer class
# ---------------------------------------------------------------------------

class MonteCarloRenderer:
    """
    Monte Carlo basis generator using the geometry from a
    :class:`PlaneDetector` instance.

    Parameters
    ----------
    detector : PlaneDetector
        Detector geometry and mapping.
    zenith_boresight_deg, azimuth_boresight_deg : float
        Boresight orientation of the telescope (degrees).
    theta_max_deg : float
        Maximum zenith angle for the simulated cosmic-ray muons.
    angle_deg_basis : float
        Half-width of the incident-angle grid (in degrees) for the basis.
    basis_resolution_mrad : float
        Incident-angle bin size for the basis (mrad), default 1.0 mrad.
    measured_resolution_mrad : float
        Rounding / binning resolution for measured angles (mrad),
        default 0.1 mrad.
    simulation_half_length_x, simulation_half_length_y : float, optional
        Half-lengths (mm) of the Monte Carlo source plane in x and y.
        If ``None``, the largest detector half-lengths are used.
    use_gpu : bool
        If ``True`` (default), use the GPU implementation where available.
        If ``False``, always use the CPU implementation.
    max_gpus : int or None
        Maximum number of GPUs to use. If ``None``, all available GPUs
        are used. The total number of events is split evenly across
        the selected GPUs.
    state_path : str or None
        Path to a ``.npz`` file where the accumulated basis is saved
        and from which it can be resumed.  If ``None``, no automatic
        checkpointing is performed.
    log_path : str or None
        Path to a text log file where (counts, std/mean) are appended
        after each iteration.  If ``None``, logging is disabled.
    """

    def __init__(self,
                 detector,
                 zenith_boresight_deg=0.0,
                 azimuth_boresight_deg=0.0,
                 theta_max_deg=30.0,
                 angle_deg_basis=25.0,
                 simulation_half_length_x=None,
                 simulation_half_length_y=None,
                 use_gpu=True,
                 max_gpus=None,
                 state_path="9449.npz",
                 log_path="9449.txt",
                 basis_resolution_mrad=1.0,
                 measured_resolution_mrad=0.1):

        if not isinstance(detector, PlaneDetector):
            raise TypeError(
                "detector must be an instance of PlaneDetector "
                "(got %r)" % (type(detector),)
            )

        self.det = detector

        # Geometry from PlaneDetector (all in mm)
        self.layer_z = np.asarray(detector.layer_z.mm, dtype=np.float64)
        self.layer_half_length_x = np.asarray(
            detector.detector_half_length_x.mm,
            dtype=np.float64,
        )
        self.layer_half_length_y = np.asarray(
            detector.detector_half_length_y.mm,
            dtype=np.float64,
        )

        # Assume uniform pixel footprint for all layers
        px = np.atleast_1d(detector.pixel_footprint_length_x.mm)
        py = np.atleast_1d(detector.pixel_footprint_length_y.mm)
        self.pixel_length_x = float(px[0])
        self.pixel_length_y = float(py[0])

        # Simulation source plane half-lengths
        if simulation_half_length_x is None:
            simulation_half_length_x = float(np.max(self.layer_half_length_x))
        if simulation_half_length_y is None:
            simulation_half_length_y = float(np.max(self.layer_half_length_y))

        self.simulation_half_length_x = float(simulation_half_length_x)
        self.simulation_half_length_y = float(simulation_half_length_y)

        self.zenith_boresight_deg = float(zenith_boresight_deg)
        self.azimuth_boresight_deg = float(azimuth_boresight_deg)
        self.theta_max_deg = float(theta_max_deg)
        self.angle_deg_basis = float(angle_deg_basis)

        # Precompute radians for Numba hot paths
        self.zenith_boresight_rad = np.radians(self.zenith_boresight_deg)
        self.azimuth_boresight_rad = np.radians(self.azimuth_boresight_deg)
        self.theta_max_rad = np.radians(self.theta_max_deg)

        # Basis resolution knobs (in mrad)
        if basis_resolution_mrad <= 0.0:
            basis_resolution_mrad = 1.0
        if measured_resolution_mrad <= 0.0:
            measured_resolution_mrad = 0.1

        # Snap measured resolution to an integer divisor of 1 mrad
        meas_factor_int = max(1, int(round(1.0 / measured_resolution_mrad)))
        self.measured_resolution_mrad = 1.0 / float(meas_factor_int)

        # Incident basis resolution is in integer mrad already
        self.basis_resolution_mrad = float(basis_resolution_mrad)

        self.use_gpu = bool(use_gpu)
        self.max_gpus = int(max_gpus) if max_gpus is not None else None
        self.state_path = state_path
        self.log_path = log_path

        # Device selection
        self.device_ids = None
        if self.use_gpu:
            self._init_device_ids()

        # Basis-related state
        self.basis = None
        self.unique_theta_x = None
        self.unique_theta_y = None
        self.theta_x_mrad = None
        self.theta_y_mrad = None
        self.ref_x = None
        self.ref_y = None

        # Geometric factor (computed lazily)
        self.geometric_factor_array = None
        self.simulated_angles_x = None
        self.simulated_angles_y = None

        # Try to resume from existing state, if available
        if self.state_path is not None:
            try:
                self._load_state(self.state_path)
                print(
                    "[MonteCarloRenderer] Loaded existing state from %s"
                    % self.state_path
                )
            except Exception:
                # Start from scratch if anything goes wrong
                pass

    # ------------------------------------------------------------------
    # Device management
    # ------------------------------------------------------------------

    def _init_device_ids(self):
        """
        Detect available GPUs and select up to ``max_gpus`` of them.
        """
        if cp is None:
            print("[MonteCarloRenderer] CuPy is not available; "
                  "GPU support disabled.")
            self.device_ids = []
            return

        if not _cuda_is_available():
            print("[MonteCarloRenderer] Numba CUDA is not available; "
                  "GPU support disabled.")
            self.device_ids = []
            return

        # Try Numba first, fall back to CuPy if needed
        try:
            n_available = len(cuda.gpus)
            print("[MonteCarloRenderer] Detected %d CUDA device(s) via Numba."
                  % n_available)
        except Exception:
            try:
                n_available = cp.cuda.runtime.getDeviceCount()
            except Exception:
                n_available = 0

        if n_available <= 0:
            self.device_ids = []
            return

        if self.max_gpus is not None and self.max_gpus > 0:
            n_use = min(self.max_gpus, n_available)
        else:
            n_use = n_available

        self.device_ids = list(range(n_use))

    def set_use_gpu(self, use_gpu, max_gpus=None):
        """
        Enable or disable GPU usage at runtime.

        Parameters
        ----------
        use_gpu : bool
            Whether to use GPU.
        max_gpus : int or None
            Optional new limit for the number of GPUs to use.
        """
        self.use_gpu = bool(use_gpu)
        if max_gpus is not None:
            self.max_gpus = int(max_gpus)
        if self.use_gpu:
            self._init_device_ids()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_n_events(self, flux, time_elapsed):
        """
        Compute the expected number of events for a given flux and live time.

        Parameters
        ----------
        flux : float
            Muon flux, in units of
            cm^-2 s^-1 sr^-1.
        time_elapsed : float
            Live time in seconds.

        Returns
        -------
        n_events : int
            Expected total number of generated events.
        """
        theta_max_rad = self.theta_max_rad
        solid_angle = 2.0 * np.pi * (1.0 - np.cos(theta_max_rad))

        # Source plane area in m^2 (rectangular: [-a,+a] x [-b,+b])
        area_mm2 = 4.0 * self.simulation_half_length_x * self.simulation_half_length_y
        area_m2 = area_mm2 / 1.0e6

        expected = flux * area_m2 * solid_angle * time_elapsed
        return int(expected)

    def run(self,
            n_events=None,
            flux=None,
            time_elapsed=None,
            runs=1,
            iters_per_run=10,
            use_gpu=None):
        """
        Run the Monte Carlo and accumulate the basis.

        Parameters
        ----------
        n_events : int, optional
            Number of generated events per iteration.  If ``None``, it is
            inferred from ``flux`` and ``time_elapsed``.
        flux : float, optional
            Muon flux [cm^-2 s^-1 sr^-1].
        time_elapsed : float, optional
            Live time (seconds).  Only used if ``n_events`` is ``None``.
        runs : int
            Number of outer runs.  A state save is performed after each run.
        iters_per_run : int
            Number of inner iterations per run.
        use_gpu : bool, optional
            Override the instance-level ``use_gpu`` flag for this call only.
        """
        if n_events is None:
            if flux is None or time_elapsed is None:
                raise ValueError(
                    "Either n_events must be provided, or both "
                    "flux and time_elapsed must be specified."
                )
            n_events = self.compute_n_events(flux, time_elapsed)

        n_events = int(n_events)
        if n_events <= 0:
            raise ValueError("n_events must be > 0 (got %d)" % n_events)

        if use_gpu is None:
            use_gpu = self.use_gpu
        use_gpu = bool(use_gpu)

        # Ensure GPU device list is initialised if needed
        if use_gpu:
            if self.device_ids is None or len(self.device_ids) == 0:
                self._init_device_ids()
            if self.device_ids is None or len(self.device_ids) == 0:
                print(
                    "[MonteCarloRenderer] GPU requested but no usable "
                    "device found; falling back to CPU."
                )
                use_gpu = False

        for run_idx in range(1, runs + 1):
            backend_label = "GPU" if use_gpu else "CPU"
            print(
                "\n[MonteCarloRenderer] Starting run %02d/%02d "
                "(n_events per iter = %d, backend = %s)"
                % (run_idx, runs, n_events, backend_label)
            )

            for iter_idx in range(1, iters_per_run + 1):
                prof = Profiler()

                # ---------------- Simulate events ----------------
                with time_block(prof, "simulate"):
                    if use_gpu:
                        hits = _run_simulation_gpu(
                            n_events,
                            self.layer_z,
                            self.pixel_length_x,
                            self.pixel_length_y,
                            self.layer_half_length_x,
                            self.layer_half_length_y,
                            self.zenith_boresight_deg,
                            self.azimuth_boresight_deg,
                            self.theta_max_deg,
                            self.simulation_half_length_x,
                            self.simulation_half_length_y,
                            self.device_ids,
                        )
                    else:
                        hits = _run_simulation_cpu(
                            n_events,
                            self.layer_z,
                            self.pixel_length_x,
                            self.pixel_length_y,
                            self.layer_half_length_x,
                            self.layer_half_length_y,
                            self.zenith_boresight_rad,
                            self.azimuth_boresight_rad,
                            self.theta_max_rad,
                            self.simulation_half_length_x,
                            self.simulation_half_length_y,
                        )

                n_valid = hits.shape[0]

                # ---------------- Initialise / update basis ---------------
                with time_block(prof, "basis"):
                    if self.basis is None:
                        (
                            self.basis,
                            self.unique_theta_x,
                            self.unique_theta_y,
                            self.theta_x_mrad,
                            self.theta_y_mrad,
                            self.ref_x,
                            self.ref_y,
                        ) = _init_basis_from_hits(
                            hits,
                            angle_deg=self.angle_deg_basis,
                            resolution_mrad=self.basis_resolution_mrad,
                            measured_resolution_mrad=self.measured_resolution_mrad,
                        )

                    _update_basis(
                        hits,
                        self.basis,
                        self.theta_x_mrad,
                        self.theta_y_mrad,
                        self.ref_x,
                        self.ref_y,
                        self.measured_resolution_mrad,
                    )

                # ---------------- Geometric factor ------------------------
                with time_block(prof, "geom"):
                    if self.geometric_factor_array is None:
                        (
                            self.simulated_angles_x,
                            self.simulated_angles_y,
                        ) = np.meshgrid(
                            self.theta_x_mrad,
                            self.theta_y_mrad,
                        )
                        self.geometric_factor_array = geometric_factor(
                            self.simulated_angles_x / 1000.0,
                            self.simulated_angles_y / 1000.0,
                            self.layer_z,
                            self.layer_half_length_x,
                            self.layer_half_length_y,
                            1.0 / 1000.0,
                            1.0 / 1000.0,
                        )

                # ---------------- Normalisation + stats -------------------
                with time_block(prof, "norm+stats"):
                    image = np.sum(self.basis, axis=(0, 1))
                    counts = float(np.sum(image))

                    mask_geom = self.geometric_factor_array > 0.0
                    image[mask_geom] = (
                        image[mask_geom] / self.geometric_factor_array[mask_geom]
                    )
                    image[~mask_geom] = 0.0

                    mask_fov = (
                        (np.abs(self.simulated_angles_x) <= np.radians(21.0) * 1000.0)
                        & (np.abs(self.simulated_angles_y) <= np.radians(21.0) * 1000.0)
                        & mask_geom
                    )

                    mean = float(np.mean(image[mask_fov]))
                    std = float(np.std(image[mask_fov]))
                    std_over_mean = std / mean if mean != 0.0 else float("nan")

                # ---------------- Logging ---------------------------------
                with time_block(prof, "log"):
                    if self.log_path is not None:
                        with open(self.log_path, "a", encoding="utf-8") as f:
                            f.write(f"{counts}, {std_over_mean}\n")

                # ---------------- Profiling output ------------------------
                total_time = prof.total()
                ns_per_event = (
                    total_time / float(n_valid) * 1.0e9
                    if n_valid > 0 else float("nan")
                )

                print(
                    "[MonteCarloRenderer | run %02d, iter %02d, backend=%s] "
                    "events=%d | ns/event=%.2f | std/mean=%.4f"
                    % (run_idx, iter_idx, backend_label, n_valid, ns_per_event, std_over_mean)
                )
                print_profile(
                    "  sections for run %02d, iter %02d" % (run_idx, iter_idx),
                    prof,
                )

            # ---- end of inner loop: save checkpoint --------------------
            if self.state_path is not None and self.basis is not None:
                self._save_state(self.state_path)
                print(
                    "[MonteCarloRenderer] Saved state to %s after run %02d"
                    % (self.state_path, run_idx)
                )

    # ------------------------------------------------------------------
    # Internal helpers for saving / loading basis state
    # ------------------------------------------------------------------

    def _load_state(self, path):
        """
        Load an existing basis state from a ``.npz`` file.
        """
        data = np.load(path)
        self.basis = data["basis"]
        measured_angles = data["measured_angles"]
        incident_angles = data["incident_angles"]
        self.geometric_factor_array = (
            data["geometric_factor"] if "geometric_factor" in data.files else None
        )

        # Optional resolution metadata (for forward compatibility)
        if "incident_resolution_mrad" in data.files:
            self.basis_resolution_mrad = float(
                data["incident_resolution_mrad"][()]
            )
        # default: 1.0 mrad if missing
        else:
            self.basis_resolution_mrad = getattr(self, "basis_resolution_mrad", 1.0)

        if "measured_resolution_mrad" in data.files:
            self.measured_resolution_mrad = float(
                data["measured_resolution_mrad"][()]
            )
        else:
            # default to 0.1 mrad for older files
            self.measured_resolution_mrad = getattr(self, "measured_resolution_mrad", 0.1)

        # Reconstruct grids
        self.unique_theta_x = measured_angles[0, 0, :]
        self.unique_theta_y = measured_angles[1, :, 0]
        self.theta_x_mrad = incident_angles[0, 0, :].astype(np.int32)
        self.theta_y_mrad = incident_angles[1, :, 0].astype(np.int32)

        # Measured-angle integer factor
        meas_factor_int = max(
            1,
            int(round(1.0 / self.measured_resolution_mrad)),
        )

        # Range of incident grid in mrad
        mrad = int(max(abs(self.theta_x_mrad[0]), abs(self.theta_x_mrad[-1])))

        Lx = 2 * mrad * meas_factor_int + 1
        Ly = 2 * mrad * meas_factor_int + 1
        self.ref_x = np.full(Lx, -1, dtype=np.int32)
        self.ref_y = np.full(Ly, -1, dtype=np.int32)

        for idx, val in enumerate(self.unique_theta_x):
            raw = int(val * meas_factor_int)
            if raw < 0:
                raw += Lx
            if 0 <= raw < Lx:
                self.ref_x[raw] = idx

        for idx, val in enumerate(self.unique_theta_y):
            raw = int(val * meas_factor_int)
            if raw < 0:
                raw += Ly
            if 0 <= raw < Ly:
                self.ref_y[raw] = idx

        # Simulated angle grids (needed for normalisation / stats)
        self.simulated_angles_x, self.simulated_angles_y = np.meshgrid(
            self.theta_x_mrad,
            self.theta_y_mrad,
        )

        # If geometric_factor was not stored, recompute it lazily later
        if self.geometric_factor_array is None:
            self.geometric_factor_array = None

    def _save_state(self, path):
        """
        Save the current basis state to a ``.npz`` file.
        """
        if (
            self.basis is None
            or self.unique_theta_x is None
            or self.unique_theta_y is None
            or self.theta_x_mrad is None
            or self.theta_y_mrad is None
        ):
            raise RuntimeError("No basis state to save.")

        unique_angles_x, unique_angles_y = np.meshgrid(
            self.unique_theta_x,
            self.unique_theta_y,
        )
        simulated_angles_x, simulated_angles_y = np.meshgrid(
            self.theta_x_mrad,
            self.theta_y_mrad,
        )

        geometric_factor_array = self.geometric_factor_array
        if geometric_factor_array is None:
            geometric_factor_array = geometric_factor(
                simulated_angles_x / 1000.0,
                simulated_angles_y / 1000.0,
                self.layer_z,
                self.layer_half_length_x,
                self.layer_half_length_y,
                1.0 / 1000.0,
                1.0 / 1000.0,
            )

        measured_angles = np.array(
            [unique_angles_x, unique_angles_y],
            dtype=np.float64,
        )
        incident_angles = np.array(
            [simulated_angles_x, simulated_angles_y],
            dtype=np.float64,
        )

        np.savez_compressed(
            path,
            basis=self.basis,
            measured_angles=measured_angles,
            incident_angles=incident_angles,
            geometric_factor=geometric_factor_array,
            incident_resolution_mrad=np.array(
                self.basis_resolution_mrad, dtype=np.float64
            ),
            measured_resolution_mrad=np.array(
                self.measured_resolution_mrad, dtype=np.float64
            ),
        )
