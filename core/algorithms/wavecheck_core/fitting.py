import numpy as np

def gaussian_func(x, a, b, c):
    return a * np.exp(-((x - b) / c) ** 2)

def gaussian_linear_func(x, a, b, c, d, e):
    return a * np.exp(-((x - b) / c) ** 2) + d * x + e

def voigt_func(x, a, b, c, d):
    gaussian_part = (1 - d) * np.exp(-((x - b) ** 2) / (2 * c ** 2))
    lorentzian_part = d / (1 + ((x - b) ** 2) / (c ** 2))
    return a * (gaussian_part + lorentzian_part)

def fwhm_cal(x_dense, y_dense):
    peak_val = np.max(y_dense)
    peak_idx = np.argmax(y_dense)
    half_val = peak_val / 2

    left_idx = peak_idx
    while left_idx > 0 and y_dense[left_idx] > half_val:
        left_idx -= 1

    if left_idx < len(y_dense) - 1:
        x1 = np.interp(half_val,
                       [y_dense[left_idx], y_dense[left_idx + 1]],
                       [x_dense[left_idx], x_dense[left_idx + 1]])
    else:
        x1 = x_dense[left_idx]

    right_idx = peak_idx
    while right_idx < len(y_dense) - 1 and y_dense[right_idx] > half_val:
        right_idx += 1

    if right_idx > 0:
        x2 = np.interp(half_val,
                       [y_dense[right_idx - 1], y_dense[right_idx]],
                       [x_dense[right_idx - 1], x_dense[right_idx]])
    else:
        x2 = x_dense[right_idx]

    return x2 - x1
