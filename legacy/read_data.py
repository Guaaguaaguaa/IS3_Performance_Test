import numpy as np
from pathlib import Path
import os
import pandas as pd
from tkinter import Tk, filedialog, messagebox


def read_spectral_data(input_path, skip_rows=3, wavelength_col=0, spectral_col=1):
    """
    向后兼容的读取函数（保守策略）：
    - 优先使用“旧逻辑”读取（与你以前程序行为一致）
    - 仅在能明确判定为“新格式：第一列是波长、后面每列为一条光谱”时，
      按新格式解析（不会无条件改变原行为）
    返回:
        wavelength, spectral_matrix, it, out_path, file_names
    """
    wavelength = np.array([])
    spectral_data = []
    file_names = []
    it = None

    input_path = Path(input_path)
    out_path = input_path.parent

    if input_path.is_file():
        file_list = [input_path]
    elif input_path.is_dir():
        file_list = [input_path / f for f in os.listdir(input_path) if (input_path / f).is_file()]
    else:
        raise ValueError("输入路径既不是文件也不是文件夹")

    for file_path in file_list:
        file_names.append(file_path.name)
        file_str = str(file_path)

        # 先试图一次性读取整个文件（不跳行），用于检测格式
        try:
            df_all = pd.read_csv(file_str, header=None, engine='python')
        except Exception:
            # 如果连整个文件都读不出来，回退到原来的逐行解析
            df_all = None

        used_new_format = False

        # ---- 判断是否为“新格式”：第一列是波长，后面每列为一个光谱 ----
        if df_all is not None:
            # 情形 A: 用户显式传 skip_rows==1（你提到会用 skiprow=1）
            # 情形 B: 或者文件有 >=3 列并且第一列大部分是数值，可以被解释为波长
            col_count = df_all.shape[1]
            row_count = df_all.shape[0]

            # 检测第一列哪几行能转换为数字
            first_col_numeric = pd.to_numeric(df_all.iloc[:, 0], errors='coerce')
            numeric_count = first_col_numeric.notna().sum()

            # 如果 skip_rows==1，且第二行及以后第一列为数字（表示第一行为标题）
            if row_count >= 2 and pd.to_numeric(df_all.iloc[1:, 0], errors='coerce').notna().all() and col_count >= 2:
                # 标准情况：第一行为 header，后续每行第1列是波长，第2..列是不同波段的值
                header_exists = True
                start_row = 1
                used_new_format = True
            # 如果不存在 header，但整张表第一列就是数值，并且列数>=2，则也可能是新格式（第一列波长）
            elif col_count >= 2 and numeric_count == row_count:
                # 第一列全部为数字，意味着没有 header，直接把第一列作为波长，后面列为光谱
                header_exists = False
                start_row = 0
                used_new_format = True
            else:
                used_new_format = False

        # ---- 如果确认为新格式则按新格式处理 ----
        if df_all is not None and used_new_format:
            try:
                # 取波长（从 start_row 开始）
                wavelength_values = pd.to_numeric(df_all.iloc[start_row:, 0], errors='coerce').values

                # 后面所有列作为光谱（每列是一条光谱），保留所有行（从 start_row 开始）
                spectra_block = df_all.iloc[start_row:, 1:].apply(pd.to_numeric, errors='coerce').values  # shape (rows, n_spectra)
                # 转置为 (n_spectra, rows)
                spectra_block = spectra_block.T

                # 去掉每条光谱中与波长长度不匹配或全 NaN 的谱线（一般不应该发生，但保守处理）
                valid_wlen_mask = ~np.isnan(wavelength_values)
                wavelength_values = wavelength_values[valid_wlen_mask]
                spectra_block = spectra_block[:, valid_wlen_mask]

                if wavelength.size == 0:
                    wavelength = wavelength_values
                else:
                    # 如果已有 wavelength，检查一致性（长度）
                    if wavelength.shape[0] != wavelength_values.shape[0]:
                        # 警告但仍尝试使用当前文件的 wavelength（保守策略：以最长为准）
                        print(f"警告: 文件 {file_path.name} 的波长点数与之前不一致：{wavelength_values.shape[0]} vs {wavelength.shape[0]}. 使用当前文件的波长覆盖。")
                        wavelength = wavelength_values

                for i in range(spectra_block.shape[0]):
                    spectral_data.append(spectra_block[i])

                continue  # 当前文件处理完成，进入下一个文件

            except Exception as e:
                print(f"尝试按新格式解析 {file_path.name} 时失败，退回旧格式解析。错误: {e}")
                # 不中断，继续走旧格式解析

        # ---- 否则，按旧格式（你原来的逻辑）处理 ----
        try:
            data = pd.read_csv(file_str, header=None, skiprows=skip_rows, sep=',', engine='python')

            # 仅当 skip_rows == 3 时，尝试提取 it（第三行第四列）
            if skip_rows == 3:
                try:
                    df_head = pd.read_csv(file_str, header=None, skiprows=2, nrows=1, engine='python')
                    if df_head.shape[1] >= 4:
                        it0 = pd.to_numeric(df_head.iat[0, 3], errors='coerce')
                        if it is None:
                            it = it0
                        else:
                            # 保持之前逻辑，如果不同则合并为 list
                            if isinstance(it, list):
                                if it0 not in it:
                                    it.append(it0)
                            else:
                                if it != it0:
                                    it = [it, it0]
                except Exception:
                    pass

            wavelength_values = data.iloc[:, wavelength_col].values
            spectral_values = data.iloc[:, spectral_col].values

        except Exception:
            # 回退，手动解析（你原先的备用解析）
            try:
                with open(file_str, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                data_lines = []
                for line in lines[skip_rows:]:
                    line = line.strip()
                    if not line or line.endswith(':'):
                        continue
                    parts = line.replace('"', '').replace("'", "").split('\t')
                    if len(parts) >= 2:
                        data_lines.append(parts)

                df = pd.DataFrame(data_lines)
                wavelength_values = pd.to_numeric(df.iloc[:, wavelength_col], errors='coerce').values
                spectral_values = pd.to_numeric(df.iloc[:, spectral_col], errors='coerce').values
            except Exception as e:
                print(f"错误: 无法解析文件 {file_path.name}，跳过。错误: {e}")
                continue

        # 最后，按旧格式继续追加
        # 去除可能的 NaN（保持索引一致）
        try:
            wv = np.array(wavelength_values, dtype=float)
            sv = np.array(spectral_values, dtype=float)
        except Exception:
            # 若转换失败，跳过该文件
            print(f"警告: 文件 {file_path.name} 中包含非数值，已跳过")
            continue

        # 若主 wavelength 尚未设置，则使用此文件的
        if wavelength.size == 0:
            wavelength = wv
        else:
            # 若长度不一致，警告但仍接受（以当前 wavelength 为准或以已有 wavelength 为准可根据需要调整）
            if wavelength.shape[0] != wv.shape[0]:
                print(f"警告: 文件 {file_path.name} 的波长长度 {wv.shape[0]} 与已知波长长度 {wavelength.shape[0]} 不一致，尝试对齐（截取共同长度）。")
                minlen = min(wavelength.shape[0], wv.shape[0])
                wavelength = wavelength[:minlen]
                sv = sv[:minlen]

        spectral_data.append(sv)

    # 转为 NumPy 矩阵
    if len(spectral_data) == 0:
        spectral_matrix = np.zeros((0, wavelength.shape[0]))
    else:
        spectral_matrix = np.vstack([np.asarray(s, dtype=float) for s in spectral_data])

    return wavelength, spectral_matrix, it, out_path, file_names


def read_multil_data():
    # --- 用来保存多条数据 ---
    curves = []   # [(wavelength, spectrum, label), ...]

    # --- tkinter 初始化 ---
    root = Tk()
    root.withdraw()   # 隐藏主窗口（只显示对话框）

    while True:
        # 1. 选择文件
        file_path = filedialog.askopenfilename(
            title="请选择一个光谱文件",
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not file_path:
            messagebox.showinfo("提示", "未选择文件，程序结束。")
            break

        # 2. 读取数据（你的函数）
        wavelength, data, _, fpath, _ = read_spectral_data(file_path, skip_rows=3)
        data = np.squeeze(data)

        # 3. 自动生成图例名称
        # label = file_path.split("/")[-1].split("\\")[-1]
        label = file_path.split("/")[-1].split("\\")[-1].split(".")[0]

        # 4. 保存
        curves.append((wavelength, data, label))

        # 5. 询问是否继续
        ans = messagebox.askyesno("继续？", "是否继续打开下一条光谱？")
        if not ans:
            break

        # 6. 如果没有数据，不画图
    if not curves:
        messagebox.showwarning("警告", "没有任何数据可绘制。")
        return
    else:
        return curves
