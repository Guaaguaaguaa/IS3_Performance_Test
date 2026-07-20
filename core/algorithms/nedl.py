import os
import numpy as np

from core.utils.spectra_utils import unify_records
from core.export.naming import make_output_name, extract_detail_from_folder


class NEDLAlgorithm:
    name = "NEDL"

    def __init__(self, serial_getter=None):
        self.get_serial = serial_getter or (lambda: "")

    def _serial(self):
        return self.get_serial()

    def run(self, records, dark=None):
        if not records:
            return {"curves": [], "log": "没有待处理数据"}

        serial = self._serial()
        try:
            records = unify_records(records)
        except Exception as e:
            return {"curves": [], "log": f"统一 records 格式失败: {e}"}

        curves = []

        for rec in records:
            wl = rec["wavelength"]
            rad = rec["data"]

            rad = rad / 10000

            nedl = np.std(rad, axis=0)
            folder = rec.get("subfolder", "")
            detail = extract_detail_from_folder(folder, "nedl")
            label = make_output_name(serial, "nedl", detail) if detail else make_output_name(serial, "nedl")
            curves.append((wl, nedl, label))

        return {
            "type": "nedl",
            "curves": curves,
            "log": "NEDL 计算完成",
            "detail": detail,
        }
