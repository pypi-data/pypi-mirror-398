import numpy as np
from numba import njit, prange
import os
import pandas as pd
from ..classes import MuTxtFormat, PlaneDetector, AnalysisConfig


# -----------------------------
# Counter / timestamp utilities
# -----------------------------

@njit(cache=True)
def pcnt_correction(pcnt, pcnt_bit_size=20, glitch_thresh_max=10000):
    """
    Monotonic correction for a wrapping counter.

    - `pcnt`          : 1D array of counter values (uint32/uint64/etc.)
    - `pcnt_bit_size` : number of bits of the hardware counter (e.g. 20)
    - `glitch_thresh` : max allowed forward jump (counts) before we call it noise
    """
    glitch_thresh = 2

    while glitch_thresh < glitch_thresh_max:
        n = pcnt.size
        out = np.empty_like(pcnt)

        wrap = np.uint64(1) << np.uint64(pcnt_bit_size)
        half_wrap = wrap >> np.uint64(1)

        prev = np.uint64(pcnt[0])
        out[0] = prev

        for i in range(1, n):
            cur = np.uint64(pcnt[i])

            # --- unwrap relative to prev ---
            if cur < prev:
                diff = prev - cur
                if diff > half_wrap:
                    # likely a real wrap: counter jumped from near wrap to small value
                    cur = cur + wrap
                else:
                    # small backward jump -> glitch, clamp
                    cur = prev

            # now cur >= prev in "unwrapped" space
            # --- forward glitch filter ---
            diff_forward = cur - prev
            if diff_forward > glitch_thresh:
                # too large jump for one step -> glitch
                cur = prev

            out[i] = cur
            prev = cur

        std = np.std(out)
        mean = np.mean(out)
        mask = (out < mean + 3 * std) & (out > mean - 3 * std)
        if np.std(out[mask]) > 0.98 * std:
            break
        else:
            glitch_thresh *= 2

    return out


def get_timestamp(pcnt, tcnt, tcnt_bit_size=32):
    """
    Compose full timestamp by packing PCNT (high bits) and TCNT (low bits).
    """
    hi = (pcnt.astype(np.uint64) << np.uint64(tcnt_bit_size))
    lo = tcnt.astype(np.uint64)
    return hi + lo


# -----------------------------
# Mappings: board→layer, (board,channel)→uid
# -----------------------------

@njit(parallel=True, cache=True)
def get_layer(board_id, lid_map):
    """
    Map BOARDID → LAYERID using a 1-based board index in lid_map.
    Returns int64 array (not float).
    """
    out = np.empty(board_id.size, dtype=np.int64)
    for i in prange(board_id.size):
        b = int(board_id[i]) - 1
        out[i] = int(lid_map[b])
    return out


@njit(parallel=True, cache=True)
def get_unique_id(board_id, channel_id, uid_map):
    """
    Map (BOARDID, CHANNELID) → UNIQUEID via 2D lookup (1-based board index).
    """
    out = np.empty(board_id.size, dtype=np.uint16)
    for i in prange(board_id.size):
        b = int(board_id[i]) - 1
        c = int(channel_id[i])
        out[i] = uid_map[b, c]
    return out


# -----------------------------
# Event labeling (time clustering)
# -----------------------------

@njit(cache=True)
def label(timestamp, event_threshold=75, hit_threshold=15):
    """
    Assign EVENTID by clustering in time.
    """
    n = timestamp.size
    labels = np.zeros(n, dtype=np.uint64)
    cur_label = np.uint64(0)
    t0 = timestamp[0]
    tp = timestamp[0]

    for i in range(1, n):
        t = timestamp[i]
        if (t - tp) > hit_threshold or (t - t0) > event_threshold:
            cur_label += 1
            t0 = t
        labels[i] = cur_label
        tp = t
    return labels


# -----------------------------
# Grouping by EVENTID (fast)
# -----------------------------

def event_grouping_fast(data, layers, max_per_layer, max_total):
    """
    Vectorized grouping & filtering.
    - layers: the 4 actual LAYERID codes in ascending order (e.g., (1,2,3,4))
    - max_per_layer: per-layer maxima in same order
    - max_total: max total hits per event
    Returns a structured array of kept rows.
    """
    eid = data["EVENTID"]
    lid = data["LAYERID"]
    n = eid.size

    dtype = [
        ("EVENTID", eid.dtype),
        ("BOARDID", data["BOARDID"].dtype),
        ("CHANNELID", data["CHANNELID"].dtype),
        ("LAYERID", lid.dtype),
        ("UNIQUEID", data["UNIQUEID"].dtype),
        ("TIMESTAMP", data["TIMESTAMP"].dtype),
        ("PCNT", data["PCNT"].dtype),
        ("TCNT", data["TCNT"].dtype),
        ("PWIDTH", data["PWIDTH"].dtype),
    ]
    if n == 0:
        return np.empty(0, dtype=dtype)

    # 1) stable sort by EVENTID
    order = np.argsort(eid, kind="mergesort")
    eid_sorted = eid[order]
    starts = np.r_[0, 1 + np.flatnonzero(np.diff(eid_sorted))]
    stops = np.r_[starts[1:], n]
    cnt_all = stops - starts  # total hits per event

    # 2) map actual LAYERID codes to {0,1,2,3}
    layers = np.asarray(layers)
    lid_sorted = lid[order]

    idx = np.searchsorted(layers, lid_sorted)

    mask = idx < layers.size
    valid = (idx < layers.size) & (layers[idx] == lid_sorted)

    lid_idx = np.where(valid, idx, -1)  # -1 = not a target layer

    # 3) per-layer counts via segment reductions
    c = []

    for k in range(layers.size):
        c_k = np.add.reduceat((lid_idx == k).astype(np.int32), starts)
        c.append(c_k)
    c0, c1, c2, c3 = c

    # 4) selection
    have_all = (c0 > 0) & (c1 > 0) & (c2 > 0) & (c3 > 0)
    limits_ok = (c0 <= max_per_layer[0]) & (c1 <= max_per_layer[1]) & \
                (c2 <= max_per_layer[2]) & (c3 <= max_per_layer[3])
    total_ok = (cnt_all <= max_total)
    keep_evt = have_all & limits_ok & total_ok

    # 5) expand to row mask and map back
    mask_sorted = np.repeat(keep_evt, cnt_all)
    row_mask = np.empty(n, dtype=bool)
    row_mask[order] = mask_sorted
    keep = np.nonzero(row_mask)[0]

    out = np.empty(keep.size, dtype=dtype)
    for name, _ in dtype:
        out[name] = data[name][keep]
    return out


# -----------------------------
# CSV parser → events
# -----------------------------

def parser(path_dir, filename,
           mu_txt_format: MuTxtFormat,
           det: PlaneDetector,
           cfg: AnalysisConfig,
           return_hits: bool = False):
    """
    Read one CSV, produce filtered hit rows grouped by event.
    Keeps the same output field names as downstream code expects.
    """
    filepath = os.path.join(path_dir, filename)

    df = pd.read_csv(
        filepath,
        sep=mu_txt_format.sep,
        header=mu_txt_format.header,
        usecols=mu_txt_format.cols,
        names=mu_txt_format.names,
        comment=mu_txt_format.comment,
        dtype=mu_txt_format.dtypes,
        engine=mu_txt_format.engine,
        memory_map=mu_txt_format.memory_map,
        na_filter=mu_txt_format.na_filter,
        skip_blank_lines=mu_txt_format.skip_blank_lines,
    )

    # column views (no copies)
    bid = df["BOARDID"].to_numpy(copy=False)
    chid = df["CHANNELID"].to_numpy(copy=False)
    tcnt = df["TCNT"].to_numpy(copy=False)
    pcnt = df["PCNT"].to_numpy(copy=False)
    pwidth = df["PWIDTH"].to_numpy(copy=False)
    ts_in = df["TIMESTAMP"].to_numpy(copy=False)  # may be present; we rebuild below

    mask = (bid < det.board_counts + 1) & (bid > 0)
    bid = bid[mask]
    chid = chid[mask]
    tcnt = tcnt[mask]
    pcnt = pcnt[mask]
    pwidth = pwidth[mask]
    ts_in = ts_in[mask]

    # pack in a dict with canonical keys (API stable)
    data = {
        "BOARDID": bid,
        "CHANNELID": chid,
        "TIMESTAMP": ts_in,  # placeholder for now; replaced below
        "PCNT": pcnt,
        "TCNT": tcnt,
        "PWIDTH": pwidth,
    }

    # --- counter fix & elapsed time ---
    data["PCNT"] = pcnt_correction(data["PCNT"], mu_txt_format.PCNT_bit_size)

    import matplotlib.pyplot as plt
    plt.hist(data["PCNT"], bins=100)
    plt.show()
    time_elapsed = np.ptp(data["PCNT"])  # max - min

    # --- full timestamp (hi: PCNT, lo: TCNT) ---
    data["TIMESTAMP"] = get_timestamp(data["PCNT"], data["TCNT"], mu_txt_format.TCNT_bit_size).astype(np.uint64)

    # --- chronological sort once ---
    order = np.argsort(data["TIMESTAMP"])
    for k in list(data.keys()):
        data[k] = data[k][order]

    # --- mappings ---
    data["UNIQUEID"] = get_unique_id(data["BOARDID"], data["CHANNELID"], det.forward_mapping)
    data["LAYERID"] = get_layer(data["BOARDID"], det.layer_mapping)

    uniqueIDS = np.copy(data["UNIQUEID"])
    # --- event IDs by time clustering ---
    data["EVENTID"] = label(
        data["TIMESTAMP"],
        event_threshold=cfg.event_threshold,
        hit_threshold=cfg.hit_threshold,
    )

    # --- filter events (vectorized) ---
    events = event_grouping_fast(
        data,
        det.layer_id,
        cfg.max_per_layer,
        cfg.max_total,
    )

    if return_hits:
        return events, time_elapsed, uniqueIDS
    else:
        return events, time_elapsed
