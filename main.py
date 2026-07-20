# main.py
import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor

from core.algorithms.nedl import NEDLAlgorithm
from core.algorithms.nonlinear import NonLinearAlgorithm
from core.algorithms.radcal import RadCalAlgorithm
from core.algorithms.reflectance import ReflectanceAlgorithm
from core.algorithms.straylight import StraylightAlgorithm
from core.algorithms.subtract import SubtractAlgorithm
from core.algorithms.wavecal import WavecalAlgorithm
from core.algorithms.wavecheck import WaveCheckAlgorithm
from core.io.spectral_reader import read_spectral_files
from core.data_manager import DataManager

from gui.left_panel import LeftPanel
from gui.right_panel import RightPanel
from gui.styles import init_fonts

from core.algorithms.snr import SNRAlgorithm
from core.algorithms.make_cal import MakeCalAlgorithm


class SpectralApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IS3 Spectral Analysis System")
        self.state("zoomed")  # Windows 最大化，任务栏不会挡

        # 核心组件
        self.data_manager = DataManager()
        self.executor = ThreadPoolExecutor(max_workers=2)

        # 先占位
        self.algorithms = {}

        # 构建 UI
        self._build_ui()

        # 注册算法（在 right_panel 创建之后）
        self._register_algorithms()

    def _build_ui(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # 先创建 LeftPanel
        self.left_panel = LeftPanel(
            paned,
            data_manager=self.data_manager,
            executor=self.executor,
            read_func=read_spectral_files,
            log_func=self.log,
            right_panel=None
        )

        # 再创建 RightPanel（传入 left_panel）
        self.right_panel = RightPanel(
            paned,
            data_manager=self.data_manager,
            executor=self.executor,
            algorithms=self.algorithms,
            left_panel=self.left_panel  # ✅ 关键这一行
        )
        self.left_panel.right_panel = self.right_panel  # 初始化后再绑定
        paned.add(self.left_panel, weight=1)
        paned.add(self.right_panel, weight=1)

    def _register_algorithms(self):
        rp = self.right_panel
        s = lambda: rp.serial_number.get() or ""
        o = lambda: rp.output_folder.get()

        self.algorithms = {
            "SNR": SNRAlgorithm(serial_getter=s),
            "MakeCal": MakeCalAlgorithm(serial_getter=s),
            "RadCal": RadCalAlgorithm(serial_getter=s),
            "NEDL": NEDLAlgorithm(serial_getter=s),
            "NonLinear": NonLinearAlgorithm(o, serial_getter=s),
            "Reflectance": ReflectanceAlgorithm(o, serial_getter=s),
            "Straylight": StraylightAlgorithm(serial_getter=s),
            "Subtract": SubtractAlgorithm(serial_getter=s),
            "WaveCal": WavecalAlgorithm(
                output_folder_getter=o,
                shift_getter=lambda: rp.wavecal_shift_var.get() or 0,
                serial_getter=s),
            "WaveCheck": WaveCheckAlgorithm(o, serial_getter=s),
        }

        # 同步给 right_panel
        self.right_panel.algorithms = self.algorithms

    def log(self, msg):
        self.right_panel.log(msg)


if __name__ == "__main__":
    app = SpectralApp()
    init_fonts(app, tk_size=11, mpl_size=11)
    app.mainloop()
