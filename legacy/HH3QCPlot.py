import numpy as np
from read_data import read_spectral_data
import matplotlib.pyplot as plt
import os

def curve_vs_plt(*curves_and_info):
    """
    绘制任意数量的光谱曲线，并可选择保存为 PNG 图片。

    参数：
    ----------
    *curves : 可变数量参数，每个为 (wavelength, data, label) 三元组
        - wavelength : array-like，波长数组
        - data       : array-like，对应波长的数据值
        - label      : str，曲线的名称

       """
    # 最后三个是 title、ylabel、save_dir
    *curves, title, ylabel, save_dir = curves_and_info
    xlabel = 'Wavelength (nm)'
    dpi = 300
    filename = title
    plt.figure(figsize=(8, 5))
    colors = plt.cm.tab10.colors

    for i, (wavelength, data, label) in enumerate(curves):
        color = colors[i % len(colors)]
        plt.plot(wavelength, data, linestyle="-", color=color, label=label)

    plt.title(title, fontsize=13)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, linestyle="--", alpha=0.6)
    # plt.legend()
    plt.tight_layout()

    # ===== 保存图片部分 =====
    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)
        # 文件名处理
        if filename is None:
            filename = title.replace(" ", "_").replace("/", "_")
        save_path = os.path.join(save_dir, f"{filename}.png")
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
        print(f"✅ 图像已保存到: {save_path}")


# 使用示例
if __name__ == "__main__":

    # 读取数据1
    wavelength1, data1, _, path, _ = read_spectral_data(
        r"D:\Productions\HH3\Instrument\25013\Cal02\HH3_nedl.csv",
        skip_rows=0)   #  r"D:\Productions\HH3\Instrument\25010\Cal1\WaveCal\HgAr250170000.csv",
    data1 = np.squeeze(data1)
    x = wavelength1
    y = data1

    
    # 创建图形
    plt.figure(figsize=(8, 5))
    # 绘制曲线
    plt.plot(x, y, '-', label='data')
    # 设置y轴为对数坐标
    plt.yscale('log')
    # 限定Y轴范围
    plt.ylim(1e-11, 1e-8)
    # 设置Y轴刻度显示为10的幂次形式
    plt.yticks([1e-9, 1e-8, 1e-7, 1e-6, 1e-5], [r'$10^{-9}$', r'$10^{-8}$', r'$10^{-7}$', r'$10^{-6}$', r'$10^{-5}$'])   # , 1e-7, 1e-6
    # 加标签
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Radiance(W/cm^2/nm/sr)')
    plt.title('NEDL: IS3 - HandHeld', pad=15, fontsize=13)
    plt.grid(True, which='both', ls='--', alpha=0.6)

    plt.tight_layout()
    plt.show()


    """
    curve_vs_plt(
        (x, y, 'Mercury Argon: IS3 - HandHeld'),
        'Mercury Argon: IS3 - HH',
        'DN',
        path
    )
    plt.show()

    """
  
