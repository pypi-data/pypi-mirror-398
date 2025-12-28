#!/usr/bin/env python3
"""
New predictor stack:

- Molière parameters (A, sigma1, s2, s3, n, w1, w2) are given by
  bivariate polynomials in (E, T), read from:

      predictors/1bivpoly_param0..6.npz  (T <= 1000 m)
      predictors/2bivpoly_param0..6.npz  (T >  1000 m)

- Survival probability P_surv(E, T) comes from

      predictors/survival_poly_global.npz

Meta in the NPZs (coeffs, term_labels, mu/std, log_space, use_E_over_T,
use_log_energy_axis, use_log_thickness_axis, log_eps) is fully used to
build the predictors.

Public API (drop-in compatible with your old forward code):

    survival_rate_ET(E, T)
    moliere_params(E, T) -> (A, sigma1, s2, s3, n, w1, w2)
    params_ET(E, T)      -> (A, sigma1, s2, s3, n, w1, w2, sr)
    params_array(E, T_array, THX, THY, IDX, IDY, PhiE, window_size)
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from numba import njit, prange

# ---------------------------------------------------------------------------
# 0. Basic configuration
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent
_DATA_DIR = _THIS_DIR / "predictors"

# T split between "1biv" and "2biv" models
_T_CUT_M = 50.0

# Parameter ordering
PARAM_NAMES = ("A", "sigma1", "s2", "s3", "n", "w1", "w2")
N_PARAMS = len(PARAM_NAMES)

# Physical limits (same spirit as your previous `limits`)
_eps = 1e-12
_LIMITS = {
    "A": (0.0, 1e8),
    "sigma1": (_eps, 1.0),
    "s2": (0.1, 10.0),
    "s3": (0.1, 10.0),
    "n": (2.0 + _eps, 10.0),
    "w1": (_eps, 1.0 - _eps),
    "w2": (_eps, 1.0 - _eps),
}


# ---------------------------------------------------------------------------
# 1. Generic bivariate polynomial predictor from NPZ meta
# ---------------------------------------------------------------------------

def _load_bivpoly_npz(path: Path) -> dict:
    """
    Load one of the {1,2}bivpoly_paramX.npz files and return its meta.
    Expected keys (from your zip):
      - coeffs          : (n_terms,)
      - term_labels     : (n_terms, 2) integer exponents (i_E, j_T)
      - mu_E, std_E     : scalars (standardization for E-axis variable)
      - mu_T, std_T     : scalars (standardization for T-axis variable)
      - param_name      : "param0"... (we map this to physical name outside)
      - log_space       : bool (poly is in log(param + log_eps))
      - log_eps         : float (small epsilon used during training)
      - use_E_over_T    : bool  (use E/T instead of E as energy axis)
      - use_log_energy_axis      : bool (log on energy axis)
      - use_log_thickness_axis   : bool (log on thickness axis)
      - deg_E, deg_T, r2, ...
    """
    z = np.load(path, allow_pickle=True)
    meta = {
        "coeffs": np.asarray(z["coeffs"], dtype=np.float64),
        "term_labels": np.asarray(z["term_labels"], dtype=np.int64),
        "mu_E": float(z["mu_E"]),
        "std_E": float(z["std_E"]),
        "mu_T": float(z["mu_T"]),
        "std_T": float(z["std_T"]),
        "log_space": bool(z["log_space"]),
        "log_eps": float(z["log_eps"]),
        "use_E_over_T": bool(z["use_E_over_T"]),
        "use_log_energy_axis": bool(z["use_log_energy_axis"]),
        "use_log_thickness_axis": bool(z["use_log_thickness_axis"]),
        "param_name": str(z["param_name"]),
    }
    return meta


def _build_bivpoly_predictor(meta: dict, phys_name: str):
    """
    Build a Numba-jitted scalar predictor:

        f(E, T) -> param_value

    using all the meta inside the NPZ.
    """

    coeffs = np.ascontiguousarray(meta["coeffs"], dtype=np.float64)
    term_labels = np.ascontiguousarray(meta["term_labels"], dtype=np.int64)

    mu_E = float(meta["mu_E"])
    std_E = float(meta["std_E"])
    mu_T = float(meta["mu_T"])
    std_T = float(meta["std_T"])

    log_space = bool(meta["log_space"])
    log_eps = float(meta["log_eps"])

    use_E_over_T = bool(meta["use_E_over_T"])
    use_log_E = bool(meta["use_log_energy_axis"])
    use_log_T = bool(meta["use_log_thickness_axis"])

    vmin, vmax = _LIMITS.get(phys_name, (-1e300, 1e300))

    @njit(cache=True)
    def predict(E, T):
        # --- 1) build axis variables ----------------------------------------
        if use_E_over_T:
            x = E / T
        else:
            x = E

        if use_log_E:
            if x < log_eps:
                x = log_eps
            x = math.log(x)

        if use_log_T:
            y = T
            if y < log_eps:
                y = log_eps
            y = math.log(y)
        else:
            y = T

        # --- 2) standardize to z_E, z_T -------------------------------------
        if std_E != 0.0:
            zE = (x - mu_E) / std_E
        else:
            zE = x - mu_E

        if std_T != 0.0:
            zT = (y - mu_T) / std_T
        else:
            zT = y - mu_T

        # --- 3) evaluate polynomial in (zE, zT) -----------------------------
        acc = 0.0
        n_terms = term_labels.shape[0]
        for i in range(n_terms):
            pE = term_labels[i, 0]
            pT = term_labels[i, 1]
            acc += coeffs[i] * (zE ** pE) * (zT ** pT)

        # --- 4) undo log-space if needed ------------------------------------
        if log_space:
            val = np.exp(acc) - log_eps
        else:
            val = acc

        # --- 5) clamp to physical limits ------------------------------------
        if val < vmin:
            val = vmin
        if val > vmax:
            val = vmax
        return val

    return predict


# ---------------------------------------------------------------------------
# 2. Build piecewise predictors for each Molière parameter
# ---------------------------------------------------------------------------

# Load all 1biv / 2biv models
_biv_lo_meta = []
_biv_hi_meta = []
for i, pname in enumerate(PARAM_NAMES):
    path_lo = _DATA_DIR / f"4bivpoly_param{i}.npz"
    path_hi = _DATA_DIR / f"bivpoly_param{i}.npz"
    _biv_lo_meta.append(_load_bivpoly_npz(path_lo))
    _biv_hi_meta.append(_load_bivpoly_npz(path_hi))

# Build Numba predictors
A_lo      = _build_bivpoly_predictor(_biv_lo_meta[0], "A")
sigma1_lo = _build_bivpoly_predictor(_biv_lo_meta[1], "sigma1")
s2_lo     = _build_bivpoly_predictor(_biv_lo_meta[2], "s2")
s3_lo     = _build_bivpoly_predictor(_biv_lo_meta[3], "s3")
n_lo      = _build_bivpoly_predictor(_biv_lo_meta[4], "n")
w1_lo     = _build_bivpoly_predictor(_biv_lo_meta[5], "w1")
w2_lo     = _build_bivpoly_predictor(_biv_lo_meta[6], "w2")

A_hi      = _build_bivpoly_predictor(_biv_hi_meta[0], "A")
sigma1_hi = _build_bivpoly_predictor(_biv_hi_meta[1], "sigma1")
s2_hi     = _build_bivpoly_predictor(_biv_hi_meta[2], "s2")
s3_hi     = _build_bivpoly_predictor(_biv_hi_meta[3], "s3")
n_hi      = _build_bivpoly_predictor(_biv_hi_meta[4], "n")
w1_hi     = _build_bivpoly_predictor(_biv_hi_meta[5], "w1")
w2_hi     = _build_bivpoly_predictor(_biv_hi_meta[6], "w2")


@njit(cache=True)
def A_pred(E, T):
    return A_lo(E, T) if T <= _T_CUT_M else A_hi(E, T)


@njit(cache=True)
def sigma1_pred(E, T):
    return sigma1_lo(E, T) if T <= _T_CUT_M else sigma1_hi(E, T)


@njit(cache=True)
def s2_pred(E, T):
    return s2_lo(E, T) if T <= _T_CUT_M else s2_hi(E, T)


@njit(cache=True)
def s3_pred(E, T):
    return s3_lo(E, T) if T <= _T_CUT_M else s3_hi(E, T)


@njit(cache=True)
def n_pred(E, T):
    return n_lo(E, T) if T <= _T_CUT_M else n_hi(E, T)


@njit(cache=True)
def w1_pred(E, T):
    return w1_lo(E, T) if T <= _T_CUT_M else w1_hi(E, T)


@njit(cache=True)
def w2_pred(E, T):
    return w2_lo(E, T) if T <= _T_CUT_M else w2_hi(E, T)


@njit(cache=True)
def moliere_params(E, T):
    """
    Return Molière parameters (A, sigma1, s2, s3, n, w1, w2)
    using 1bivpoly below/at 1000 m and 2bivpoly above 1000 m.
    """
    return (
        A_pred(E, T),
        sigma1_pred(E, T),
        s2_pred(E, T),
        s3_pred(E, T),
        n_pred(E, T),
        w1_pred(E, T),
        w2_pred(E, T),
    )


# ---------------------------------------------------------------------------
# 3. Survival P_surv(E, T) from survival_poly_global.npz
# ---------------------------------------------------------------------------

# Numeric safety knobs (same as your survival fitter)
_LOG_EPS = 1e-12
_EXPO_MIN = -700.0
_EXPO_MAX = 0.0

_surv_npz = np.load(_DATA_DIR / "survival_poly_global.npz", allow_pickle=True)
_surv_cE0   = np.ascontiguousarray(_surv_npz["coeff_E0"].astype(np.float64))
_surv_cLogC = np.ascontiguousarray(_surv_npz["coeff_logC"].astype(np.float64))
_surv_cA    = np.ascontiguousarray(_surv_npz["coeff_A"].astype(np.float64))
_surv_cN    = np.ascontiguousarray(_surv_npz["coeff_n"].astype(np.float64))

_surv_mu_T  = float(_surv_npz["mu_T"])
_surv_std_T = float(_surv_npz["std_T"])


@njit(cache=True)
def _poly_eval_z(z, coeff):
    """Simple Horner-like polynomial evaluation in z."""
    acc = 0.0
    deg = coeff.shape[0] - 1
    for i in range(coeff.shape[0]):
        p = deg - i
        acc += coeff[i] * (z ** p)
    return acc


@njit(cache=True)
def survival_rate_ET(E, T):
    """
    Survival probability P_surv(E, T) from survival_poly_global.npz.
    """
    # standardize thickness
    zT = (T - _surv_mu_T) / (_surv_std_T if _surv_std_T != 0.0 else 1.0)

    # parameter fields in zT
    E0   = _poly_eval_z(zT, _surv_cE0)
    logC = _poly_eval_z(zT, _surv_cLogC)
    A    = _poly_eval_z(zT, _surv_cA)
    n    = _poly_eval_z(zT, _surv_cN)

    E0_safe = max(E0, 1e-6)
    A_safe  = max(A,  1e-6)
    n_safe  = max(n,  0.1)
    C_safe  = np.exp(logC)

    if E <= 0.0 or E <= E0_safe:
        return 0.0

    logE  = math.log(max(E, _LOG_EPS))
    logE0 = math.log(max(E0_safe, _LOG_EPS))
    delta = logE - logE0
    if delta <= 0.0:
        return 0.0

    x = max(delta, 1e-6)
    den = x ** n_safe
    if den < 1e-300:
        den = 1e-300

    expo = -A_safe / den
    if expo < _EXPO_MIN:
        expo = _EXPO_MIN
    if expo > _EXPO_MAX:
        expo = _EXPO_MAX

    P = C_safe * np.exp(expo)
    if P < 0.0:
        P = 0.0
    if P > 1.0:
        P = 1.0
    return P


@njit(cache=True)
def params_ET(E, T):
    """
    Combined parameter predictor:

        (A, sigma1, s2, s3, n, w1, w2, survival)
    """
    A, sigma1, s2, s3, n_param, w1, w2 = moliere_params(E, T)
    sr = survival_rate_ET(E, T)
    return A, sigma1, s2, s3, n_param, w1, w2, sr


# ---------------------------------------------------------------------------
# 4. Molière PDF (NumPy / Numba version) and params_array wrapper
# ---------------------------------------------------------------------------

@njit(cache=True, fastmath=True)
def gaussian(x, sigma):
    if sigma < _eps:
        sigma = _eps
    coeff = 2.0 / (sigma * np.sqrt(2.0 * np.pi))
    exponent = -0.5 * (x / sigma) ** 2
    return coeff * np.exp(exponent)
#
# @njit(cache=True, fastmath=True)
# def power_law(x, sigma, n):
#     if sigma < eps:
#         sigma = eps
#     norm = (n - 1.0) / sigma
#     value = 1.0 / (1.0 + (x / sigma) ** n)
#     return norm * value

@njit(cache=True, fastmath=True)
def power_law(x, sigma, n):
    if sigma < _eps:
        sigma = _eps
    if n <= 1.0:
        n = 1.0 + 1e-9  # ensure the integral converges

    # normalization so that ∫_0^∞ power_law(x, sigma, n) dx = 1
    norm = (n * np.sin(np.pi / n)) / (np.pi * sigma)
    value = 1.0 / (1.0 + (x / sigma) ** n)
    return norm * value

@njit(cache=True, fastmath=True)
def exponential(x, sigma):
    if sigma < _eps:
        sigma = _eps
    coeff = 1.0 / sigma
    exponent = -x / sigma
    return coeff * np.exp(exponent)

@njit(cache=True, fastmath=True)
def trapz(y, x):
    n = y.shape[0]
    s = 0.0
    for i in range(n - 1):
        dx = x[i + 1] - x[i]
        s += 0.5 * (y[i] + y[i + 1]) * dx
    return s

@njit(cache=True)
def moliere_pdf(x, A, sigma1, sigma2, sigma3, n, w1, w2):
    # guard NaNs early
    if (np.isnan(A) or np.isnan(sigma1) or np.isnan(sigma2) or
        np.isnan(sigma3) or np.isnan(n) or np.isnan(w1) or np.isnan(w2)):
        return np.zeros(x.shape[0])

    # scales (floors)
    if sigma1 < _eps: sigma1 = _eps
    if sigma2 < _eps: sigma2 = _eps
    if sigma3 < _eps: sigma3 = _eps
    if n < 1.0 + 1e-9: n = 1.0 + 1e-9

    if w1 < 0.0: w1 = 0.0
    if w1 > 1.0: w1 = 1.0
    if w2 < 0.0: w2 = 0.0
    if w2 > 1.0: w2 = 1.0

    # mixture weights
    f1 = w1
    f2 = w2 * (1.0 - w1)
    f3 = (1.0 - w1) * (1.0 - w2)

    xabs = np.abs(x)  # robust to any negative angles
    s = np.sin(xabs)

    y1 = gaussian(xabs, sigma1)
    y2 = power_law(xabs, sigma2, n)
    y3 = exponential(xabs, sigma3)

    y = f1 * y1 + f2 * y2 + f3 * y3
    func_ = 2 * np.pi * s * y

    y = A * func_

    # ensure finite output
    out = np.empty_like(y)
    for i in range(y.size):
        v = y[i]
        if not np.isfinite(v):
            out[i] = 1e300
        else:
            out[i] = v
    return out

@njit(cache=True)
def moliere_pdf_numpy(x, A, sigma1, s2, s3, n, w1, w2):
    sigma2 = s2 * sigma1
    sigma3 = s3 * sigma1
    return moliere_pdf(x, A, sigma1, sigma2, sigma3, n, w1, w2)


# --- small helper for number of θ-samples (same as your N(ratio)) ---------

@njit(cache=True)
def _N_samples(ratio):
    rlog = math.log10(ratio)
    p7, p6, p5, p4, p3, p2, p1, p0 = (
        5.75878234, -23.15540197, 32.5761094, -15.60652603,
        -11.64811135, 32.12022855, -34.78329596, 17.15939426,
    )
    y = (p7 * rlog**7 + p6 * rlog**6 + p5 * rlog**5 +
         p4 * rlog**4 + p3 * rlog**3 + p2 * rlog**2 +
         p1 * rlog + p0)
    y = math.ceil(y)
    if rlog < -1.0:
        y = 50.0
    if y < 2.0:
        y = 2.0
    return y


def predictor_testing(E, T):
    A_val      = A_pred(E, T)
    sigma1_val = sigma1_pred(E, T)
    s2_val     = s2_pred(E, T)
    s3_val     = s3_pred(E, T)
    n_val      = n_pred(E, T)
    w1_val     = w1_pred(E, T)
    w2_val     = w2_pred(E, T)
    return A_val, sigma1_val, s2_val, s3_val, n_val, w1_val, w2_val


@njit(cache=True, parallel=True)
def params_array(E, T_array, THX, THY, IDX, IDY, PhiE, window_size):
    """
    Vectorized parameter dump:

      out[..., 0:7]  = (A, sigma1, s2, s3, n, w1, w2)
      out[..., 7]    = survival_rate_ET
      out[..., 8:12] = THX, THY, IDX, IDY
      out[..., 12]   = linear index
      out[..., 13]   = PhiE
      out[..., 14]   = N_samples(sigma1 / window_size)
      out[..., 15]   = 0.0 (spare)
    """
    shape = T_array.shape
    T_flat   = T_array.ravel()
    THX_flat = THX.ravel()
    THY_flat = THY.ravel()
    IDX_flat = IDX.ravel()
    IDY_flat = IDY.ravel()
    PhiE_flat = PhiE.ravel()

    n = T_flat.shape[0]
    out = np.empty((n, 16), dtype=np.float64)

    for i in prange(n):
        T = T_flat[i]
        sr = survival_rate_ET(E, T)
        
        if sr == 0.0:
            # blocked: fill zeros + geometry
            out[i, 0] = 0.0  # A
            out[i, 1] = 0.0  # sigma1
            out[i, 2] = 0.0  # s2
            out[i, 3] = 0.0  # s3
            out[i, 4] = 0.0  # n
            out[i, 5] = 0.0  # w1
            out[i, 6] = 0.0  # w2
            out[i, 7] = 0.0  # survival
            out[i, 8] = THX_flat[i]
            out[i, 9] = THY_flat[i]
            out[i, 10] = IDX_flat[i]
            out[i, 11] = IDY_flat[i]
            out[i, 12] = i
            out[i, 13] = 0.0
            out[i, 14] = 0.0
            out[i, 15] = 0.0
            continue

        A_val      = A_pred(E, T)
        sigma1_val = sigma1_pred(E, T)
        s2_val     = s2_pred(E, T)
        s3_val     = s3_pred(E, T)
        n_val      = n_pred(E, T)
        w1_val     = w1_pred(E, T)
        w2_val     = w2_pred(E, T)
        
        if sigma1_val > 0.2:
            sigma1_val = 0.2  # cap to avoid huge angles / slow integrals
            
        x = np.linspace(0, sigma1_val * 25, 1000)
        pdf_vals = moliere_pdf(x, A_val, sigma1_val, s2_val, s3_val, n_val, w1_val, w2_val)
        integral = np.trapz(pdf_vals, x)

        out[i, 0] = A_val / integral  # normalize A
        out[i, 1] = sigma1_val
        out[i, 2] = s2_val
        out[i, 3] = s3_val
        out[i, 4] = n_val
        out[i, 5] = w1_val
        out[i, 6] = w2_val
        out[i, 7] = sr
        out[i, 8] = THX_flat[i]
        out[i, 9] = THY_flat[i]
        out[i, 10] = IDX_flat[i]
        out[i, 11] = IDY_flat[i]
        out[i, 12] = i
        out[i, 13] = PhiE_flat[i]
        out[i, 14] = _N_samples(sigma1_val / window_size)
        out[i, 15] = 0.0

    return out.reshape((*shape, 16))
