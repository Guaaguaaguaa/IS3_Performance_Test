import numpy as np


def plyfit(xx,data,p):
    coeffs = np.polyfit(xx, data, p)  # 三次拟合
    y_pred = np.polyval(coeffs, xx)
    r2 = 1 - np.sum((data - y_pred)**2) / np.sum((data - np.mean(data))**2)

    # 格式化公式
    terms = []
    n = len(coeffs) - 1
    for i, c in enumerate(coeffs):
        power = n - i
        if abs(c) < 1e-8:  # 系数太小就跳过
            continue
        if power == 0:
            terms.append(f"{c:.4f}")
        elif power == 1:
            terms.append(f"{c:.4f}·x")
        else:
            terms.append(f"{c:.4f}·x^{power}")
    formula = " + ".join(terms)

    print("拟合公式: y =", formula)
    print("R² =", r2)

    return formula, r2
