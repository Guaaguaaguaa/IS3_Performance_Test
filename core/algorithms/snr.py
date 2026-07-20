# core/algorithms/snr.py

import numpy as np
from core.utils.spectra_utils import unify_records
from core.export.naming import make_output_name


class SNRAlgorithm:
    name = "SNR"

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
        log_msgs = []

        for rec in records:
            wl = rec["wavelength"]
            data = rec["data"]

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

            dns_mean = np.mean(data, axis=0)
            dns_stdev = np.std(data, axis=0)

            dns_stdev[dns_stdev == 0] = 1e-12
            snr = dns_mean / dns_stdev
            label = make_output_name(serial, "snr")
            curves.append((wl, snr, label))

            snr_max = np.max(snr)
            snr_mean = np.mean(snr)
            log_msgs.append(f"{rec.get('filename', 'SNR')} SNR Max: {snr_max:.3f}, Mean: {snr_mean:.3f}")

        return {"type": "snr", "curves": curves, "log": "\n".join(log_msgs)}
