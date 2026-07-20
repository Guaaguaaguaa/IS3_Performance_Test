import numpy as np
import matplotlib.patches as patches


class PlotInteractor:
    """
    光谱曲线交互类：支持十字线追踪、最近点吸附、滚动缩放。
    采用底层事件模拟选框，解决内置 RectangleSelector 失效问题。
    """

    def __init__(self, canvas, ax):
        self.canvas = canvas
        self.ax = ax
        self.status_callback = None
        self.curves = []

        self.vline = None
        self.hline = None

        # 原始范围记录，用于右键复位
        self._xlim_orig = None
        self._ylim_orig = None

        # --- 手动选框状态控制 ---
        self.is_dragging = False
        self.rect_patch = None
        self.start_pos = (None, None)

        # 连接 Matplotlib 事件句柄
        print("[Debug] Connecting events to canvas...")
        self.cid_move = canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.cid_leave = canvas.mpl_connect("figure_leave_event", self.on_mouse_leave)
        self.cid_scroll = canvas.mpl_connect("scroll_event", self.on_scroll)
        self.cid_press = canvas.mpl_connect("button_press_event", self.on_button_press)
        self.cid_release = canvas.mpl_connect("button_release_event", self.on_button_release)

        self.create_crosshair()

    def record_original_axes(self, force=True):
        """ 记录当前坐标轴范围，作为复位基准 """
        if force or (self._xlim_orig is None and self._ylim_orig is None):
            self._xlim_orig = self.ax.get_xlim()
            self._ylim_orig = self.ax.get_ylim()
            print(f"[Debug] Recorded original axes: {self._xlim_orig}")

    def set_status_callback(self, callback):
        self.status_callback = callback

    def set_curves(self, curves):
        """ 设置当前绘图区的所有曲线数据，用于吸附计算 """
        self.curves = curves

    # ===================== 底层重写：手动选框逻辑 =====================
    def on_button_press(self, event):
        """ 鼠标按下：区分右键复位和左键选框起点 """
        if event.inaxes != self.ax:
            return

        # 强制 Canvas 获取焦点，确保事件流连续
        self.canvas.get_tk_widget().focus_set()

        if event.button == 3:  # 右键复位
            if self._xlim_orig is not None and self._ylim_orig is not None:
                self.ax.set_xlim(self._xlim_orig)
                self.ax.set_ylim(self._ylim_orig)
                self.canvas.draw_idle()
            return

        if event.button == 1:  # 左键开始选框
            self.is_dragging = True
            self.start_pos = (event.xdata, event.ydata)

            # 创建并添加可视化矩形
            if self.rect_patch:
                self.rect_patch.remove()

            # 初始宽和高设为 0
            self.rect_patch = patches.Rectangle(
                (event.xdata, event.ydata), 0, 0,
                facecolor='blue', edgecolor='black', alpha=0.15, fill=True, zorder=100
            )
            self.ax.add_patch(self.rect_patch)

    def on_button_release(self, event):
        """ 鼠标释放：执行缩放并清理选框 """
        if not self.is_dragging:
            return

        self.is_dragging = False

        # 获取最终坐标
        x1, y1 = self.start_pos
        x2, y2 = event.xdata, event.ydata

        # 如果释放时在坐标轴外，尝试取 event 最后的有效坐标（Matplotlib 通常会提供最后 valid 的坐标）
        if x2 is None: x2 = x1
        if y2 is None: y2 = y1

        # 只有当移动距离足够大时才缩放，防止误触
        if abs(x1 - x2) > 1e-7 and abs(y1 - y2) > 1e-7:
            self.ax.set_xlim(sorted([x1, x2]))
            self.ax.set_ylim(sorted([y1, y2]))

        # 清理矩形并重绘
        if self.rect_patch:
            self.rect_patch.remove()
            self.rect_patch = None

        self.canvas.draw_idle()

    # ===================== 鼠标移动与状态更新 =====================
    def on_mouse_move(self, event):
        """ 鼠标移动处理：更新十字线和选框实时预览 """
        if event.inaxes != self.ax:
            # 即使在轴外，如果正在拖拽也应该允许更新矩形（直到释放）
            if not self.is_dragging:
                self.hide_crosshair()
                if self.status_callback:
                    self.status_callback(None, None)
                return

        # 1. 如果正在拖拽，更新矩形预览
        if self.is_dragging and self.rect_patch and event.xdata is not None:
            x1, y1 = self.start_pos
            x2, y2 = event.xdata, event.ydata

            # 改进：直接设置宽高和起点，不再强制 min，确保视觉跟随鼠标
            # Matplotlib 的坐标：x 向右正，y 向上正
            width = x2 - x1
            height = y2 - y1

            # Rectangle 的 xy 是左下角，这里需要根据方向调整
            new_x = x1 if width > 0 else x2
            new_y = y1 if height > 0 else y2

            self.rect_patch.set_xy((new_x, new_y))
            self.rect_patch.set_width(abs(width))
            self.rect_patch.set_height(abs(height))

        # 2. 更新十字线和吸附 (非拖拽状态或即使拖拽也显示吸附参考)
        x0, y0 = event.xdata, event.ydata
        if x0 is not None:
            nearest = self.find_nearest_point(x0, y0)
            if nearest is not None:
                nx, ny, label = nearest
                self.show_crosshair(nx, ny)
                if self.status_callback:
                    self.status_callback(nx, ny, label)
            else:
                self.show_crosshair(x0, y0)
                if self.status_callback:
                    self.status_callback(x0, y0)

        self.canvas.draw_idle()

    # ===================== 十字线控制 =====================
    def create_crosshair(self):
        """ 初始化十字线 """
        self.ax.set_autoscale_on(False)
        if self.vline is None or self.vline.axes != self.ax:
            self.vline = self.ax.axvline(0, color="gray", lw=0.8, ls="--", alpha=0.5, zorder=50)
        if self.hline is None or self.hline.axes != self.ax:
            self.hline = self.ax.axhline(0, color="gray", lw=0.8, ls="--", alpha=0.5, zorder=50)

    def hide_crosshair(self):
        """ 隐藏十字线 """
        if self.vline: self.vline.set_visible(False)
        if self.hline: self.hline.set_visible(False)

    def recreate_crosshair(self):
        """ 同步十字线状态 """
        self.create_crosshair()
        self.canvas.draw_idle()

    def show_crosshair(self, x, y):
        """ 更新十字线坐标 """
        if self.vline and self.hline:
            self.vline.set_xdata([x])
            self.hline.set_ydata([y])
            self.vline.set_visible(True)
            self.hline.set_visible(True)

    def on_mouse_leave(self, event):
        """ 鼠标离开清理 """
        if not self.is_dragging:
            self.hide_crosshair()
            if self.status_callback:
                self.status_callback(None, None)
            self.canvas.draw_idle()

    def find_nearest_point(self, x0, y0):
        """ 查找最近点 """
        if not self.curves:
            return None
        best = None
        best_dist = np.inf
        for x, y, label in self.curves:
            x_arr = np.asarray(x).ravel()
            y_arr = np.asarray(y).ravel()
            xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()
            aspect = abs((ylim[1] - ylim[0]) / (xlim[1] - xlim[0] + 1e-9))
            dist = (x_arr - x0) ** 2 + ((y_arr - y0) / (aspect + 1e-9)) ** 2
            idx = np.argmin(dist)
            if dist[idx] < best_dist:
                best_dist = dist[idx]
                best = (x_arr[idx], y_arr[idx], str(label))
        return best

    # ===================== 滚轮缩放 =====================
    def on_scroll(self, event):
        """ 以鼠标指针为中心进行缩放 """
        if event.inaxes != self.ax:
            return
        scale = 0.8 if event.button == 'up' else 1.25
        cur_xlim, cur_ylim = self.ax.get_xlim(), self.ax.get_ylim()
        xdata, ydata = event.xdata, event.ydata
        new_w = (cur_xlim[1] - cur_xlim[0]) * scale
        new_h = (cur_ylim[1] - cur_ylim[0]) * scale
        if scale > 1.0 and self._xlim_orig is not None:
            if new_w > (self._xlim_orig[1] - self._xlim_orig[0]):
                self.ax.set_xlim(self._xlim_orig)
                self.ax.set_ylim(self._ylim_orig)
                self.canvas.draw_idle()
                return
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0] + 1e-9)
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0] + 1e-9)
        self.ax.set_xlim(xdata - new_w * (1 - relx), xdata + new_w * relx)
        self.ax.set_ylim(ydata - new_h * (1 - rely), ydata + new_h * rely)
        self.canvas.draw_idle()