import matplotlib.pyplot as plt
from read_data import read_multil_data
from curve_plot import curve_vs_plt
from screen_size import get_screen_figsize
import matplotlib

matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 支持中文
matplotlib.rcParams['axes.unicode_minus'] = False  # 正确显示负号
fig_width, fig_height = get_screen_figsize(dpi=120, scale=1.0)


def main():

    curves = read_multil_data()

    # 调用绘图函数（可变参数）
    # curves 是 [(wl, data, label), ...]，需要解包成参数形式
    title = "Spectra"
    y_label = "Intensity"
    save_path = None  # 如果你想保存，可以传路径

    curve_vs_plt(*curves, title, y_label, save_path)

    plt.show()


if __name__ == "__main__":
    main()
