# screen_size.py
import tkinter as tk


def get_screen_figsize(dpi=120, scale=1.0):
    """
    获取屏幕尺寸对应的 matplotlib figsize（英寸）。

    参数:
        dpi (int): 保存图片时使用的 DPI。
        scale (float): 放大倍数（1.0 = 原大小，1.5 = 放大 50%）。

    返回:
        (fig_width, fig_height): 以英寸为单位的尺寸元组
    """
    root = tk.Tk()
    root.withdraw()  # 不显示窗口
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()

    fig_width = screen_width * scale / dpi
    fig_height = screen_height * scale / dpi

    return fig_width, fig_height
