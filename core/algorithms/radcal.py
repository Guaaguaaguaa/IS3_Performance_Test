# core/algorithms/radcal_algorithm.py

from tkinter import filedialog, messagebox

import numpy as np
import os

from core.io.spectral_reader import read_spectral_files
from core.utils.spectra_utils import unify_records
from core.export.naming import make_output_name


class RadCalAlgorithm:
    name = "RadCal"

    def __init__(self, serial_getter=None):
        self.get_serial = serial_getter or (lambda: "")

    def _serial(self):
        return self.get_serial()

    def run(self, records, dark=None):
        if not records:
            return {"type": "radcal", "curves": [], "log": "未选择样本文件"}

        serial = self._serial()

        cal_path = filedialog.askopenfilename(
            title="请选择 Cal 文件 (CSV)",
            filetypes=[("Spectral files", "*.csv *.txt "), ("All files", "*.*")]
        )
        if not cal_path:
            return {"type": "radcal", "curves": [], "log": "未选择 Cal 文件，终止 RadCal"}

        cal_curve = read_spectral_files(cal_path)
        if not cal_curve:
            return {"curves": [], "log": "灯文件读取失败"}
        cal = cal_curve[0]["data"]

        curves = []
        log_msgs = []

        for rec in records:
            wl = rec["wavelength"]
            data = rec["data"]
            IT_test = rec.get("it", 12)
            stem = os.path.splitext(os.path.basename(rec["filename"]))[0]

            if dark is not None:
                if dark.ndim == 1:
                    dark = dark[np.newaxis, :]
                if data.ndim == 1:
                    data = data[np.newaxis, :]
                try:
                    data = data - dark
                except Exception:
                    log_msgs.append("暗电流维度不匹配，已跳过")
                    continue

            sample_rad = data * cal / IT_test
            sample_rad = np.asarray(sample_rad).ravel()
            label = make_output_name(serial, "radcal", stem)
            curves.append((wl, sample_rad, label))
            log_msgs.append(f"{stem} 处理完成，使用 Cal 文件: {os.path.basename(cal_path)}")

        return {
            "type": "rad",
            "curves": curves,
            "log": "\n".join(log_msgs)
        }
