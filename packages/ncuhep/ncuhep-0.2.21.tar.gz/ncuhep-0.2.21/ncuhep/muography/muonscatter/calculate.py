#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calculate_parallel.py

Parallel multi-GPU (one process per GPU) with per-GPU tqdm bars in the main process.

Key fixes vs your crashing version:
- Use mp_context.Manager().Queue() (pickle-safe) instead of mp_context.Queue()
- Do NOT pass big numpy arrays through ProcessPoolExecutor (would pickle) -> dump to .npy, load via mmap in worker
- Workers report progress via manager queue; main thread renders per-GPU tqdm bars.

Works on Linux + Windows.
"""

from __future__ import annotations

import os
import time
import uuid
import tempfile
import threading
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, List, Tuple, Dict

import numpy as np
import cv2
from numba import cuda

try:
    from tqdm import tqdm
    HAS_TQDM = True
except Exception:
    tqdm = None
    HAS_TQDM = False

# ----------------------------
# Your project imports (KEEP as in your codebase)
# ----------------------------
from .constructor import params_array
from ..utils.coordinates import det2zenith
from .flux_model import differential_flux
from .gpu import splat_kernels, splat_kernels_track
from .constants import (
    sigma_window_ratio_lower,
    sigma_window_ratio_middle,
    sigma_window_ratio_upper,
)
from ..profiler import Profiler, print_profile


# =============================================================================
# Multiprocessing context (CUDA-safe)
# =============================================================================

def _mp_context():
    """
    CUDA + multiprocessing:
    - Windows: spawn only
    - Linux: forkserver is safer than fork for CUDA; fallback to spawn if not available
    """
    if os.name == "nt":
        return mp.get_context("spawn")
    # Linux / POSIX
    try:
        return mp.get_context("forkserver")
    except Exception:
        return mp.get_context("spawn")


# =============================================================================
# Shared helpers (same logic as your existing code)
# =============================================================================

def params_array_wrapper(energy, L, THX, THY, PhiE, window_size, flatten=True):
    idx = np.arange(THX.shape[0])
    idy = np.arange(THY.shape[1])
    IDX, IDY = np.meshgrid(idx, idy, indexing="ij")
    params = params_array(energy, L, THX, THY, IDX, IDY, PhiE, window_size)
    if flatten:
        params = params.reshape(-1, params.shape[-1])
    return params


def crop_indices(THX, THY, angle_deg):
    mrad = int(np.round(np.radians(angle_deg) * 1000))
    thx = THX[:, 0]
    thy = THY[0, :]

    idx_min = np.argmin(np.abs(thx + mrad * 0.001))
    idx_max = np.argmin(np.abs(thx - mrad * 0.001))
    idy_min = np.argmin(np.abs(thy + mrad * 0.001))
    idy_max = np.argmin(np.abs(thy - mrad * 0.001))

    if idx_min > idx_max:
        idx_min, idx_max = idx_max, idx_min
    if idy_min > idy_max:
        idy_min, idy_max = idy_max, idy_min

    return idx_min, idx_max, idy_min, idy_max


def crop(THX, THY, OUTPUT, angle_deg):
    idx_min, idx_max, idy_min, idy_max = crop_indices(THX, THY, angle_deg)
    THX_ = THX[idx_min:idx_max + 1, idy_min:idy_max + 1]
    THY_ = THY[idx_min:idx_max + 1, idy_min:idy_max + 1]
    OUTPUT_ = OUTPUT[idx_min:idx_max + 1, idy_min:idy_max + 1]
    return THX_, THY_, OUTPUT_


def split_params_strided(params: np.ndarray, n_parts: int) -> List[np.ndarray]:
    if n_parts <= 0:
        raise ValueError("n_parts must be >= 1")
    return [np.ascontiguousarray(params[i::n_parts]) for i in range(n_parts)]


def split_branches_for_gpus(params0, params1, params2, params3, n_gpus):
    chunks0 = split_params_strided(params0, n_gpus)
    chunks1 = split_params_strided(params1, n_gpus)
    chunks2 = split_params_strided(params2, n_gpus)
    chunks3 = split_params_strided(params3, n_gpus)
    return [(chunks0[g], chunks1[g], chunks2[g], chunks3[g]) for g in range(n_gpus)]


# =============================================================================
# Disk-backed params transfer (avoid pickling huge arrays)
# =============================================================================

def _dump_npy(tmpdir: str, arr: np.ndarray, tag: str) -> str:
    """
    Save array to .npy and return path.
    Worker will load with mmap_mode='r' to avoid RAM blowup.
    """
    path = os.path.join(tmpdir, f"{tag}_{uuid.uuid4().hex}.npy")
    np.save(path, np.ascontiguousarray(arr))
    return path


def _load_npy_mmap(path: str, dtype=np.float32) -> np.ndarray:
    """
    Load saved .npy as memory map.
    """
    a = np.load(path, mmap_mode="r")
    # ensure dtype float32 for kernels
    if a.dtype != np.float32:
        return np.asarray(a, dtype=np.float32)
    return a


# =============================================================================
# Progress monitor (per-GPU tqdm bars in main process)
# =============================================================================

def _progress_monitor(q, totals: List[int], desc_prefix: str = "GPU"):
    """
    Main-process thread.
    Receives messages (g_idx, n_done) and updates tqdm bars.

    Sentinel: (g_idx, None) means worker g_idx finished.
    """
    if not HAS_TQDM:
        # Drain queue until all finished
        finished = 0
        n = len(totals)
        while finished < n:
            g, inc = q.get()
            if inc is None:
                finished += 1
        return

    bars = []
    for g_idx, tot in enumerate(totals):
        bars.append(tqdm(total=int(tot), desc=f"{desc_prefix} {g_idx}", position=g_idx, leave=True, unit="job"))

    finished = 0
    n = len(totals)
    try:
        while finished < n:
            g_idx, inc = q.get()
            if inc is None:
                finished += 1
                continue
            if 0 <= g_idx < n and inc:
                bars[g_idx].update(int(inc))
    finally:
        for b in bars:
            try:
                b.close()
            except Exception:
                pass


# =============================================================================
# Worker helpers
# =============================================================================

def _run_kernel_chunked(kernel, params_dev, img_dev, n_jobs: int, tpb: int, blocks_per_launch: int,
                        progress_q, g_idx: int):
    """
    Chunked kernel launch:
      blocks_per_grid = chunk_size (1 block per row)
    Reports progress per chunk to main via progress_q.
    """
    start = 0
    while start < n_jobs:
        end = min(start + blocks_per_launch, n_jobs)
        chunk = end - start
        # slice view on device is not trivial; easiest: pass offset via device array slice
        # Numba supports device array slicing
        kernel[chunk, tpb](params_dev[start:end], img_dev)
        cuda.synchronize()
        if progress_q is not None:
            progress_q.put((g_idx, chunk))
        start = end


def _run_kernel_chunked_track(kernel, params_dev, img_dev, track_dev, n_jobs: int, tpb: int,
                              blocks_per_launch: int, progress_q, g_idx: int):
    start = 0
    while start < n_jobs:
        end = min(start + blocks_per_launch, n_jobs)
        chunk = end - start
        kernel[chunk, tpb](params_dev[start:end], img_dev, track_dev)
        cuda.synchronize()
        if progress_q is not None:
            progress_q.put((g_idx, chunk))
        start = end


# =============================================================================
# Worker: ONE GPU per PROCESS (non-tracking)
# =============================================================================

def _worker_gpu_nontrack_from_files(
    g_idx: int,
    p0_path: str, p1_path: str, p2_path: str, p3_path: str,
    H: int, W: int,
    pixel_size: float, window_size: float, bins: int,
    blocks_per_launch: int,
    progress_q,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Worker process:
    - binds to one GPU (cuda.select_device)
    - loads params from npy (mmap)
    - builds kernels locally
    - returns partial images
    """
    import numpy as np
    from numba import cuda
    from .gpu import splat_kernels

    cuda.select_device(int(g_idx))

    p0 = _load_npy_mmap(p0_path)
    p1 = _load_npy_mmap(p1_path)
    p2 = _load_npy_mmap(p2_path)
    p3 = _load_npy_mmap(p3_path)

    splat1_kernel, splat2_kernel, splat3_kernel = splat_kernels(float(pixel_size), float(window_size), int(bins))

    img0 = np.zeros((H, W), dtype=np.float32)
    img1 = np.zeros((H, W), dtype=np.float32)
    img2 = np.zeros((H, W), dtype=np.float32)
    img3 = np.zeros((H, W), dtype=np.float32)

    # Branch 0: CPU direct accumulate (counts as progress too)
    if p0.shape[0] > 0:
        for p in np.asarray(p0, dtype=np.float32):
            (_A,_sigma,_s2,_s3,_n,_f1,_f2, sr, _thx, _thy, idx, idy, _window, PhiE, _d1, _d2) = p
            img0[int(idx), int(idy)] += float(PhiE * sr)
        if progress_q is not None:
            progress_q.put((g_idx, int(p0.shape[0])))

    # Branches 1-3: GPU
    def _gpu_branch(params, kernel, img, tpb):
        n = int(params.shape[0])
        if n <= 0:
            return
        img_dev = cuda.to_device(img)
        params_dev = cuda.to_device(np.asarray(params, dtype=np.float32))
        _run_kernel_chunked(kernel, params_dev, img_dev, n, tpb, int(blocks_per_launch), progress_q, g_idx)
        img_dev.copy_to_host(img)

    _gpu_branch(p1, splat1_kernel, img1, 32)
    _gpu_branch(p2, splat2_kernel, img2, 32)
    _gpu_branch(p3, splat3_kernel, img3, 256)

    # signal finished
    if progress_q is not None:
        progress_q.put((g_idx, None))

    return img0, img1, img2, img3


# =============================================================================
# Worker: ONE GPU per PROCESS (tracking -> memmap)
# =============================================================================

def _worker_gpu_track_to_memmap_from_files(
    g_idx: int,
    p0_path: str, p1_path: str, p2_path: str, p3_path: str,
    H: int, W: int,
    pixel_size: float, window_size: float, bins: int,
    blocks_per_launch: int,
    track_path: str,
    track_dtype: str,
    progress_q,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, str]:
    import numpy as np
    from numba import cuda
    from .gpu import splat_kernels_track

    cuda.select_device(int(g_idx))

    p0 = _load_npy_mmap(p0_path)
    p1 = _load_npy_mmap(p1_path)
    p2 = _load_npy_mmap(p2_path)
    p3 = _load_npy_mmap(p3_path)

    splat1_kernel, splat2_kernel, splat3_kernel = splat_kernels_track(float(pixel_size), float(window_size), int(bins))

    img0 = np.zeros((H, W), dtype=np.float32)
    img1 = np.zeros((H, W), dtype=np.float32)
    img2 = np.zeros((H, W), dtype=np.float32)
    img3 = np.zeros((H, W), dtype=np.float32)

    dtype = np.dtype(track_dtype)
    track = np.memmap(track_path, mode="w+", dtype=dtype, shape=(H, W, H, W))
    track[...] = 0
    track.flush()

    # Branch 0: CPU direct accumulate + TRACK diag
    if p0.shape[0] > 0:
        for p in np.asarray(p0, dtype=np.float32):
            (_A,_sigma,_s2,_s3,_n,_f1,_f2, sr, _thx, _thy, idx, idy, _window, PhiE, _d1, _d2) = p
            ii = int(idx); jj = int(idy)
            val = float(PhiE * sr)
            img0[ii, jj] += val
            track[ii, jj, ii, jj] += val
        if progress_q is not None:
            progress_q.put((g_idx, int(p0.shape[0])))

    # upload TRACK once
    track_dev = cuda.to_device(np.asarray(track, dtype=np.float32))

    def _gpu_branch_track(params, kernel, img, tpb):
        n = int(params.shape[0])
        if n <= 0:
            return
        img_dev = cuda.to_device(img)
        params_dev = cuda.to_device(np.asarray(params, dtype=np.float32))
        _run_kernel_chunked_track(kernel, params_dev, img_dev, track_dev, n, tpb, int(blocks_per_launch), progress_q, g_idx)
        img_dev.copy_to_host(img)

    _gpu_branch_track(p1, splat1_kernel, img1, 32)
    _gpu_branch_track(p2, splat2_kernel, img2, 32)
    _gpu_branch_track(p3, splat3_kernel, img3, 256)

    # bring TRACK back and flush
    track_dev.copy_to_host(track)
    track.flush()

    if progress_q is not None:
        progress_q.put((g_idx, None))

    return img0, img1, img2, img3, track_path


# =============================================================================
# Public API: calculate (RESULT only) - parallel multi-GPU + per-GPU tqdm
# =============================================================================

def calculate(
    path,
    density_map,
    crop_angle,
    E_min,
    E_max,
    E_N,
    E_scale,
    window_size=20.0,
    bins=128,
    *,
    profiler: Optional[Profiler] = None,
    profile: bool = False,
    max_gpus: Optional[int] = None,
    blocks_per_launch: int = 4096,   # progress granularity + overhead tradeoff
    tmpdir: Optional[str] = None,    # where to dump params chunks
):
    wall_t0 = time.perf_counter()
    prof = profiler if profiler is not None else Profiler()

    mp_context = _mp_context()

    if tmpdir is None:
        tmpdir = tempfile.gettempdir()
    run_dir = os.path.join(tmpdir, f"calc_parallel_{uuid.uuid4().hex}")
    os.makedirs(run_dir, exist_ok=True)

    # ---------------- I/O ----------------
    with prof.section("io:load_npz"):
        data = np.load(path, allow_pickle=True)
        meta = data["meta"].item()
        THX = data["THX_rad"]
        THY = data["THY_rad"]
        THX_mrad = data["THX_mrad"]
        THY_mrad = data["THY_mrad"]

    # ---------------- pixel size ----------------
    with prof.section("setup:pixel_size"):
        x_ = THX[:, 0]
        y_ = THX[0, :]
        dx_ = np.abs(x_[1] - x_[0])
        dy_ = np.abs(y_[1] - y_[0])
        pixel_size = float(np.max([dx_, dy_]))
        print(f"Pixel size: {pixel_size * 1000:.3f} mrad")

    # ---------------- density map ----------------
    with prof.section("density:prepare"):
        if density_map is None:
            density_map = np.ones_like(THX, dtype=np.float32) * 2.65
        else:
            THX_cropped, THY_cropped, _ = crop(THX, THY, np.zeros_like(THX), crop_angle)
            density_map = cv2.resize(
                density_map,
                (THX_cropped.shape[1], THX_cropped.shape[0]),
                interpolation=cv2.INTER_AREA,
            )
            pad_y = THX.shape[0] - density_map.shape[0]
            pad_x = THX.shape[1] - density_map.shape[1]
            pad_width = (
                (pad_y // 2, pad_y - pad_y // 2),
                (pad_x // 2, pad_x - pad_x // 2),
            )
            density_map = np.pad(density_map, pad_width, mode="edge")

    # ---------------- thickness & zenith ----------------
    with prof.section("thickness:scale_and_zenith"):
        L = data["L"] / 2.65 * density_map
        L = np.clip(L, 1, 3500)
        zenith = det2zenith(
            THX_mrad,
            -THY_mrad,
            np.radians(meta["angle_deg"]),
            0,
        )

    # ---------------- build params ----------------
    with prof.section("loop:build_all_params"):
        if E_scale == "linear":
            energies = np.linspace(E_min, E_max, E_N)
        elif E_scale == "log":
            energies = np.logspace(np.log10(E_min), np.log10(E_max), E_N)
        else:
            raise ValueError(f"Invalid E_scale: {E_scale}")

        dE = energies[1:] - energies[:-1]
        energies_mid = 0.5 * (energies[1:] + energies[:-1])

        params = None
        for i, energy in enumerate(energies_mid):
            PhiE = differential_flux(zenith, energy) * dE[i]
            params_ = params_array_wrapper(energy, L, THX, THY, PhiE, pixel_size, flatten=True)
            params_ = params_[params_[:, 7] > 0]
            if params_ is None or params_.size == 0:
                continue
            params = params_ if params is None else np.concatenate((params, params_), axis=0)

    if params is None or params.shape[0] == 0:
        return THX, THY, np.zeros_like(THX, dtype=np.float32), density_map

    # ---------------- split branches ----------------
    with prof.section("params:sort_and_split"):
        argsort = np.argsort(params[:, 1])
        params = params[argsort]
        sigma_ps = params[:, 1] / pixel_size

        mask0 = sigma_ps < sigma_window_ratio_lower
        mask1 = (sigma_ps > sigma_window_ratio_lower) & (sigma_ps < sigma_window_ratio_middle)
        mask2 = (sigma_ps >= sigma_window_ratio_middle) & (sigma_ps < sigma_window_ratio_upper)
        mask3 = sigma_ps >= sigma_window_ratio_upper

        params0 = params[mask0]
        params1 = params[mask1]
        params2 = params[mask2]
        params3 = params[mask3]

    # ---------------- GPUs ----------------
    with prof.section("gpu:setup_devices"):
        all_gpus = list(cuda.gpus)
        if max_gpus is not None:
            all_gpus = all_gpus[:max_gpus]
        n_gpus = len(all_gpus)
        if n_gpus == 0:
            raise RuntimeError("No CUDA GPUs available.")
        gpu_parts = split_branches_for_gpus(params0, params1, params2, params3, n_gpus)

    H, W = THX.shape

    # Dump per-GPU params to files (avoid pickling huge arrays)
    with prof.section("ipc:dump_params_to_files"):
        gpu_files = []
        totals = []
        for g_idx in range(n_gpus):
            p0_g, p1_g, p2_g, p3_g = gpu_parts[g_idx]
            p0_path = _dump_npy(run_dir, p0_g, f"p0_g{g_idx}")
            p1_path = _dump_npy(run_dir, p1_g, f"p1_g{g_idx}")
            p2_path = _dump_npy(run_dir, p2_g, f"p2_g{g_idx}")
            p3_path = _dump_npy(run_dir, p3_g, f"p3_g{g_idx}")
            gpu_files.append((p0_path, p1_path, p2_path, p3_path))
            totals.append(int(len(p0_g) + len(p1_g) + len(p2_g) + len(p3_g)))

    # Manager queue (pickle-safe) + monitor thread (tqdm bars)
    manager = mp_context.Manager()
    progress_q = manager.Queue(maxsize=200_000)

    mon = threading.Thread(target=_progress_monitor, args=(progress_q, totals, "GPU"), daemon=True)
    mon.start()

    partial0, partial1, partial2, partial3 = [], [], [], []

    try:
        with prof.section("gpu:launch_parallel_processes"):
            with ProcessPoolExecutor(max_workers=n_gpus, mp_context=mp_context) as ex:
                futures = []
                for g_idx in range(n_gpus):
                    p0_path, p1_path, p2_path, p3_path = gpu_files[g_idx]
                    futures.append(ex.submit(
                        _worker_gpu_nontrack_from_files,
                        int(g_idx),
                        p0_path, p1_path, p2_path, p3_path,
                        int(H), int(W),
                        float(pixel_size), float(window_size), int(bins),
                        int(blocks_per_launch),
                        progress_q,
                    ))

                for fut in futures:
                    img0, img1, img2, img3 = fut.result()
                    partial0.append(img0)
                    partial1.append(img1)
                    partial2.append(img2)
                    partial3.append(img3)

    finally:
        # Ensure monitor exits even if something crashes
        try:
            for _ in range(n_gpus):
                progress_q.put((0, None))
        except Exception:
            pass
        mon.join(timeout=5.0)
        try:
            manager.shutdown()
        except Exception:
            pass

        # cleanup params files
        for p0_path, p1_path, p2_path, p3_path in gpu_files:
            for p in (p0_path, p1_path, p2_path, p3_path):
                try:
                    os.remove(p)
                except Exception:
                    pass
        try:
            os.rmdir(run_dir)
        except Exception:
            pass

    # ---------------- reduce ----------------
    with prof.section("post:reduce_partial_results"):
        RESULT0 = np.sum(partial0, axis=0)
        RESULT1 = np.sum(partial1, axis=0)
        RESULT2 = np.sum(partial2, axis=0)
        RESULT3 = np.sum(partial3, axis=0)

    # ---------------- crop/combine ----------------
    with prof.section("post:crop_and_combine"):
        _, _, RESULT0_c = crop(THX, THY, RESULT0, crop_angle)
        _, _, RESULT1_c = crop(THX, THY, RESULT1, crop_angle)
        _, _, RESULT2_c = crop(THX, THY, RESULT2, crop_angle)
        THX_c, THY_c, RESULT3_c = crop(THX, THY, RESULT3, crop_angle)
        RESULT = RESULT0_c + RESULT1_c + RESULT2_c + RESULT3_c

    if profile:
        print_profile("calculate_parallel()", prof)
        wall_t1 = time.perf_counter()
        print(f"[calculate_parallel] wall time = {wall_t1 - wall_t0:.3f} s")

    return THX_c, THY_c, RESULT, L


# =============================================================================
# Public API: calculate_and_track (RESULT + TRACK memmap) - parallel multi-GPU
# =============================================================================

def calculate_and_track(
    path,
    density_map,
    crop_angle,
    E_min,
    E_max,
    E_N,
    E_scale,
    window_size=20.0,
    bins=128,
    *,
    profiler: Optional[Profiler] = None,
    profile: bool = False,
    max_gpus: Optional[int] = None,
    blocks_per_launch: int = 4096,
    tmpdir: Optional[str] = None,
    track_dir: Optional[str] = None,
    track_dtype: str = "float32",
    return_full_track: bool = False,   # default False: returning full TRACK can be enormous
):
    wall_t0 = time.perf_counter()
    prof = profiler if profiler is not None else Profiler()

    mp_context = _mp_context()

    if tmpdir is None:
        tmpdir = tempfile.gettempdir()
    run_dir = os.path.join(tmpdir, f"calc_track_parallel_{uuid.uuid4().hex}")
    os.makedirs(run_dir, exist_ok=True)

    if track_dir is None:
        track_dir = tempfile.gettempdir()
    os.makedirs(track_dir, exist_ok=True)

    # ---------------- I/O ----------------
    with prof.section("io:load_npz"):
        data = np.load(path, allow_pickle=True)
        meta = data["meta"].item()
        THX = data["THX_rad"]
        THY = data["THY_rad"]
        THX_mrad = data["THX_mrad"]
        THY_mrad = data["THY_mrad"]

    # ---------------- pixel size ----------------
    with prof.section("setup:pixel_size"):
        x_ = THX[:, 0]
        y_ = THY[0, :]
        dx_ = np.abs(x_[1] - x_[0])
        dy_ = np.abs(y_[1] - y_[0])
        pixel_size = float(np.max([dx_, dy_]))
        print(f"Pixel size: {pixel_size * 1000:.3f} mrad")

    # ---------------- density map ----------------
    with prof.section("density:prepare"):
        if density_map is None:
            density_map = np.ones_like(THX, dtype=np.float32) * 2.65
        else:
            THX_cropped, THY_cropped, _ = crop(THX, THY, np.zeros_like(THX), crop_angle)
            density_map = cv2.resize(
                density_map,
                (THX_cropped.shape[1], THX_cropped.shape[0]),
                interpolation=cv2.INTER_AREA,
            )
            pad_y = THX.shape[0] - density_map.shape[0]
            pad_x = THX.shape[1] - density_map.shape[1]
            pad_width = (
                (pad_y // 2, pad_y - pad_y // 2),
                (pad_x // 2, pad_x - pad_x // 2),
            )
            density_map = np.pad(density_map, pad_width, mode="edge")

    # ---------------- thickness & zenith ----------------
    with prof.section("thickness:scale_and_zenith"):
        L = data["L"] / 2.65 * density_map
        L = np.clip(L, 1, 3500)
        zenith = det2zenith(
            THX_mrad,
            -THY_mrad,
            np.radians(meta["angle_deg"]),
            0,
        )

    # ---------------- build params ----------------
    with prof.section("loop:build_all_params"):
        if E_scale == "linear":
            energies = np.linspace(E_min, E_max, E_N)
        elif E_scale == "log":
            energies = np.logspace(np.log10(E_min), np.log10(E_max), E_N)
        else:
            raise ValueError(f"Invalid E_scale: {E_scale}")

        dE = energies[1:] - energies[:-1]
        energies_mid = 0.5 * (energies[1:] + energies[:-1])

        params = None
        for i, energy in enumerate(energies_mid):
            PhiE = differential_flux(zenith, energy) * dE[i]
            params_ = params_array_wrapper(energy, L, THX, THY, PhiE, pixel_size, flatten=True)
            params_ = params_[params_[:, 7] > 0]
            if params_ is None or params_.size == 0:
                continue
            params = params_ if params is None else np.concatenate((params, params_), axis=0)

    if params is None or params.shape[0] == 0:
        return (
            THX, THY,
            np.zeros_like(THX, dtype=np.float32),
            density_map,
            np.zeros((0, 0, 0, 0), dtype=np.float32),
            np.zeros((0, 0), dtype=np.float32),
            np.zeros((0, 0, 0, 0), dtype=np.float32),
        )

    # ---------------- split branches ----------------
    with prof.section("params:sort_and_split"):
        argsort = np.argsort(params[:, 1])
        params = params[argsort]
        sigma_ps = params[:, 1] / pixel_size

        mask0 = sigma_ps < sigma_window_ratio_lower
        mask1 = (sigma_ps > sigma_window_ratio_lower) & (sigma_ps < sigma_window_ratio_middle)
        mask2 = (sigma_ps >= sigma_window_ratio_middle) & (sigma_ps < sigma_window_ratio_upper)
        mask3 = sigma_ps >= sigma_window_ratio_upper

        params0 = params[mask0]
        params1 = params[mask1]
        params2 = params[mask2]
        params3 = params[mask3]

    # ---------------- GPUs ----------------
    with prof.section("gpu:setup_devices"):
        all_gpus = list(cuda.gpus)
        if max_gpus is not None:
            all_gpus = all_gpus[:max_gpus]
        n_gpus = len(all_gpus)
        if n_gpus == 0:
            raise RuntimeError("No CUDA GPUs available.")
        gpu_parts = split_branches_for_gpus(params0, params1, params2, params3, n_gpus)

    H, W = THX.shape
    track_bytes = np.dtype(track_dtype).itemsize * H * W * H * W
    print(f"TRACK per GPU memmap size: {track_bytes / (1024**3):.3f} GB (dtype={track_dtype})")

    # Dump params to files
    with prof.section("ipc:dump_params_to_files"):
        gpu_files = []
        track_paths = []
        totals = []
        for g_idx in range(n_gpus):
            p0_g, p1_g, p2_g, p3_g = gpu_parts[g_idx]
            p0_path = _dump_npy(run_dir, p0_g, f"p0_g{g_idx}")
            p1_path = _dump_npy(run_dir, p1_g, f"p1_g{g_idx}")
            p2_path = _dump_npy(run_dir, p2_g, f"p2_g{g_idx}")
            p3_path = _dump_npy(run_dir, p3_g, f"p3_g{g_idx}")
            gpu_files.append((p0_path, p1_path, p2_path, p3_path))

            tp = os.path.join(track_dir, f"track_gpu{g_idx}_{uuid.uuid4().hex}.mmap")
            track_paths.append(tp)

            totals.append(int(len(p0_g) + len(p1_g) + len(p2_g) + len(p3_g)))

    # progress
    manager = mp_context.Manager()
    progress_q = manager.Queue(maxsize=200_000)
    mon = threading.Thread(target=_progress_monitor, args=(progress_q, totals, "GPU"), daemon=True)
    mon.start()

    partial0, partial1, partial2, partial3 = [], [], [], []
    track_written_paths = []

    try:
        with prof.section("gpu:launch_parallel_processes"):
            with ProcessPoolExecutor(max_workers=n_gpus, mp_context=mp_context) as ex:
                futures = []
                for g_idx in range(n_gpus):
                    p0_path, p1_path, p2_path, p3_path = gpu_files[g_idx]
                    futures.append(ex.submit(
                        _worker_gpu_track_to_memmap_from_files,
                        int(g_idx),
                        p0_path, p1_path, p2_path, p3_path,
                        int(H), int(W),
                        float(pixel_size), float(window_size), int(bins),
                        int(blocks_per_launch),
                        track_paths[g_idx],
                        track_dtype,
                        progress_q,
                    ))

                for fut in futures:
                    img0, img1, img2, img3, tp = fut.result()
                    partial0.append(img0)
                    partial1.append(img1)
                    partial2.append(img2)
                    partial3.append(img3)
                    track_written_paths.append(tp)

    finally:
        try:
            for _ in range(n_gpus):
                progress_q.put((0, None))
        except Exception:
            pass
        mon.join(timeout=5.0)
        try:
            manager.shutdown()
        except Exception:
            pass

        # cleanup params files
        for p0_path, p1_path, p2_path, p3_path in gpu_files:
            for p in (p0_path, p1_path, p2_path, p3_path):
                try:
                    os.remove(p)
                except Exception:
                    pass
        try:
            os.rmdir(run_dir)
        except Exception:
            pass

    # reduce RESULT
    with prof.section("post:reduce_partial_results"):
        RESULT0 = np.sum(partial0, axis=0)
        RESULT1 = np.sum(partial1, axis=0)
        RESULT2 = np.sum(partial2, axis=0)
        RESULT3 = np.sum(partial3, axis=0)

    # reduce TRACK by streaming memmaps (avoid huge RAM spike)
    with prof.section("post:reduce_track_memmaps"):
        track_sum_path = os.path.join(track_dir, f"track_sum_{uuid.uuid4().hex}.mmap")
        TRACK = np.memmap(track_sum_path, mode="w+", dtype=np.dtype(track_dtype), shape=(H, W, H, W))
        TRACK[...] = 0.0

        for tp in track_written_paths:
            mm = np.memmap(tp, mode="r", dtype=np.dtype(track_dtype), shape=(H, W, H, W))
            TRACK[...] += mm[...]
            del mm
            try:
                os.remove(tp)
            except Exception:
                pass

        TRACK.flush()

    # crop + combine
    with prof.section("post:crop_and_combine"):
        idx_min, idx_max, idy_min, idy_max = crop_indices(THX, THY, crop_angle)

        THX_c = THX[idx_min:idx_max + 1, idy_min:idy_max + 1]
        THY_c = THY[idx_min:idx_max + 1, idy_min:idy_max + 1]

        RESULT0_c = RESULT0[idx_min:idx_max + 1, idy_min:idy_max + 1]
        RESULT1_c = RESULT1[idx_min:idx_max + 1, idy_min:idy_max + 1]
        RESULT2_c = RESULT2[idx_min:idx_max + 1, idy_min:idy_max + 1]
        RESULT3_c = RESULT3[idx_min:idx_max + 1, idy_min:idy_max + 1]
        RESULT_c = RESULT0_c + RESULT1_c + RESULT2_c + RESULT3_c

        TRACK_SUM_CHECK = np.sum(TRACK, axis=(0, 1))[idx_min:idx_max + 1, idy_min:idy_max + 1].astype(np.float32)

        TRACK_c = TRACK[
            idx_min:idx_max + 1,
            idy_min:idy_max + 1,
            idx_min:idx_max + 1,
            idy_min:idy_max + 1,
        ].astype(np.float32)

    if return_full_track:
        # WARNING: can be massive
        TRACK_full = np.asarray(TRACK, dtype=np.float32)
    else:
        TRACK_full = np.zeros((0, 0, 0, 0), dtype=np.float32)

    # keep sum memmap for debugging; delete if you want
    # try: os.remove(track_sum_path) except: pass

    if profile:
        print_profile("calculate_and_track_parallel()", prof)
        wall_t1 = time.perf_counter()
        print(f"[calculate_and_track_parallel] wall time = {wall_t1 - wall_t0:.3f} s")

    return THX_c, THY_c, RESULT_c, density_map, TRACK_c, TRACK_SUM_CHECK, TRACK_full


# =============================================================================
# Windows-safe entry point
# =============================================================================
if __name__ == "__main__":
    mp.freeze_support()
