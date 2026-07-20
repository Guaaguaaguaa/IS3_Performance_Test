import tkinter as tk
from tkinter import filedialog
import os
import json

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "last_path.json")


def _load_last_path(key):
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(key, "")
        except:
            return ""
    return ""


def _save_last_path(key, path):
    data = {}
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass
    data[key] = path
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def select_file(title="请选择文件"):
    root = tk.Tk()
    root.withdraw()
    initial = _load_last_path("file")

    # 如果上次路径存在且是文件夹，就在该文件夹下
    if os.path.isdir(initial):
        initialdir = initial
        initialfile = ""
    else:
        initialdir = os.path.dirname(initial) if initial else ""
        initialfile = os.path.basename(initial) if initial else ""

    path = filedialog.askopenfilename(title=title, initialdir=initialdir, initialfile=initialfile)
    if not path:
        return None

    _save_last_path("file", os.path.dirname(path))
    return path


def select_folder(title="请选择文件夹"):
    root = tk.Tk()
    root.withdraw()
    initial = _load_last_path("folder")

    # 默认进入上次选择的文件夹
    initialdir = initial if os.path.isdir(initial) else os.path.dirname(initial) if initial else ""

    path = filedialog.askdirectory(title=title, initialdir=initialdir)
    if not path:
        return None

    _save_last_path("folder", path)
    return path
