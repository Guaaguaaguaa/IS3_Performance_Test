import os
import numpy as np
import pandas as pd

from core.algorithms.wavecal_core import build_wavecal, write_peakfind_log
from core.export.naming import make_output_name


class WavecalAlgorithm:
    name = "Wavecal"

    def __init__(self, output_folder_getter=None, shift_getter=None,
                 serial_getter=None):
        self.get_output_folder = output_folder_getter
        self.get_shift = shift_getter or (lambda: 0)
        self.get_serial = serial_getter or (lambda: "")

    def _serial(self):
        return self.get_serial()

    def run(self, records, dark=None):
        if not records:
            return {"type": "curve", "curves": [], "log": "没有输入数据"}

        serial = self._serial()

        # ==================== 安全转换 shift ====================
        try:
            shift_value = self.get_shift()
            if isinstance(shift_value, str):
                shift = int(shift_value.strip())
            elif isinstance(shift_value, (int, float)):
                shift = int(shift_value)
            else:
                shift = 0
        except Exception:
            shift = 0

        try:
            poly, coeffs, fit_df, peak_detail, all_diag, all_candidates = \
                build_wavecal(records, shift)
        except Exception as e:
            return {"type": "curve", "curves": [], "log": f"Wavecal 失败: {e}"}

        out_dir = self.get_output_folder() if self.get_output_folder else None
        curves = []
        all_peak_x, all_peak_y = [], []

        for rec in records:
            signal = rec["data"].ravel()
            fname = rec["filename"]
            stem = os.path.splitext(os.path.basename(fname))[0]

            lamp = None
            if "KR" in fname.upper():
                lamp = "KR"
            elif "AR" in fname.upper():
                lamp = "AR"
            elif "NM" in fname.upper():
                lamp = "NM"

            index_axis = np.arange(len(signal))
            wl_new = poly(index_axis)

            label = make_output_name(serial, "wavecal", stem)

            info_lines = [
                f"a = {coeffs[0]}",
                f"b = {coeffs[1]}",
                f"c = {coeffs[2]}",
                f"d = {coeffs[3]}",
                f"peaks used = {len(peak_detail)}"
            ]
            curves.append((wl_new, signal, label, info_lines))

            for item in peak_detail:
                item_lamp, _, idx, _ = item
                if item_lamp != lamp:
                    continue
                try:
                    idx = int(round(idx))
                    if 0 <= idx < len(signal):
                        all_peak_x.append(wl_new[idx])
                        all_peak_y.append(signal[idx])
                except Exception:
                    continue

        if all_peak_x:
            all_peak_x = np.array(all_peak_x)
            all_peak_y = np.array(all_peak_y)
            order = np.argsort(all_peak_x)
            all_peak_x = all_peak_x[order]
            all_peak_y = all_peak_y[order]
            peaks_label = make_output_name(serial, "wavecal", "peaks")
            curves.append((all_peak_x, all_peak_y, peaks_label, None))

        # -------- 输出 定标参数 + 寻峰日志（跨记录共用） --------
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

            # 定标参数（跨记录共用，不绑定某条曲线）
            params_label = make_output_name(serial, "wavecal", "params")
            param_path = os.path.join(out_dir, f"{params_label}.csv")
            fit_df.to_csv(param_path, index=False, encoding="utf-8-sig")
            with open(param_path, "a", encoding="utf-8") as f:
                f.write("\n\n")
                f.write(f"a,{coeffs[0]}\n")
                f.write(f"b,{coeffs[1]}\n")
                f.write(f"c,{coeffs[2]}\n")
                f.write(f"d,{coeffs[3]}\n")
                f.write(f"shift,{shift}\n")
                f.write(f"peaks_used,{len(peak_detail)}\n")

            # 寻峰日志（跨记录共用）
            log_label = make_output_name(serial, "wavecal", "peakfind_log")
            log_path = os.path.join(out_dir, f"{log_label}.txt")
            write_peakfind_log(all_candidates, fit_df, log_path)

        # ── 质心诊断日志（GUI 内显示）─────────────────────────────────
        diag_lines = [f"Wavecal 完成 (shift={shift})"]
        diag_lines.append(f"{'峰':<12} {'质心':>8} {'argmax':>7} {'偏差':>6} "
                          f"{'核宽':>4} {'峰高':>8} {'方法'}")
        for (lamp, name), d in sorted(all_diag.items(),
                                       key=lambda x: x[1]["centroid"] if x[1] else 0):
            if d is None:
                continue
            c = d["centroid"]
            a = d["argmax_px"]
            dev = d["deviation"]
            cw = d["core_width"]
            ph = d["peak_height"]
            method = d["method"]
            warn = " !" if dev > 1.0 else ""
            diag_lines.append(
                f"{lamp}/{name:<9} {c:8.3f} {a:7d} {dev:6.3f} "
                f"{cw:4d} {ph:8.0f} {method}{warn}")
        rms = float(np.sqrt(np.mean(fit_df["delta"] ** 2)))
        diag_lines.append(f"RMS = {rms:.4f} nm, 使用 {len(peak_detail)} 个峰")
        log_msg = "\n".join(diag_lines)

        return {"type": "wavecal", "curves": curves, "log": log_msg, "detail": ""}
