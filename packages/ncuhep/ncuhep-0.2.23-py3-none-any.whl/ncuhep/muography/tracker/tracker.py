import numpy as np
from numba import njit, prange
from ..utils import track_reconstruction
from ..classes import PlaneDetector


# ==========================
# Per-hit coordinate mapping
# ==========================
@njit(cache=True, fastmath=True)
def uniqueid2position(uid, lid,
                      base_tab,
                      nx_tab, ny_tab,
                      halfx_tab, halfy_tab,
                      px, py,
                      z_tab,
                      id2idx):
    li = id2idx[lid]
    u  = uid - base_tab[li]
    nx = nx_tab[li]
    ny = ny_tab[li]

    # centering convention: yy uses halfx, xx uses halfy
    yy = (u // ny) * py - py * halfx_tab[li]
    xx = (u %  nx) * px - px * halfy_tab[li]
    zz = z_tab[li]

    return xx, yy, zz


@njit(cache=True, fastmath=True, parallel=True)
def uniqueid2positions(uids, lids,
                       base_tab,
                       nx_tab, ny_tab,
                       halfx_tab, halfy_tab,
                       px, py,
                       z_tab,
                       id2idx):
    n = uids.shape[0]
    pos = np.empty((n, 3), dtype=np.float64)

    for k in prange(n):
        li = id2idx[lids[k]]
        u  = uids[k] - base_tab[li]
        nx = nx_tab[li]
        ny = ny_tab[li]

        yy = (u // ny) * py - py * halfx_tab[li]
        xx = (u %  nx) * px - px * halfy_tab[li]
        zz = z_tab[li]

        pos[k, 0] = xx
        pos[k, 1] = yy
        pos[k, 2] = zz

    return pos


# ==========================
# Fit quality (chi^2 / dof)
# ==========================
@njit(cache=True, fastmath=True)
def lsq(pos, track, sigma2_x, sigma2_y):
    """
    Chi^2/(N-2) with axis-specific variances:
      sigma2_x = px^2 / 12
      sigma2_y = py^2 / 12
    """
    x = pos[:, 0]
    y = pos[:, 1]
    z = pos[:, 2]

    ix, iy, thx, thy = track
    mx = np.tan(thx)
    my = np.tan(thy)

    x_ = mx * z + ix
    y_ = my * z + iy

    # axis-specific weighting
    chi2 = np.sum((x - x_)**2 / sigma2_x + (y - y_)**2 / sigma2_y)
    n = pos.shape[0]
    dof = n - 2 if n > 2 else 1  # keep your original convention
    # (use n-4 if you prefer to count ix,iy,thx,thy as 4 fitted params)
    return chi2 / dof


# ==========================
# Public API
# ==========================
def tracker(events, det: PlaneDetector):
    # geometry tables
    n_tab   = det.pixel_count_per_layer.astype(np.int64)
    nx_tab  = det.pixel_count_per_layer_x.astype(np.int64)
    ny_tab  = det.pixel_count_per_layer_y.astype(np.int64)
    px      = float(det.pixel_footprint_length_x.mm)
    py      = float(det.pixel_footprint_length_y.mm)
    z_tab   = det.layer_z.mm.astype(np.float64)
    lid_ref = det.layer_id.astype(np.int64)

    L = lid_ref.shape[0]

    # base offsets (exclusive prefix sum)
    base_tab = np.empty(L, dtype=np.int64)
    s = 0
    for i in range(L):
        base_tab[i] = s
        s += n_tab[i]

    # half extents
    halfx_tab = (nx_tab.astype(np.float64) - 1.0) * 0.5
    halfy_tab = (ny_tab.astype(np.float64) - 1.0) * 0.5

    # layer id → index mapping
    max_lid = int(lid_ref.max())
    id2idx  = np.full(max_lid + 1, -1, dtype=np.int64)
    for i in range(L):
        id2idx[lid_ref[i]] = i

    # axis-specific noise variances
    sigma2_x = (px * px) / 12.0
    sigma2_y = (py * py) / 12.0

    out = []
    for ev in events:
        if ev is None:
            continue

        uids = ev["UNIQUEID"].astype(np.int64, copy=False)
        lids = ev["LAYERID"].astype(np.int64, copy=False)

        pos = uniqueid2positions(uids, lids,
                                 base_tab,
                                 nx_tab, ny_tab,
                                 halfx_tab, halfy_tab,
                                 px, py,
                                 z_tab,
                                 id2idx)

        track = track_reconstruction(pos)
        chi2  = lsq(pos, track, sigma2_x, sigma2_y)

        out.append({
            "LAYERID":   ev["LAYERID"],
            "UNIQUEID":  ev["UNIQUEID"],
            "TIMESTAMP": ev["TIMESTAMP"],
            "PCNT":      ev["PCNT"],
            "TCNT":      ev["TCNT"],
            "PWIDTH":    ev["PWIDTH"],
            "TRACK":     track,
            "CHI2":      chi2,
        })

    return np.array(out, dtype=object)
