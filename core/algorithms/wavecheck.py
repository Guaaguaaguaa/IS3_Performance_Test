import numpy as np
import os
from scipy.optimize import curve_fit

from core.algorithms.wavecheck_core.fitting import gaussian_func, gaussian_linear_func, voigt_func, fwhm_cal
from core.algorithms.wavecheck_core.peak_detection import find_peak_boundaries, find_real_peak_index
from core.algorithms.wavecheck_core.lamp_registry import detect_lamp
from core.algorithms.wavecheck_core.exporters import save_summary
from core.export.naming import make_output_name
from core.export.wavecheck_report import save_wavecheck_report


class WaveCheckAlgorithm:

    name = "WaveCheck"

    def __init__(self, get_output_folder=None, serial_getter=None):
        self.get_output_folder = get_output_folder
        self.get_serial = serial_getter or (lambda: "")

    def _serial(self):
        return self.get_serial()

    def run(self, records, dark=None):

        if not records:
            return {"type": "wavecheck_core", "curves": [], "peaks": [], "log": "没有输入数据"}

        serial = self._serial()
        out_dir = self.get_output_folder() if self.get_output_folder else os.getcwd()

        curves = []
        peak_results = []
        summary_rows = []

        # ── 采样间隔（只输出一次，所有灯共用波长轴）──
        if records:
            first_wl = records[0]["wavelength"].ravel()
            if len(first_wl) > 1:
                intervals = np.diff(first_wl)
                mean_interval = float(np.mean(intervals))
            else:
                intervals = np.array([])
                mean_interval = np.nan
            info = {f'mean_interval = {mean_interval}'}
            interval_label = make_output_name(serial, "wavecheck", "interval")
            curves.append((first_wl[:-1], intervals, interval_label, info, False, True))  # skip_csv=False, skip_png=True

        for rec in records:

            wavelength = rec["wavelength"].ravel()
            intensity = rec["data"].ravel()
            filename = rec["filename"]
            stem = os.path.splitext(filename)[0]

            lamp, wave_peaks = detect_lamp(filename)

            all_peak_x = []
            all_peak_y = []

            for center in wave_peaks:

                peak_idx, left, right = find_real_peak_index(wavelength, intensity, center)

                measured = wavelength[peak_idx]
                delta = center - measured

                if abs(delta) >= 5:
                    continue

                start_idx, end_idx = find_peak_boundaries(
                    intensity, peak_idx, left, right, flat_thresh=100, flat_count=5)

                if end_idx - start_idx < 5:
                    continue

                wl_sub = wavelength[start_idx:end_idx + 1]
                int_sub = intensity[start_idx:end_idx + 1]

                x_dense = np.linspace(wl_sub.min(), wl_sub.max(), 1000)

                y_g = y_gl = y_v = None
                fwhm_g = fwhm_gl = fwhm_v = np.nan

                try:
                    popt, _ = curve_fit(gaussian_func, wl_sub, int_sub,
                                        p0=[int_sub.max(), measured, (wl_sub.ptp()) / 4])
                    y_g = gaussian_func(x_dense, *popt)
                    fwhm_g = fwhm_cal(x_dense, y_g)
                except:
                    pass

                try:
                    popt, _ = curve_fit(gaussian_linear_func, wl_sub, int_sub,
                                        p0=[int_sub.max(), measured, (wl_sub.ptp()) / 4, 0, int_sub.min()])
                    y_gl = gaussian_linear_func(x_dense, *popt)
                    fwhm_gl = fwhm_cal(x_dense, y_gl)
                except:
                    pass

                try:
                    popt, _ = curve_fit(voigt_func, wl_sub, int_sub,
                                        p0=[int_sub.max(), measured, (wl_sub.ptp()) / 8, 0.5])
                    y_v = voigt_func(x_dense, *popt)
                    fwhm_v = fwhm_cal(x_dense, y_v)
                except:
                    pass

                all_peak_x.append(measured)
                all_peak_y.append(intensity[peak_idx])

                peak_results.append({
                    "file": filename,
                    "pixel": int(peak_idx),
                    "measured_wl": float(measured),
                    "delta": float(delta),

                    "fit_data": {
                        "x": wl_sub.tolist(),
                        "y": int_sub.tolist(),
                        "x_dense": x_dense.tolist(),
                        "gaussian": y_g.tolist() if y_g is not None else None,
                        "gaussian_linear": y_gl.tolist() if y_gl is not None else None,
                        "voigt": y_v.tolist() if y_v is not None else None,
                        "fwhm": {
                            "gaussian": float(fwhm_g),
                            "gaussian_linear": float(fwhm_gl),
                            "voigt": float(fwhm_v)
                        }
                    }
                })

                summary_rows.append({
                    "File": filename,
                    "Lamp": lamp,
                    "Ref_Wavelength": center,
                    "Measured_Wavelength": measured,
                    "Delta": delta,
                    "FWHM_Gaussian": fwhm_g,
                    "FWHM_Gaussian_Linear": fwhm_gl,
                    "FWHM_Voigt": fwhm_v
                })

        save_summary(summary_rows, out_dir, serial)

        # 4合1 报告图
        interval_curve = None
        for c in curves:
            if "interval" in str(c[2]).lower():
                interval_curve = (c[0], c[1])
                break
        save_wavecheck_report(peak_results, summary_rows,
                              interval_curve, serial, out_dir)

        return {
            "type": "wavecheck",
            "curves": curves,
            "peaks": peak_results,
            "log": f"WaveCheck完成，共检测 {len(peak_results)} 个有效峰"
        }
