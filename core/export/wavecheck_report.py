"""
wavecheck_report.py — WaveCheck 4合1 报告图
"""
import numpy as np
import matplotlib.pyplot as plt
from core.export.naming import make_output_name


def _draw_fit_on_ax(ax, peak, title):
    """在指定 Axes 上画单个峰的分辨率拟合图（逻辑复用 PeakViewerWindow）"""
    fd = peak["fit_data"]

    ax.plot(fd["x"], fd["y"], "k.", ms=4, label="Raw")

    if fd.get("gaussian") is not None:
        ax.plot(fd["x_dense"], fd["gaussian"], label="Gaussian")
    if fd.get("gaussian_linear") is not None:
        ax.plot(fd["x_dense"], fd["gaussian_linear"],
                "--", label="Gaussian+Linear")
    if fd.get("voigt") is not None:
        ax.plot(fd["x_dense"], fd["voigt"], ":", label="Voigt")

    ax.axvline(peak["measured_wl"], color="r", linestyle="--", alpha=0.5)

    fwhm = fd["fwhm"]
    info = (
        f"Delta = {peak.get('delta', 0):.4f} nm\n"
        f"FWHM(G)  = {fwhm.get('gaussian', np.nan):.3f}\n"
        f"FWHM(GL) = {fwhm.get('gaussian_linear', np.nan):.3f}\n"
        f"FWHM(V)  = {fwhm.get('voigt', np.nan):.3f}"
    )
    ax.text(0.02, 0.98, info, transform=ax.transAxes,
            va="top", ha="left", fontsize=8,
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.7))
    ax.set_title(title)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Intensity")
    ax.legend(fontsize=7, loc="upper right")


def _find_peak(peak_results, target_wl):
    """在 peak_results 中找最接近 target_wl 的峰"""
    return min(peak_results, key=lambda p: abs(p["measured_wl"] - target_wl))


def save_wavecheck_report(peak_results, summary_rows, interval_curve,
                          serial, out_dir):
    """
    保存 WaveCheck 4合1 报告图：
      左上 — 696nm 分辨率
      右上 — 763nm 分辨率
      左下 — 采样间隔
      右下 — 结果汇总表
    """
    if not peak_results:
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # ── 分辨率图 ──
    for ax, target_wl in [(axes[0, 0], 696), (axes[0, 1], 763)]:
        try:
            peak = _find_peak(peak_results, target_wl)
            _draw_fit_on_ax(ax, peak, f"{target_wl} nm")
        except Exception:
            ax.text(0.5, 0.5, f"{target_wl} nm 峰未找到",
                    transform=ax.transAxes, ha="center", va="center")

    # ── 采样间隔图 ──
    ax_int = axes[1, 0]
    if interval_curve is not None and len(interval_curve) >= 2:
        ax_int.plot(interval_curve[0], interval_curve[1], "b.-", ms=2)
        ax_int.set_title("Sampling Interval")
        ax_int.set_xlabel("Wavelength (nm)")
        ax_int.set_ylabel("Interval (nm)")
    else:
        ax_int.text(0.5, 0.5, "无采样间隔数据",
                    transform=ax_int.transAxes, ha="center", va="center")

    # ── 汇总表 ──
    ax_tbl = axes[1, 1]
    ax_tbl.axis("off")
    if summary_rows:
        import pandas as pd
        df = pd.DataFrame(summary_rows)
        df = df.sort_values("Ref_Wavelength", ascending=True)
        # 精简显示列
        disp_cols = ["Lamp", "Ref_Wavelength", "Measured_Wavelength",
                      "Delta", "FWHM_Gaussian", "FWHM_Voigt"]
        disp_cols = [c for c in disp_cols if c in df.columns]
        tbl_data = df[disp_cols].round(3).values
        tbl = ax_tbl.table(cellText=tbl_data, colLabels=disp_cols,
                           loc="center", cellLoc="center", fontsize=7)
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(7)
        tbl.scale(1, 1.2)  # 行高 ×1.2，列宽不变
        ax_tbl.set_title("WaveCheck Summary", fontsize=11, fontweight="bold")

    fig.tight_layout()
    name = make_output_name(serial, "wavecheck", "report")
    out_path = f"{out_dir}/{name}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path
