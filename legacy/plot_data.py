import matplotlib.pyplot as plt
from screen_size import get_screen_figsize

fig_width, fig_height = get_screen_figsize(dpi=120, scale=1.0)


def plot_spectra_data(wavelength1, data1, wavelength2, data2):
    plt.figure(figsize=(fig_width, fig_height))
    # 原始数据
    plt.plot(wavelength2, data2, 'k-', label='Data2')
    # 重采样结果
    plt.plot(wavelength1, data1, 'ro-', markersize=3, label='Data1')
    plt.xlabel("Wavelength")
    # plt.ylabel("Radiance")
    plt.title("Spectra Data")
    plt.legend()
    plt.grid(True)
    plt.show()