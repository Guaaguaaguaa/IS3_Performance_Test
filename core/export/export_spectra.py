# core/export/spectra_export.py
import numpy as np
import os
import pandas as pd
from core.export.screen_size import get_screen_figsize

fig_width, fig_height = get_screen_figsize(dpi=120, scale=1.0)


def save_spectra_csv(curves, output_folder, skip_info=False):
    """
    保存光谱数据到 CSV 文件
    curves: List of tuples [(x, y, label)] 或 [(x, y, label, info)]
        info 可以是字符串或字符串列表，会写入 CSV 数据末尾（空两行后）
    output_folder: str
    skip_info: bool, 跳过 info 写入（用于定标系数等不应进 CSV 的场景）
    """

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for curve in curves:
        skip_csv = False
        if len(curve) == 3:
            x, y, label = curve
            info = None
        elif len(curve) == 4:
            x, y, label, info = curve
        elif len(curve) >= 5:
            x, y, label, info, skip_csv = curve[:5]
        else:
            continue

        if skip_csv:
            continue

        # 文件名去掉非法字符
        safe_label = "".join(c if c.isalnum() or c in "_-" else "_" for c in label)
        filename = os.path.join(output_folder, f"{safe_label}.csv")
        x = np.asarray(x).ravel()
        y = np.asarray(y).ravel()
        df = pd.DataFrame({"Wavelength": x, "Value": y})
        df.to_csv(filename, index=False, sep=',', encoding='utf-8-sig')

        # 如果有 info 且不跳过，在末尾追加（空两行后）
        if info and not skip_info:
            if isinstance(info, str):
                info_lines = [info]
            else:
                info_lines = list(map(str, info))

            with open(filename, "a", encoding="utf-8") as f:
                f.write("\n\n")  # 空两行
                for line in info_lines:
                    f.write(line + "\n")

    return output_folder
