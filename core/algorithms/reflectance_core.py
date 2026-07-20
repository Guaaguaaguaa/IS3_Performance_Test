from tkinter import filedialog
import numpy as np
from core.io.spectral_reader import read_spectral_files
from core.utils.spectra_utils import unify_records


def load_wr_and_compute_reflectance(records, dark=None):
    """
    records: unify_records 之后的样本 records
    wr_records: unify_records 之后的 WR records
    dark: ndarray | None

    return:
        list of dict:
        [
            {
                "wavelength": wl,
                "reflectance": 1D ndarray
            },
            ...
        ]
    """
    # ---------- 选择 WR 文件 ----------
    wr_path = filedialog.askopenfilenames(
        title="请选择白板（WR）文件",
        filetypes=[("Spectral files", "*.csv *.txt "), ("All files", "*.*")]
    )

    if not wr_path:
        return {"type": "curve", "curves": [], "log": "未选择 WR 文件，已取消"}

    try:
        wr_records = read_spectral_files(wr_path)
        wr_records = unify_records(wr_records)

        if not wr_records:
            raise ValueError("WR 文件为空")

        wr_data = wr_records[0]["data"]
        if wr_data.ndim == 1:
            wr_data = wr_data[np.newaxis, :]
        else:
            wr_data = np.mean(wr_data, axis=0)

    except Exception as e:
        return {"type": "curve", "curves": [], "log": f"读取 WR 文件失败: {e}"}

    results = []

    for rec in records:

        wl = rec["wavelength"]
        raw = rec["data"]

        if raw.ndim == 1:
            raw = raw[np.newaxis, :]

        wr_use = wr_data.copy()

        if dark is not None:
            if dark.ndim == 1:
                dark_use = dark[np.newaxis, :]
            else:
                dark_use = dark

            try:
                raw = raw - dark_use
                wr_use = wr_use - dark_use
            except Exception as e:
                raise ValueError("暗电流维度不匹配") from e

        eps = 1e-12
        reflectance = raw / (wr_use + eps)

        reflectance = reflectance[0]  # 转成 1D

        results.append({
            "wavelength": wl,
            "reflectance": reflectance
        })

    return results
