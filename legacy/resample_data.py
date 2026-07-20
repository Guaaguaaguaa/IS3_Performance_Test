import numpy as np
from scipy.interpolate import splev, splrep, interp1d


def resample_spectrum(wavelength, wavelength0, light_rad):
    """
    将光谱曲线重采样，并适配波段范围，去除多余的长波，补足缺少的短波
    """
    light_rad = np.ravel(light_rad)  # 把数据压平成一维 (2151)
    # 1. 截取 wavelength0, light_rad 到 wavelength 的最大值范围
    mask = wavelength0 <= wavelength.max()
    wl0_cut = wavelength0[mask]
    rad_cut = light_rad[mask]

    # 2. 处理 wavelength 的最小值小于 wl0_cut 的情况 (外推)
    if wavelength.min() < wl0_cut.min():
        nfit = min(10, len(wl0_cut))  # 防止数据太少
        f_fit = np.polyfit(wl0_cut[:nfit], rad_cut[:nfit], deg=1)
        f_poly = np.poly1d(f_fit)

        # 生成整数波长范围 (比如 327 ~ 349)
        wl_extend = np.arange(wavelength.min(), int(wl0_cut.min()))
        rad_extend = f_poly(wl_extend)

        # 保证大于0
        if np.any(rad_extend <= 0):
            rad_extend[rad_extend <= 0] = np.min(rad_cut[rad_cut > 0])

        # 合并外推和原始数据
        wl0_cut = np.concatenate([wl_extend, wl0_cut])
        rad_cut = np.concatenate([rad_extend, rad_cut])

    # 3. 排序 + 去重，确保 wl0_cut 严格单调递增
    order = np.argsort(wl0_cut)
    wl0_cut = wl0_cut[order]
    rad_cut = rad_cut[order]
    wl0_cut, unique_idx = np.unique(wl0_cut, return_index=True)
    rad_cut = rad_cut[unique_idx]

    # 4. 拟合并重采样到 wavelength
    tck = splrep(wl0_cut, rad_cut, k=3)  # 三次样条
    resampledata = splev(wavelength, tck)

    # plot_spectra_data(wavelength, resampledata, wavelength0, light_rad)

    return resampledata


def resample_to1nm(wavelength, data):

    # 目标波长范围
    wl = np.arange(325, 1076, 1)

    # 线性插值（也可以改成 'cubic' 三次样条）
    f = interp1d(wavelength, data, kind='linear', bounds_error=False, fill_value="extrapolate")

    # 得到重采样后的数据
    data_resampled = f(wl)

    # 如果波长是降序排列，翻转成升序
    if wl[0] > wl[-1]:
        wl = wl[::-1]
        data_resampled = data_resampled[::-1]

    return wl, data_resampled
