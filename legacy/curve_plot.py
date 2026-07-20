import matplotlib.pyplot as plt
import os
from screen_size import get_screen_figsize

fig_width, fig_height = get_screen_figsize(dpi=120, scale=1.0)


def curve_plt(wavelength, data, title, y_lable, save_dir, info=None):
    # 画图
    plt.figure(figsize=(fig_width, fig_height))
    plt.plot(wavelength, data,  linestyle="-", color="b")
    # 设置标题和坐标轴标签
    plt.title(title)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel(y_lable)
    # 网格 & 显示
    plt.grid(True)
    # -------- 右上角信息显示 --------
    if info:
        # 如果是字符串 → 转成列表
        if isinstance(info, str):
            lines = [info]
        else:
            # 假设是可迭代的列表/tuple
            lines = list(info)

        # 拼成多行字符串
        text = "\n".join(lines)

        # 放在右上角
        plt.text(
            0.02, 0.98, text,
            transform=plt.gca().transAxes,
            ha='left', va='top',
            fontsize=10,
            family='monospace',  # 左对齐更美观
            bbox=dict(boxstyle="round,pad=0.3", alpha=0.1)
        )
    # ===== 保存图片部分 =====
    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)
        # 文件名处理
        filename = title.replace(" ", "_").replace("/", "_")
        save_path = os.path.join(save_dir, f"{filename}.png")
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ 图像已保存到: {save_path}")

    # plt.show()


def curve_vs_plt1(wavelength1, data1, wavelength2, data2, title, y_lable, info=None):
    lable1 = 'IS3_'+y_lable
    lable2 = 'HH2_' + y_lable
    # -------- 图2：画两组数据 --------
    plt.figure(figsize=(fig_width, fig_height))
    plt.plot(wavelength1, data1, linestyle="-", color="b", label=lable1)
    plt.plot(wavelength2, data2, linestyle="-", color="r", label=lable2)
    plt.title(title)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel(y_lable)
    plt.grid(True)
    plt.legend()
    # plt.show()


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
    xlabel = 'Wavelength (nm)'   # 'SNR'
    dpi = 300
    plt.figure(figsize=(fig_width, fig_height))
    colors = plt.cm.tab10.colors

    for i, (wavelength, data, label) in enumerate(curves):
        color = colors[i % len(colors)]
        plt.plot(wavelength, data, linestyle="-", color=color, label=label)

    plt.title(title, fontsize=13)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()

    # ===== 保存图片部分 =====
    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)
        # 文件名处理
        filename = title.replace(" ", "_").replace("/", "_")
        save_path = os.path.join(save_dir, f"{filename}.png")
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
        print(f"✅ 图像已保存到: {save_path}")
