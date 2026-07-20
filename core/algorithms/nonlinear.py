import os

import numpy as np

from core.export.plot_utils import save_result_image_headless
from core.export.naming import make_output_name
from core.math.plyfit import plyfit
from core.utils.spectra_utils import unify_records


class NonLinearAlgorithm:

    name = "NonLinear"

    def __init__(self, output_folder_getter, serial_getter=None):
        self.get_output_folder = output_folder_getter
        self.get_serial = serial_getter or (lambda: "")

    def _serial(self):
        return self.get_serial()

    def run(self, records, dark=None):

        if not records:
            return {"type": "curve", "curves": [], "log": "没有待处理数据"}

        serial = self._serial()

        try:
            records = unify_records(records)
        except Exception as e:
            return {"type": "curve", "curves": [], "log": f"统一 records 格式失败: {e}"}

        rec = records[0]

        wl = rec["wavelength"]
        data = rec["data"]
        it = np.array(rec["it"], dtype=float).ravel()

        idx_sort = np.argsort(it)
        it = it[idx_sort]
        data = data[idx_sort, :]

        idx_500 = np.argmin(np.abs(wl - 500))
        idx_1000 = np.argmin(np.abs(wl - 1000))

        file_idx, wl_idx_max = np.unravel_index(np.argmax(data), data.shape)
        wl_max = wl[wl_idx_max]

        group_500 = data[:, idx_500]
        group_1000 = data[:, idx_1000]
        group_max = data[:, wl_idx_max]

        formula_500, r2_500 = plyfit(it, group_500, 3)
        formula_1000, r2_1000 = plyfit(it, group_1000, 3)
        formula_max, r2_max = plyfit(it, group_max, 3)

        output_folder = self.get_output_folder()
        if not output_folder:
            raise ValueError("output_folder is empty")

        info_500 = [f'y = {formula_500}', f'R² = {r2_500}']
        info_1000 = [f'y = {formula_1000}', f'R² = {r2_1000}']

        curves_500 = [(it, group_500, make_output_name(serial, "nonlinear", "500nm"), info_500)]
        curves_1000 = [(it, group_1000, make_output_name(serial, "nonlinear", "1000nm"), info_1000)]

        info = [f'y = {formula_max}', f'R² = {r2_max}']

        main_label = make_output_name(serial, "nonlinear", f"{wl_max:.0f}nm")
        curves_main = [(it, group_max, main_label, info)]

        log_msg = (
            f"NonLinear 拟合完成\n"
            f"500nm R² = {r2_500:.5f}\n"
            f"1000nm R² = {r2_1000:.5f}\n"
            f"最大波长 {wl_max:.2f} nm R² = {r2_max:.5f}\n"
            f"500nm 与 1000nm 图已保存至: {output_folder}"
        )
        result_500 = {"type": "curve", "curves": curves_500}
        result_1000 = {"type": "curve", "curves": curves_1000}

        png_500 = make_output_name(serial, "nonlinear", "500nm")
        png_1000 = make_output_name(serial, "nonlinear", "1000nm")
        save_result_image_headless(result_500, os.path.join(output_folder, f"{png_500}.png"))
        save_result_image_headless(result_1000, os.path.join(output_folder, f"{png_1000}.png"))

        return {
            "type": "nonlinear",
            "curves": curves_main,
            "log": log_msg,
            "detail": f"{wl_max:.0f}nm",
        }
