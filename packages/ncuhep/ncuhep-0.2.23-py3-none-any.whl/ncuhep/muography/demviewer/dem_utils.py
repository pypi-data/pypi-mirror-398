import json
import numpy as np


def _unit(v, eps=1e-12):
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    return v * 0.0 if n < eps else v / n


def boresight_from_zen_az(zenith_deg: float, azimuth_deg: float):
    th = np.radians(float(zenith_deg))
    az = np.radians(float(azimuth_deg))
    x = np.sin(th) * np.cos(az)
    y = np.sin(th) * np.sin(az)
    z = np.cos(th)
    return _unit([x, y, z])


def detector_frame_from_boresight(zp_world):
    up = np.array([0.0, 0.0, 1.0], dtype=float)
    zprime = _unit(zp_world)

    xprime = np.cross(up, zprime)
    if np.linalg.norm(xprime) < 1e-8:
        xprime = np.array([1.0, 0.0, 0.0], dtype=float)
    xprime = _unit(xprime)

    yprime = _unit(np.cross(zprime, xprime))
    return xprime, yprime, zprime


def project_to_detector_thetas(points_xyz, det_center_xyz, xprime, yprime, zprime):
    v = points_xyz - det_center_xyz[None, :]
    vx = v @ xprime
    vy = v @ yprime
    vz = v @ zprime
    theta_x = np.arctan2(vx, vz)
    theta_y = np.arctan2(vy, vz)
    return theta_x, theta_y, vz


def direction_from_detector_thetas(theta_x, theta_y, xprime, yprime, zprime):
    tx = float(theta_x)
    ty = float(theta_y)
    vx = np.tan(tx)
    vy = np.tan(ty)
    vz = 1.0
    d_world = vx * xprime + vy * yprime + vz * zprime
    return _unit(d_world)


def sanitize_dem_points(DEM, dedupe_round_decimals=6, max_points=250_000):
    """
    DEM: (N,3) point cloud
    - removes NaN/inf
    - optional downsample to max_points
    - dedupe by rounding X,Y
    """
    DEM = np.asarray(DEM, dtype=float)
    if DEM.ndim != 2 or DEM.shape[1] < 3:
        raise ValueError("DEM must be (N,3): x,y,z")

    ok = np.isfinite(DEM[:, 0]) & np.isfinite(DEM[:, 1]) & np.isfinite(DEM[:, 2])
    DEM = DEM[ok]

    if DEM.shape[0] > int(max_points):
        step = int(np.ceil(DEM.shape[0] / float(max_points)))
        DEM = DEM[::max(1, step)]

    xy = np.round(DEM[:, :2], int(dedupe_round_decimals))
    _, idx = np.unique(xy, axis=0, return_index=True)
    DEM = DEM[np.sort(idx)]
    return DEM


def _dem_points_to_grid(DEM, round_decimals=6):
    """
    Try to reshape (N,3) DEM points into a regular grid.
    Returns (ux, uy, Z) where:
      ux: (nx,) sorted x coordinates
      uy: (ny,) sorted y coordinates
      Z : (ny,nx) grid of z values
    or (None, None, None) if not griddable.
    """
    DEM = np.asarray(DEM, dtype=float)
    if DEM.ndim != 2 or DEM.shape[1] < 3:
        return None, None, None

    x = DEM[:, 0]
    y = DEM[:, 1]
    z = DEM[:, 2]

    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    x = x[ok]; y = y[ok]; z = z[ok]
    if x.size == 0:
        return None, None, None

    rx = np.round(x, int(round_decimals))
    ry = np.round(y, int(round_decimals))

    ux = np.unique(rx)
    uy = np.unique(ry)
    nx = ux.size
    ny = uy.size
    n = rx.size

    if nx * ny != n:
        return None, None, None

    x_to_i = {float(v): i for i, v in enumerate(ux)}
    y_to_i = {float(v): i for i, v in enumerate(uy)}
    Z = np.full((ny, nx), np.nan, dtype=float)

    for k in range(n):
        xi = x_to_i.get(float(rx[k]), None)
        yi = y_to_i.get(float(ry[k]), None)
        if xi is None or yi is None:
            return None, None, None
        Z[yi, xi] = float(z[k])

    if not np.all(np.isfinite(Z)):
        return None, None, None

    return ux.astype(float), uy.astype(float), Z


def upscale_dem_bilinear_points(DEM, factor=2, round_decimals=6):
    """
    Upscale a griddable DEM (N,3) by an integer factor using bilinear interpolation.

    - Works ONLY if DEM is a complete regular grid in X and Y (nx*ny points).
    - If not griddable, returns original DEM with meta["used"]=False.

    Returns: (DEM_up, meta)
    """
    DEM = np.asarray(DEM, dtype=float)
    factor = int(factor)

    if factor <= 1:
        return DEM, {"used": False, "reason": "factor<=1"}

    ux, uy, Z = _dem_points_to_grid(DEM, round_decimals=round_decimals)
    if ux is None:
        return DEM, {"used": False, "reason": "DEM not on a complete regular grid"}

    nx = ux.size
    ny = uy.size

    # preserve endpoints: new size = (n-1)*factor + 1
    nx2 = (nx - 1) * factor + 1
    ny2 = (ny - 1) * factor + 1

    x2 = np.linspace(float(ux[0]), float(ux[-1]), nx2)
    y2 = np.linspace(float(uy[0]), float(uy[-1]), ny2)

    # bilinear via two-pass 1D linear interpolation
    Zx = np.empty((ny, nx2), dtype=float)
    for j in range(ny):
        Zx[j, :] = np.interp(x2, ux, Z[j, :])

    Z2 = np.empty((ny2, nx2), dtype=float)
    for i in range(nx2):
        Z2[:, i] = np.interp(y2, uy, Zx[:, i])

    X2, Y2 = np.meshgrid(x2, y2, indexing="xy")
    DEM_up = np.column_stack([X2.ravel(), Y2.ravel(), Z2.ravel()]).astype(float)

    return DEM_up, {
        "used": True,
        "factor": factor,
        "nx0": int(nx), "ny0": int(ny),
        "nx1": int(nx2), "ny1": int(ny2),
        "n0": int(DEM.shape[0]),
        "n1": int(DEM_up.shape[0]),
    }


def triangle_plane_intersections(pts_xyz, triangles, plane_n, plane_p0, eps=1e-8):
    pts_xyz = np.asarray(pts_xyz, dtype=float)
    triangles = np.asarray(triangles, dtype=int)
    n = _unit(plane_n)

    P = pts_xyz[triangles]
    S = (P - plane_p0[None, None, :]) @ n

    cand = (np.min(S, axis=1) <= eps) & (np.max(S, axis=1) >= -eps) & (~np.all(np.abs(S) < eps, axis=1))
    idxs = np.nonzero(cand)[0]

    segs = []
    for i in idxs:
        p = P[i]
        s = S[i]
        inter = []
        edges = ((0, 1), (1, 2), (2, 0))
        for a, b in edges:
            p0, p1 = p[a], p[b]
            s0, s1 = s[a], s[b]
            a_on = abs(s0) < eps
            b_on = abs(s1) < eps
            if a_on and b_on:
                inter.append(p0)
                inter.append(p1)
            elif a_on:
                inter.append(p0)
            elif b_on:
                inter.append(p1)
            elif s0 * s1 < 0.0:
                t = s0 / (s0 - s1)
                inter.append(p0 + t * (p1 - p0))

        uniq = []
        for q in inter:
            if not any(np.sum((q - u) ** 2) < (1e-6 ** 2) for u in uniq):
                uniq.append(q)

        if len(uniq) >= 2:
            uu = np.asarray(uniq, dtype=float)
            best = None
            best_d2 = -1.0
            for a in range(uu.shape[0]):
                for b in range(a + 1, uu.shape[0]):
                    d2 = float(np.sum((uu[a] - uu[b]) ** 2))
                    if d2 > best_d2:
                        best_d2 = d2
                        best = (uu[a], uu[b])
            if best is not None and best_d2 > 0:
                segs.append([best[0], best[1]])

    if not segs:
        return np.zeros((0, 2, 3), dtype=float)
    return np.asarray(segs, dtype=float)


def _ceil_to_step(x, step):
    return float(np.ceil(float(x) / float(step)) * float(step))


def _extract_meta_dict(raw_meta):
    """
    Best-effort conversion of a loaded NPZ "meta" entry to a plain dict.
    Supports common cases such as 0d object arrays storing a dict or a JSON string.
    """
    meta = raw_meta

    try:
        if isinstance(meta, np.ndarray) and meta.shape == ():
            meta = meta.item()
    except Exception:
        pass

    if isinstance(meta, (bytes, bytearray)):
        try:
            meta = meta.decode("utf-8")
        except Exception:
            pass

    if isinstance(meta, str):
        try:
            parsed = json.loads(meta)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    if isinstance(meta, dict):
        return meta

    return None


def build_density_interpolator(RADX, RADY, RHO, round_decimals=12, eps=1e-12):
    """
    Despite name, used for ANY field (RHO/FLUX/THICK).
    Returns callable interp(tx,ty) and meta.
    """
    RADX = np.asarray(RADX, dtype=float).ravel()
    RADY = np.asarray(RADY, dtype=float).ravel()
    RHO = np.asarray(RHO, dtype=float).ravel()

    if not (RADX.size == RADY.size == RHO.size):
        raise ValueError("NPZ arrays must have same length: RADX, RADY, FIELD")

    rx = np.round(RADX, round_decimals)
    ry = np.round(RADY, round_decimals)

    ux = np.unique(rx)
    uy = np.unique(ry)
    nx, ny, n = ux.size, uy.size, RADX.size

    # Perfect grid => fast bilinear interpolation
    if nx * ny == n:
        x_to_i = {float(v): i for i, v in enumerate(ux)}
        y_to_i = {float(v): i for i, v in enumerate(uy)}
        grid = np.full((ny, nx), np.nan, dtype=float)

        ok = True
        for k in range(n):
            xv = float(rx[k])
            yv = float(ry[k])
            if (xv not in x_to_i) or (yv not in y_to_i):
                ok = False
                break
            grid[y_to_i[yv], x_to_i[xv]] = float(RHO[k])

        if ok and np.all(np.isfinite(grid)):
            ux_sorted = ux.astype(float)
            uy_sorted = uy.astype(float)
            x0, x1 = ux_sorted[0], ux_sorted[-1]
            y0, y1 = uy_sorted[0], uy_sorted[-1]

            def interp(tx, ty):
                tx = np.asarray(tx, dtype=float)
                ty = np.asarray(ty, dtype=float)

                out = np.full(np.broadcast(tx, ty).shape, np.nan, dtype=float)
                inside = (tx >= x0) & (tx <= x1) & (ty >= y0) & (ty <= y1)
                if not np.any(inside):
                    return out

                txi = tx[inside]
                tyi = ty[inside]
                ix1 = np.searchsorted(ux_sorted, txi, side="right") - 1
                iy1 = np.searchsorted(uy_sorted, tyi, side="right") - 1
                ix1 = np.clip(ix1, 0, nx - 2)
                iy1 = np.clip(iy1, 0, ny - 2)
                ix2 = ix1 + 1
                iy2 = iy1 + 1

                xL = ux_sorted[ix1]
                xR = ux_sorted[ix2]
                yB = uy_sorted[iy1]
                yT = uy_sorted[iy2]

                wx = (txi - xL) / (xR - xL + eps)
                wy = (tyi - yB) / (yT - yB + eps)

                f11 = grid[iy1, ix1]
                f21 = grid[iy1, ix2]
                f12 = grid[iy2, ix1]
                f22 = grid[iy2, ix2]

                out[inside] = (
                    (1 - wx) * (1 - wy) * f11 +
                    wx * (1 - wy) * f21 +
                    (1 - wx) * wy * f12 +
                    wx * wy * f22
                )
                return out

            return interp, {"type": "grid", "nx": nx, "ny": ny}

    # Fallback: nearest neighbor in (θx,θy)
    pts = np.stack([RADX, RADY], axis=1)

    def interp(tx, ty):
        tx = np.asarray(tx, dtype=float).ravel()
        ty = np.asarray(ty, dtype=float).ravel()
        q = np.stack([tx, ty], axis=1)
        d2 = np.sum((q[:, None, :] - pts[None, :, :]) ** 2, axis=2)
        idx = np.argmin(d2, axis=1)
        return RHO[idx]

    return interp, {"type": "nearest", "n": n}
