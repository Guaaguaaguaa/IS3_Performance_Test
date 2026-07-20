import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
import os
import tkinter as tk
from tkinter import filedialog
import warnings
from read_data import read_spectral_data

def gaussian_func(x, a, b, c):
    """高斯函数"""
    return a * np.exp(-((x - b) / c) ** 2)


def gaussian_linear_func(x, a, b, c, d, e):
    """高斯+线性背景函数"""
    return a * np.exp(-((x - b) / c) ** 2) + d * x + e


def voigt_func(x, a, b, c, d):
    """Voigt函数（高斯+洛伦兹混合）"""
    # a: 振幅, b: 中心位置, c: 宽度参数, d: 混合因子(0-1)
    gaussian_part = (1 - d) * np.exp(-((x - b) ** 2) / (2 * c ** 2))
    lorentzian_part = d / (1 + ((x - b) ** 2) / (c ** 2))
    return a * (gaussian_part + lorentzian_part)


def fwhm_cal(x_dense, y_dense):
    """计算FWHM"""
    # 找拟合峰值 & 半高
    peak_val = np.max(y_dense)
    peak_idx = np.argmax(y_dense)
    half_val = peak_val / 2

    # 找左侧半高点
    left_idx = peak_idx
    while left_idx > 0 and y_dense[left_idx] > half_val:
        left_idx -= 1

    # 线性插值找精确横坐标
    if left_idx < len(y_dense) - 1:
        x1 = np.interp(half_val,
                       [y_dense[left_idx], y_dense[left_idx + 1]],
                       [x_dense[left_idx], x_dense[left_idx + 1]])
    else:
        x1 = x_dense[left_idx]

    # 找右侧半高点
    right_idx = peak_idx
    while right_idx < len(y_dense) - 1 and y_dense[right_idx] > half_val:
        right_idx += 1

    # 线性插值找精确横坐标
    if right_idx > 0:
        x2 = np.interp(half_val,
                       [y_dense[right_idx - 1], y_dense[right_idx]],
                       [x_dense[right_idx - 1], x_dense[right_idx]])
    else:
        x2 = x_dense[right_idx]

    # 实际FWHM
    fwhm_actual = x2 - x1
    return fwhm_actual


def find_peak_boundaries(wavelength, intensity, peak_idx, left_limit, right_limit, flat_thresh, flat_count):
    """查找峰的边界"""
    # 左边界
    start_idx = peak_idx
    flat_counter = 0
    last_val = intensity[peak_idx]

    while start_idx > left_limit:
        curr_val = intensity[start_idx - 1]
        delta = abs(curr_val - last_val)

        if delta < flat_thresh:
            flat_counter += 1
        else:
            flat_counter = 0

        # 同时判断是否是下降趋势
        if flat_counter >= flat_count or curr_val > last_val:
            start_idx = start_idx + flat_counter - 1
            break

        last_val = curr_val
        start_idx -= 1

    # 右边界
    end_idx = peak_idx
    flat_counter = 0
    last_val = intensity[peak_idx]

    while end_idx < right_limit:
        curr_val = intensity[end_idx + 1]
        delta = abs(curr_val - last_val)

        if delta < flat_thresh:
            flat_counter += 1
        else:
            flat_counter = 0

        # 同时判断是否是下降趋势
        if flat_counter >= flat_count or curr_val > last_val:
            end_idx = end_idx - flat_counter + 1
            break

        last_val = curr_val
        end_idx += 1

    return start_idx, end_idx


def main():
    # 文件选择对话框，支持多种格式
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    file_path = filedialog.askopenfilename(
        title='选择光谱数据文件',
        filetypes=[
            ('CSV files', '*.csv'),
            ('Text files', '*.txt'),
            ('All files', '*.*')
        ]
    )

    if not file_path:
        print("未选择文件，程序退出")
        return

    try:
        # 读取数据
        wavelength, intensity, _, filepath, filename= read_spectral_data(file_path, skip_rows=3)
        intensity = np.squeeze(intensity)
        print(f"成功读取文件: {filename}")
        print(f"数据点数: {len(wavelength)}")
        print(f"波长范围: {wavelength[0]:.2f} - {wavelength[-1]:.2f} nm")
        print(f"强度范围: {intensity.min():.2f} - {intensity.max():.2f}")

    except Exception as e:
        print(f"错误: {str(e)}")
        return

    basename = None

    # 计算采样间隔
    sample_interval = np.diff(wavelength)

    # 判断文件名中是否包含灯的类型
    filename_upper = str(filename).upper()

    if 'HGAR' in filename_upper:
        wave_peaks = [404.656, 435.833, 546.074, 579.066, 696.543, 706.722, 727.294, 738.393,
                      750.387, 763.511, 772.376, 794.818, 800.616, 811.531, 826.452, 842.465,
                      852.144, 866.794, 912.292, 922.45]
        basename = 'HgAr'
    elif 'NM' in filename_upper:
        wave_peaks = [404.656, 435.833, 546.074, 1013.976]
        basename = 'NM'
    elif 'AR' in filename_upper and 'HG' not in filename_upper:
        wave_peaks = [696.543, 727.294, 763.511, 826.452, 866.794, 912.292, 922.45, 965.779]
        basename = 'AR'
    elif 'KR' in filename_upper:
        wave_peaks = [587.092, 785.482, 850.887, 892.869]
        basename = 'KR'
    else:
        warnings.warn('文件名中未检测到灯的类型，使用默认峰值')
        wave_peaks = [435.833, 546.074, 696.543, 763.511]  # 默认值

    # 设置目标波长
    target_peaks = wave_peaks.copy()

    # 初始化结果数组
    peak_val = np.zeros(len(wave_peaks))
    peak_wl = np.zeros(len(wave_peaks))
    wave_delta = np.zeros(len(wave_peaks))

    # 初始化FWHM结果数组
    fwhm_gaussian = np.full(len(wave_peaks), np.nan)
    fwhm_gaussian_linear = np.full(len(wave_peaks), np.nan)
    fwhm_voigt = np.full(len(wave_peaks), np.nan)

    # 设置峰底识别参数
    flat_thresh = 100  # 连续点之间变化的最小阈值
    flat_count = 5  # 需要连续多少个点变化都很小才算到底部

    valid_peak_count = 0

    for i, center in enumerate(wave_peaks):
        # 找到最接近目标波长的点
        center_idx = np.argmin(np.abs(wavelength - center))

        # 在附近搜索局部最大值
        search_range = 20
        left = max(center_idx - search_range, 0)
        right = min(center_idx + search_range, len(wavelength) - 1)

        # 局部窗口数据
        local_wl = wavelength[left:right + 1]
        local_int = intensity[left:right + 1]

        # 找局部峰值
        peaks, properties = find_peaks(local_int, height=500)

        if len(peaks) == 0:
            warnings.warn(f'未找到任何局部峰值，可能数据过平或窗口过小 (波长: {center}nm)')
            peak_idx = center_idx  # 回退使用中心点
        else:
            # 局部峰的波长坐标
            peak_wls = local_wl[peaks]

            # 距离中心波长
            distances = np.abs(peak_wls - wavelength[center_idx])
            min_idx = np.argmin(distances)

            # 找到最近的峰值位置（全局索引）
            peak_idx = left + peaks[min_idx]

        peak_val[i] = intensity[peak_idx]
        peak_wl[i] = wavelength[peak_idx]
        wave_delta[i] = wave_peaks[i] - peak_wl[i]

        # 只处理偏移小于5nm的峰
        if abs(wave_delta[i]) < 5 and wave_peaks[i] in target_peaks:
            # 查找峰边界
            start_idx, end_idx = find_peak_boundaries(
                wavelength, intensity, peak_idx, left, right, flat_thresh, flat_count)

            # 确保索引不越界
            start_idx = max(start_idx, left)
            end_idx = min(end_idx, right)

            range_val = min(peak_idx - start_idx, end_idx - peak_idx)

            if range_val > 0:  # 确保有足够的范围
                start_idx = peak_idx - range_val
                end_idx = peak_idx + range_val

                # 截取拟合区间
                wl_sub = wavelength[start_idx:end_idx + 1]
                int_sub = intensity[start_idx:end_idx + 1]

                # 检查数据点是否足够
                if len(int_sub) < 5:
                    warnings.warn(f'数据点过少，跳过拟合 (波长: {center}nm)')
                    continue

                # 生成密集点用于绘制拟合曲线
                x_dense = np.linspace(np.min(wl_sub), np.max(wl_sub), 1000)

                # 方法1: 高斯拟合
                try:
                    # 初始参数估计
                    a0 = np.max(int_sub)
                    b0 = peak_wl[i]
                    c0 = (np.max(wl_sub) - np.min(wl_sub)) / 4

                    # 高斯拟合
                    popt_g, pcov_g = curve_fit(gaussian_func, wl_sub, int_sub,
                                               p0=[a0, b0, c0], maxfev=5000)

                    # 计算FWHM
                    y_dense_g = gaussian_func(x_dense, *popt_g)
                    fwhm_gaussian[i] = fwhm_cal(x_dense, y_dense_g)

                except Exception as e:
                    warnings.warn(f'高斯拟合失败 (波长: {center}nm): {str(e)}')
                    fwhm_gaussian[i] = np.nan

                # 方法2: 高斯+线性背景拟合
                try:
                    # 初始参数估计
                    a0 = np.max(int_sub) - np.min(int_sub)
                    b0 = center
                    c0 = (np.max(wl_sub) - np.min(wl_sub)) / 4
                    d0 = 0
                    e0 = np.min(int_sub)

                    # 高斯+线性背景拟合
                    popt_gl, pcov_gl = curve_fit(gaussian_linear_func, wl_sub, int_sub,
                                                 p0=[a0, b0, c0, d0, e0], maxfev=5000)

                    # 计算FWHM
                    y_dense_gl = gaussian_linear_func(x_dense, *popt_gl)
                    fwhm_gaussian_linear[i] = fwhm_cal(x_dense, y_dense_gl)

                except Exception as e:
                    warnings.warn(f'高斯+线性背景拟合失败 (波长: {center}nm): {str(e)}')
                    fwhm_gaussian_linear[i] = np.nan

                # 方法3: Voigt拟合
                try:
                    # 初始参数估计
                    a0 = np.max(int_sub)
                    b0 = center
                    c0 = (np.max(wl_sub) - np.min(wl_sub)) / 4 / 2.355
                    d0 = 0.5  # 混合因子

                    # Voigt拟合
                    popt_v, pcov_v = curve_fit(voigt_func, wl_sub, int_sub,
                                               p0=[a0, b0, c0, d0], maxfev=5000)

                    # 计算FWHM
                    y_dense_v = voigt_func(x_dense, *popt_v)
                    fwhm_voigt[i] = fwhm_cal(x_dense, y_dense_v)

                except Exception as e:
                    warnings.warn(f'Voigt拟合失败 (波长: {center}nm): {str(e)}')
                    fwhm_voigt[i] = np.nan

                # 绘制四种曲线
                plt.figure(figsize=(12, 8))
                plt.plot(wl_sub, int_sub, 'k-', linewidth=2, label='Original Data')

                # 绘制三种拟合曲线，并在图例中显示FWHM值
                if not np.isnan(fwhm_gaussian[i]):
                    plt.plot(x_dense, y_dense_g, 'r-', linewidth=1.5,
                             label=f'Gaussian FWHM: {fwhm_gaussian[i]:.3f} nm')

                if not np.isnan(fwhm_gaussian_linear[i]):
                    plt.plot(x_dense, y_dense_gl, 'g-', linewidth=1.5,
                             label=f'Gaussian+Linear FWHM: {fwhm_gaussian_linear[i]:.3f} nm')

                if not np.isnan(fwhm_voigt[i]):
                    plt.plot(x_dense, y_dense_v, 'b-', linewidth=1.5,
                             label=f'Voigt FWHM: {fwhm_voigt[i]:.3f} nm')

                plt.xlabel('Wavelength (nm)')
                plt.ylabel('Intensity')
                plt.title(f'Three Fitting Methods Comparison (Ref: {wave_peaks[i]:.3f} nm)')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.show()

                valid_peak_count += 1

            else:
                print(f'波长 {wave_peaks[i]:.3f} nm 处范围不足，跳过拟合')
        else:
            if wave_peaks[i] in target_peaks:
                print(f'波长 {wave_peaks[i]:.3f} nm 处偏移大于5 nm，请确认数据准确性')

    if abs(wave_delta[i]) < 5 and wave_peaks[i] in target_peaks:
        # ... 拟合代码 ...
        valid_peak_count += 1
    else:
        if wave_peaks[i] in target_peaks:
            if abs(wave_delta[i]) >= 5:
                print(f'波长 {wave_peaks[i]:.3f} nm 处偏移大于5 nm，请确认数据准确性')
            else:
                print(f'波长 {wave_peaks[i]:.3f} nm 处范围不足，跳过拟合')

    # 在循环结束后，添加Delta表格打印
    delta_results = []
    for i in range(len(wave_peaks)):
        if abs(wave_delta[i]) < 5:  # 只保存有效结果
            delta_results.append({
                'Wave_Ref': wave_peaks[i],
                'Wave_Measured': peak_wl[i],
                'Delta': wave_delta[i]
            })

    if delta_results:
        delta_df = pd.DataFrame(delta_results)
        delta_file = os.path.join(filepath, f'{basename}_WaveCheck_results.csv')
        delta_df.to_csv(delta_file, index=False)
        print(f'Delta结果已保存到: {delta_file}')

        # 添加Delta表格打印
        print("\nDelta Results:")
        print("Reference Wave(nm)\tMeasured Wave(nm)\tDelta(nm)")
        print("-" * 60)
        for result in delta_results:
            print(f"{result['Wave_Ref']:.3f}\t\t\t{result['Wave_Measured']:.3f}\t\t\t{result['Delta']:.3f}")

    # FWHM结果的表格打印保持不变
    fwhm_results = []
    for i in range(len(wave_peaks)):
        if not np.isnan(fwhm_gaussian[i]) or not np.isnan(fwhm_gaussian_linear[i]) or not np.isnan(fwhm_voigt[i]):
            fwhm_results.append({
                'Wavelength': wave_peaks[i],
                'FWHM_Gaussian': fwhm_gaussian[i],
                'FWHM_Gaussian_Linear': fwhm_gaussian_linear[i],
                'FWHM_Voigt': fwhm_voigt[i]
            })

    if fwhm_results:
        fwhm_df = pd.DataFrame(fwhm_results)
        fwhm_file = os.path.join(filepath, f'{basename}_Resolution_results.csv')
        fwhm_df.to_csv(fwhm_file, index=False)
        print(f'FWHM结果已保存到: {fwhm_file}')

        # 打印FWHM结果
        print("\nFWHM Results:")
        print("Wave(nm)\tGaussian\tGaussian+Linear\tVoigt")
        print("-" * 50)
        for result in fwhm_results:
            print(f"{result['Wavelength']:.3f}\t\t"
                  f"{result['FWHM_Gaussian']:.3f}\t\t"
                  f"{result['FWHM_Gaussian_Linear']:.3f}\t\t"
                  f"{result['FWHM_Voigt']:.3f}")

    # 保存采样间隔
    if len(sample_interval) > 0:
        sample_file = os.path.join(filepath, f'{basename}_Wave_SampleInterval.csv')
        np.savetxt(sample_file, sample_interval, delimiter=',')
        print(f'采样间隔已保存到: {sample_file}')
        print(f'平均采样间隔: {np.mean(sample_interval):.6f} nm')


if __name__ == "__main__":
    main()