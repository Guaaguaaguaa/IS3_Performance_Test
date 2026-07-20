import numpy as np


def unify_records(records):
    """
    将多条 records 格式统一成单个记录：
    - 每条 record: {"wavelength": ndarray, "data": ndarray, "it": int|None}
    - 输出: [{"wavelength": ndarray, "data": 2D ndarray, "it": int|None}]

    参数:
        records: list of dict

    返回:
        list of dict (长度 1)

    Raises:
        ValueError: 波长或积分时间不一致
    """
    if not records:
        raise ValueError("records 为空")

    # 如果只有一条且 data 已经是二维数组，直接返回
    if len(records) == 1 and records[0]["data"].ndim == 2:
        return records

    # ----------------- 统一波长 -----------------
    base_wl = records[0]["wavelength"]
    data_list = []
    it_list = []

    for rec in records:
        wl = rec["wavelength"]
        if not np.allclose(base_wl, wl):
            raise ValueError("多条光谱波长不一致")

        data = rec["data"]
        # 如果是一维，扩展为二维
        if data.ndim == 1:
            data = data[np.newaxis, :]
        data_list.append(data)

        if "it" in rec and rec["it"] is not None:
            it_list.append(rec["it"])

    # ----------------- 合并 -----------------
    final_data = np.vstack(data_list)
    if not it_list:
        final_it = None
    elif all(it == it_list[0] for it in it_list):
        final_it = it_list[0]
    else:
        final_it = it_list  # 保持原顺序

    # 保留第一条记录的 filename 和 subfolder（用于命名）
    extra = {}
    for k in ("filename", "subfolder"):
        if k in records[0]:
            extra[k] = records[0][k]

    return [{
        "wavelength": base_wl,
        "data": final_data,
        "it": final_it,
        **extra,
    }]
