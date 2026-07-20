import os
import re
import numpy as np
from core.algorithms.reflectance_core import load_wr_and_compute_reflectance
from core.export.naming import make_output_name


class StraylightAlgorithm:
    name = "Straylight"

    def __init__(self, serial_getter=None):
        self.get_serial = serial_getter or (lambda: "")

    def _serial(self):
        return self.get_serial()

    def run(self, records, dark=None):

        if not records:
            return {"type": "stray", "curves": [], "log": "没有待处理数据"}

        serial = self._serial()
        filenames = [r.get("filename", "unknown") for r in records]

        ref_results = load_wr_and_compute_reflectance(records, dark)

        curves = []
        logs = []
        detail = ""

        for i, res in enumerate(ref_results):

            wl = res["wavelength"]
            trans = res["reflectance"]

            mask_mean = (wl >= 550) & (wl <= 750)
            mean_val = float(np.mean(trans[mask_mean]))

            mask_plot = (wl >= 400) & (wl <= 794)

            wl_cut = wl[mask_plot]
            trans_cut = trans[mask_plot]

            raw = os.path.splitext(os.path.basename(filenames[i]))[0]
            # 去掉无意义的 _UP 后缀，截取滤光片名（最后一段，去数字）
            if raw.endswith("_UP"):
                raw = raw[:-3]
            detail = raw.rsplit("_", 1)[-1] if "_" in raw else raw
            detail = re.sub(r'\d+$', '', detail)
            label = make_output_name(serial, "straylight", detail)

            curves.append((wl_cut, trans_cut, label, f"550-750 nm straylight_mean = {mean_val:.6e}"))

            logs.append(f"{label} 平均杂散光(550-750nm): {mean_val:.6e}")

        return {
            "type": "straylight",
            "curves": curves,
            "log": "\n".join(logs),
            "detail": detail,
        }
