import numpy as np

pixel_size = 0.002
window_size = 20.0
bins = 128
sigma_window_ratio_lower = 0.2
sigma_window_ratio_middle = 1
sigma_window_ratio_upper = 10
_ONE   = np.float32(1.0)
_EPSC  = np.float32(1e-7)   # guard for cos near 0
_EPS2 = np.float32(1e-20)  # tiny guard for squared norms
EPS = np.float32(1e-8)
ONE = np.float32(1.0)
NEG_HALF = np.float32(-0.5)
TWO_PI_INV_SQRT = np.float32(1.0 / np.sqrt(2.0 * np.pi))
gaussian_factor = TWO_PI_INV_SQRT