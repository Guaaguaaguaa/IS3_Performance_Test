import numpy as np
from read_data import read_spectral_data
from plinefit import plyfit
from curve_plot import curve_plt
import matplotlib.pyplot as plt
from file_selector import select_folder
import sys
import re

# 使用示例
if __name__ == "__main__":
    basename = 'IS3_'
    # 读取DN数据
    path = select_folder("请选择光谱文件或数据文件夹")

    if path is None:
        print("未选择任何文件，操作已取消。")
        sys.exit(0)  # 直接退出程序，0表示正常退出
    else:
        wavelength, data, it, save_dir, filename = read_spectral_data(path, skip_rows=3)
        match = re.match(r'(IS3_\d+-\d+)', filename[0])
        if match:
            basename = match.group(1)

    # 1. 找到最接近 500nm 的索引
    idx_500 = np.argmin(np.abs(wavelength - 500))
    wl_500 = wavelength[idx_500]

    # 2. 找到最接近 1000nm 的索引
    idx_1000 = np.argmin(np.abs(wavelength - 1000))
    wl_1000 = wavelength[idx_1000]

    # 3. 找到全局最大值所在的位置
    file_idx, wl_idx_max = np.unravel_index(np.argmax(data), data.shape)
    wl_max = wavelength[wl_idx_max]

    # 4. 提取 3 个波长对应的 3 组数据（每组都是长度=10）
    group_500 = np.sort(data[:, idx_500])     # 所有文件在 ~500nm 处的数据
    group_1000 = np.sort(data[:, idx_1000])   # 所有文件在 ~1000nm 处的数据
    group_max = np.sort(data[:, wl_idx_max])  # 所有文件在 "最大值波长" 处的数据

    it = sorted(it)  # 返回新的排序列表

    formula1, r21 = plyfit(it, group_500, 3)
    formula2, r22 = plyfit(it, group_1000, 3)
    formula3, r23 = plyfit(it, group_max, 3)

    curve_plt(it, group_500, "IS3 5-2_500 nm_NoneLiner", "NoneLiner", save_dir, [f'y = {formula1}', f'R² = {r21}'])
    curve_plt(it, group_1000, "IS3 5-2_1000 nm_NoneLiner", "NoneLiner", save_dir, [f'y = {formula2}', f'R² = {r22}'])
    curve_plt(it, group_max, f"IS3 5-2_{wl_max:.3f}nm_NoneLiner", "NoneLiner", save_dir, [f'y = {formula3}', f'R² = {r23}'])

    plt.show()
