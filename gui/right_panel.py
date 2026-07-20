import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
import numpy as np
from matplotlib.figure import Figure

from core.export.export_spectra import save_spectra_csv
from core.export.plot_utils import draw_result_on_ax
from core.export.naming import make_output_name
from core.algorithms.wavecal_core import auto_find_shift
from gui.peak_viewer_window import PeakViewerWindow
from gui.plot.plot_controller import PlotController


BTN_WIDTH = 10
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "IS3Pro.cfg")


class RightPanel(ttk.Frame):
    def __init__(self, master, data_manager, executor, algorithms, left_panel):
        super().__init__(master)

        self.peak_window = None
        self.data_manager = data_manager
        self.executor = executor
        self.algorithms = algorithms
        self.left_panel = left_panel   # ✅ 新增
        self.current_algorithm_name = None

        self.wavecal_shift_var = tk.StringVar(value="0")
        self.wavecal_shift_var.trace_add("write", self._on_wavecal_shift_change)

        self.serial_number = tk.StringVar(value="")
        self.output_folder = tk.StringVar()
        self.load_config()
        self._build_ui()

    # ================= 序列号 + 输出路径 =================
    def set_serial(self, serial, results_root=None):
        if not serial or serial == self.serial_number.get():
            return
        self.serial_number.set(serial)
        if results_root:
            self.output_folder.set(results_root)
        self.save_config()
        self.log(f"序列号: {serial}")

    # ================= 配置管理 =================
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    folder = cfg.get("last_output_folder", "")
                    if folder:
                        self.output_folder.set(folder)
            except Exception:
                self.output_folder.set(os.path.expanduser("~"))
        else:
            self.output_folder.set(os.path.expanduser("~"))
            self.save_config()

    def save_config(self):
        cfg = {"last_output_folder": self.output_folder.get()}
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("保存配置失败:", e)

    # ================= UI =================
    def _build_ui(self):
        self.columnconfigure(0, weight=1)

        self.rowconfigure(2, weight=0)  # 日志区
        self.rowconfigure(3, weight=4)  # 绘图区（核心）

        # ===== 输出目录区 =====
        folder_frame = ttk.LabelFrame(self, text="")
        folder_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        folder_frame.columnconfigure(1, weight=1)

        ttk.Label(folder_frame, text="输出文件夹:").grid(row=0, column=0, sticky="w")
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.output_folder)
        self.folder_entry.grid(row=0, column=1, sticky="ew", padx=3)
        ttk.Button(folder_frame, text="浏览", width=BTN_WIDTH, command=self.browse_folder).grid(row=0, column=2, padx=3)

        # ===== 功能区 =====
        func_frame = ttk.LabelFrame(self, text="")
        func_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        for i in range(5):
            func_frame.columnconfigure(i, weight=1)

        ttk.Button(
            func_frame, text="WaveCal", width=BTN_WIDTH,
            command=lambda: self.run_algorithm("WaveCal")
        ).grid(row=0, column=0, padx=3, pady=2)

        shift_frame = tk.Frame(func_frame)
        shift_frame.grid(row=1, column=5, padx=3, pady=2, sticky="w")
        ttk.Label(shift_frame, text="Shift:").grid(row=1, column=5, sticky="w")
        shift_entry = ttk.Entry(
            shift_frame,
            width=6,
            textvariable=self.wavecal_shift_var
        )
        shift_entry.grid(row=1, column=6, padx=3)
        ttk.Button(shift_frame, text="Auto", width=4,
                   command=self._auto_shift).grid(row=1, column=7, padx=1)

        ttk.Button(
            func_frame, text="WaveCheck", width=BTN_WIDTH,
            command=lambda: self.run_algorithm("WaveCheck")
        ).grid(row=0, column=1, padx=3, pady=2)

        ttk.Button(
            func_frame, text="SNR", width=BTN_WIDTH,
            command=lambda: self.run_algorithm("SNR")
        ).grid(row=0, column=2, padx=3, pady=2)

        ttk.Button(
            func_frame, text="MakeCal", width=BTN_WIDTH,
            command=lambda: self.run_algorithm("MakeCal")
        ).grid(row=0, column=4, padx=3, pady=2)

        ttk.Button(func_frame, text="RadCal", width=BTN_WIDTH, command=lambda: self.run_algorithm("RadCal")).grid(row=0, column=3, padx=3, pady=2)

        self.dark_current_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            func_frame,
            text="Dark",
            variable=self.dark_current_var,
            font=("Arial", 11)
        ).grid(row=0, column=5, padx=3, pady=2)

        ttk.Button(
            func_frame, text="NEDL", width=BTN_WIDTH,
            command=lambda: self.run_algorithm("NEDL")
        ).grid(row=1, column=0, padx=3, pady=2)

        ttk.Button(
            func_frame, text="NonLinear", width=BTN_WIDTH,
            command=lambda: self.run_algorithm("NonLinear")
        ).grid(row=1, column=1, padx=3, pady=2)

        ttk.Button(
            func_frame, text="Reflectance", width=BTN_WIDTH,
            command=lambda: self.run_algorithm("Reflectance")
        ).grid(row=1, column=3, padx=3, pady=2)

        ttk.Button(
            func_frame, text="Straylight", width=BTN_WIDTH,
            command=lambda: self.run_algorithm("Straylight")
        ).grid(row=1, column=2, padx=3, pady=2)

        ttk.Button(
            func_frame, text="Subtract", width=BTN_WIDTH,
            command=lambda: self.run_algorithm("Subtract")
        ).grid(row=1, column=4, padx=3, pady=2)

        # ===== 日志区 =====
        self.log_box = ScrolledText(self, height=8)
        self.log_box.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # ===== 绘图区 =====
        plot_frame = ttk.Frame(self)
        plot_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Data Value")

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)

        self.plot_ctrl = PlotController(plot_frame, self.canvas, self.ax)
        self.plot_ctrl.attach()

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_folder.get())
        if folder:
            self.output_folder.set(folder)
            self.save_config()

    def log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    # ================= 核心算法调用（工程化） =================
    def run_algorithm(self, name):
        self.current_algorithm_name = name
        selected_files = self.left_panel.get_selected_filenames()
        records = self.data_manager.get_records_by_filenames(selected_files)

        if not records:
            self.log("未选择文件")
            return

        # ----- 暗电流处理 -----
        dark = None
        if self.dark_current_var.get():
            # 弹窗选择暗电流文件
            from tkinter import messagebox
            from core.io.spectral_reader import read_spectral_files

            files = filedialog.askopenfilenames(title="请选择暗电流文件")
            if not files:
                self.log("未选择暗电流文件，取消运算")
                return

            try:
                dark_records = read_spectral_files(list(files))
            except Exception as e:
                self.log(f"读取暗电流文件失败: {e}")
                return

            # 检查波长一致性
            base_wl = dark_records[0]["wavelength"]
            consistent = all(np.array_equal(base_wl, r["wavelength"]) for r in dark_records)
            if not consistent:
                messagebox.showerror("暗电流文件不一致", "选择的暗电流文件波长不一致，请检查")
                return

            # 如果一致，计算平均值
            dark_stack = np.stack([r["data"] if r["data"].ndim > 1 else r["data"][np.newaxis, :]
                                   for r in dark_records], axis=0)
            dark = np.mean(dark_stack, axis=0)

            # 保存到 DataManager 供复用
            self.data_manager.clear_dark_records()
            self.data_manager.add_dark_records(dark_records)

            self.log(f"已加载暗电流文件，共 {len(dark_records)} 条，已计算平均值")

        # ----- 执行算法 -----
        algo = self.algorithms.get(name)
        if not algo:
            self.log(f"算法 {name} 未注册")
            return

        self.log(f"开始执行 {name} ...")
        future = self.executor.submit(algo.run, records, dark)
        self.after(100, lambda: self.check_future(future))

    def _calc_dark_average(self, dark_records):
        """计算暗电流平均"""
        import numpy as np

        stack = []
        for rec in dark_records:
            stack.append(rec["data"])

        return np.mean(stack, axis=0)

    def check_future(self, future):
        if not future.done():
            self.after(100, lambda: self.check_future(future))
            return

        try:
            result = future.result()

            if not isinstance(result, dict):
                raise ValueError("算法返回结果不是 dict")

            curves = result.get("curves", [])
            algo_type = result.get("type", "result")
            label = None
            saved = False

            # ===== WaveCheck 峰值窗口 =====
            if result.get("type") == "wavecheck" and "peaks" in result:
                if self.peak_window is None or not self.peak_window.winfo_exists():
                    self.peak_window = PeakViewerWindow(self)

                self.peak_window.load_peaks(result["peaks"])
                self.peak_window.deiconify()
                self.peak_window.lift()
                self.peak_window.focus_force()

            # ===== 绘图与保存 =====
            if curves:
                save_spectra_csv(curves, self.output_folder.get(),
                                skip_info=(algo_type == "wavecal"))

                # PNG：仅当存在非 skip_png 的曲线时才保存
                has_visible = any(
                    not (len(c) >= 6 and c[5]) for c in curves)
                save_path = None
                if has_visible:
                    serial = self.serial_number.get()
                    png_label = (make_output_name(serial, self.current_algorithm_name.lower())
                                 if serial else self.current_algorithm_name)
                    safe_label = "".join(c if c.isalnum() or c in "_-" else "_" for c in png_label)
                    save_path = os.path.join(self.output_folder.get(), f"{safe_label}.png")

                self._plot_result(result, save_path=save_path)
                saved = True

            if saved:
                self.log(f"{algo_type} 结果已保存")

            if result.get("log"):
                self.log(result["log"])
            else:
                self.log("算法执行完成")

        except Exception as e:
            self.log(f"算法执行失败: {e}")

    def _plot_result(self, result, save_path=None):
        import threading
        import os

        if threading.current_thread().name != "MainThread":
            self.after(0, lambda: self._plot_result(result, save_path))
            return

        self.ax.clear()
        self.plot_ctrl.restore_axes()

        curves = result.get("curves", [])
        draw_result_on_ax(self.ax, result)

        # 3. 关键：强制 Matplotlib 计算最新的坐标范围
        self.ax.relim()
        self.ax.autoscale_view()

        # 4. 同步数据到交互器
        self.canvas.draw()
        self.plot_ctrl.set_curves(curves)
        self.plot_ctrl.interactor.record_original_axes()
        print("BEFORE recreate_crosshair:", self.ax.get_ylim(), self.ax.get_xlim())
        self.plot_ctrl.interactor.recreate_crosshair()
        print("AFTER recreate_crosshair:", self.ax.get_ylim(), self.ax.get_xlim())

        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            self.canvas.figure.savefig(save_path, dpi=150, bbox_inches="tight")

    def clear_plot(self):
        self.plot_ctrl.clear_plot(self.plot_ctrl.restore_axes)
        self.log("曲线已清空")

    def _on_wavecal_shift_change(self, *args):
        # 非 WaveCal 状态不触发
        if self.current_algorithm_name != "WaveCal":
            return

        # 非法值保护
        try:
            int(self.wavecal_shift_var.get())
        except ValueError:
            return

        # 防抖
        if hasattr(self, "_shift_timer"):
            self.after_cancel(self._shift_timer)

        def run_with_selection_preserved():
            # 保存当前选中
            selected_files = self.left_panel.get_selected_filenames()

            # 执行算法
            self.run_algorithm("WaveCal")

            # 刷新后恢复选中
            self.left_panel.refresh_file_list(select_all=False)
            for i, name in enumerate(self.left_panel.data_manager.get_all_filenames()):
                if name in selected_files:
                    self.left_panel.file_listbox.selection_set(i)

        self._shift_timer = self.after(300, run_with_selection_preserved)

    # ================= Auto Shift =================
    def _auto_shift(self):
        """Auto 按钮回调：后台扫描最佳 shift，填入输入框"""
        selected_files = self.left_panel.get_selected_filenames()
        records = self.data_manager.get_records_by_filenames(selected_files)
        if not records:
            self.log("请先选择光谱文件")
            return

        self.log("Auto Shift 扫描中...")
        future = self.executor.submit(self._do_auto_shift, records)
        self.after(100, lambda: self._check_auto_shift(future))

    @staticmethod
    def _do_auto_shift(records):
        return auto_find_shift(records)

    def _check_auto_shift(self, future):
        if not future.done():
            self.after(100, lambda: self._check_auto_shift(future))
            return
        try:
            best_shift, n_found = future.result()
            if n_found == 0:
                self.log("Auto Shift 失败：未能找到特征峰，请手动调整")
                return
            self.current_algorithm_name = "WaveCal"
            self.wavecal_shift_var.set(str(best_shift))
            self.log(f"Auto Shift = {best_shift} (找到 {n_found} 个峰)")
            # shift 输入框的 trace 会在 300ms 后自动触发 WaveCal
        except Exception as e:
            self.log(f"Auto Shift 异常: {e}")






