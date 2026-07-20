# plot_controller.py

from gui.plot.plot_interactor import PlotInteractor
from gui.plot.plot_status_bar import StatusBar


class PlotController:
    def __init__(self, parent_frame, canvas, ax):
        self.parent = parent_frame
        self.canvas = canvas
        self.ax = ax

        self.status_bar = StatusBar(parent_frame)

        self.interactor = PlotInteractor(canvas, ax)
        self.interactor.set_status_callback(self.status_bar.update_xy)

    def attach(self, canvas_row=0, status_row=1):
        self.parent.rowconfigure(canvas_row, weight=1)
        self.parent.rowconfigure(status_row, weight=0)
        self.parent.columnconfigure(0, weight=1)

        self.canvas.get_tk_widget().grid(
            row=canvas_row, column=0, sticky="nsew"
        )

        self.status_bar.grid(
            row=status_row, column=0, sticky="ew"
        )

    def set_curves(self, curves):
        """
        接受两种格式：
          1. (x_array, y_array, label)
          2. (x_array, y_array, label, info)
        将 info 忽略，保证 interactor 接口兼容
        """
        # 统一处理
        clean_curves = []
        for c in curves:
            if len(c) >= 3:
                x, y, label = c[:3]  # 只取前三项
            else:
                # 防御式，缺 label 用空字符串
                x, y = c[:2]
                label = ""
            clean_curves.append((x, y, label))

        # 传给 interactor
        self.interactor.set_curves(clean_curves)

    def clear_plot(self, restore_axes_func=None):
        # 1. 彻底清空坐标轴
        self.ax.clear()

        # 2. 重置坐标轴（如果提供）
        if restore_axes_func:
            restore_axes_func()

        # 3. 重绘
        self.canvas.draw_idle()

        # 4. 同步交互器
        self.set_curves([])
        self.interactor.recreate_crosshair()

    def restore_axes(self):
        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Intensity")
        self.ax.grid(True, alpha=0.3)