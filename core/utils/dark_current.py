# core/utils/dark_current.py
import numpy as np
from tkinter import filedialog, messagebox


def select_dark_current_files():
    """弹窗选择暗电流文件（可多选），返回文件路径列表"""
    paths = filedialog.askopenfilenames(title="请选择暗电流文件")
    return list(paths)


def load_dark_records(paths, read_func):
    """
    paths: list of 文件路径
    read_func: 用户读取文件的函数，返回 list of dict {data: ndarray, wavelength: ndarray, filename: str}
    返回：
        dark_records: list of dict
        或 None 如果差异过大
    """
    if not paths:
        return []

    all_records = []
    for p in paths:
        records = read_func([p])
        all_records.extend(records)

    # 合并所有 data
    data_list = []
    for r in all_records:
        d = r["data"]
        if d.ndim == 1:
            data_list.append(d)
        else:
            data_list.extend(d)

    arr = np.stack(data_list, axis=0)
    std_dev = np.max(np.std(arr, axis=0))
    if std_dev > 1e-3:  # 可调整阈值
        messagebox.showerror("暗电流文件错误", "暗电流文件差异过大，请检查！")
        return None

    # 返回平均暗电流
    mean_dark = np.mean(arr, axis=0)
    for r in all_records:
        r["mean_data"] = mean_dark  # 新增字段，可供算法使用
    return all_records
