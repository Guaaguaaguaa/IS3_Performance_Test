# peak_viewer_window.py
import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gui.plot.plot_controller import PlotController


class PeakViewerWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("WaveCheck 峰值查看器")
        self.geometry("1000x650")

        self.peaks = []

        self._build_ui()

    # ================= UI 构建 =================

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)  # 表格区
        self.rowconfigure(1, weight=2)  # 绘图区

        # ---------- 表格区域 ----------
        table_frame = ttk.Frame(self)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = (
            "file", "pixel", "wavelength", "delta",
            "fwhm_g", "fwhm_gl", "fwhm_v"
        )

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")

        headers = {
            "file": "File",
            "pixel": "Pixel",
            "wavelength": "Wavelength (nm)",
            "delta": "Delta (nm)",
            "fwhm_g": "FWHM(G)",
            "fwhm_gl": "FWHM(GL)",
            "fwhm_v": "FWHM(V)"
        }

        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=110, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # ---------- 绘图区域 ----------
        plot_frame = ttk.Frame(self)
        plot_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        # Figure / Axes 只创建一次
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)

        self.ax = ax
        self.canvas = FigureCanvasTkAgg(fig, master=plot_frame)

        # ✅ 统一使用 PlotController（关键）
        self.plot_ctrl = PlotController(plot_frame, self.canvas, ax)
        self.plot_ctrl.attach()

        # ---------- 事件绑定 ----------
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # ================= 数据加载 =================

    def load_peaks(self, peaks):
        self.peaks = peaks

        for i in self.tree.get_children():
            self.tree.delete(i)

        for i, p in enumerate(peaks):
            fwhm = p.get("fit_data", {}).get("fwhm", {})

            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    p.get("file", ""),
                    p.get("pixel", ""),
                    f"{p.get('measured_wl', 0):.3f}",
                    f"{p.get('delta', 0):.3f}",
                    f"{fwhm.get('gaussian', np.nan):.2f}",
                    f"{fwhm.get('gaussian_linear', np.nan):.2f}",
                    f"{fwhm.get('voigt', np.nan):.2f}",
                )
            )

    # ================= 事件处理 =================

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return

        idx = int(sel[0])
        peak = self.peaks[idx]

        self._draw_peak(peak)

    # ================= 绘图逻辑 =================

    def _draw_peak(self, peak):
        self.ax.clear()

        fit_data = peak["fit_data"]

        self.ax.plot(fit_data["x"], fit_data["y"], "k.-", label="Raw")

        if fit_data.get("gaussian") is not None:
            self.ax.plot(fit_data["x_dense"], fit_data["gaussian"], label="Gaussian")

        if fit_data.get("gaussian_linear") is not None:
            self.ax.plot(fit_data["x_dense"], fit_data["gaussian_linear"], label="Gaussian+Linear")

        if fit_data.get("voigt") is not None:
            self.ax.plot(fit_data["x_dense"], fit_data["voigt"], label="Voigt")

        self.ax.axvline(peak["measured_wl"], color="r", linestyle="--")

        fwhm = fit_data["fwhm"]

        info = (
            f"Δ = {peak.get('delta', 0):.4f} nm\n"
            f"FWHM(G) = {fwhm.get('gaussian', np.nan):.3f}\n"
            f"FWHM(GL) = {fwhm.get('gaussian_linear', np.nan):.3f}\n"
            f"FWHM(V) = {fwhm.get('voigt', np.nan):.3f}"
        )

        self.ax.text(
            0.02, 0.98, info,
            transform=self.ax.transAxes,
            va="top", ha="left",
            fontsize=10,
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.7)
        )

        self.ax.set_title(f"{peak.get('file', '')} @ {peak.get('measured_wl', 0):.2f} nm")
        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Intensity")
        self.ax.legend(loc="upper right")

        curves = [
            (fit_data["x"], fit_data["y"], f"{peak.get('file', '')} @ {peak.get('measured_wl', 0):.2f} nm"),
        ]

        # 重新创建十字线（防止被 clear 清掉）
        self.plot_ctrl.set_curves(curves)
        self.plot_ctrl.interactor.record_original_axes()
        self.plot_ctrl.interactor.recreate_crosshair()

        self.canvas.draw_idle()
