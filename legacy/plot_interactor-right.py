import numpy as np


class PlotInteractor:
    def __init__(self, canvas, ax, status_callback=None):
        print("PlotInteractor created:", id(self))

        self.canvas = canvas
        self.ax = ax
        self.status_callback = status_callback

        self.orig_xlim = None
        self.orig_ylim = None

        # 十字线
        self.vline = ax.axvline(color='gray', lw=0.8, ls='--', alpha=0.6)
        self.hline = ax.axhline(color='gray', lw=0.8, ls='--', alpha=0.6)
        self.vline.set_zorder(1000)
        self.hline.set_zorder(1000)

        self.curves_data = []

        self._connect_events()

    def set_status_callback(self, cb):
        self.status_callback = cb

    def _connect_events(self):
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self.canvas.mpl_connect("scroll_event", self._on_scroll_zoom)
        self.canvas.mpl_connect("axes_leave_event", self._on_mouse_leave)

    def set_curves_data(self, curves):
        data = []
        for curve in curves:
            if len(curve) >= 2:
                x = np.asarray(curve[0]).ravel()
                y = np.asarray(curve[1]).ravel()
                if len(x) == len(y) and len(x) > 0:
                    order = np.argsort(x)
                    data.append((x[order], y[order]))
        self.curves_data = data

    def _on_mouse_move(self, event):
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        x, y = event.xdata, event.ydata

        # 吸附
        if self.curves_data:
            snap = self._snap_to_nearest_point(x)
            if snap:
                sx, sy = snap
                x_range = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
                if abs(sx - x) < x_range * 0.01:
                    x, y = sx, sy

        self.vline.set_visible(True)
        self.hline.set_visible(True)
        self.vline.set_xdata([x, x])
        self.hline.set_ydata([y, y])

        if self.status_callback:
            self.status_callback(x, y)

        self.canvas.draw_idle()

    def _on_mouse_leave(self, event):
        self.vline.set_visible(False)
        self.hline.set_visible(False)

        if self.status_callback:
            self.status_callback(None, None)

        self.canvas.draw_idle()

    def _on_scroll_zoom(self, event):
        if event.inaxes != self.ax:
            return
        if self.orig_xlim is None or self.orig_ylim is None:
            return

        base_scale = 1.2
        scale = 1 / base_scale if event.button == 'up' else base_scale

        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        xdata = event.xdata
        ydata = event.ydata
        if xdata is None or ydata is None:
            return

        cur_width = cur_xlim[1] - cur_xlim[0]
        cur_height = cur_ylim[1] - cur_ylim[0]

        new_width = cur_width * scale
        new_height = cur_height * scale

        orig_left, orig_right = self.orig_xlim
        orig_bottom, orig_top = self.orig_ylim

        new_width = min(new_width, orig_right - orig_left)
        new_height = min(new_height, orig_top - orig_bottom)

        relx = (cur_xlim[1] - xdata) / cur_width
        rely = (cur_ylim[1] - ydata) / cur_height

        new_left = xdata - new_width * (1 - relx)
        new_right = xdata + new_width * relx
        new_bottom = ydata - new_height * (1 - rely)
        new_top = ydata + new_height * rely

        new_left = max(orig_left, new_left)
        new_right = min(orig_right, new_right)
        new_bottom = max(orig_bottom, new_bottom)
        new_top = min(orig_top, new_top)

        self.ax.set_xlim(new_left, new_right)
        self.ax.set_ylim(new_bottom, new_top)

        self.canvas.draw_idle()

    def capture_original_limits_once(self):
        if self.orig_xlim is None and self.orig_ylim is None:
            self.orig_xlim = self.ax.get_xlim()
            self.orig_ylim = self.ax.get_ylim()

    def recreate_crosshair(self):
        if self.vline:
            self.vline.remove()
        if self.hline:
            self.hline.remove()

        self.vline = self.ax.axvline(color='gray', lw=0.8, ls='--', alpha=0.6)
        self.hline = self.ax.axhline(color='gray', lw=0.8, ls='--', alpha=0.6)
        self.vline.set_zorder(1000)
        self.hline.set_zorder(1000)

    def _snap_to_nearest_point(self, x_mouse):
        best_dx = None
        best_xy = None

        for x_arr, y_arr in self.curves_data:
            idx = np.searchsorted(x_arr, x_mouse)
            for i in (idx, idx - 1):
                if 0 <= i < len(x_arr):
                    dx = abs(x_arr[i] - x_mouse)
                    if best_dx is None or dx < best_dx:
                        best_dx = dx
                        best_xy = (x_arr[i], y_arr[i])

        return best_xy
