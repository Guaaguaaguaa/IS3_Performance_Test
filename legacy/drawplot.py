import numpy as np
from read_data import read_spectral_data
from curve_plot import curve_vs_plt
import matplotlib.pyplot as plt

# 使用示例
if __name__ == "__main__":

    # 读取数据1
    wavelength1, data1, _, path, _ = read_spectral_data(
         r"D:\Productions\HH3\Instrument\25011\Cal1\data\TestData\NEDL.txt",
        skip_rows=0)
    data1 = np.squeeze(data1)

    """
    # 选取波段范围
    mask1 = (wavelength1 >= 324) & (wavelength1 <= 1076)

    curve_vs_plt(
        (wavelength1[mask1], data1[mask1], 'IS3 4-1 Sample Interval'),
        'IS3 4vsHH2-Sample Interval',
        'Sample Interval',
        path
    )
    """""
    # 读取数据2
    wavelength2, data2, _, _, _ = read_spectral_data(
         r"D:\Productions\HH3\IS3\ContrastTest1\HH2\NEDL\HH2_1927_NEDL.txt",
        skip_rows=0)
    data2 = np.squeeze(data2)

    # 选取波段范围
    mask1 = (wavelength1 >= 324) & (wavelength1 <= 1076)
    mask2 = (wavelength2 >= 324) & (wavelength2 <= 1076)

    curve_vs_plt(
        (wavelength1[mask1], data1[mask1], 'IS3 4-1 Sample Interval'),
        (wavelength2[mask2], data2[mask2], 'IS3 4-2 Sample Interval'),
        'IS3 4vsHH2-Sample Interval',
        'Sample Interval',
        path
    )
    plt.show()