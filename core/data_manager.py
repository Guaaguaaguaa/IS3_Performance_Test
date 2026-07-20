class DataManager:
    """管理文件与光谱记录(dict格式)"""

    def __init__(self):
        self.file_index = {}   # filename -> list[dict]
        self.dark_records = []  # ⭐ 新增：暗电流记录列表
        self.current_cal = None

    def clear(self):
        self.file_index.clear()

    def add_records(self, records):
        """
        records: list of dict
        {
            wavelength: ndarray
            data: ndarray
            it: int | None
            filename: str (外部补充)
        }
        """
        for r in records:
            fname = r["filename"]
            self.file_index.setdefault(fname, []).append(r)

    def remove_files(self, filenames):
        for f in filenames:
            self.file_index.pop(f, None)

    def get_all_filenames(self):
        return list(self.file_index.keys())

    def get_records_by_file(self, filename):
        return self.file_index.get(filename, [])

    def get_records_by_filenames(self, filenames):
        res = []
        for f in filenames:
            res.extend(self.file_index.get(f, []))
        return res

    # ================= 暗电流相关 =================

    def clear_dark_records(self):
        self.dark_records.clear()

    def add_dark_records(self, records):
        self.dark_records.extend(records)

    def get_dark_records(self):
        return self.dark_records
