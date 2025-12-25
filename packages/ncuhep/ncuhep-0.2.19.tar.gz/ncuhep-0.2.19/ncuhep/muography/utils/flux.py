import numpy as np
from numba import njit, prange
from .coordinates import projection2cart, cart2spherical


@njit
def effective_area(theta_x_rad: float, theta_y_rad: float,layer_z: np.ndarray, layer_half_length_x: np.ndarray, layer_half_length_y: np.ndarray):

    half_length_x = effective_length(theta_x_rad, layer_z, layer_half_length_x)
    half_length_y = effective_length(theta_y_rad, layer_z, layer_half_length_y)

    if half_length_x <= 0 or half_length_y <= 0:
        return 0.0

    return 4 * half_length_x * half_length_y

@njit
def effective_length(theta_rad: float, layer_z: np.ndarray, layer_half_length: np.ndarray):
    c = layer_half_length - layer_z * np.tan(theta_rad)

    return np.amin(c)


@njit
def solid_angle(theta_x_rad: float, theta_y_rad: float, d_theta_x_rad: float, d_theta_y_rad: float):

    p1 = np.array([1, theta_x_rad - d_theta_x_rad / 2, theta_y_rad - d_theta_y_rad / 2])
    p2 = np.array([1, theta_x_rad + d_theta_x_rad / 2, theta_y_rad - d_theta_y_rad / 2])
    p3 = np.array([1, theta_x_rad + d_theta_x_rad / 2, theta_y_rad + d_theta_y_rad / 2])
    p4 = np.array([1, theta_x_rad - d_theta_x_rad / 2, theta_y_rad + d_theta_y_rad / 2])

    x1 = projection2cart(p1[0], p1[1], p1[2])
    x2 = projection2cart(p2[0], p2[1], p2[2])
    x3 = projection2cart(p3[0], p3[1], p3[2])
    x4 = projection2cart(p4[0], p4[1], p4[2])

    solid_angle_1 = solid_angle_tetrahedron(x1, x2, x3)
    solid_angle_2 = solid_angle_tetrahedron(x3, x4, x1)

    return solid_angle_1 + solid_angle_2


@njit
def dot(a: np.ndarray, b: np.ndarray):
    val = 0.0
    if len(a) != len(b):
        return np.nan
    for i in range(len(a)):
        val += a[i] * b[i]
    return val

@njit
def norm(v: np.ndarray):
    return np.sqrt(dot(v, v))

@njit
def cross(a: np.ndarray, b: np.ndarray):
    if len(a) != 3 or len(b) != 3:
        return np.array([np.nan, np.nan, np.nan])
    return np.array([
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    ])

@njit
def solid_angle_tetrahedron(v1: np.ndarray, v2: np.ndarray, v3: np.ndarray):

    scalar_triple_product = np.abs(dot(v1, cross(v2, v3)))

    norm1 = norm(v1)
    norm2 = norm(v2)
    norm3 = norm(v3)

    v1_v2 = dot(v1, v2)
    v2_v3 = dot(v2, v3)
    v3_v1 = dot(v3, v1)

    denominator = (norm1 * norm2 * norm3 +
                   v1_v2 * norm3 +
                   v2_v3 * norm1 +
                   v3_v1 * norm2)

    numerator = scalar_triple_product
    omega = 2 * np.arctan(numerator/denominator)

    return omega if omega >= 0 else -omega


@njit(parallel=True)
def geometric_factor(theta_x_rad: np.ndarray, theta_y_rad: np.ndarray, layer_z: np.ndarray, layer_half_length_x: np.ndarray, layer_half_length_y: np.ndarray, d_theta_x_rad: float, d_theta_y_rad: float):

    area = np.zeros(theta_x_rad.shape, dtype=np.float64)
    sa = np.zeros(theta_x_rad.shape, dtype=np.float64)
    for i in prange(theta_x_rad.shape[0]):
        for j in prange(theta_x_rad.shape[1]):
            area[i, j] = effective_area(theta_x_rad[i, j], theta_y_rad[i, j], layer_z, layer_half_length_x, layer_half_length_y) / 1000 / 1000
            sa[i, j] = solid_angle(theta_x_rad[i, j], theta_y_rad[i, j], d_theta_x_rad, d_theta_y_rad)

    return area * sa

