# gui/styles.py
from tkinter import font
import matplotlib.pyplot as plt


def init_fonts(root, tk_size=12, mpl_size=12):
    """
    全局字体设置
    root: Tk 根窗口
    tk_size: Tkinter 控件字体大小
    mpl_size: Matplotlib 图表字体大小
    """
    # Tk 控件字体
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(size=tk_size)
    root.option_add("*Font", default_font)

    # Matplotlib 字体
    plt.rcParams.update({'font.size': mpl_size})
