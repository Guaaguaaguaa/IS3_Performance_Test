import os
from core.algorithms.reflectance_core import load_wr_and_compute_reflectance
from core.export.naming import make_output_name


class ReflectanceAlgorithm:
    name = "Reflectance"

    def __init__(self, output_folder_getter=None, serial_getter=None):
        self.get_output_folder = output_folder_getter
        self.get_serial = serial_getter or (lambda: "")

    def _serial(self):
        return self.get_serial()

    def run(self, records, dark=None):

        if not records:
            return {"type": "ref", "curves": [], "log": "没有待处理数据"}

        serial = self._serial()
        filenames = [r.get("filename", "HH3") for r in records]

        curves = []
        logs = []

        ref_results = load_wr_and_compute_reflectance(records, dark)

        for i, res in enumerate(ref_results):

            wl = res["wavelength"]
            ref = res["reflectance"]

            stem = os.path.splitext(os.path.basename(filenames[i]))[0]
            label = make_output_name(serial, "reflectance", stem)

            curves.append((wl, ref, label))
            logs.append(f"{label} 计算完成")

        return {
            "type": "ref",
            "curves": curves,
            "log": "\n".join(logs)
        }
