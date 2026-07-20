# left_panel.py
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pathlib import Path
from gui.plot.plot_controller import PlotController

BTN_WIDTH = 10

# 已知测试项子文件夹名（用于向上定位序列号文件夹）
_TEST_FOLDERS = {
    "WaveCal", "SNR", "WaveCheck", "NEDL", "NonLinear",
    "Straylight", "RadCal", "MakeCal", "Reflectance", "Subtract", "DC",
}


def _find_serial_and_results(file_path):
    """
    从文件路径向上找序列号文件夹和数据根。

    序列号文件夹：包含至少一个已知测试项子文件夹的目录。
    数据根：序列号文件夹的父目录，Results/ 建在这里。

    Returns (serial, results_dir) 或 (None, None)
    """
    path = Path(file_path).resolve()
    current = path.parent

    # 跳过已知测试项子文件夹
    while current.name in _TEST_FOLDERS:
        current = current.parent

    # 向上找第一个包含测试子文件夹的目录 → 序列号
    while current.parent != current:
        try:
            children = {c.name for c in current.iterdir() if c.is_dir()}
        except Exception:
            children = set()
        if children & _TEST_FOLDERS:
            # 找到了：current 包含测试子文件夹 → 是序列号目录
            serial = current.name
            data_root = str(current.parent)
            results_dir = os.path.join(data_root, "Results", serial)
            return serial, results_dir
        current = current.parent

    return None, None


class LeftPanel(ttk.Frame):
    def __init__(self, master, data_manager, executor, read_func, log_func, right_panel=None):
        super().__init__(master)

        self.data_manager = data_manager
        self.executor = executor
        self.read_func = read_func
        self.log = log_func
        self.right_panel = right_panel

        self.current_paths = []

        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # ================= 顶部按钮 =================
        top_frame = ttk.Frame(self)
        top_frame.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        ttk.Button(top_frame, text="打开文件", width=BTN_WIDTH, command=self.open_files).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="添加文件", width=BTN_WIDTH, command=self.add_files).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="删除文件", width=BTN_WIDTH, command=self.delete_files).pack(side=tk.LEFT, padx=3)

        # ================= 文件列表 =================
        list_frame = ttk.Frame(self)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5)

        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self.file_listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.configure(yscrollcommand=scrollbar.set)

        # ================= 操作按钮 =================
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, sticky="w", padx=5, pady=5)

        ttk.Button(btn_frame, text="查看文件", width=BTN_WIDTH, command=self.view_files).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="清空曲线", width=BTN_WIDTH, command=self.clear_plot).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="保存图片", width=BTN_WIDTH, command=self.save_image).pack(side=tk.LEFT, padx=3)

        # ================= 图像区域 =================
        plot_frame = ttk.Frame(self)
        plot_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        # ---- Matplotlib Figure ----
        from matplotlib.figure import Figure
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Data Value")

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)

        # ---- Plot Controller (核心扩展点) ----
        self.plot_ctrl = PlotController(plot_frame, self.canvas, self.ax)
        self.plot_ctrl.attach()

        # ================= 事件 =================
        self.file_listbox.bind("<Button-1>", self._on_listbox_click)

    # ================= 文件操作 =================

    def open_files(self):
        paths = filedialog.askopenfilenames()
        if not paths:
            return

        self.clear_plot()

        if self.right_panel:
            self.right_panel.clear_plot()

        self.current_paths = list(paths)
        self.try_read_files(select_all=True)

    def add_files(self):
        paths = filedialog.askopenfilenames()
        if not paths:
            return

        self.current_paths.extend(paths)
        self.try_read_files(select_all=False)

    def delete_files(self):
        names = self.get_selected_filenames()
        if not names:
            self.log("未选择要删除的文件")
            return

        self.clear_plot()

        if self.right_panel:
            self.right_panel.clear_plot()

        self.data_manager.remove_files(names)
        self.refresh_file_list()
        self.log(f"已删除 {len(names)} 个文件")

    # ================= 显示 =================

    def view_files(self):
        records = self.get_selected_records()
        if not records:
            self.log("未选择任何文件")
            return

        self.ax.clear()
        self.plot_ctrl.restore_axes()
        curves = []

        for r in records:
            wv = r["wavelength"]
            data = r["data"]
            fname = r["filename"]

            if data.ndim == 1:
                self.ax.plot(wv, data, label=fname)
                curves.append((wv, data, fname))
            else:
                for i in range(data.shape[0]):
                    self.ax.plot(wv, data[i], label=f"{fname}_{i}")
                    curves.append((wv, data[i],fname))

            # 限制图例最多显示6条
            lines = self.ax.get_lines()
            labels = [line.get_label() for line in lines if line.get_label() != "_nolegend_"]
            if labels:
                self.ax.legend(labels[:6], loc="upper right", frameon=True)

        # 关键顺序
        self.canvas.draw()
        self.plot_ctrl.set_curves(curves)
        self.plot_ctrl.interactor.record_original_axes()
        self.plot_ctrl.interactor.recreate_crosshair()

        self.log(f"显示 {len(records)} 条记录")

    def clear_plot(self):
        self.plot_ctrl.clear_plot(self.plot_ctrl.restore_axes)
        self.log("曲线已清空")

    def save_image(self):
        if not self.ax.lines:
            messagebox.showwarning("提示", "当前没有曲线可保存")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存图片",
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg"),
                ("PDF File", "*.pdf"),
            ],
        )

        if not file_path:
            return

        try:
            self.fig.savefig(file_path, dpi=300, bbox_inches="tight")
            self.log(f"图片已保存: {file_path}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    # ================= 读取 =================

    def _on_listbox_click(self, event):
        size = self.file_listbox.size()
        if size == 0:
            return

        index = self.file_listbox.nearest(event.y)
        bbox = self.file_listbox.bbox(index)

        clicked_on_item = False
        if bbox:
            y1 = bbox[1]
            y2 = y1 + bbox[3]
            if y1 <= event.y <= y2:
                clicked_on_item = True

        if not clicked_on_item:
            self.file_listbox.selection_clear(0, tk.END)
            return "break"

    def try_read_files(self, select_all=True):
        if not self.current_paths:
            return

        # 提取序列号：从文件向上走，找到包含测试子文件夹的那个目录
        serial = None
        results_root = None
        try:
            first_path = Path(self.current_paths[0]).resolve()
            serial, results_root = _find_serial_and_results(first_path)
            if results_root:
                os.makedirs(results_root, exist_ok=True)
        except Exception:
            pass

        def task():
            raw = self.read_func(self.current_paths)
            results = []
            for p, r in zip(self.current_paths, raw):
                r = dict(r)
                r["filename"] = Path(p).name
                results.append(r)
            return results

        def on_done(future):
            try:
                records = future.result()
            except Exception as e:
                self.after(0, lambda e=e: messagebox.showerror("读取异常", str(e)))
                return

            def update_ui():
                self.data_manager.clear()
                self.data_manager.add_records(records)
                self.refresh_file_list(select_all=select_all)
                self.log(f"成功读取 {len(records)} 条数据")
                if serial and results_root:
                    self.right_panel.set_serial(serial, results_root)

            self.after(0, update_ui)

        self.executor.submit(task).add_done_callback(on_done)

    # ================= 工具 =================

    def refresh_file_list(self, select_all=False):
        selected_files = [] if select_all else self.get_selected_filenames()

        self.file_listbox.delete(0, tk.END)
        for name in self.data_manager.get_all_filenames():
            self.file_listbox.insert(tk.END, name)

        if select_all and self.file_listbox.size() > 0:
            self.file_listbox.selection_set(0, tk.END)
        else:
            for i, name in enumerate(self.data_manager.get_all_filenames()):
                if name in selected_files:
                    self.file_listbox.selection_set(i)

    def get_selected_filenames(self):
        return [self.file_listbox.get(i) for i in self.file_listbox.curselection()]

    def get_selected_records(self):
        names = self.get_selected_filenames()
        return self.data_manager.get_records_by_filenames(names)
