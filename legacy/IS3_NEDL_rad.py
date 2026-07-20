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
    Cal_Dark_DN = []
    data_stdev = []
    basename = 'IS3_'

    # 读取文件夹中的所有待处理文件
    path = select_folder("请选择光谱文件或数据文件夹")

    if path is None:
        print("未选择任何文件，操作已取消。")
        sys.exit(0)  # 直接退出程序，0表示正常退出
    else:
        wavelength, Sample_Rad, IT_test, path, filename = read_spectral_data(path, skip_rows=3)
        match = re.match(r'(IS3_\d+-\d+)', filename[0])
        if match:
            basename = match.group(1)

    Sample_Rad = Sample_Rad / 10000 # 10000   w/m2/nm/sr    10000000  w/m2/nm/sr

    # Sample_Rad = Sample_Rad / 10000000    #直接处理辐射亮度数据的时候使用

    rad_stdev = np.std(Sample_Rad, axis=0)

    # 将data_stdev转换为数组
    NEDL = np.array(rad_stdev)

    wl, NEDL = resample_to1nm(wavelength, NEDL)

 # 将wavelength作为第一列，stability作为第二列，将二者其导出到一个stability.txt文件
    dataframe1 = pd.DataFrame({'wavelength': wl, 'NEDL_resampled': NEDL})
    dataframe1.to_csv(path / f"{basename}_NEDL.csv",index=False,sep=',')
    mask1 = (wl >= 324) & (wl <= 1078)
    curve_plt(wl, NEDL, f"{basename}_NEDL", "NEDL", path)
    plt.show()

    # 读取HH2数据
    wavelength1, nedl_hh2, _, _, _ = read_spectral_data(
        r"D:\Productions\HH3\IS3\ContrastTest1\HH2\NEDL\HH2_1927_NEDL.txt",
        skip_rows=1)
    nedl_hh2 = np.squeeze(nedl_hh2)

    data_list = [(wavelength1, nedl_hh2, 'HH2 NEDL'), (wl, NEDL, f"{basename}_NEDL")]
    while True:
        fpath = select_file("请选择光谱文件")
        if not fpath:
            break  # 用户点击取消，结束循环

        # 读取数据
        wavelength2, nedl2, _, _, _ = read_spectral_data(fpath, skip_rows=1)
        nedl2 = np.squeeze(nedl2)

        # 自动生成图例
        basename1 = os.path.basename(fpath)
        match = re.match(r'(IS3_\d+-\d+)', basename1)
        if match:
            basename1 = match.group(1)
        legend_name = f"{basename1}_NEDL"  # 去掉后缀
        # 如果是 IS3 或 HH2 文件，可以根据命名规则再处理
        # 例如取 "IS3 5-4" 可以自己写 split 或正则，这里简单用文件名
        data_list.append((wavelength2, nedl2, legend_name))

    if not data_list:
        print("未选择任何文件，程序退出")
        sys.exit(0)

    # 调用你现有的 curve_vs_plt，支持任意条数
    curve_vs_plt(*data_list, "IS3vsHH2-NEDL", "NEDL", path)
    plt.show()
