import numpy as np
from read_data import read_spectral_data
import matplotlib.pyplot as plt

# 使用示例
if __name__ == "__main__":

    # 读取文件夹中的所有待处理文件
    wavelength, data_rads, it, path = read_spectral_data(r"D:\Productions\HH3\IS3\ContrastTest6\RadTest\Rad-dark",
                                                               skip_rows=3)
    idd = data_rads[:, 300]
    order1 = np.argsort(idd)
    data_Rad = data_rads[order1]

    # 读取HH2数据
    wavelength1, rad_hh2, _, _ = read_spectral_data(
        r"D:\Productions\HH3\IS3\ContrastTest1\HH2\Radtest\Rad",
        skip_rows=0)

    plt.figure(figsize=(8, 6))

    # 为每组数据创建不同的颜色
    colors = ['b', 'g', 'r', 'c', 'm']

    for i in range(len(data_rads)):

        label1 = f'IS3_Radiance_{(i + 1) *1000}'
        label2 = f'HH2_Radiance_{(i + 1) *1000}'

        plt.plot(wavelength, data_Rad[i], linestyle="-", color=colors[i],
                 label=label1, alpha=0.7)
        plt.plot(wavelength1, rad_hh2[i], linestyle="--", color=colors[i],
                 label=label2, alpha=0.7)

    plt.title('IS3vsHH2-RadTest')
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Radiance")
    plt.grid(True)
    plt.legend(loc='upper left', framealpha=0.7)
    plt.tight_layout()  # 确保布局合适
    plt.show()