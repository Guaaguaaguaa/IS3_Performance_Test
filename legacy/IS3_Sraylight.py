import numpy as np
import pandas as pd
from read_data import read_spectral_data
from resample_data import resample_to1nm
from curve_plot import curve_plt, curve_vs_plt
import matplotlib.pyplot as plt
from file_selector import select_folder, select_file
import sys
import os
import re

# 使用示例
if __name__ == "__main__":
    Dark_DN = []
    basename = 'IS3_'

    # 读取文件夹中的所有待处理文件
    path = select_folder("请选择光谱文件或数据文件夹")

    if path is None:
        print("未选择任何文件，操作已取消。")
        sys.exit(0)  # 直接退出程序，0表示正常退出
    else:
        wavelength, data_dns, _, path, filename = read_spectral_data(path, skip_rows=3)
        match = re.match(r'(IS3_\d+-\d+)', filename[0])
        if match:
            basename = match.group(1)
    # 读取暗电流
    dpath = select_folder("请选择暗电流文件或文件夹")
    if dpath is None:
        print("未选择任何暗电流文件。")
    else:
        _, Dark_DN, _, _, _ = read_spectral_data(dpath, skip_rows=3)

    if len(Dark_DN) > 0:
        Dark_mean = np.mean(Dark_DN, axis=0)
    else:
        Dark_mean = 0

    data_dns = data_dns - Dark_mean

    if data_dns[0][200] > 10000:
        trans = data_dns[1] / data_dns[0]
    else:
        trans = data_dns[0] / data_dns[1]

    # 将data转换为数组
    trans = np.array(trans)

    wl, trans = resample_to1nm(wavelength, trans)

    # 将wavelength作为第一列，stability作为第二列，将二者其导出到一个stability.txt文件
    dataframe1 = pd.DataFrame({'Wavelength': wl, 'Straylight': trans, })
    dataframe1.to_csv(path / f"{basename}_Straylight.csv", index=False, sep=',')

    # 选取 550 - 750 nm 范围
    mask = (wl >= 550) & (wl <= 750)
    # 提取对应范围的数据
    spec1_range = trans[mask]
    # 分别求平均
    mean1 = np.mean(spec1_range)
    print("杂散光在550-750nm的平均值:", mean1)

    mask1 = (wl >= 400) & (wl <= 794)
    curve_plt(wl, trans, f"{basename}_Straylight", "Straylight", None)

    # 读取HH2数据
    wavelength1, trans_hh2, _, _, _ = read_spectral_data(
        r"D:\Productions\HH3\IS3\ContrastTest1\HH2\StrayLight\HH2_1927_FilterLight_Trans.txt",
        skip_rows=0)
    trans_hh2 = np.squeeze(trans_hh2)[mask1]
    data_list = [(wavelength1[mask1], trans_hh2, 'HH2 Straylight'),(wl[mask1], trans[mask1], f"{basename}_Straylight")]
    while True:
        fpath = select_file("请选择光谱文件")
        if not fpath:
            break  # 用户点击取消，结束循环

        # 读取数据
        wavelength, trans, _, _, _ = read_spectral_data(fpath, skip_rows=1)
        trans = np.squeeze(trans)

        # 根据 mask 截取
        try:
            trans_masked = trans[mask1]
            wavelength_masked = wavelength[mask1]
        except:
            trans_masked = trans
            wavelength_masked = wavelength

        # 自动生成图例
        basename1 = os.path.basename(fpath)
        match = re.match(r'(IS3_\d+-\d+)', basename1)
        if match:
            basename1 = match.group(1)
        legend_name = f"{basename1}_Straylight"  # 去掉后缀
        # 如果是 IS3 或 HH2 文件，可以根据命名规则再处理
        # 例如取 "IS3 5-4" 可以自己写 split 或正则，这里简单用文件名
        data_list.append((wavelength_masked, trans_masked, legend_name))

    if not data_list:
        print("未选择任何文件，程序退出")
        sys.exit(0)

    # 调用你现有的 curve_vs_plt，支持任意条数
    curve_vs_plt(*data_list, "IS3vsHH2-Straylight", "Straylight", path)
    plt.show()