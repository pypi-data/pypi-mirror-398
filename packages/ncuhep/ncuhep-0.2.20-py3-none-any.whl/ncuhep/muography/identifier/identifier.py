from ..utils import multiple_intercept, array2combo
import numpy as np
from numba import njit
from ..classes import PlaneDetector


# ------------------------------
# Per-hit coordinate (Numba)
# ------------------------------
@njit(cache=True, fastmath=True)
def uniqueid2position(uid, lid, i,
                      xrow, yrow, irow,
                      base_tab, nx_tab, ny_tab,
                      px, py,
                      z_tab, id2idx,
                      halfx_tab, halfy_tab):
    li = id2idx[lid]
    u  = uid - base_tab[li]
    nx = nx_tab[li]
    ny = ny_tab[li]

    # centering convention: yy uses halfx, xx uses halfy
    yy = (u // ny) * py - py * halfx_tab[li]
    xx = (u %  nx) * px - px * halfy_tab[li]
    zz = z_tab[li]

    xrow[0] = xx;   xrow[1] = zz
    yrow[0] = yy;   yrow[1] = zz
    irow[0] = i;    irow[1] = zz


def split_events_sorted(arr):
    order  = np.argsort(arr['EVENTID'], kind='mergesort')
    eid    = arr['EVENTID'][order]
    starts = np.r_[0, 1 + np.flatnonzero(eid[1:] != eid[:-1])]
    stops  = np.r_[starts[1:], eid.size]

    out = []
    for s, e in zip(starts, stops):
        sl = order[s:e]
        out.append({
            "BOARDID":   arr['BOARDID'][sl],
            "CHANNELID": arr['CHANNELID'][sl],
            "LAYERID":   arr['LAYERID'][sl],
            "UNIQUEID":  arr['UNIQUEID'][sl],
            "TIMESTAMP": arr['TIMESTAMP'][sl],
            "PCNT":      arr['PCNT'][sl],
            "TCNT":      arr['TCNT'][sl],
            "PWIDTH":    arr['PWIDTH'][sl],
        })
    return out


def identify(events, det: PlaneDetector):
    # geometry tables
    n_tab   = det.pixel_count_per_layer.astype(np.int64)
    nx_tab  = det.pixel_count_per_layer_x.astype(np.int64)
    ny_tab  = det.pixel_count_per_layer_y.astype(np.int64)
    px      = float(det.pixel_footprint_length_x.mm)
    py      = float(det.pixel_footprint_length_y.mm)
    z_tab   = det.layer_z.mm.astype(np.float64)
    lid_ref = det.layer_id.astype(np.int64)

    L = lid_ref.size

    # base offsets (exclusive prefix sum)
    base_tab = np.empty(L, dtype=np.int64)
    s = 0
    for j in range(L):
        base_tab[j] = s
        s += n_tab[j]

    # half spans
    halfx_tab = (nx_tab.astype(np.float64) - 1.0) * 0.5
    halfy_tab = (ny_tab.astype(np.float64) - 1.0) * 0.5

    # layer-id → index map
    max_lid = int(lid_ref.max())
    id2idx  = np.full(max_lid + 1, -1, dtype=np.int64)
    for j in range(L):
        id2idx[lid_ref[j]] = j

    # per-axis hit resolution (standard deviation)
    sigma_x = px / np.sqrt(12.0)
    sigma_y = py / np.sqrt(12.0)

    results = np.empty(len(events), dtype=object)

    for ei, ev in enumerate(events):
        uid = ev["UNIQUEID"]
        lid = ev["LAYERID"]

        n_hits = len(uid)
        idx = np.arange(n_hits, dtype=np.float32)

        x_hits = np.empty((n_hits, 2), np.float32)
        y_hits = np.empty_like(x_hits)
        i_hits = np.empty_like(x_hits)

        # map each hit
        for k in range(n_hits):
            uniqueid2position(uid[k], lid[k], idx[k],
                              x_hits[k], y_hits[k], i_hits[k],
                              base_tab, nx_tab, ny_tab,
                              px, py,
                              z_tab, id2idx,
                              halfx_tab, halfy_tab)

        # layer-wise combinations
        x_combos = array2combo(x_hits, z_tab)
        y_combos = array2combo(y_hits, z_tab)
        i_combos = array2combo(i_hits, z_tab)

        best = None
        best_idx = None

        for xc, yc, ic in zip(x_combos, y_combos, i_combos):
            # # use axis-specific sigma
            # x_lsq = multiple_intercept(xc, sigma_x)
            # y_lsq = multiple_intercept(yc, sigma_y)
            #
            # if np.isnan(x_lsq) or np.isnan(y_lsq):
            #     continue
            #
            # chi = x_lsq + y_lsq

            rc = np.zeros_like(xc)
            rc[:, 0] = np.sqrt(xc[:, 0] ** 2 + yc[:, 0] ** 2)
            rc[:, 1] = xc[:, 1]

            sigma = np.sqrt(sigma_x ** 2 + sigma_y ** 2)
            chi = multiple_intercept(rc, sigma)

            if np.isnan(chi):
                continue

            if (best is None) or (chi < best):
                best = chi
                best_idx = ic[:, 0]

        if best_idx is not None:
            sel  = np.isfinite(best_idx)
            idxs = best_idx[sel].astype(np.intp, copy=False)
            mask = np.zeros(n_hits, dtype=bool)
            mask[idxs] = True

            results[ei] = {
                "BOARDID":   ev["BOARDID"][mask],
                "CHANNELID": ev["CHANNELID"][mask],
                "LAYERID":   ev["LAYERID"][mask],
                "UNIQUEID":  ev["UNIQUEID"][mask],
                "TIMESTAMP": ev["TIMESTAMP"][mask],
                "PCNT":      ev["PCNT"][mask],
                "TCNT":      ev["TCNT"][mask],
                "PWIDTH":    ev["PWIDTH"][mask],
            }
        else:
            results[ei] = None

    return results


def identifier(events, det: PlaneDetector):
    evs = split_events_sorted(events)
    return identify(evs, det)
