# core/algorithms/subtract.py

import os
import numpy as np
from tkinter import filedialog

from core.io.spectral_reader import read_spectral_files
from core.utils.spectra_utils import unify_records
from core.export.naming import make_output_name


class SubtractAlgorithm:
    name = "Subtract"

    def __init__(self, output_folder_getter=None, serial_getter=None):
        self.get_output_folder = output_folder_getter
        self.get_serial = serial_getter or (lambda: "")

    def _serial(self):
        return self.get_serial()

    def run(self, records, dark=None):

        if not records:
            return {"type": "curve", "curves": [], "log": "未选择待处理文件"}

        # ---------- 选择参考文件 ----------
        ref_path = filedialog.askopenfilename(
            title="请选择要减去的参考光谱文件",
            filetypes=[("Spectral files", "*.csv *.txt"), ("All files", "*.*")]
        )

        if not ref_path:
            return {"type": "curve", "curves": [], "log": "未选择参考文件，已取消"}

        try:
            ref_records = read_spectral_files(ref_path)
            ref_records = unify_records(ref_records)

            if not ref_records:
                raise ValueError("WR 文件为空")
            ref_rec = ref_records[0]
            ref_wl = ref_rec["wavelength"]
            ref_data = ref_rec["data"]
            if ref_data.ndim == 1:
                ref_data = ref_data[np.newaxis, :]
            else:
                ref_data = np.mean(ref_data, axis=0)

        except Exception as e:
            return {"type": "curve", "curves": [], "log": f"读取参考文件失败: {e}"}

        serial = self._serial()
        curves = []
        log_msgs = []

        # ---------- 逐文件相减 ----------
        for rec in records:

            wl = rec["wavelength"]
            raw = rec["data"]

            if raw.ndim == 1:
                raw = raw[np.newaxis, :]

            # 波长一致性检查
            if not np.array_equal(wl, ref_wl):
                log_msgs.append(f"{rec.get('filename', 'unknown')} 波长不一致，已跳过")
                continue

            try:
                result = raw - ref_data
            except Exception:
                log_msgs.append(f"{rec.get('filename', 'unknown')} 维度不匹配，已跳过")
                continue

            fname = rec.get("filename", "unknown")
            stem = os.path.splitext(os.path.basename(fname))[0]
            label = make_output_name(serial, "subtract", stem)

            curves.append((wl, result, label))
            log_msgs.append(f"{fname} 减法完成")

        if self.get_output_folder:
            out_dir = self.get_output_folder()
            log_msgs.append(f"结果保存目录: {out_dir}")

        return {
            "type": "sub",
            "curves": curves,
            "log": "\n".join(log_msgs)
        }
