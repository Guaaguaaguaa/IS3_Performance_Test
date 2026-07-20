# core/plot_utils.py
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import os


def draw_result_on_ax(ax, result):

    curves = result["curves"]

    info_blocks = []  # 收集所有 info

    for curve in curves:
        if len(curve) >= 4:
            x, y, label, info = curve[0], curve[1], curve[2], curve[3]
        elif len(curve) == 3:
            x, y, label = curve
            info = None
        else:
            continue

        x = np.asarray(x).ravel()
        y = np.asarray(y).ravel()
        if len(x) != len(y):
            min_len = min(len(x), len(y))
            x = x[:min_len]
            y = y[:min_len]

        # ===========================
        # ✅ 新增：峰点散点绘制
        # 如果 label 后缀是 _peaks 或数据点很少（假设 < 5）
        if label.lower().endswith("_peaks") or len(x) < 5:
            ax.scatter(
                x, y,
                s=50,  # 点大一点
                color='red',  # 可以选颜色
                marker='o',
                zorder=6,
                label=label
            )
        else:
            ax.plot(x, y, label=label)

        if info:
            if isinstance(info, dict):
                info_blocks.append(
                    "\n".join(f"{k}: {v}" for k, v in info.items())
                )
            elif isinstance(info, (list, tuple)):
                info_blocks.append("\n".join(map(str, info)))
            else:
                info_blocks.append(str(info))

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Value")

    # ===== 限制图例最多显示6条 =====
    lines = ax.get_lines() + [c for c in ax.collections if hasattr(c, 'get_label')]  # scatter 也算
    labels = [line.get_label() for line in lines if line.get_label() != "_nolegend_"]
    if labels:
        ax.legend(labels[:6], loc="upper right", frameon=True)

    # ===== 统一绘制 info =====
    if info_blocks:
        # 去重
        unique_info = []
        for info in info_blocks:
            if info not in unique_info:
                unique_info.append(info)

        final_text = "\n\n".join(unique_info)  # 空行分隔不同曲线的 info

        ax.text(
            0.98, 0.65,
            final_text,
            transform=ax.transAxes,
            ha='right',
            va='top',
            fontsize=10,
            family='monospace',
            bbox=dict(boxstyle="round,pad=0.35", alpha=0.15)
        )


def save_result_image_headless(result, save_path, figsize=(8, 4), dpi=150):
    fig = Figure(figsize=figsize, dpi=dpi)
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)

    draw_result_on_ax(ax, result)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.savefig(save_path, dpi=dpi, bbox_inches="tight")
