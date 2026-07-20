import pandas as pd
import os
import numpy as np


def save_sample_interval(wavelength, stem, out_dir):
    if len(wavelength) > 1:
        df = pd.DataFrame({
            "Wavelength_nm": wavelength[:-1],
            "SampleInterval_nm": np.diff(wavelength)
        })
        df.to_csv(os.path.join(out_dir, f"{stem}_Wave_SampleInterval.csv"), index=False)


def save_delta_results(rows, stem, out_dir):
    if rows:
        pd.DataFrame(rows).to_csv(
            os.path.join(out_dir, f"{stem}_WaveCheck_results.csv"), index=False)


def save_resolution_results(rows, stem, out_dir):
    if rows:
        pd.DataFrame(rows).to_csv(
            os.path.join(out_dir, f"{stem}_Resolution_results.csv"), index=False)


def save_summary(rows, out_dir, serial=""):
    if rows:
        from core.export.naming import make_output_name
        name = make_output_name(serial, "wavecheck", "summary")
        df = pd.DataFrame(rows)
        # 按波长降序排列
        df = df.sort_values("Ref_Wavelength", ascending=True)
        # 删掉第一列 File，Lamp 移到最后
        cols = [c for c in df.columns if c != "File" and c != "Lamp"] + ["Lamp"]
        df = df[cols]
        df.to_csv(os.path.join(out_dir, f"{name}.csv"), index=False)
