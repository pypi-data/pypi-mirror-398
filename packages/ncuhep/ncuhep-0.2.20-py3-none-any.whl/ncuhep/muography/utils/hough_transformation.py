import numpy as np
from numba import njit
from math import atan2


@njit(cache=True)
def array2combo(array: np.ndarray, layer_z: np.ndarray):
    L = layer_z.size
    N = array.shape[0]

    # Collect indices per layer just once
    idx_mat = -np.ones((L, N), dtype=np.int32)
    counts  = np.zeros(L, dtype=np.int32)

    for i in range(N):
        z = array[i, 1]
        for j in range(L):
            if z == layer_z[j]:
                idx_mat[j, counts[j]] = i
                counts[j] += 1
                break

    # number of combos = product of counts>1 (your original rule)
    combos = 1
    for j in range(L):
        c = counts[j]
        if c > 1:
            combos *= c

    # handle edge case: if all counts <=1, you still want 1 combo
    if combos == 0:
        combos = 1

    result = np.empty((combos, L, 2), dtype=array.dtype)

    # mixed-radix counter
    ctr = np.zeros(L, dtype=np.int32)
    for i in range(combos):
        for j in range(L):
            c = counts[j]
            if c == 0:
                result[i, j, 0] = np.nan
                result[i, j, 1] = layer_z[j]
            else:
                k = idx_mat[j, ctr[j] % c]
                result[i, j, 0] = array[k, 0]
                result[i, j, 1] = array[k, 1]

        # increment counter
        for j in range(L - 1, -1, -1):
            if counts[j] > 1:           # only radix>1 participates
                ctr[j] += 1
                if ctr[j] < counts[j]:
                    break
                ctr[j] = 0

    return result



@njit(cache=True, fastmath=True)
def multiple_intercept(positions: np.ndarray, delta_b: float):
    n = positions.shape[0]
    valid = np.empty(n, np.uint8)
    y = np.empty(n, np.float64)
    for i in range(n):
        valid[i] = 0 if np.isnan(positions[i, 0]) else 1
        y[i] = positions[i, 1]

    S_aw = 0.0; S_w = 0.0; S_b = 0.0; S_b2 = 0.0; m = 0
    S_z2a2 = 0.0; S_z2a = 0.0; S_z2 = 0.0

    for i in range(n):
        if valid[i] == 0:
            continue
        yi = y[i]
        xi = positions[i, 0]
        zi = positions[i, 1]
        for j in range(i):
            if valid[j] == 0:
                continue
            zjabs = yi - y[j]
            if zjabs < 0.0: zjabs = -zjabs
            if zjabs == 0.0:  # avoid 1/0
                continue

            xj = positions[j, 0]; zj = positions[j, 1]
            dx = xi - xj
            dz = zi - zj

            a = atan2(dx, dz)
            # b = xi - tan(a)*zi  but tan(a)=dx/dz
            b = xi - (zi * dx) / dz

            if np.isnan(a) or np.isnan(b):
                continue

            invz = 1.0 / zjabs
            z2   = zjabs * zjabs

            S_aw += a * invz;   S_w += invz
            S_b  += b;          S_b2 += b * b;    m += 1
            S_z2a2 += z2 * a * a
            S_z2a  += z2 * a
            S_z2   += z2

    if m == 0 or S_w == 0.0:
        return np.nan

    ca = S_aw / S_w
    cb = S_b / m
    inv_db2 = 1.0 / (delta_b * delta_b)

    a_lsq = inv_db2 * (S_z2a2 - 2.0 * ca * S_z2a + ca * ca * S_z2)
    b_lsq = inv_db2 * (S_b2    - 2.0 * cb * S_b  + cb * cb * m)
    return a_lsq + b_lsq



