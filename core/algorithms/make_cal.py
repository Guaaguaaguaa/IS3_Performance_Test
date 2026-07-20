# core/algorithms/make_cal.py
from tkinter import filedialog

import numpy as np
from scipy.interpolate import splrep, splev
from core.io.spectral_reader import read_spectral_files
from core.utils.spectra_utils import unify_records
from core.export.naming import make_output_name


class MakeCalAlgorithm:
    name = "MakeCal"

    def __init__(self, serial_getter=None):
        self.get_serial = serial_getter or (lambda: "")

    def _serial(self):
        return self.get_serial()

    @staticmethod
    def resample_spectrum(wavelength, wavelength0, light_rad):
        """
        将光谱曲线重采样，并适配波段范围
        """
        light_rad = np.ravel(light_rad)
        mask = wavelength0 <= wavelength.max()
        wl0_cut = wavelength0[mask]
        rad_cut = light_rad[mask]

        if wavelength.min() < wl0_cut.min():
            nfit = min(10, len(wl0_cut))
            f_fit = np.polyfit(wl0_cut[:nfit], rad_cut[:nfit], deg=1)
            f_poly = np.poly1d(f_fit)

            wl_extend = np.arange(wavelength.min(), int(wl0_cut.min()))
            rad_extend = f_poly(wl_extend)
            rad_extend[rad_extend <= 0] = np.min(rad_cut[rad_cut > 0])

            wl0_cut = np.concatenate([wl_extend, wl0_cut])
            rad_cut = np.concatenate([rad_extend, rad_cut])

        order = np.argsort(wl0_cut)
        wl0_cut = wl0_cut[order]
        rad_cut = rad_cut[order]

        tck = splrep(wl0_cut, rad_cut, k=3)
        return splev(wavelength, tck)

    def run(self, records, dark=None, lamp_path=None):
        """
        records: 定标文件记录，list长度=1
        dark: 暗电流平均值 ndarray 或 None
        lamp_path: 积分球光源灯文件路径 str

        返回 dict：
        {
            "curves": [(wavelength, cal, label)],
            "log": str
        }
        """
        if not records:
            return {"curves": [], "log": "没有待处理数据"}

        # ----------------- 统一 records 格式 -----------------
        try:
            records = unify_records(records)
        except Exception as e:
            return {"curves": [], "log": f"统一 records 格式失败: {e}"}

        curves = []
        log_msgs = []

        for rec in records:
            wl = rec["wavelength"]
            data = rec["data"]
            IT_cal = rec["it"]

            # 在 Algorithm.run 里，暗电流扣除前
            if dark is not None:
                # 统一维度
                if dark.ndim == 1:
                    dark = dark[np.newaxis, :]
                if data.ndim == 1:
                    data = data[np.newaxis, :]
                try:
                    data = data - dark
                except Exception:
                    log_msgs.append(f"{rec['filename']} 暗电流维度不匹配，已跳过")
                    continue
            Cal_DN = np.mean(data, axis=0)

            lamp_path = filedialog.askopenfilenames(title="请选择标准灯文件")
            # 读取灯文件
            if not lamp_path:
                return {"curves": [], "log": "未选择灯文件"}

            lamp_records = read_spectral_files(lamp_path)
            if not lamp_records:
                return {"curves": [], "log": "灯文件读取失败"}
            wavelength0 = lamp_records[0]["wavelength"]
            light_rad = lamp_records[0]["data"]

            # 重采样
            light_rad_resampled = self.resample_spectrum(wl, wavelength0, light_rad)

            # 计算 Cal
            cal_curve = light_rad_resampled * IT_cal / Cal_DN
            label = make_output_name(self._serial(), "makecal")
            curves.append((wl, cal_curve, label))

            log_msgs = f"Cal 文件生成完成: 定标文件={label}"

        return {"type": "cal", "curves": curves, "log": log_msgs}
