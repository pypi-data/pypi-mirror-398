from numba import cuda, float32, types, njit
from numba.cuda.libdevice import (
    sinf, cosf, tanf, sqrtf, fabsf, fmaxf, fminf, acosf, rsqrtf, fmaf, fabs
)
import numpy as np

from .constants import _ONE, _EPSC, _EPS2

@cuda.jit(types.UniTuple(float32, 6)(float32, float32),
          device=True, inline=True, fastmath=True)

def jacobian_xyz_from_t(tx, ty):
    # cos/sin
    cx = cosf(tx)
    cy = cosf(ty)
    sx = sinf(tx)
    sy = sinf(ty)

    # Guard cos against exact zeros to avoid INF (optional but practical)
    # This keeps numerics sane near pi/2 while preserving fp32 path.
    acx = fmaxf(fabsf(cx), _EPSC)
    acy = fmaxf(fabsf(cy), _EPSC)

    inv_cx  = _ONE / acx
    inv_cy  = _ONE / acy
    cx2_inv = inv_cx * inv_cx   # 1 / cos^2(tx)
    cy2_inv = inv_cy * inv_cy   # 1 / cos^2(ty)

    # tan = sin / cos (uses guarded cos)
    txan = sx * inv_cx
    tyan = sy * inv_cy

    # (tan(tx)^2 + tan(ty)^2 + 1)^(3/2) = d * sqrt(d), with d = txan^2 + tyan^2 + 1
    txx  = txan * txan
    tyy  = tyan * tyan
    d    = txx + tyy + _ONE
    d32  = d * sqrtf(d)         # (3/2) power without powf
    invd32 = _ONE / fmaxf(d32, np.float32(1e-20))  # tiny guard

    # Common factor patterns from your formulas
    c_xy = invd32 * cx2_inv * cy2_inv
    c_x  = invd32 * cx2_inv
    c_y  = invd32 * cy2_inv

    # Derivatives:
    # dx/dtx =  1 / (d^(3/2) * cos^2(tx) * cos^2(ty))
    dx_dtx = c_xy

    # dx/dty = -tan(tx)*tan(ty) / (d^(3/2) * cos^2(ty))
    dx_dty = -(txan * tyan) * c_y

    # dy/dtx = -tan(tx)*tan(ty) / (d^(3/2) * cos^2(tx))
    dy_dtx = -(txan * tyan) * c_x

    # dy/dty =  1 / (d^(3/2) * cos^2(tx) * cos^2(ty))
    dy_dty = c_xy

    # dz/dtx = -tan(tx) / (d^(3/2) * cos^2(tx))
    dz_dtx = -txan * c_x

    # dz/dty = -tan(ty) / (d^(3/2) * cos^2(ty))
    dz_dty = -tyan * c_y

    return dx_dtx, dx_dty, dy_dtx, dy_dty, dz_dtx, dz_dty


@cuda.jit(types.UniTuple(float32, 3)(float32, float32),
          device=True, inline=True, fastmath=True)
def angle2cart(tx, ty):
    z = _ONE / sqrtf(_ONE + tanf(tx) * tanf(tx) + tanf(ty) * tanf(ty))
    x = tanf(tx) * z
    y = tanf(ty) * z
    return x, y, z


@cuda.jit("float32(float32, float32, float32, float32, float32, float32)",
          device=True, inline=True, fastmath=True)
def angle(x1, y1, z1, x2, y2, z2):
    dot = fmaf(x1, x2, fmaf(y1, y2, z1 * z2))

    n1 = fmaxf(fmaf(x1, x1, fmaf(y1, y1, z1 * z1)), _EPS2)
    n2 = fmaxf(fmaf(x2, x2, fmaf(y2, y2, z2 * z2)), _EPS2)

    inv1 = rsqrtf(n1)
    inv2 = rsqrtf(n2)

    cos_angle = dot * inv1 * inv2

    cos_angle = fminf(_ONE, fmaxf(cos_angle, -_ONE))

    return acosf(cos_angle)


@cuda.jit("float32(float32, float32, float32, float32, float32)",
          device=True, inline=True, fastmath=True)
def x_lin(x0, dx_dtx, dx_dty, dtx, dty):
    return x0 + dx_dtx * dtx + dx_dty * dty


@cuda.jit("float32(float32, float32, float32, float32, float32)",
          device=True, inline=True, fastmath=True)
def y_lin(y0, dy_dtx, dy_dty, dtx, dty):
    return y0 + dy_dtx * dtx + dy_dty * dty


@cuda.jit("float32(float32, float32, float32, float32, float32)",
            device=True, inline=True, fastmath=True)
def z_lin(z0, dz_dtx, dz_dty, dtx, dty):
    return z0 + dz_dtx * dtx + dz_dty * dty


@cuda.jit("float32(float32, float32, float32)",
          device=True, inline=True, fastmath=True)
def weight(i, j, N):
    wx = (N + 1 ) - fabs(i - N)
    wy = (N + 1 ) - fabs(j - N)
    return wx * wy


@cuda.jit("float32(float32, float32)",
            device=True, inline=True, fastmath=True)
def jacobian(tx, ty):
    return 1.0 / (1.0 + tanf(tx) * tanf(tx) + tanf(ty) * tanf(ty))**1.5 / (cosf(tx)**2 * cosf(ty)**2)



