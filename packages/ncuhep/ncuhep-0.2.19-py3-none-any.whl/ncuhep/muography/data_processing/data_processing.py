"""
Backend utilities for the YMS 4444 detector analysis (no Qt).

This module contains all the non-GUI logic (filename parsing,
multiprocessing, hitmap building, and flux computation).  It is used by
`ncuhep.muography.data_processing_gui.gui`, but can also be used
standalone in scripts.
"""

from __future__ import annotations

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Tuple, List, Optional

import numpy as np

from ncuhep.muography.classes import PlaneDetector, MuTxtFormat, AnalysisConfig
from ncuhep.units import Time, Counts, GeometricFactor

# ============================================================
#  Logging setup (shared with GUI)
# ============================================================
LOG_FILE = "4444_gui_debug.log"
logger = logging.getLogger("4444_gui")

if not logger.handlers:
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] pid=%(process)d tid=%(threadName)s %(name)s: %(message)s"
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    logger.info("Logger initialized, writing to %s", LOG_FILE)

# -------------------------------------------------------------------
# JSON <-> NumPy compatibility patch
# -------------------------------------------------------------------
_original_json_default = json.JSONEncoder.default


def _json_numpy_default(self, obj):
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return _original_json_default(self, obj)


json.JSONEncoder.default = _json_numpy_default
logger.debug("Patched json.JSONEncoder.default for numpy types")

# ---------- Globals for worker processes ----------
_det = None
_mutxt = None
_ana = None
_data_folder = None


# ============================================================
#  Filename parsing and filtering
# ============================================================
def parse_run_filename(filename: str) -> Tuple[date, int, int]:
    """
    Parse filenames like '20251122_Run_3_0_Mu.txt'
    and return (date_obj, run_number, run_sub_number).
    """
    pattern = r"^(?P<datestr>\d{8})_Run_?(?P<run>\d+)_(?P<sub>\d+)_Mu\.txt$"

    m = re.match(pattern, filename)
    if not m:
        raise ValueError(f"Filename not in expected format: {filename!r}")

    date_obj = datetime.strptime(m.group("datestr"), "%Y%m%d").date()
    run_number = int(m.group("run"))
    run_sub_number = int(m.group("sub"))

    return date_obj, run_number, run_sub_number


def filter_files(
    files: List[str],
    mode: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    run_start: Optional[int] = None,
    run_end: Optional[int] = None,
) -> List[str]:
    """
    Filter a list of *_Mu.txt filenames either by date range or by run number range.
    mode: "date" or "run"
    """
    selected: List[str] = []
    logger.debug(
        "Filtering %d files with mode=%s start_date=%s end_date=%s run_start=%s run_end=%s",
        len(files), mode, start_date, end_date, run_start, run_end
    )

    for f in files:
        try:
            d, r, s = parse_run_filename(os.path.basename(f))
        except ValueError:
            continue

        if mode == "date":
            if start_date is None or end_date is None:
                continue
            if start_date <= d <= end_date:
                selected.append(f)
        else:  # "run"
            if run_start is None or run_end is None:
                continue
            if run_start <= r <= run_end:
                selected.append(f)

    logger.info("Filter result: %d files selected", len(selected))
    return selected


# ============================================================
#  Detector geometry helper (non-uniform boards_per_layer)
# ============================================================
def build_layer_geometry(det: PlaneDetector):
    """
    From a PlaneDetector instance, compute per-layer geometry.
    """
    layer_count = int(det.layer_count)
    chx = int(det.channels_per_board_x)
    chy = int(det.channels_per_board_y)

    bpx = np.asarray(det.boards_per_layer_x, dtype=int)
    bpy = np.asarray(det.boards_per_layer_y, dtype=int)

    nx_per_layer = np.empty(layer_count, dtype=int)
    ny_per_layer = np.empty(layer_count, dtype=int)
    ncell_per_layer = np.empty(layer_count, dtype=int)

    for i in range(layer_count):
        nx_i = chx * bpx[i]
        ny_i = chy * bpy[i]
        nx_per_layer[i] = nx_i
        ny_per_layer[i] = ny_i
        ncell_per_layer[i] = nx_i * ny_i

    ncell_total = int(ncell_per_layer.sum())
    logger.debug(
        "build_layer_geometry: layer_count=%d, nx_per_layer=%s, ny_per_layer=%s, ncell_total=%d",
        layer_count, nx_per_layer, ny_per_layer, ncell_total
    )
    return layer_count, nx_per_layer, ny_per_layer, ncell_per_layer, ncell_total


def compute_layer_pixel_mapping(det: PlaneDetector) -> List[np.ndarray]:
    """
    Reproduce the per-layer 2D mapping (global channel ID / UNIQUEID)
    as in PlaneDetector.create_mapping, but returning a list of 2D arrays.
    """
    ch_per_board = int(det.channels_per_board)
    chx = int(det.channels_per_board_x)
    chy = int(det.channels_per_board_y)

    boards_per_layer = np.asarray(det.boards_per_layer, dtype=int)
    boards_per_layer_x = np.asarray(det.boards_per_layer_x, dtype=int)
    boards_per_layer_y = np.asarray(det.boards_per_layer_y, dtype=int)

    layer_count = int(det.layer_count)
    board_flip_x = np.asarray(det.board_flip_x, dtype=int)
    board_flip_y = np.asarray(det.board_flip_y, dtype=int)
    layer_flip_x = np.asarray(det.layer_flip_x, dtype=int)
    layer_flip_y = np.asarray(det.layer_flip_y, dtype=int)
    board_flip_z = int(det.board_flip_z)

    # Initial channel pattern within a board
    channel = np.arange(0, ch_per_board, dtype=np.int64)
    if board_flip_z:
        channel = channel[::-1]

    # Create layers as [board_counts, channels_per_board]
    layers_list = []
    for i in range(layer_count):
        tile = np.tile(channel, boards_per_layer[i]).reshape(boards_per_layer[i], ch_per_board)
        layers_list.append(tile)
    layers = np.concatenate(layers_list, axis=0).astype(np.int64)

    # Assign global channel IDs
    for boardID in range(layers.shape[0]):
        for channelID in range(ch_per_board):
            layers[boardID, channelID] = boardID * ch_per_board + layers[boardID, channelID]

    # Reshape per layer -> (boards_per_layer[i], chx, chy)
    layers_per_layer = []
    val = 0
    for i in range(layer_count):
        nboards = boards_per_layer[i]
        arr = layers[val:val + nboards].reshape(nboards, chx, chy)
        layers_per_layer.append(arr)
        val += nboards

    # Apply board flips
    val = 0
    for i in range(layer_count):
        for j in range(boards_per_layer[i]):
            if board_flip_x[val] == 1:
                layers_per_layer[i][j] = np.flip(layers_per_layer[i][j], axis=1)
            if board_flip_y[val] == 1:
                layers_per_layer[i][j] = np.flip(layers_per_layer[i][j], axis=0)
            val += 1

    # Combine boards into per-layer 2D layout
    per_layer_2d: List[np.ndarray] = []
    for i in range(layer_count):
        bpx = boards_per_layer_x[i]
        bpy = boards_per_layer_y[i]
        arr = layers_per_layer[i]
        arr = arr.reshape(bpx, bpy, chx, chy)
        arr = np.transpose(arr, (0, 2, 1, 3))
        arr = arr.reshape(bpx * chx, bpy * chy)
        per_layer_2d.append(arr)

    # Apply layer flips
    for i in range(layer_count):
        if layer_flip_x[i] == 1:
            per_layer_2d[i] = np.flip(per_layer_2d[i], axis=1)
        if layer_flip_y[i] == 1:
            per_layer_2d[i] = np.flip(per_layer_2d[i], axis=0)

    return per_layer_2d


# ============================================================
#  Track angle extraction (from in-memory tracks)
# ============================================================
def _extract_good_track_angles(tracks, chi2_max: Optional[float] = None):
    """
    From a sequence of track objects (as returned by tracker),
    extract tx, ty for tracks (optionally) with CHI2 <= chi2_max.

    Returns:
        tx_arr, ty_arr, total_tracks, rejected_tracks
    """
    tx_list: List[float] = []
    ty_list: List[float] = []
    total = 0
    rejected = 0

    if tracks is None:
        return (
            np.empty(0, dtype=np.float64),
            np.empty(0, dtype=np.float64),
            0,
            0,
        )

    for tr in tracks:
        total += 1

        # --- CHI2 (optional) ---
        chi2 = None
        try:
            chi2 = tr["CHI2"]
        except Exception:
            try:
                chi2 = tr.CHI2
            except Exception:
                chi2 = None

        if chi2_max is not None and chi2 is not None and chi2 > chi2_max:
            rejected += 1
            continue

        # --- TRACK = (dx, dy, tx, ty) ---
        try:
            track_vec = tr["TRACK"]
        except Exception:
            try:
                track_vec = tr.TRACK
            except Exception:
                rejected += 1
                continue

        if track_vec is None or len(track_vec) < 4:
            rejected += 1
            continue

        try:
            _, _, tx, ty = track_vec
        except Exception:
            rejected += 1
            continue

        tx_list.append(float(tx))
        ty_list.append(float(ty))

    tx_arr = np.asarray(tx_list, dtype=np.float64)
    ty_arr = np.asarray(ty_list, dtype=np.float64)
    return tx_arr, ty_arr, total, rejected


# ============================================================
#  Multiprocessing helpers (global hist over UNIQUEID)
# ============================================================
def _init_worker(
    detector_config_path: str,
    mutxt_config_path: str,
    analysis_config_path: str,
    data_folder: str,
):
    """
    Per-process initializer: load configs once into globals.
    """
    global _det, _mutxt, _ana, _data_folder
    from ncuhep.muography.classes import PlaneDetector, MuTxtFormat, AnalysisConfig

    logger.info(
        "[worker init] detector=%s mutxt=%s analysis=%s data_folder=%s",
        detector_config_path, mutxt_config_path, analysis_config_path, data_folder
    )

    _det = PlaneDetector()
    _det._import(detector_config_path)

    _mutxt = MuTxtFormat()
    _mutxt._import(mutxt_config_path)

    _ana = AnalysisConfig()
    _ana._import(analysis_config_path)

    _data_folder = data_folder


def _uids_to_hist_global(uids: np.ndarray, ncell_total: int) -> np.ndarray:
    """
    Convert UNIQUEID array -> global 1D histogram [0 .. ncell_total-1]
    """
    if uids.size == 0:
        return np.zeros(ncell_total, dtype=np.int64)
    uids = uids.astype(np.int64, copy=False)
    h = np.bincount(uids, minlength=ncell_total)
    if h.size < ncell_total:
        h = np.pad(h, (0, ncell_total - h.size))
    elif h.size > ncell_total:
        h = h[:ncell_total]
    return h.astype(np.int64)


def _process_one(filename: str):
    """
    Worker: process a single *_Mu.txt file.
    Returns:
      (filename, ok, err, filesize,
       h_hits, h_events, h_tracks,
       tx_arr, ty_arr, live_time_s,
       ntracks_file, nrej_file)
    """
    from ncuhep.muography import parser, identifier, tracker

    global _det, _mutxt, _ana, _data_folder

    src = Path(_data_folder) / filename
    filesize = -1.0
    logger.debug("[worker] start file=%s", filename)
    try:
        filesize = os.path.getsize(src) / (1024 * 1024)  # MiB
        logger.debug("[worker] file=%s size=%.2f MiB", filename, filesize)

        layer_count, nx_per_layer, ny_per_layer, ncell_per_layer, ncell_total = \
            build_layer_geometry(_det)

        # parse → identify → track
        events, timeelapsed, uids_hits = parser(
            str(_data_folder), filename, _mutxt, _det, _ana, True
        )
        uids_events = events["UNIQUEID"]

        events_id = identifier(events, _det)
        tracks = tracker(events_id, _det)

        if len(tracks) > 0:
            uids_tracks = np.concatenate([t["UNIQUEID"] for t in tracks])
        else:
            uids_tracks = np.empty(0, dtype=np.int64)

        # Track angles for flux (no CHI² cut by default)
        tx_arr, ty_arr, ntracks_file, nrej_file = _extract_good_track_angles(
            tracks, chi2_max=None
        )

        # live time (s)
        try:
            live_time_s = float(getattr(timeelapsed, "s", timeelapsed))
        except Exception:
            live_time_s = 0.0

        # Build global histograms over UNIQUEID
        h_hits = _uids_to_hist_global(uids_hits, ncell_total)
        h_events = _uids_to_hist_global(uids_events, ncell_total)
        h_tracks = _uids_to_hist_global(uids_tracks, ncell_total)

        logger.debug(
            "[worker] done file=%s, hits_sum=%d, events_sum=%d, tracks_sum=%d, "
            "good_tracks=%d, rejected_tracks=%d, live_time=%.3fs",
            filename, int(h_hits.sum()), int(h_events.sum()), int(h_tracks.sum()),
            int(tx_arr.size), int(nrej_file), live_time_s
        )
        return (
            filename,
            True,
            None,
            filesize,
            h_hits,
            h_events,
            h_tracks,
            tx_arr,
            ty_arr,
            live_time_s,
            ntracks_file,
            nrej_file,
        )

    except Exception:
        logger.exception("[worker] exception in file=%s", filename)
        return (
            filename,
            False,
            "Worker exception",
            filesize,
            None,
            None,
            None,
            None,
            None,
            0.0,
            0,
            0,
        )


def compute_hitmaps_parallel(
    data_folder: str,
    config_folder: str,
    selected_files: List[str],
    max_workers: Optional[int] = None,
    progress_callback=None,
):
    """
    Parallel parser/identifier/tracker with ProcessPoolExecutor.

    Returns:
      counts_hits_layers, counts_events_layers, counts_tracks_layers,
      det, summary, failures,
      tx_all, ty_all, live_time_total, total_tracks_global, total_rejected_global
    """
    logger.info(
        "compute_hitmaps_parallel: data_folder=%s config_folder=%s files=%d",
        data_folder, config_folder, len(selected_files)
    )
    if not selected_files:
        raise ValueError("No files selected for analysis.")

    from concurrent.futures import ProcessPoolExecutor, as_completed

    config_folder_path = Path(config_folder)
    detector_config_path = str(config_folder_path / "detector_config.json")
    analysis_config_path = str(config_folder_path / "analysis_config.json")
    mutxt_config_path = str(config_folder_path / "mutxt_config.json")

    det = PlaneDetector()
    logger.debug("compute_hitmaps_parallel: importing detector_config=%s", detector_config_path)
    det._import(detector_config_path)

    (
        layer_count,
        nx_per_layer,
        ny_per_layer,
        ncell_per_layer,
        ncell_total,
    ) = build_layer_geometry(det)

    if max_workers is None:
        max_workers = os.cpu_count() or 4

    successes = 0
    failures = []

    counts_hits_total = None
    counts_events_total = None
    counts_tracks_total = None

    # Flux-related accumulators
    all_tx: List[np.ndarray] = []
    all_ty: List[np.ndarray] = []
    live_time_total = 0.0
    total_tracks_global = 0
    total_rejected_global = 0

    total = len(selected_files)
    logger.info("compute_hitmaps_parallel: using max_workers=%d", max_workers)

    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=_init_worker,
        initargs=(detector_config_path, mutxt_config_path, analysis_config_path, data_folder),
    ) as ex:
        futures = {ex.submit(_process_one, fn): fn for fn in selected_files}

        done = 0
        for fut in as_completed(futures):
            done += 1
            try:
                (
                    fname,
                    ok,
                    err,
                    fs,
                    h_hits,
                    h_events,
                    h_tracks,
                    tx_arr,
                    ty_arr,
                    live_time_s,
                    ntracks_file,
                    nrej_file,
                ) = fut.result()
            except Exception as e:
                ok = False
                err = f"{type(e).__name__}: {e}"
                fname = futures[fut]
                fs = -1.0
                h_hits = h_events = h_tracks = None
                tx_arr = ty_arr = None
                live_time_s = 0.0
                ntracks_file = 0
                nrej_file = 0
                logger.exception("Exception in future for file=%s", fname)

            if ok:
                successes += 1
                # --- Hit/event/track histograms ---
                if h_hits is not None:
                    if h_hits.size != ncell_total:
                        raise ValueError(
                            f"{fname}: hist_hits size {h_hits.size}, expected {ncell_total}"
                        )
                    counts_hits_total = (
                        h_hits if counts_hits_total is None else counts_hits_total + h_hits
                    )
                if h_events is not None:
                    if h_events.size != ncell_total:
                        raise ValueError(
                            f"{fname}: hist_events size {h_events.size}, expected {ncell_total}"
                        )
                    counts_events_total = (
                        h_events if counts_events_total is None else counts_events_total + h_events
                    )
                if h_tracks is not None:
                    if h_tracks.size != ncell_total:
                        raise ValueError(
                            f"{fname}: hist_tracks size {h_tracks.size}, expected {ncell_total}"
                        )
                    counts_tracks_total = (
                        h_tracks if counts_tracks_total is None else counts_tracks_total + h_tracks
                    )

                # --- Flux-related accumulations ---
                if tx_arr is not None and tx_arr.size > 0:
                    all_tx.append(tx_arr)
                if ty_arr is not None and ty_arr.size > 0:
                    all_ty.append(ty_arr)

                live_time_total += float(live_time_s)
                total_tracks_global += int(ntracks_file)
                total_rejected_global += int(nrej_file)

            else:
                logger.error("Worker failure on file=%s: %s", fname, err)
                failures.append((fname, err, fs))

            if progress_callback is not None:
                percent = int(done * 100 / total) if total else 0
                progress_callback(percent, done, total)

    def to_layer_maps(global_arr: Optional[np.ndarray]) -> Optional[List[np.ndarray]]:
        if global_arr is None:
            return None
        maps: List[np.ndarray] = []
        offset = 0
        for i in range(layer_count):
            ncell_i = int(ncell_per_layer[i])
            nx_i = int(nx_per_layer[i])
            ny_i = int(ny_per_layer[i])
            layer_flat = global_arr[offset: offset + ncell_i]
            if layer_flat.size != ncell_i:
                raise ValueError(
                    f"Layer {i}: slice size {layer_flat.size}, expected {ncell_i}"
                )
            maps.append(layer_flat.reshape((nx_i, ny_i)))
            offset += ncell_i
        if offset != global_arr.size:
            raise ValueError(
                f"Used {offset} cells but global arr has {global_arr.size} entries."
            )
        return maps

    counts_hits_layers = to_layer_maps(counts_hits_total)
    counts_events_layers = to_layer_maps(counts_events_total)
    counts_tracks_layers = to_layer_maps(counts_tracks_total)

    summary = f"Done. Success {successes}/{total}"
    if failures:
        summary += f" | Failures: {len(failures)}"

    logger.info("compute_hitmaps_parallel summary: %s", summary)

    if all_tx:
        tx_all = np.concatenate(all_tx)
    else:
        tx_all = np.empty(0, dtype=np.float64)

    if all_ty:
        ty_all = np.concatenate(all_ty)
    else:
        ty_all = np.empty(0, dtype=np.float64)

    logger.info(
        "Flux accumulators: total_tracks_global=%d, used_tracks=%d, "
        "rejected_tracks=%d, live_time_total=%.3fs",
        total_tracks_global,
        tx_all.size,
        total_rejected_global,
        live_time_total,
    )

    return (
        counts_hits_layers,
        counts_events_layers,
        counts_tracks_layers,
        det,
        summary,
        failures,
        tx_all,
        ty_all,
        live_time_total,
        total_tracks_global,
        total_rejected_global,
    )


# ============================================================
#  Flux computation from in-memory track angles
# ============================================================
def compute_flux_from_tracks(
    tx_all: np.ndarray,
    ty_all: np.ndarray,
    total_live_time_s: float,
    recon_path: str,
    fov_deg: float = 13.0,
):
    """
    Compute flux directly from in-memory track angles (tx_all, ty_all)
    and total live time (seconds), using the provided recon basis.

    Returns:
        flux_raw, unc_raw, fov_deg, unit_str, summary_string
    """
    if tx_all is None or ty_all is None or tx_all.size == 0:
        raise ValueError("No track angles provided for flux computation.")
    if total_live_time_s <= 0.0:
        raise ValueError("Total live time must be > 0 for flux computation.")

    logger.info(
        "compute_flux_from_tracks: Ntracks=%d, time=%.3fs, recon=%s, fov=%g",
        tx_all.size, total_live_time_s, recon_path, fov_deg
    )

    recon = np.load(recon_path)
    basis = recon["basis"]
    measured_angles = recon["measured_angles"]
    geom_array = recon["geometric_factor"]

    geometric_factor = GeometricFactor()
    geometric_factor.m2_sr = geom_array

    ux = np.unique(measured_angles[0])
    uy = np.unique(measured_angles[1])

    # counts array has the same shape as measured_angles[0]
    counts = np.zeros_like(measured_angles[0], dtype=np.float64)

    # Vectorized binning: tx,ty (rad) -> mrad grid used by recon (round to 0.1 mrad)
    tx_scaled = np.round(tx_all * 1000.0, 1)
    ty_scaled = np.round(ty_all * 1000.0, 1)

    ix = np.searchsorted(ux, tx_scaled)
    iy = np.searchsorted(uy, ty_scaled)

    valid_mask = (
        (ix >= 0) & (ix < len(ux)) &
        (iy >= 0) & (iy < len(uy))
    )
    ix_valid = ix[valid_mask]
    iy_valid = iy[valid_mask]

    np.add.at(counts, (ix_valid, iy_valid), 1)

    total_tracks = tx_all.size
    valid_tracks = ix_valid.size

    summary = (
        f"Flux: total tracks={total_tracks}, used={valid_tracks}, "
        f"time={total_live_time_s:.1f}s"
    )
    logger.info("compute_flux_from_tracks summary: %s", summary)

    # Build N(θx, θy) and U(θx, θy) in basis space
    N = Counts()
    U = Counts()

    N.counts = np.zeros_like(basis[0, 0], dtype=np.float64)

    for i in range(len(ux)):
        for j in range(len(uy)):
            s = np.sum(basis[i, j])
            if s == 0:
                continue
            weight = counts[i, j] / s
            N.counts += basis[i, j] * weight
            U.counts += basis[i, j] * np.sqrt(counts[i, j]) / s

    # Crop to field-of-view
    def crop(image, deg):
        mrad = int(np.radians(deg) * 1000)
        cx = image.shape[1] // 2
        cy = image.shape[0] // 2
        return image[cy - mrad:cy + mrad + 1, cx - mrad:cx + mrad + 1]

    geometric_factor.m2_sr = crop(geometric_factor.m2_sr, fov_deg)
    N.counts = crop(N.counts, fov_deg)
    U.counts = crop(U.counts, fov_deg)

    # Compute flux (unsmoothed)
    timeelapsed = Time()
    timeelapsed.s = float(total_live_time_s)

    flux = N / (geometric_factor * timeelapsed)
    uncertainty = U / (geometric_factor * timeelapsed)

    flux_raw = np.array(flux.counts_m2_s_sr, copy=True)
    unc_raw = np.array(uncertainty.counts_m2_s_sr, copy=True)

    logger.debug(
        "compute_flux_from_tracks: flux shape=%s, uncertainty shape=%s, unit=%s",
        flux_raw.shape, unc_raw.shape, flux.unit
    )
    return flux_raw, unc_raw, fov_deg, "$m^{-2}sr^{-1}s^{-1}$", summary


__all__ = [
    "parse_run_filename",
    "filter_files",
    "build_layer_geometry",
    "compute_layer_pixel_mapping",
    "compute_hitmaps_parallel",
    "compute_flux_from_tracks",
]
