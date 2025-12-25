from numba import cuda, float32, int32
from .angle import angle2cart, jacobian_xyz_from_t, angle, x_lin, y_lin, z_lin, jacobian
from .moliere import PDF

MAX_JOBS = int(4096 * 2)


def splat_kernels(pixel_size, window_size, bins):
    @cuda.jit("void(float32[:, :], float32[:, :])", fastmath=True)
    def splat1_kernel(PARAMS, OUTPUT):
        n = cuda.blockIdx.x
        t = cuda.threadIdx.x
        T = cuda.blockDim.x

        # --- Shared PARAMS[n] ---
        p = cuda.shared.array(16, dtype=float32)
        for k in range(t, 16, T):
            p[k] = PARAMS[n, k]
        cuda.syncthreads()

        A, sigma, s2, s3, nval, f1, f2, sr = p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]
        # print(A, sigma, s2, s3, nval, f1, f2, sr, "\n")
        src_thx, src_thy = p[8], p[9]
        src_idx, src_idy = int32(p[10]), int32(p[11])
        PhiE = p[13]
        N = int32(p[14])
        Ni = N - 1

        # window + geometry
        pixels = int((window_size * sigma + 1e-7) * 0.5 / pixel_size) + 1
        total = (2 * pixels + 1) * (2 * pixels + 1)
        px = float32(pixel_size)

        src_x, src_y, src_z = angle2cart(src_thx, src_thy)
        sdx_thx, sdx_thy, sdy_thx, sdy_thy, sdz_thx, sdz_thy = jacobian_xyz_from_t(src_thx, src_thy)

        # per-thread area partial
        local_area = float32(0.0)

        # --- Shared buffer to keep per-job area_ so we don't recompute ---
        # NOTE: we can only store up to MAX_JOBS into shared memory
        area_buf = cuda.shared.array(MAX_JOBS, dtype=float32)
        can_buffer = total <= MAX_JOBS
        if not can_buffer:
            # print("Warning: splat1_kernel cannot buffer area_, recomputing values")
            return 
        # ---------- Phase 1: compute area_[job] once and (if possible) store ----------
        for job in range(t, total, T):
            di = job // (2 * pixels + 1) - pixels
            dj = job % (2 * pixels + 1) - pixels

            dst_thx = src_thx + di * px
            dst_thy = src_thy + dj * px

            # dst central ray + jacobian
            dst_x, dst_y, dst_z = angle2cart(dst_thx, dst_thy)
            ddx_thx, ddx_thy, ddy_thx, ddy_thy, ddz_thx, ddz_thy = jacobian_xyz_from_t(dst_thx, dst_thy)

            # per-job local histogram
            hist = cuda.local.array(bins, dtype=float32)
            for k in range(bins):
                hist[k] = 0.0

            # estimate angle range (2x2x2x2 probe)
            angle_min = float32(3.14159265)
            angle_max = float32(0.0)
            for ii in range(2):
                src_dthx = (ii - 0.5) * px
                for jj in range(2):
                    src_dthy = (jj - 0.5) * px
                    sx = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                    sy = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                    sz = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)
                    for kk in range(2):
                        dst_dthx = (kk - 0.5) * px
                        for ll in range(2):
                            dst_dthy = (ll - 0.5) * px
                            dx = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                            dy = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                            dz = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)
                            ang_ = angle(sx, sy, sz, dx, dy, dz)
                            if ang_ < angle_min:
                                angle_min = ang_
                            if ang_ > angle_max:
                                angle_max = ang_

            d_angle = (angle_max - angle_min) / float32(bins)

            if Ni <= 0:
                ang0 = angle(src_x, src_y, src_z, dst_x, dst_y, dst_z)
                b = int((ang0 - angle_min) / d_angle)
                if b < 0:
                    b = 0
                elif b >= bins:
                    b = bins - 1
                hist[b] += 1.0
            else:
                invNi = 1.0 / float32(Ni)
                for diN in range(-(N - 1), N):
                    dthx = float32(diN) * invNi * px
                    wx = (N - abs(diN))
                    src_dthx = -0.5 * dthx
                    dst_dthx = +0.5 * dthx
                    for djN in range(-(N - 1), N):
                        dthy = float32(djN) * invNi * px
                        wy = (N - abs(djN))
                        w = float32(wx * wy)
                        src_dthy = -0.5 * dthy
                        dst_dthy = +0.5 * dthy

                        sx = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                        sy = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                        sz = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)

                        dx = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                        dy = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                        dz = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)

                        ang_ = angle(sx, sy, sz, dx, dy, dz)
                        b = int((ang_ - angle_min) / d_angle)
                        if b < 0:
                            b = 0
                        elif b >= bins:
                            b = bins - 1
                        hist[b] += w

            # expectation -> area_
            sum_hist = float32(0.0)
            for k in range(bins):
                sum_hist += hist[k]
            if sum_hist > 0.0:
                inv_sum = 1.0 / sum_hist
                expected_val = float32(0.0)
                for k in range(bins):
                    angle_k = angle_min + (k + 0.5) * d_angle
                    expected_val += hist[k] * PDF(angle_k, A, sigma, s2, s3, nval, f1, f2) * inv_sum
                area_ = expected_val * px * px * jacobian(dst_thx, dst_thy)
                local_area += area_
                if can_buffer:
                    area_buf[job] = area_
            else:
                if can_buffer:
                    area_buf[job] = 0.0

        # ---------- reduction for total_area ----------
        # use a shared buffer sized to blockDim.x
        part = cuda.shared.array(256, dtype=float32)  # assumes T<=256; raise if you use bigger blocks
        part[t] = local_area
        cuda.syncthreads()
        stride = T // 2
        while stride > 0:
            if t < stride:
                part[t] += part[t + stride]
            cuda.syncthreads()
            stride //= 2
        total_area = part[0]
        cuda.syncthreads()

        # ---------- Phase 2: emit normalized value (no recompute if buffered) ----------
        if total_area > 0.0:
            for job in range(t, total, T):
                di = job // (2 * pixels + 1) - pixels
                dj = job % (2 * pixels + 1) - pixels

                if can_buffer:
                    a = area_buf[job]
                else:
                    # fallback: recompute area_ if total > MAX_JOBS
                    dst_thx = src_thx + di * px
                    dst_thy = src_thy + dj * px
                    dst_x, dst_y, dst_z = angle2cart(dst_thx, dst_thy)
                    ddx_thx, ddx_thy, ddy_thx, ddy_thy, ddz_thx, ddz_thy = jacobian_xyz_from_t(dst_thx, dst_thy)

                    hist = cuda.local.array(bins, dtype=float32)
                    for k in range(bins):
                        hist[k] = 0.0
                    angle_min = float32(3.14159265)
                    angle_max = float32(0.0)
                    for ii in range(2):
                        src_dthx = (ii - 0.5) * px
                        for jj in range(2):
                            src_dthy = (jj - 0.5) * px
                            sx = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                            sy = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                            sz = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)
                            for kk in range(2):
                                dst_dthx = (kk - 0.5) * px
                                for ll in range(2):
                                    dst_dthy = (ll - 0.5) * px
                                    dx = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                                    dy = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                                    dz = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)
                                    ang_ = angle(sx, sy, sz, dx, dy, dz)
                                    if ang_ < angle_min:
                                        angle_min = ang_
                                    if ang_ > angle_max:
                                        angle_max = ang_
                    d_angle = (angle_max - angle_min) / float32(bins)
                    if Ni <= 0:
                        ang0 = angle(src_x, src_y, src_z, dst_x, dst_y, dst_z)
                        b = int((ang0 - angle_min) / d_angle)
                        if b < 0:
                            b = 0
                        elif b >= bins:
                            b = bins - 1
                        hist[b] += 1.0
                    else:
                        invNi = 1.0 / float32(Ni)
                        for diN in range(-(N - 1), N):
                            dthx = float32(diN) * invNi * px
                            wx = (N - abs(diN))
                            src_dthx = -0.5 * dthx
                            dst_dthx = +0.5 * dthx
                            for djN in range(-(N - 1), N):
                                dthy = float32(djN) * invNi * px
                                wy = (N - abs(djN))
                                w = float32(wx * wy)
                                src_dthy = -0.5 * dthy
                                dst_dthy = +0.5 * dthy
                                sx = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                                sy = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                                sz = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)
                                dx = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                                dy = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                                dz = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)
                                ang_ = angle(sx, sy, sz, dx, dy, dz)
                                b = int((ang_ - angle_min) / d_angle)
                                if b < 0:
                                    b = 0
                                elif b >= bins:
                                    b = bins - 1
                                hist[b] += w
                    sum_hist = float32(0.0)
                    for k in range(bins):
                        sum_hist += hist[k]
                    if sum_hist > 0.0:
                        inv_sum = 1.0 / sum_hist
                        expected_val = float32(0.0)
                        for k in range(bins):
                            angle_k = angle_min + (k + 0.5) * d_angle
                            expected_val += hist[k] * PDF(angle_k, A, sigma, s2, s3, nval, f1, f2) * inv_sum
                        a = expected_val * px * px * jacobian(dst_thx, dst_thy)
                    else:
                        a = 0.0

                if a > 0.0:
                    val = a * PhiE * sr / total_area
                    x = src_idx + di
                    y = src_idy + dj
                    if 0 <= x < OUTPUT.shape[0] and 0 <= y < OUTPUT.shape[1]:
                        cuda.atomic.add(OUTPUT, (x, y), val)

        # write out total area for diagnostics
        if t == 0:
            PARAMS[n, 15] = total_area

    @cuda.jit("void(float32[:, :], float32[:, :])", fastmath=True)
    def splat2_kernel(PARAMS, OUTPUT):
        n = cuda.blockIdx.x
        t = cuda.threadIdx.x
        T = cuda.blockDim.x

        # === Shared memory cache for PARAMS[n] ===
        p = cuda.shared.array(16, dtype=float32)
        for k in range(t, 16, T):
            p[k] = PARAMS[n, k]
        cuda.syncthreads()

        # === Unpack shared parameters ===
        A = p[0]
        sigma = p[1]
        s2 = p[2]
        s3 = p[3]
        nval = p[4]
        f1 = p[5]
        f2 = p[6]
        sr = p[7]

        src_thx = p[8]
        src_thy = p[9]

        src_idx = int32(p[10])
        src_idy = int32(p[11])

        # p[12] unused
        PhiE = p[13]
        N = int32(p[14])
        Ni = N - 1

        # === Precompute window geometry ===
        pixels_f = (window_size * sigma + 1e-7) * 0.5 / pixel_size
        pixels = int(pixels_f) + 1
        if pixels < 0:
            pixels = 0

        side = 2 * pixels + 1
        total = side * side

        H = OUTPUT.shape[0]
        W = OUTPUT.shape[1]

        # source direction (always needed)
        src_x, src_y, src_z = angle2cart(src_thx, src_thy)

        # jacobian of source direction only needed when N > 1
        if Ni > 0:
            sdx_thx, sdx_thy, sdy_thx, sdy_thy, sdz_thx, sdz_thy = jacobian_xyz_from_t(src_thx, src_thy)

        pix_area = pixel_size * pixel_size
        flux_factor = PhiE * sr * pix_area

        if total <= 0 or flux_factor == 0.0:
            return

        px = float32(pixel_size)

        # === Main parallelized loop over window pixels ===
        for job in range(t, total, T):
            # decode window coordinate
            di = job // side - pixels
            dj = job % side - pixels

            # integer coordinates in output
            x = src_idx + di
            y = src_idy + dj

            # early skip if outside OUTPUT
            if x < 0 or x >= H or y < 0 or y >= W:
                continue

            dst_thx = src_thx + di * pixel_size
            dst_thy = src_thy + dj * pixel_size

            # ------------------------------------------------------------------
            # SIMPLE CASE: N <= 1 (no triangular supersampling)
            # ------------------------------------------------------------------
            if Ni <= 0:
                dst_x, dst_y, dst_z = angle2cart(dst_thx, dst_thy)
                ang = angle(src_x, src_y, src_z, dst_x, dst_y, dst_z)
                val = PDF(ang, A, sigma, s2, s3, nval, f1, f2)
                if val <= 0.0:
                    continue
                val *= jacobian(dst_thx, dst_thy) * flux_factor
                if val > 0.0:
                    cuda.atomic.add(OUTPUT, (x, y), val)
                continue

            # ------------------------------------------------------------------
            # FULL CASE: N > 1 (triangular weighting & local histogram)
            # ------------------------------------------------------------------
            dst_x, dst_y, dst_z = angle2cart(dst_thx, dst_thy)
            ddx_thx, ddx_thy, ddy_thx, ddy_thy, ddz_thx, ddz_thy = jacobian_xyz_from_t(dst_thx, dst_thy)

            # local histogram
            hist = cuda.local.array(bins, dtype=float32)
            for k in range(bins):
                hist[k] = 0.0

            # --- Estimate angle range with 2×2×2×2 probe ---
            angle_min = float32(3.14159265)
            angle_max = float32(0.0)

            for ii in range(2):
                src_dthx = (ii - 0.5) * px
                for jj in range(2):
                    src_dthy = (jj - 0.5) * px
                    src_x_ = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                    src_y_ = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                    src_z_ = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)

                    for kk in range(2):
                        dst_dthx = (kk - 0.5) * px
                        for ll in range(2):
                            dst_dthy = (ll - 0.5) * px
                            dst_x_ = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                            dst_y_ = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                            dst_z_ = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)
                            ang_ = angle(src_x_, src_y_, src_z_, dst_x_, dst_y_, dst_z_)
                            if ang_ < angle_min:
                                angle_min = ang_
                            if ang_ > angle_max:
                                angle_max = ang_

            d_angle = (angle_max - angle_min) / float32(bins)

            # pathological case: degenerate angle range → fall back to single angle
            if d_angle <= 0.0:
                ang = angle(src_x, src_y, src_z, dst_x, dst_y, dst_z)
                val = PDF(ang, A, sigma, s2, s3, nval, f1, f2)
                if val <= 0.0:
                    continue
                val *= jacobian(dst_thx, dst_thy) * flux_factor
                cuda.atomic.add(OUTPUT, (x, y), val)
                continue

            # --- Δ-grid histogram fill with triangular weights ---
            invNi = 1.0 / float32(Ni)
            for diN in range(-Ni, N):
                dthx = float32(diN) * invNi * px
                wx = N - abs(diN)
                src_dthx = -0.5 * dthx
                dst_dthx = +0.5 * dthx

                for djN in range(-Ni, N):
                    dthy = float32(djN) * invNi * px
                    wy = N - abs(djN)
                    w = float32(wx * wy)

                    src_dthy = -0.5 * dthy
                    dst_dthy = +0.5 * dthy

                    src_x_ = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                    src_y_ = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                    src_z_ = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)

                    dst_x_ = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                    dst_y_ = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                    dst_z_ = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)

                    ang_ = angle(src_x_, src_y_, src_z_, dst_x_, dst_y_, dst_z_)
                    b = int((ang_ - angle_min) / d_angle)
                    if b < 0:
                        b = 0
                    elif b >= bins:
                        b = bins - 1
                    hist[b] += w

            # === Normalize histogram and compute expectation of PDF ===
            sum_hist = float32(0.0)
            for k in range(bins):
                sum_hist += hist[k]

            if sum_hist <= 0.0:
                continue

            inv_sum = 1.0 / sum_hist
            expected_val = float32(0.0)
            for k in range(bins):
                angle_k = angle_min + (k + 0.5) * d_angle
                expected_val += hist[k] * PDF(angle_k, A, sigma, s2, s3, nval, f1, f2)

            expected_val *= inv_sum

            # === Compute splat value ===
            val = expected_val * jacobian(dst_thx, dst_thy) * flux_factor
            if val > 0.0:
                cuda.atomic.add(OUTPUT, (x, y), val)

    @cuda.jit("void(float32[:, :], float32[:, :])", fastmath=True)
    def splat3_kernel(PARAMS, OUTPUT):
        n = cuda.blockIdx.x
        t = cuda.threadIdx.x
        T = cuda.blockDim.x

        # --- 1. Load PARAMS[n, :] into shared memory once per block -------------
        p = cuda.shared.array(shape=16, dtype=float32)
        for k in range(t, 16, T):
            p[k] = PARAMS[n, k]
        cuda.syncthreads()

        A = p[0]
        sigma = p[1]
        s2 = p[2]
        s3 = p[3]
        nval = p[4]
        f1 = p[5]
        f2 = p[6]
        sr = p[7]

        src_thx = p[8]
        src_thy = p[9]

        src_idx = int32(p[10])
        src_idy = int32(p[11])

        # p[12] unused in your snippet
        PhiE = p[13]
        # p[14], p[15] unused in your snippet

        # --- 2. Precompute stuff that is constant for this source ----------------
        # number of pixels around the source
        # (same formula as you had, just slightly rearranged)
        pixels_f = (window_size * sigma + 1e-7) * 0.5 / pixel_size
        pixels = int(pixels_f) + 1
        if pixels < 0:
            pixels = 0

        side = 2 * pixels + 1
        total = side * side

        # source direction in Cartesian
        src_x, src_y, src_z = angle2cart(src_thx, src_thy)

        # output dimensions (avoid repeated OUTPUT.shape[...] loads in the loop)
        H = OUTPUT.shape[0]
        W = OUTPUT.shape[1]

        # combine constant factors once
        pix_area = pixel_size * pixel_size
        flux_factor = PhiE * sr * pix_area

        # nothing to do for this source
        if total <= 0 or flux_factor == 0.0:
            return

        # --- 3. Loop over jobs (pixels in the window) ---------------------------
        for job in range(t, total, T):
            # decode 2D offset from linear index
            di = job // side - pixels
            dj = job % side - pixels

            # integer image coordinates
            x = src_idx + di
            y = src_idy + dj

            # skip if this pixel lies outside the OUTPUT array
            if x < 0 or x >= H or y < 0 or y >= W:
                continue

            # spherical angles at destination pixel
            dst_thx = src_thx + di * pixel_size
            dst_thy = src_thy + dj * pixel_size

            # Cartesian direction for destination
            dst_x, dst_y, dst_z = angle2cart(dst_thx, dst_thy)

            # scattering angle between source and destination directions
            ang = angle(src_x, src_y, src_z, dst_x, dst_y, dst_z)

            # Molière-like PDF (or your custom PDF)
            pdf_val = PDF(ang, A, sigma, s2, s3, nval, f1, f2)
            if pdf_val <= 0.0:
                continue

            # jacobian at destination (only if we know PDF is nonzero)
            jac = jacobian(dst_thx, dst_thy)

            val = pdf_val * jac * flux_factor

            # add to OUTPUT if positive (skip zeros/negatives)
            if val > 0.0:
                cuda.atomic.add(OUTPUT, (x, y), val)

    return splat1_kernel, splat2_kernel, splat3_kernel


def splat_kernels_track(pixel_size, window_size, bins):
    @cuda.jit("void(float32[:, :], float32[:, :], float32[:, :, :, :])", fastmath=True)
    def splat1_kernel(PARAMS, OUTPUT, TRACK):
        n = cuda.blockIdx.x
        t = cuda.threadIdx.x
        T = cuda.blockDim.x

        # --- Shared PARAMS[n] ---
        p = cuda.shared.array(16, dtype=float32)
        for k in range(t, 16, T):
            p[k] = PARAMS[n, k]
        cuda.syncthreads()

        A, sigma, s2, s3, nval, f1, f2, sr = p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]
        src_thx, src_thy = p[8], p[9]
        src_idx, src_idy = int32(p[10]), int32(p[11])
        PhiE = p[13]
        N = int32(p[14])
        Ni = N - 1

        # window + geometry
        pixels = int((window_size * sigma + 1e-7) * 0.5 / pixel_size) + 1
        total = (2 * pixels + 1) * (2 * pixels + 1)
        px = float32(pixel_size)

        src_x, src_y, src_z = angle2cart(src_thx, src_thy)
        sdx_thx, sdx_thy, sdy_thx, sdy_thy, sdz_thx, sdz_thy = jacobian_xyz_from_t(src_thx, src_thy)

        # per-thread area partial
        local_area = float32(0.0)

        # --- Shared buffer to keep per-job area_ so we don't recompute ---
        area_buf = cuda.shared.array(MAX_JOBS, dtype=float32)
        can_buffer = total <= MAX_JOBS
        if not can_buffer:
            # if you really want, you can early-return here as in non-track
            # return
            pass

        # ---------- Phase 1: compute area_[job] once and (if possible) store ----------
        for job in range(t, total, T):
            di = job // (2 * pixels + 1) - pixels
            dj = job % (2 * pixels + 1) - pixels

            dst_thx = src_thx + di * px
            dst_thy = src_thy + dj * px

            # dst central ray + jacobian
            dst_x, dst_y, dst_z = angle2cart(dst_thx, dst_thy)
            ddx_thx, ddx_thy, ddy_thx, ddy_thy, ddz_thx, ddz_thy = jacobian_xyz_from_t(dst_thx, dst_thy)

            # per-job local histogram
            hist = cuda.local.array(bins, dtype=float32)
            for k in range(bins):
                hist[k] = 0.0

            # estimate angle range (2x2x2x2 probe)
            angle_min = float32(3.14159265)
            angle_max = float32(0.0)
            for ii in range(2):
                src_dthx = (ii - 0.5) * px
                for jj in range(2):
                    src_dthy = (jj - 0.5) * px
                    sx = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                    sy = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                    sz = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)
                    for kk in range(2):
                        dst_dthx = (kk - 0.5) * px
                        for ll in range(2):
                            dst_dthy = (ll - 0.5) * px
                            dx = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                            dy = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                            dz = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)
                            ang_ = angle(sx, sy, sz, dx, dy, dz)
                            if ang_ < angle_min:
                                angle_min = ang_
                            if ang_ > angle_max:
                                angle_max = ang_

            d_angle = (angle_max - angle_min) / float32(bins)

            if Ni <= 0:
                ang0 = angle(src_x, src_y, src_z, dst_x, dst_y, dst_z)
                b = int((ang0 - angle_min) / d_angle)
                if b < 0:
                    b = 0
                elif b >= bins:
                    b = bins - 1
                hist[b] += 1.0
            else:
                invNi = 1.0 / float32(Ni)
                for diN in range(-(N - 1), N):
                    dthx = float32(diN) * invNi * px
                    wx = (N - abs(diN))
                    src_dthx = -0.5 * dthx
                    dst_dthx = +0.5 * dthx
                    for djN in range(-(N - 1), N):
                        dthy = float32(djN) * invNi * px
                        wy = (N - abs(djN))
                        w = float32(wx * wy)
                        src_dthy = -0.5 * dthy
                        dst_dthy = +0.5 * dthy

                        sx = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                        sy = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                        sz = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)

                        dx = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                        dy = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                        dz = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)

                        ang_ = angle(sx, sy, sz, dx, dy, dz)
                        b = int((ang_ - angle_min) / d_angle)
                        if b < 0:
                            b = 0
                        elif b >= bins:
                            b = bins - 1
                        hist[b] += w

            # expectation -> area_
            sum_hist = float32(0.0)
            for k in range(bins):
                sum_hist += hist[k]
            if sum_hist > 0.0:
                inv_sum = 1.0 / sum_hist
                expected_val = float32(0.0)
                for k in range(bins):
                    angle_k = angle_min + (k + 0.5) * d_angle
                    expected_val += hist[k] * PDF(angle_k, A, sigma, s2, s3, nval, f1, f2) * inv_sum
                area_ = expected_val * px * px * jacobian(dst_thx, dst_thy)
                local_area += area_
                if can_buffer:
                    area_buf[job] = area_
            else:
                if can_buffer:
                    area_buf[job] = 0.0

        # ---------- reduction for total_area ----------
        part = cuda.shared.array(256, dtype=float32)  # assumes T<=256
        part[t] = local_area
        cuda.syncthreads()
        stride = T // 2
        while stride > 0:
            if t < stride:
                part[t] += part[t + stride]
            cuda.syncthreads()
            stride //= 2
        total_area = part[0]
        cuda.syncthreads()

        # ---------- Phase 2: emit normalized value (no recompute if buffered) ----------
        if total_area > 0.0:
            H = OUTPUT.shape[0]
            W = OUTPUT.shape[1]
            for job in range(t, total, T):
                di = job // (2 * pixels + 1) - pixels
                dj = job % (2 * pixels + 1) - pixels

                if can_buffer:
                    a = area_buf[job]
                else:
                    # fallback: recompute area_ if total > MAX_JOBS
                    dst_thx = src_thx + di * px
                    dst_thy = src_thy + dj * px
                    dst_x, dst_y, dst_z = angle2cart(dst_thx, dst_thy)
                    ddx_thx, ddx_thy, ddy_thx, ddy_thy, ddz_thx, ddz_thy = jacobian_xyz_from_t(dst_thx, dst_thy)

                    hist = cuda.local.array(bins, dtype=float32)
                    for k in range(bins):
                        hist[k] = 0.0
                    angle_min = float32(3.14159265)
                    angle_max = float32(0.0)
                    for ii in range(2):
                        src_dthx = (ii - 0.5) * px
                        for jj in range(2):
                            src_dthy = (jj - 0.5) * px
                            sx = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                            sy = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                            sz = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)
                            for kk in range(2):
                                dst_dthx = (kk - 0.5) * px
                                for ll in range(2):
                                    dst_dthy = (ll - 0.5) * px
                                    dx = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                                    dy = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                                    dz = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)
                                    ang_ = angle(sx, sy, sz, dx, dy, dz)
                                    if ang_ < angle_min:
                                        angle_min = ang_
                                    if ang_ > angle_max:
                                        angle_max = ang_
                    d_angle = (angle_max - angle_min) / float32(bins)
                    if Ni <= 0:
                        ang0 = angle(src_x, src_y, src_z, dst_x, dst_y, dst_z)
                        b = int((ang0 - angle_min) / d_angle)
                        if b < 0:
                            b = 0
                        elif b >= bins:
                            b = bins - 1
                        hist[b] += 1.0
                    else:
                        invNi = 1.0 / float32(Ni)
                        for diN in range(-(N - 1), N):
                            dthx = float32(diN) * invNi * px
                            wx = (N - abs(diN))
                            src_dthx = -0.5 * dthx
                            dst_dthx = +0.5 * dthx
                            for djN in range(-(N - 1), N):
                                dthy = float32(djN) * invNi * px
                                wy = (N - abs(djN))
                                w = float32(wx * wy)
                                src_dthy = -0.5 * dthy
                                dst_dthy = +0.5 * dthy
                                sx = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                                sy = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                                sz = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)
                                dx = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                                dy = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                                dz = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)
                                ang_ = angle(sx, sy, sz, dx, dy, dz)
                                b = int((ang_ - angle_min) / d_angle)
                                if b < 0:
                                    b = 0
                                elif b >= bins:
                                    b = bins - 1
                                hist[b] += w
                    sum_hist = float32(0.0)
                    for k in range(bins):
                        sum_hist += hist[k]
                    if sum_hist > 0.0:
                        inv_sum = 1.0 / sum_hist
                        expected_val = float32(0.0)
                        for k in range(bins):
                            angle_k = angle_min + (k + 0.5) * d_angle
                            expected_val += hist[k] * PDF(angle_k, A, sigma, s2, s3, nval, f1, f2) * inv_sum
                        a = expected_val * px * px * jacobian(dst_thx, dst_thy)
                    else:
                        a = 0.0

                if a > 0.0:
                    val = a * PhiE * sr / total_area
                    x = src_idx + di
                    y = src_idy + dj
                    if 0 <= x < H and 0 <= y < W:
                        cuda.atomic.add(OUTPUT, (x, y), val)
                        TRACK[src_idx, src_idy, x, y] += val

        # write out total area for diagnostics
        if t == 0:
            PARAMS[n, 15] = total_area

    @cuda.jit("void(float32[:, :], float32[:, :], float32[:, :, :, :])", fastmath=True)
    def splat2_kernel(PARAMS, OUTPUT, TRACK):
        n = cuda.blockIdx.x
        t = cuda.threadIdx.x
        T = cuda.blockDim.x

        # === Shared memory cache for PARAMS[n] ===
        p = cuda.shared.array(16, dtype=float32)
        for k in range(t, 16, T):
            p[k] = PARAMS[n, k]
        cuda.syncthreads()

        # === Unpack shared parameters ===
        A, sigma, s2, s3, nval, f1, f2, sr = p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]
        src_thx, src_thy = p[8], p[9]
        src_idx, src_idy = int32(p[10]), int32(p[11])
        PhiE = p[13]
        N = int32(p[14])
        Ni = N - 1

        # === Precompute window geometry ===
        pixels_f = (window_size * sigma + 1e-7) * 0.5 / pixel_size
        pixels = int(pixels_f) + 1
        if pixels < 0:
            pixels = 0

        side = 2 * pixels + 1
        total = side * side

        H = OUTPUT.shape[0]
        W = OUTPUT.shape[1]

        # source direction
        src_x, src_y, src_z = angle2cart(src_thx, src_thy)

        # source jacobian only needed if we supersample
        if Ni > 0:
            sdx_thx, sdx_thy, sdy_thx, sdy_thy, sdz_thx, sdz_thy = jacobian_xyz_from_t(src_thx, src_thy)

        pix_area = pixel_size * pixel_size
        flux_factor = PhiE * sr * pix_area

        if total <= 0 or flux_factor == 0.0:
            return

        px = float32(pixel_size)

        # === Main parallelized loop ===
        for job in range(t, total, T):
            di = job // side - pixels
            dj = job % side - pixels

            x = src_idx + di
            y = src_idy + dj

            # early skip if outside OUTPUT
            if x < 0 or x >= H or y < 0 or y >= W:
                continue

            dst_thx = src_thx + di * pixel_size
            dst_thy = src_thy + dj * pixel_size

            # SIMPLE CASE: N <= 1 (no triangular supersampling)
            if Ni <= 0:
                dst_x, dst_y, dst_z = angle2cart(dst_thx, dst_thy)
                ang = angle(src_x, src_y, src_z, dst_x, dst_y, dst_z)
                val = PDF(ang, A, sigma, s2, s3, nval, f1, f2)
                if val <= 0.0:
                    continue
                val *= jacobian(dst_thx, dst_thy) * flux_factor
                if val > 0.0:
                    cuda.atomic.add(OUTPUT, (x, y), val)
                    TRACK[src_idx, src_idy, x, y] += val
                continue

            # FULL CASE: N > 1 (triangular weighting & local histogram)
            dst_x, dst_y, dst_z = angle2cart(dst_thx, dst_thy)
            ddx_thx, ddx_thy, ddy_thx, ddy_thy, ddz_thx, ddz_thy = jacobian_xyz_from_t(dst_thx, dst_thy)

            # local histogram
            hist = cuda.local.array(bins, dtype=float32)
            for k in range(bins):
                hist[k] = 0.0

            # Estimate angle range with 2×2×2×2 probe
            angle_min = float32(3.14159265)
            angle_max = float32(0.0)

            for ii in range(2):
                src_dthx = (ii - 0.5) * px
                for jj in range(2):
                    src_dthy = (jj - 0.5) * px
                    src_x_ = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                    src_y_ = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                    src_z_ = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)

                    for kk in range(2):
                        dst_dthx = (kk - 0.5) * px
                        for ll in range(2):
                            dst_dthy = (ll - 0.5) * px
                            dst_x_ = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                            dst_y_ = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                            dst_z_ = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)
                            ang_ = angle(src_x_, src_y_, src_z_, dst_x_, dst_y_, dst_z_)
                            if ang_ < angle_min:
                                angle_min = ang_
                            if ang_ > angle_max:
                                angle_max = ang_

            d_angle = (angle_max - angle_min) / float32(bins)

            # degeneracy guard
            if d_angle <= 0.0:
                ang = angle(src_x, src_y, src_z, dst_x, dst_y, dst_z)
                val = PDF(ang, A, sigma, s2, s3, nval, f1, f2)
                if val <= 0.0:
                    continue
                val *= jacobian(dst_thx, dst_thy) * flux_factor
                cuda.atomic.add(OUTPUT, (x, y), val)
                TRACK[src_idx, src_idy, x, y] += val
                continue

            # Δ-grid histogram fill with triangular weights
            invNi = 1.0 / float32(Ni)
            for diN in range(-Ni, N):
                dthx = float32(diN) * invNi * px
                wx = N - abs(diN)
                src_dthx = -0.5 * dthx
                dst_dthx = +0.5 * dthx

                for djN in range(-Ni, N):
                    dthy = float32(djN) * invNi * px
                    wy = N - abs(djN)
                    w = float32(wx * wy)

                    src_dthy = -0.5 * dthy
                    dst_dthy = +0.5 * dthy

                    src_x_ = x_lin(src_x, sdx_thx, sdx_thy, src_dthx, src_dthy)
                    src_y_ = y_lin(src_y, sdy_thx, sdy_thy, src_dthx, src_dthy)
                    src_z_ = z_lin(src_z, sdz_thx, sdz_thy, src_dthx, src_dthy)

                    dst_x_ = x_lin(dst_x, ddx_thx, ddx_thy, dst_dthx, dst_dthy)
                    dst_y_ = y_lin(dst_y, ddy_thx, ddy_thy, dst_dthx, dst_dthy)
                    dst_z_ = z_lin(dst_z, ddz_thx, ddz_thy, dst_dthx, dst_dthy)

                    ang_ = angle(src_x_, src_y_, src_z_, dst_x_, dst_y_, dst_z_)
                    b = int((ang_ - angle_min) / d_angle)
                    if b < 0:
                        b = 0
                    elif b >= bins:
                        b = bins - 1
                    hist[b] += w

            # Normalize histogram and compute expectation of PDF
            sum_hist = float32(0.0)
            for k in range(bins):
                sum_hist += hist[k]

            if sum_hist <= 0.0:
                continue

            inv_sum = 1.0 / sum_hist
            expected_val = float32(0.0)
            for k in range(bins):
                angle_k = angle_min + (k + 0.5) * d_angle
                expected_val += hist[k] * PDF(angle_k, A, sigma, s2, s3, nval, f1, f2)

            expected_val *= inv_sum

            # Compute splat value (no area accumulation)
            val = expected_val * jacobian(dst_thx, dst_thy) * flux_factor

            if val > 0.0:
                cuda.atomic.add(OUTPUT, (x, y), val)
                TRACK[src_idx, src_idy, x, y] += val

    @cuda.jit("void(float32[:, :], float32[:, :], float32[:, :, :, :])", fastmath=True)
    def splat3_kernel(PARAMS, OUTPUT, TRACK):
        n = cuda.blockIdx.x
        t = cuda.threadIdx.x
        T = cuda.blockDim.x

        # shared load of PARAMS[n]
        p = cuda.shared.array(16, dtype=float32)
        for k in range(t, 16, T):
            p[k] = PARAMS[n, k]
        cuda.syncthreads()

        A, sigma, s2, s3, nval, f1, f2, sr = p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]
        src_thx, src_thy = p[8], p[9]
        src_idx, src_idy = int32(p[10]), int32(p[11])
        PhiE = p[13]
        # p[14], p[15] unused

        # window geometry
        pixels_f = (window_size * sigma + 1e-7) * 0.5 / pixel_size
        pixels = int(pixels_f) + 1
        if pixels < 0:
            pixels = 0
        side = 2 * pixels + 1
        total = side * side

        # source direction
        src_x, src_y, src_z = angle2cart(src_thx, src_thy)

        # output dims
        H = OUTPUT.shape[0]
        W = OUTPUT.shape[1]

        pix_area = pixel_size * pixel_size
        flux_factor = PhiE * sr * pix_area

        if total <= 0 or flux_factor == 0.0:
            return

        # loop over window pixels
        for job in range(t, total, T):
            di = job // side - pixels
            dj = job % side - pixels

            x = src_idx + di
            y = src_idy + dj

            if x < 0 or x >= H or y < 0 or y >= W:
                continue

            dst_thx = src_thx + di * pixel_size
            dst_thy = src_thy + dj * pixel_size

            dst_x, dst_y, dst_z = angle2cart(dst_thx, dst_thy)
            ang = angle(src_x, src_y, src_z, dst_x, dst_y, dst_z)

            pdf_val = PDF(ang, A, sigma, s2, s3, nval, f1, f2)
            if pdf_val <= 0.0:
                continue

            jac = jacobian(dst_thx, dst_thy)

            val = pdf_val * jac * flux_factor
            if val > 0.0:
                cuda.atomic.add(OUTPUT, (x, y), val)
                TRACK[src_idx, src_idy, x, y] += val

    return splat1_kernel, splat2_kernel, splat3_kernel

