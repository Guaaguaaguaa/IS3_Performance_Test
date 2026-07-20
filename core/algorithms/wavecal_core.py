import numpy as np
import pandas as pd
from scipy.signal import find_peaks as scipy_find_peaks

from core.algorithms.wavecal_peaks import PEAK_INDEX_WINDOWS, PEAK_WAVELENGTHS
from core.algorithms.baseline import estimate_baseline


# ═══════════════════════════════════════════════════════════════════════════════
# 质心定位（改编自 SpecWaveCal_HH3/wavecal/peak_finder.py）
# ═══════════════════════════════════════════════════════════════════════════════

def compute_centroid(pixels, I_win):
    """
    强度加权质心：centroid = sum(I[i] * pixel[i]) / sum(I[i])

    Parameters
    ----------
    pixels : np.ndarray, 像素坐标
    I_win  : np.ndarray, 扣基线后的强度（应已 clip 到 >= 0）

    Returns
    -------
    float — 亚像素质心位置。total <= 0 时回退到窗口中心。
    """
    I_clipped = np.clip(I_win, 0, None)
    total = I_clipped.sum()
    if total <= 0:
        return float(pixels[len(pixels) // 2])
    return float(np.dot(I_clipped, pixels) / total)


def _top_n_centroid(I_win, pixels, n):
    """
    取窗口内强度最高的 n 个像素计算质心。
    用于排除不对称峰的拖尾干扰。
    """
    sorted_idx = np.argsort(I_win)[::-1]
    top_n = min(n, len(sorted_idx))
    top_idx = sorted_idx[:top_n]
    return compute_centroid(pixels[top_idx], I_win[top_idx])


def _find_boundary(I_corr, peak_idx, direction, threshold,
                   max_half_width=15, consec=3):
    """
    从峰顶向一侧逐像素行走，找连续回落点作为边界。

    Parameters
    ----------
    I_corr        : 扣基线后的强度数组
    peak_idx      : 峰顶像素位置
    direction     : -1 向左搜索，+1 向右搜索
    threshold     : 基线回落阈值（如 3 * noise_std）
    max_half_width: 最大搜索范围，超时强制截断
    consec        : 连续低于阈值的点数要求

    Returns
    -------
    int — 边界像素位置
    """
    n = len(I_corr)
    consec_count = 0
    first_hit = None

    idx = peak_idx + direction
    steps = 0
    while 0 <= idx < n and steps < max_half_width:
        if I_corr[idx] <= threshold:
            if consec_count == 0:
                first_hit = idx
            consec_count += 1
            if consec_count >= consec:
                return first_hit
        else:
            consec_count = 0
            first_hit = None
        idx += direction
        steps += 1

    # 未自然收敛，回退到最后有效位置
    return max(0, min(n - 1, idx - direction))


def _find_core_window(I_corr, peak_idx, left, right, peak_height, ratio=0.5):
    """
    在 [left, right] 内找到强度 >= ratio*peak_height 的核心区域，
    排除峰裙边对质心的干扰。

    Returns
    -------
    (core_left, core_right)
    """
    core_thresh = peak_height * ratio

    core_left = left
    for idx in range(peak_idx, left - 1, -1):
        if I_corr[idx] < core_thresh:
            core_left = idx + 1
            break

    core_right = right
    for idx in range(peak_idx, right + 1):
        if I_corr[idx] < core_thresh:
            core_right = idx - 1
            break

    core_left = max(left, min(core_left, peak_idx))
    core_right = min(right, max(core_right, peak_idx))
    return core_left, core_right


def extract_peak_window(I_corr, left, right):
    """返回 [left, right] 闭区间的像素坐标和扣基线强度。"""
    pixels = np.arange(left, right + 1, dtype=float)
    I_win = I_corr[left: right + 1].copy()
    return pixels, I_win


# ═══════════════════════════════════════════════════════════════════════════════
# 寻峰（质心模式）
# ═══════════════════════════════════════════════════════════════════════════════

def find_peaks_by_index(signal, index_windows, shift=0,
                        baseline=None, noise_std=None):
    """
    在预设窗口内寻找特征峰，返回亚像素质心位置。

    Parameters
    ----------
    signal        : 原始光谱强度
    index_windows : PEAK_INDEX_WINDOWS[lamp] 的窗口字典
    shift         : 全局像素偏移
    baseline      : 逐像素基线（None 时退化为纯 argmax）
    noise_std     : 全局噪声标准差（用于边界回落阈值）

    Returns
    -------
    peaks : dict[name -> float or None]  亚像素质心位置
    diag  : dict[name -> dict or None]   每峰的诊断信息
            {"centroid": float, "argmax_px": int, "deviation": float,
             "core_width": int, "peak_height": float, "method": str}
    """
    peaks = {}
    diag = {}
    n = len(signal)
    signal_arr = np.asarray(signal, dtype=float)

    if baseline is not None and noise_std is not None:
        I_corr = signal_arr - np.asarray(baseline, dtype=float)
        threshold = 3.0 * noise_std
        use_centroid = True
    else:
        I_corr = signal_arr
        threshold = 0
        use_centroid = False

    for name, (l, r) in index_windows.items():
        l2 = max(0, l + shift)
        r2 = min(n - 1, r + shift)

        if l2 >= r2:
            peaks[name] = None
            diag[name] = None
            continue

        seg = I_corr[l2: r2 + 1]
        peak_local = int(np.argmax(seg))
        peak_pixel = l2 + peak_local

        if use_centroid:
            peak_height = I_corr[peak_pixel]

            if peak_height <= threshold:
                # 峰太弱（不高于噪声），退化为 argmax
                peaks[name] = float(peak_pixel)
                diag[name] = {"centroid": float(peak_pixel),
                              "argmax_px": peak_pixel, "deviation": 0.0,
                              "core_width": 0, "peak_height": peak_height,
                              "method": "argmax_fallback"}
                continue

            # 动态边界扩展
            left = _find_boundary(I_corr, peak_pixel, -1, threshold)
            right = _find_boundary(I_corr, peak_pixel, +1, threshold)

            # 50% 核心窗口质心
            core_left, core_right = _find_core_window(
                I_corr, peak_pixel, left, right, peak_height, 0.5)
            core_width = core_right - core_left + 1
            method = "centroid"

            # 窄峰保护：核心窗口只有 1 px → 降到 20% 取更宽窗口
            if core_width <= 1:
                core_left, core_right = _find_core_window(
                    I_corr, peak_pixel, left, right, peak_height, 0.2)
                core_width = core_right - core_left + 1
                method = "centroid_20pct"

            pixels, I_win = extract_peak_window(I_corr, core_left, core_right)
            centroid = compute_centroid(pixels, I_win)
            deviation = abs(centroid - peak_pixel)

            # 不对称核心窗口 且 偏差 > 0.5 → top-5 修正
            # （核心窗口左右不对称说明 50% 截断偏了一侧，需要用 top-N 纠偏）
            left_span = peak_pixel - core_left
            right_span = core_right - peak_pixel
            core_asymmetric = abs(left_span - right_span) >= 2

            if (deviation > 1.0) or (core_asymmetric and deviation > 0.5):
                pixels_f, I_win_f = extract_peak_window(I_corr, left, right)
                centroid = _top_n_centroid(I_win_f, pixels_f, 5)
                deviation = abs(centroid - peak_pixel)
                method = "centroid_top5"
                # top-5 仍不理想 → top-3 兜底
                if deviation > 1.0 or (core_asymmetric and deviation > 0.5):
                    centroid = _top_n_centroid(I_win_f, pixels_f, 3)
                    deviation = abs(centroid - peak_pixel)
                    method = "centroid_top3"

            # 以上兜底后偏差仍 > 0.5 → 尝试更高核心比例（取峰顶）
            # 用于底部有拖尾的宽峰：60%/70%/80% 逐级聚焦上半部分
            if deviation > 0.5:
                for hi_ratio in (0.6, 0.7, 0.8):
                    cl_hi, cr_hi = _find_core_window(
                        I_corr, peak_pixel, left, right, peak_height, hi_ratio)
                    if cr_hi - cl_hi + 1 >= 2:
                        p_hi, iw_hi = extract_peak_window(I_corr, cl_hi, cr_hi)
                        c_hi = compute_centroid(p_hi, iw_hi)
                        dev_hi = abs(c_hi - peak_pixel)
                        if dev_hi < deviation:
                            centroid = c_hi
                            deviation = dev_hi
                            method = f"centroid_{int(hi_ratio*100)}pct"
                        if deviation <= 0.5:
                            break

            peaks[name] = float(centroid)
            diag[name] = {"centroid": centroid,
                          "argmax_px": peak_pixel, "deviation": deviation,
                          "core_width": core_width, "peak_height": peak_height,
                          "method": method,
                          "boundary_left": left, "boundary_right": right}
        else:
            peaks[name] = float(peak_pixel)
            diag[name] = None

    return peaks, diag


# ═══════════════════════════════════════════════════════════════════════════════
# 灯类型检测
# ═══════════════════════════════════════════════════════════════════════════════

def detect_lamp_type(filename):
    fname = filename.upper()
    for k in PEAK_INDEX_WINDOWS.keys():
        if k in fname:
            return k
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 全光谱寻峰（候选峰库，供 peakfind_log 使用）
# ═══════════════════════════════════════════════════════════════════════════════

def find_all_peaks_full_spectrum(signal, baseline, noise_std):
    """
    用 scipy.find_peaks 扫描全光谱，返回所有候选峰及其质心。

    Parameters
    ----------
    signal   : 原始光谱强度
    baseline : 逐像素基线
    noise_std: 噪声标准差

    Returns
    -------
    list of dict: 每个候选峰的诊断信息（按 centroid 排序）
    """
    signal_arr = np.asarray(signal, dtype=float)
    I_corr = signal_arr - np.asarray(baseline, dtype=float)
    threshold = 3.0 * noise_std
    min_height = 5.0 * noise_std

    # Step 1: 粗寻峰（scipy.find_peaks）
    raw_peaks, _ = scipy_find_peaks(I_corr, height=min_height)

    # Step 2: 对每个候选峰计算质心
    candidates = []
    for px in raw_peaks:
        peak_height = float(I_corr[px])
        if peak_height <= threshold:
            continue

        # 动态边界
        left = _find_boundary(I_corr, px, -1, threshold)
        right = _find_boundary(I_corr, px, +1, threshold)

        # 标准质心路径（与 find_peaks_by_index 一致）
        core_l, core_r = _find_core_window(I_corr, px, left, right, peak_height, 0.5)
        core_width = core_r - core_l + 1
        method = "centroid"

        if core_width <= 1:
            core_l, core_r = _find_core_window(I_corr, px, left, right, peak_height, 0.2)
            core_width = core_r - core_l + 1
            method = "centroid_20pct"

        pixels, I_win = extract_peak_window(I_corr, core_l, core_r)
        centroid = compute_centroid(pixels, I_win)
        deviation = abs(centroid - px)

        left_span = px - core_l
        right_span = core_r - px
        core_asymmetric = abs(left_span - right_span) >= 2

        if (deviation > 1.0) or (core_asymmetric and deviation > 0.5):
            pixels_f, I_win_f = extract_peak_window(I_corr, left, right)
            centroid = _top_n_centroid(I_win_f, pixels_f, 5)
            deviation = abs(centroid - px)
            method = "centroid_top5"
            if deviation > 1.0 or (core_asymmetric and deviation > 0.5):
                centroid = _top_n_centroid(I_win_f, pixels_f, 3)
                deviation = abs(centroid - px)
                method = "centroid_top3"

        if deviation > 0.5:
            for hi_ratio in (0.6, 0.7, 0.8):
                cl_hi, cr_hi = _find_core_window(I_corr, px, left, right, peak_height, hi_ratio)
                if cr_hi - cl_hi + 1 >= 2:
                    p_hi, iw_hi = extract_peak_window(I_corr, cl_hi, cr_hi)
                    c_hi = compute_centroid(p_hi, iw_hi)
                    dev_hi = abs(c_hi - px)
                    if dev_hi < deviation:
                        centroid = c_hi
                        deviation = dev_hi
                        method = f"centroid_{int(hi_ratio*100)}pct"
                    if deviation <= 0.5:
                        break

        candidates.append({
            "peak_pixel": int(px),
            "centroid": float(centroid),
            "deviation": deviation,
            "peak_height": peak_height,
            "core_width": core_width,
            "method": method,
            "boundary_left": left,
            "boundary_right": right,
        })

    candidates.sort(key=lambda d: d["centroid"])
    return candidates


# ═══════════════════════════════════════════════════════════════════════════════
# 定标主流程
# ═══════════════════════════════════════════════════════════════════════════════

def build_wavecal(records, shift=0):
    lamp_records = {"KR": [], "AR": [], "NM": []}

    for rec in records:
        lamp = detect_lamp_type(rec["filename"])
        if lamp:
            lamp_records[lamp].append(rec)

    for k, v in lamp_records.items():
        if len(v) == 0:
            raise RuntimeError(f"缺少 {k} 灯文件，Wavecal 需要 KR / AR / NM 三种灯")

    all_indexes = []
    all_ref_wls = []
    peak_detail = []
    all_diag = {}         # {(lamp, peak_name): diag_dict} — 定标用峰
    all_candidates = {}   # {lamp: [candidate_dict, ...]} — 全光谱候选峰库

    for lamp, recs in lamp_records.items():
        rec = recs[0]  # 每种灯只取一条
        signal = rec["data"].ravel()

        # 基线估计（滚动百分位数法）
        baseline, noise_std = estimate_baseline(signal)

        # 全光谱寻峰（候选峰库）
        candidates = find_all_peaks_full_spectrum(signal, baseline, noise_std)
        all_candidates[lamp] = candidates

        # 窗口匹配（定标用）
        peaks, diag = find_peaks_by_index(
            signal, PEAK_INDEX_WINDOWS[lamp], shift,
            baseline=baseline, noise_std=noise_std,
        )

        for (peak_name, idx), ref_wl in zip(peaks.items(),
                                            PEAK_WAVELENGTHS[lamp]):
            if idx is not None:
                all_indexes.append(idx)
                all_ref_wls.append(ref_wl)
                peak_detail.append((lamp, peak_name, idx, ref_wl))
                all_diag[(lamp, peak_name)] = diag.get(peak_name)

    all_indexes = np.asarray(all_indexes)
    all_ref_wls = np.asarray(all_ref_wls)

    # 按索引升序排序
    order = np.argsort(all_indexes)
    all_indexes = all_indexes[order]
    all_ref_wls = all_ref_wls[order]

    coeffs = np.polyfit(all_indexes, all_ref_wls, 3)
    poly = np.poly1d(coeffs)

    calibrated = poly(all_indexes)
    delta = all_ref_wls - calibrated

    fit_df = pd.DataFrame({
        "index": all_indexes,
        "ref_wavelength": all_ref_wls,
        "calibrated_wavelength": calibrated,
        "delta": delta,
    })

    return poly, coeffs, fit_df, peak_detail, all_diag, all_candidates


# ═══════════════════════════════════════════════════════════════════════════════
# 寻峰日志
# ═══════════════════════════════════════════════════════════════════════════════

def write_peakfind_log(all_candidates, fit_df, output_path):
    """
    输出全光谱候选峰库日志（所有 scipy.find_peaks 找到的峰）。

    Parameters
    ----------
    all_candidates : {lamp: [candidate_dict, ...]}
    fit_df         : 多项式拟合结果 DataFrame
    output_path    : 日志文件输出路径
    """
    import datetime
    sep = "-" * 72
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total = sum(len(v) for v in all_candidates.values())

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"{sep}\n")
        f.write(f"WaveCal 全光谱寻峰日志  生成时间: {timestamp}\n")
        f.write(f"{sep}\n\n")

        f.write("[INFO]  Step 1: 基线估计 (滚动百分位数法)\n")
        f.write("[INFO]  Step 2: 全光谱寻峰 (scipy.find_peaks)\n\n")

        for lamp in sorted(all_candidates.keys()):
            f.write(f"--- {lamp} 灯 ({len(all_candidates[lamp])} 个候选峰) ---\n")
            for d in all_candidates[lamp]:
                c = d["centroid"]
                px = d["peak_pixel"]
                dev = d["deviation"]
                ph = d["peak_height"]
                cw = d["core_width"]
                method = d["method"]
                bl = d["boundary_left"]
                br = d["boundary_right"]
                warn = " !" if dev > 0.5 else ""
                f.write(f"  px={px:4d}  centroid={c:8.3f}  dev={dev:.3f}  "
                        f"height={ph:8.0f}  core_w={cw:2d}  "
                        f"method={method:<18s}  boundary=[{bl},{br}]{warn}\n")
            f.write("\n")

        rms = float(np.sqrt(np.mean(fit_df["delta"] ** 2)))
        n_warn = sum(1 for v in all_candidates.values()
                     for d in v if d["deviation"] > 0.5)
        f.write(f"[SUMMARY]  候选峰总数: {total}  偏差>0.5: {n_warn}  "
                f"RMS={rms:.4f} nm\n")
        f.write(f"{sep}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 自动 Shift 扫描
# ═══════════════════════════════════════════════════════════════════════════════

def auto_find_shift(records, search_radius=50):
    """
    用 NM 灯 1014nm 最强峰作为锚点，自动确定全局 pixel shift。

    原理：NM_F3（1013.976 nm）是最强、最孤立的特征峰。在宽范围内
    找到它的真实位置，与预设窗口中心的偏差即为全局 shift。

    Parameters
    ----------
    records       : list of dict
    search_radius : 在预设窗口 ±search_radius 像素内搜索锚点峰

    Returns
    -------
    (shift, n_peaks) : (int, int)
        shift=0 且 n_peaks=0 表示未找到 NM 灯或锚点峰
    """
    # ── 1. 找到 NM 灯记录 ──────────────────────────────────────────
    nm_signal = None
    for rec in records:
        if detect_lamp_type(rec["filename"]) == "NM":
            nm_signal = np.asarray(rec["data"].ravel(), dtype=float)
            break

    if nm_signal is None:
        return 0, 0

    # ── 2. 基线估计 + 锚点峰定位 ──────────────────────────────────
    baseline, noise_std = estimate_baseline(nm_signal)
    I_corr = nm_signal - baseline

    # NM_F3 预设窗口 (46, 52)，中心 49
    nm_f3_win = PEAK_INDEX_WINDOWS["NM"]["NM_F3"]
    center_expected = (nm_f3_win[0] + nm_f3_win[1]) / 2.0  # 49.0

    n = len(I_corr)
    search_l = max(0, nm_f3_win[0] - search_radius)
    search_r = min(n - 1, nm_f3_win[1] + search_radius)

    # 在搜索范围内找 I_corr 最大值 → 锚点峰粗位置
    search_seg = I_corr[search_l: search_r + 1]
    anchor_local = int(np.argmax(search_seg))
    anchor_px = search_l + anchor_local
    anchor_height = float(I_corr[anchor_px])

    if anchor_height <= 3.0 * noise_std:
        return 0, 0  # 锚点峰太弱

    # ── 3. shift = argmax - 预设窗口中心 ─────────────────────────────
    #     用 argmax（整数最强像素）而非质心（浮点），避免不对称峰
    #     导致 round 偏差 1px。亚像素精度由多项式拟合自然吸收。
    shift = anchor_px - int(round(center_expected))

    # ── 5. 用此 shift 验证能找到多少峰 ─────────────────────────────
    n_found = 0
    for rec in records:
        lamp = detect_lamp_type(rec["filename"])
        if lamp is None:
            continue
        sig = np.asarray(rec["data"].ravel(), dtype=float)
        bl, ns = estimate_baseline(sig)
        Ic = sig - bl
        for _name, (win_l, win_r) in PEAK_INDEX_WINDOWS[lamp].items():
            l2 = max(0, win_l + shift)
            r2 = min(len(Ic) - 1, win_r + shift)
            if l2 < r2 and float(Ic[l2: r2 + 1].max()) > 3.0 * ns:
                n_found += 1

    return shift, n_found
