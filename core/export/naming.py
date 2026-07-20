"""
naming.py — 统一输出文件命名
所有算法通过 make_output_name() 构造 label，保证命名一致。
"""

import re


def make_output_name(serial, test_type, *parts):
    """
    统一输出名: <serial>_<test_type>[_<parts>]

    Parameters
    ----------
    serial    : str, 仪器序列号（如 "7-1"）
    test_type : str, 测试项名（如 "wavecal", "snr"）
    parts     : str..., 可选的额外标识（如文件名 stem、波段等）

    Returns
    -------
    str, 如 "7-1_wavecal_KR2_UP"

    Examples
    --------
    >>> make_output_name("7-1", "wavecal", "KR2_UP")
    '7-1_wavecal_KR2_UP'
    >>> make_output_name("7-1", "snr")
    '7-1_snr'
    >>> make_output_name("7-1", "wavecal", "KR2_UP", "params")
    '7-1_wavecal_KR2_UP_params'
    """
    base = f"{serial}_{test_type}"
    if parts:
        base += "_" + "_".join(str(p) for p in parts if p)
    return base


def extract_detail_from_folder(folder_name, test_type=""):
    """
    从文件夹名提取有意义的标识。
    去掉 Data-/data_/Data_/data- 前缀；如果结果等于测试项名（如 SNR），返回空。
    """
    detail = re.sub(r'^[Dd]ata[-_]', '', folder_name) if folder_name else ""
    if detail.lower() == test_type.lower():
        return ""
    return detail
