import numpy as np
from read_data import read_spectral_data
import matplotlib.pyplot as plt
from radcal_spectra import radcal

# 使用示例
if __name__ == "__main__":
    Cal_Dark_DN = []

    # 读取光谱仪定标所采的DN数据
    _, Cal_DN, IT_cal, _ = read_spectral_data(r"D:\Productions\HH3\IS3\ContrastTest6\NEDL\2500", skip_rows=3)
    Cal_DN = np.mean(Cal_DN, axis=0)

    # 读取光谱仪定标时的暗电流
    _, Cal_Dark_DN, _, _ = read_spectral_data(r"D:\Productions\HH3\IS3\ContrastTest6\NEDL\2500-dark", skip_rows=3)

    if len(Cal_Dark_DN) > 0:
        Cal_Dark_mean = np.mean(Cal_Dark_DN, axis=0)
    else:
        Cal_Dark_mean = 0

    Cal_DN = Cal_DN - Cal_Dark_mean

    # 读取文件夹中的所有待处理文件
    wavelength, data_dns, it, path = read_spectral_data(r"D:\Productions\HH3\IS3\ContrastTest6\RadTest\DN",
                                                               skip_rows=3)
    _, darks, dit, _ = read_spectral_data(r"D:\Productions\HH3\IS3\ContrastTest6\RadTest\Dark", skip_rows=3)
    it = np.array(it)
    order1 = np.argsort(-it)
    it = it[order1]
    data_dns = data_dns[order1]

    common, idx1, idx2 = np.intersect1d(it, dit, return_indices=True)
    data = data_dns[idx1] - darks[idx2]

    itc = it / it[0]
    data_Rad = radcal(wavelength, IT_cal, Cal_DN, data, it[0]) / itc[:, np.newaxis]

    # 读取HH2数据
    wavelength1, rad_hh2, _, _ = read_spectral_data(
        r"D:\Productions\HH3\IS3\ContrastTest1\HH2\Radtest\Rad",
        skip_rows=0)

    plt.figure(figsize=(8, 6))

    # 为每组数据创建不同的颜色
    colors = ['b', 'g', 'r', 'c', 'm']

    for i in range(5):

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