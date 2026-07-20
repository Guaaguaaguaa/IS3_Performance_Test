import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
import os

# ============================================================
# 峰 index 窗口（你给的，原封不动）
# ============================================================
PEAK_INDEX_WINDOWS = {
    "KR": {
        "KR_F1": (334, 338),
        "KR_F2": (199, 203),
        "KR_F3": (155, 159),
        "KR_F4": (126, 132),
    },
    "AR": {
        "AR_F1": (259, 263),
        "AR_F2": (239, 243),
        "AR_F3": (145, 149),
        "AR_F4": (77, 83),
    },
    "NM": {
        "NM_F1": (434, 440),
        "NM_F2": (360, 366),
        "NM_F3": (46, 52),
    },
}

# ============================================================
# 理论波长（用于拟合）
# ============================================================
PEAK_WAVELENGTHS = {
    "KR": [587.092, 785.482, 850.887, 892.869],
    "AR": [696.543, 727.294, 866.794, 965.779],
    "NM": [435.833, 546.074, 1013.976],
}


# ============================================================
# 读取光谱文件
# ============================================================
def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    start = 0
    for i, line in enumerate(lines):
        parts = line.strip().split(",")
        if len(parts) >= 2:
            try:
                float(parts[0])
                float(parts[1])
                start = i
                break
            except:
                pass

    df = pd.read_csv(path, skiprows=start, header=None)
    wavelength = df.iloc[:, 0].values.astype(float)
    signal = df.iloc[:, 1].values.astype(float)
    return wavelength, signal


# ============================================================
# index 域寻峰（带 shift）
# ============================================================
def find_peaks_by_index(signal, index_windows, shift=0):
    peaks = {}
    n = len(signal)

    for name, (l, r) in index_windows.items():
        l2 = max(0, l + shift)
        r2 = min(n - 1, r + shift)

        if l2 >= r2:
            peaks[name] = None
            continue

        seg = signal[l2:r2 + 1]
        idx = l2 + np.argmax(seg)
        peaks[name] = idx

    return peaks


# ============================================================
# 主程序
# ============================================================
def main():
    shift = 0   # <<< 以后 GUI 里改这个即可

    root = tk.Tk()
    root.withdraw()
    paths = filedialog.askopenfilenames(
        title="请选择 KR / AR / NM 光谱文件",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )

    if len(paths) == 0:
        print("未选择文件")
        return

    all_indexes = []
    all_ref_wavelengths = []

    plt.figure(figsize=(11, 6))

    for path in paths:
        fname = os.path.basename(path).upper()

        lamp = None
        for k in PEAK_INDEX_WINDOWS.keys():
            if k in fname:
                lamp = k
                break

        if lamp is None:
            print(f"{path} 无法识别灯类型")
            continue

        wavelength, signal = read_file(path)

        # ---- index 域寻峰 ----
        peak_idxs = find_peaks_by_index(
            signal,
            PEAK_INDEX_WINDOWS[lamp],
            shift=shift
        )

        # ---- 收集拟合点 ----
        for idx, wl in zip(
            peak_idxs.values(),
            PEAK_WAVELENGTHS[lamp]
        ):
            if idx is not None:
                all_indexes.append(idx)
                all_ref_wavelengths.append(wl)

        # ---- 画光谱 ----
        plt.plot(signal, label=lamp)
        dy = 0.03 * (signal.max() - signal.min())
        # ---- 标注峰 ----
        for name, idx in peak_idxs.items():
            if idx is None:
                continue
            plt.axvline(idx, linestyle="--", alpha=0.4)
            label = f"{name} {idx}"
            plt.text(idx, signal[idx] + dy, label,
                     rotation=90, fontsize=8,
                     fontweight="bold",
                     verticalalignment="bottom")
            plt.scatter(idx, signal[idx], s=50, marker='o', zorder=6)

    # ========================================================
    # 拟合
    # ========================================================
    all_indexes = np.asarray(all_indexes)
    all_ref_wavelengths = np.asarray(all_ref_wavelengths)

    order = np.argsort(all_indexes)
    all_indexes = all_indexes[order]
    all_ref_wavelengths = all_ref_wavelengths[order]

    coeffs = np.polyfit(all_indexes, all_ref_wavelengths, 3)
    poly = np.poly1d(coeffs)

    print("拟合系数：", coeffs)

    plt.xlabel("Index")
    plt.ylabel("Signal")
    plt.title("Spectra with Peak Index Windows")
    plt.legend()
    plt.grid()
    plt.show()


# ============================================================
if __name__ == "__main__":
    main()
