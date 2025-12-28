from numba import cuda, float32
from numba.cuda.libdevice import expf, powf, fmaxf, sinf, fabsf
import numpy as np

from .constants import EPS, ONE  # you can keep gaussian_factor/NEG_HALF if used elsewhere

# ------------------------------------------------------------------
# Constants (float32)
# ------------------------------------------------------------------
PI = np.float32(np.pi)
SQRT_2PI = np.float32(np.sqrt(2.0 * np.pi))
GAUSS_COEFF = np.float32(2.0) / SQRT_2PI  # 2 / sqrt(2*pi)  (matches new model)
N_MIN = np.float32(1.0 + 1e-6)


# ------------------------------------------------------------------
# Component PDFs: gaussian, power-law, exponential
# ------------------------------------------------------------------

@cuda.jit("float32(float32, float32)", device=True, inline=True, fastmath=True)
def gaussian(x, sigma):
    """
    Same as CPU/Torch version:

        gaussian(x, sigma) = 2 / (sigma * sqrt(2*pi)) * exp(-(x/sigma)^2 / 2)

    normalized so that ∫_0^∞ gaussian(x, sigma) dx = 1.
    """
    x = fabsf(x)
    sigma = fmaxf(sigma, EPS)
    inv_sigma = ONE / sigma
    t = x * inv_sigma

    exponent = np.float32(-0.5) * t * t
    # 2 / (sqrt(2*pi)) * 1/sigma
    coeff = GAUSS_COEFF * inv_sigma

    return coeff * expf(exponent)


@cuda.jit("float32(float32, float32)", device=True, inline=True, fastmath=True)
def exponential(x, sigma):
    """
    Same as CPU/Torch version:

        exponential(x, sigma) = (1 / sigma) * exp(-x/sigma)

    normalized so that ∫_0^∞ exponential(x, sigma) dx = 1.
    """
    x = fabsf(x)
    sigma = fmaxf(sigma, EPS)
    inv_sigma = ONE / sigma
    return inv_sigma * expf(-x * inv_sigma)


@cuda.jit("float32(float32, float32, float32)", device=True, inline=True, fastmath=True)
def power_law(x, sigma, n):
    """
    Updated to the new normalization:

        power_law(x, sigma, n) =
            [ n * sin(pi/n) / (pi * sigma) ] * 1 / (1 + (x/sigma)^n)

    so that ∫_0^∞ power_law(x, sigma, n) dx = 1, with n > 1.
    """
    x = fabsf(x)
    sigma = fmaxf(sigma, EPS)

    # ensure convergence (n > 1)
    if n <= np.float32(1.0):
        n = N_MIN

    inv_sigma = ONE / sigma
    t = x * inv_sigma

    # normalization factor
    norm = (n * sinf(PI / n)) / (PI * sigma)
    value = ONE / (ONE + powf(t, n))

    return norm * value


# ------------------------------------------------------------------
# Full Molière PDF (directional version, matching moliere_pdf_numpy)
# ------------------------------------------------------------------

@cuda.jit(
    "float32(float32, float32, float32, float32, float32, float32, float32, float32)",
    device=True,
    inline=True,
    fastmath=True,
)
def PDF(x, A, sigma1, s2, s3, n, w1, w2):
    """
    CUDA device version of your new model, aligned with:

        moliere_pdf_numpy(x, A, sigma1, s2, s3, n, w1, w2)

    but returning the *directional* mixture:

        PDF_dir(theta) = A * [ f1 * G(theta; sigma1)
                              + f2 * P(theta; sigma2, n)
                              + f3 * E(theta; sigma3) ]

    where:
      - sigma2 = s2 * sigma1
      - sigma3 = s3 * sigma1
      - f1 = w1
        f2 = w2 * (1 - w1)
        f3 = (1 - w1) * (1 - w2)

    Note: the 2π sin(theta) factor lives in the radial form; we keep
    the directional form here, just like your old CUDA PDF, so the
    splat kernels remain correct.
    """
    # basic clamps (mirror CPU numba version)
    sigma1 = fmaxf(sigma1, EPS)
    sigma2 = fmaxf(s2 * sigma1, EPS)
    sigma3 = fmaxf(s3 * sigma1, EPS)

    if n <= np.float32(1.0):
        n = N_MIN

    # clamp mixture weights to [0, 1]
    if w1 < np.float32(0.0):
        w1 = np.float32(0.0)
    elif w1 > np.float32(1.0):
        w1 = np.float32(1.0)

    if w2 < np.float32(0.0):
        w2 = np.float32(0.0)
    elif w2 > np.float32(1.0):
        w2 = np.float32(1.0)

    # mixture weights
    f1 = w1
    f2 = w2 * (ONE - w1)
    f3 = (ONE - w1) * (ONE - w2)

    xabs = fabsf(x)

    g_val = gaussian(xabs, sigma1)
    p_val = power_law(xabs, sigma2, n)
    e_val = exponential(xabs, sigma3)

    y_mix = f1 * g_val + f2 * p_val + f3 * e_val

    return A * y_mix
