
import re
import numpy as np
import pandas as pd
from pathlib import Path

# -----------------------------
# 积分时间解析
# -----------------------------
def extract_integration_time_from_lines(lines):
    """
    从文本行中提取积分时间 (int)
    支持关键词: integration / 积分 / upshutter
    只提取这些关键词"后面"出现的数字，分隔符不限（空格、=、,、: 等）
    """
    patterns = [
        r"integration[^0-9]*([0-9]+)",
        r"积分[^0-9]*([0-9]+)",
        r"upshutter[^0-9]*([0-9]+)",
    ]

    for line in lines:
        low = line.lower()
        for pat in patterns:
            m = re.search(pat, low)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    pass
    return None

# -----------------------------
# 数据起始行智能检测
# -----------------------------
def detect_data_start_and_load(path):
    """
    自动检测数据起始行并返回 DataFrame + it
    支持 CSV / TXT 文件
    支持多列光谱 (格式 A) 或单光谱 (格式 B)
    """
    path = Path(path)
    lines = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        raise ValueError(f"无法读取文件: {path.name}")

    # 先提取积分时间
    it = extract_integration_time_from_lines(lines)

    # 逐行检测数据起始行
    start_row = None
    max_scan_lines = min(20, len(lines))
    for idx in range(max_scan_lines):
        line = lines[idx].strip()
        if not line:
            continue

        # 忽略表头或参数行
        if re.search(r"(date|temperature|weavelenth|weavelength|index)", line, re.I):
            continue

        # 分割行（逗号 / 空格 / 制表符）
        parts = [p for p in re.split(r"[,\t ]+", line) if p]
        if len(parts) < 2:
            continue

        # 判断列中数字比例
        num_pattern = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
        numeric_count = sum(1 for p in parts if num_pattern.match(p))
        if numeric_count / len(parts) >= 0.8:
            start_row = idx
            break

    if start_row is None:
        raise ValueError(f"无法识别数据起始行: {path.name}")

    # 从 start_row 开始读取整个文件
    try:
        df = pd.read_csv(
            path,
            header=None,
            skiprows=start_row,
            sep=r"[,\t ]+",
            engine="python"
        )
    except Exception:
        # 尝试 txt 空格分隔
        try:
            df = pd.read_csv(path, header=None, skiprows=start_row, delim_whitespace=True, engine="python")
        except Exception:
            raise ValueError(f"无法解析数据区: {path.name}")

    # 清理列，确保第一列波长为 float
    df.iloc[:, 0] = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    df = df.dropna(subset=[0])

    # 👉 加这一行（防止“假成功”）
    if df.shape[0] == 0:
        raise ValueError(f"数据解析失败（全为空）: {path.name}")

    # 对其他列也转 float
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df, it


# -----------------------------
# 格式读取函数
# -----------------------------
def read_format_A(df):
    wavelength = np.asarray(df.iloc[:, 0], dtype=float)
    spectra = df.iloc[:, 1:].values.T
    valid = ~np.isnan(wavelength)
    wavelength = wavelength[valid]
    spectra = spectra[:, valid]
    return wavelength, spectra


def read_format_B(df):
    wavelength = np.asarray(df.iloc[:, 0], dtype=float)
    spectrum = np.asarray(df.iloc[:, 1], dtype=float)
    valid = ~np.isnan(wavelength)
    wavelength = wavelength[valid]
    spectrum = spectrum[valid]
    return wavelength, spectrum


# ================================
# 格式 C: txt 特殊格式
# ================================

def read_format_C(path):
    data = np.loadtxt(path)

    if data.ndim != 2 or data.shape[1] < 2:
        raise ValueError("TXT 数据格式错误")

    wavelength = data[:, 0]
    spectrum = data[:, 1]

    return wavelength, spectrum


# ================================
# 总入口函数
# ================================

def read_spectral_files(paths):
    if isinstance(paths, (str, Path)):
        paths = [paths]

    results = []

    for p in paths:
        path = Path(p)
        if not path.exists():
            continue

        it = None

        # -------- 尝试 A / B 格式 --------
        try:
            df, it = detect_data_start_and_load(path)

            col_count = df.shape[1]

            if col_count >= 3:
                wavelength, data = read_format_A(df)
            else:
                wavelength, data = read_format_B(df)

        except Exception:
            # -------- 尝试 C 格式 --------
            try:
                wavelength, data = read_format_C(path)
            except Exception:
                raise ValueError(f"文件解析失败: {path.name}")

        results.append({
            "wavelength": wavelength,
            "data": data,
            "it": it
        })

    if not results:
        raise ValueError("未读取到任何有效光谱数据")

    return results
