# core/export/spectra_export.py
import numpy as np
import os
import pandas as pd
from core.export.screen_size import get_screen_figsize

fig_width, fig_height = get_screen_figsize(dpi=120, scale=1.0)


def save_spectra_csv(curves, output_folder):
    """
    保存光谱数据到 CSV 文件（纯数据，不含 info）。
    curves: List of tuples [(x, y, label)] 或 [(x, y, label, info)]
        5+ 元素时第 5 个为 skip_csv 标志
    """

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for curve in curves:
        skip_csv = False
        if len(curve) == 3:
            x, y, label = curve
        elif len(curve) >= 4:
            x, y, label = curve[0], curve[1], curve[2]
            skip_csv = bool(curve[4]) if len(curve) >= 5 else False
        else:
            continue

        if skip_csv:
            continue

        safe_label = "".join(c if c.isalnum() or c in "_-" else "_" for c in label)
        filename = os.path.join(output_folder, f"{safe_label}.csv")
        x = np.asarray(x).ravel()
        y = np.asarray(y).ravel()
        df = pd.DataFrame({"Wavelength": x, "Value": y})
        df.to_csv(filename, index=False, sep=',', encoding='utf-8-sig')

    return output_folder
