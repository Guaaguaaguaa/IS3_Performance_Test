"""
baseline.py — 基线与噪声估计
职责：从原始光谱中估计逐像素基线和全局噪声标准差

暴露接口：
    estimate_baseline(intensity, window_size, percentile) -> (baseline, noise_std)

设计说明：
    基线平坦假设下，采用滚动百分位数法：
    - 将光谱分成若干小窗口，每窗口取低百分位数作为局部基线估计
    - 再用线性插值还原到逐像素分辨率
    - noise_std 用无峰区域（低于基线 + 粗阈值）的像素估计

来源：改编自 SpecWaveCal_HH3/wavecal/baseline.py
"""

import numpy as np
from typing import Tuple


def estimate_baseline(
    intensity: np.ndarray,
    window_size: int = 100,
    percentile: float = 10.0,
) -> Tuple[np.ndarray, float]:
    """
    滚动百分位数基线估计。

    Parameters
    ----------
    intensity    : 原始强度数组，shape (N,)
    window_size  : 滚动窗口宽度（像素），默认 100
                   建议 >> 最宽峰宽，<< 探测器总长
    percentile   : 取窗口内第几百分位数作为基线，默认 10
                   基线平坦时 10 已足够；有缓变背景时可适当提高到 20

    Returns
    -------
    baseline  : np.ndarray shape (N,)，逐像素基线
    noise_std : float，无峰区域的噪声标准差

    Notes
    -----
    - window_size 应远大于单峰宽度，否则峰脚会压低百分位数估计
    - 对于 2048 px 探测器，window_size=100 通常是合理起点
    """
    intensity = np.asarray(intensity, dtype=float)
    n = len(intensity)

    # ── Step 1：滚动窗口百分位数，得到稀疏控制点 ────────────────────────────
    half = window_size // 2
    centers = np.arange(half, n - half, half)  # 每半窗步进一个控制点

    # 边界补充首尾控制点
    if len(centers) == 0:
        centers = np.array([0, n - 1])
    else:
        if centers[0] != 0:
            centers = np.concatenate([[0], centers])
        if centers[-1] != n - 1:
            centers = np.concatenate([centers, [n - 1]])

    baseline_ctrl = np.array([
        np.percentile(intensity[max(0, c - half): min(n, c + half)], percentile)
        for c in centers
    ])

    # ── Step 2：线性插值还原到逐像素 ─────────────────────────────────────────
    baseline = np.interp(np.arange(n), centers, baseline_ctrl)

    # ── Step 3：估计噪声标准差（只用"无峰"区域）────────────────────────────
    # 粗判：强度低于 baseline + 3×粗噪声 的区域认为是纯背景
    # 先用全局 MAD 做粗噪声估计，再精化
    residual = intensity - baseline
    mad = np.median(np.abs(residual - np.median(residual)))
    rough_noise = mad * 1.4826  # MAD → sigma 换算系数（高斯假设）

    background_mask = residual < 3.0 * rough_noise
    if background_mask.sum() < 10:
        # 极端情况：几乎全是峰，退回全局 MAD
        noise_std = rough_noise
    else:
        noise_std = residual[background_mask].std()
        if noise_std < 1e-6:
            noise_std = rough_noise  # 防止除零

    return baseline, float(noise_std)
