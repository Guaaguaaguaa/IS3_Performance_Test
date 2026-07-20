import sys
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import pandas as pd
import os
from matplotlib import pyplot as plt
from curve_plot import curve_plt
from read_data import read_multil_data
from screen_size import get_screen_figsize

# ==========================================================
# Window size
# ==========================================================
dpi = 120
fig_width, fig_height = get_screen_figsize(dpi, scale=1.0)
win_w = int(fig_width * dpi*0.6)
win_h = int(fig_height * dpi*0.8)

# ==========================================================
# 核心处理函数
# ==========================================================
def process_multi_wavelength_delta(
    data_list,
    peak_list,
    basename,
    path,
    curve_plt,
    save_csv=True,
):
    os.makedirs(path, exist_ok=True)

    if len(data_list) < 2:
        raise ValueError("Delta 分析至少需要两条数据")

    ref_w = data_list[0][0]
    for i, (w, _, fname) in enumerate(data_list):
        if not np.allclose(w, ref_w):
            raise ValueError(f"波长不一致：第 0 个 与 第 {i} 个 ({fname})")

    wavelength_axis = ref_w.astype(float)
    data_matrix = np.array([v for _, v, _ in data_list])
    n_files, _ = data_matrix.shape

    for w in peak_list:
        idx = int(np.argmin(np.abs(wavelength_axis - w)))

        values = data_matrix[:, idx]
        Index = np.arange(n_files)

        Delta = np.full(n_files, np.nan)
        Delta[1:] = values[1:] - values[:-1]

        label = f"{w:.2f} nm"

        if save_csv:
            df = pd.DataFrame({
                "Index": Index,
                "Value": values,
                "Delta": Delta,
                "Wavelength": w
            })
            csv_path = os.path.join(
                path,
                f"{basename}_Delta_{w:.2f}nm.csv"
            )
            df.to_csv(csv_path, index=False, encoding="utf-8")

        curve_plt(
            Index[1:],
            Delta[1:],
            f"{basename}_Delta_{w:.2f}nm",
            f"AgingTest ({label})",
            path,
        )

    plt.show()

# ==========================================================
# GUI
# ==========================================================
class DataDeltaGUI:

    def __init__(self, master, curve_plt):
        self.master = master
        self.master.title("Data Delta Analysis Tool")
        self.master.geometry(f"{win_w}x{win_h}")
        self.master.minsize(600, 700)
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        self.curve_plt = curve_plt
        self.basename = "AgingTest"
        self.output_path = "./output"

        self.data_list = None
        self.wavelength_axis = None

        # Tk variables
        self.save_csv = tk.BooleanVar(value=True)

        # Widgets
        self.cb_csv = None
        self.file_label = None

        self.build_ui()
        self.set_ui_state("disabled")

    def on_close(self):
        import os
        try:
            self.master.quit()
            self.master.destroy()
        finally:
            os._exit(0)

    # ------------------------------------------------------
    # UI
    # ------------------------------------------------------
    def build_ui(self):

        # ---------- File ----------
        lf_file = ttk.LabelFrame(self.master, text="Data")
        lf_file.pack(fill="x", padx=10, pady=10)

        self.open_btn = ttk.Button(
            lf_file,
            text="Open Data Files",
            command=self.open_files
        )
        self.open_btn.pack(fill="x", padx=10, pady=(8, 4))

        self.file_label = ttk.Label(
            lf_file,
            text="No data loaded",
            foreground="gray",
            anchor="center"
        )
        self.file_label.pack(fill="x", padx=10, pady=(0, 8))

        # ---------- Wavelength ----------
        lf_w = ttk.LabelFrame(self.master, text="Select Wavelengths (nm)")
        lf_w.pack(fill="both", expand=True, padx=10, pady=10)

        container = ttk.Frame(lf_w)
        container.pack(fill="both", expand=True, padx=5, pady=5)

        self.listbox = tk.Listbox(container, selectmode=tk.MULTIPLE)
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(container, command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # ---------- Options ----------
        lf_opt = ttk.LabelFrame(self.master, text="Options")
        lf_opt.pack(fill="x", padx=10, pady=(0, 10))

        self.cb_csv = ttk.Checkbutton(
            lf_opt,
            text="Save CSV files",
            variable=self.save_csv
        )
        self.cb_csv.pack(anchor="w", padx=10, pady=5)

        # ---------- Run ----------
        self.run_btn = ttk.Button(
            self.master,
            text="Run Analysis",
            command=self.run
        )
        self.run_btn.pack(fill="x", padx=60, pady=15)

    # ------------------------------------------------------
    # UI enable / disable
    # ------------------------------------------------------
    def set_ui_state(self, state):
        widgets = [self.listbox, self.cb_csv, self.run_btn]
        for w in widgets:
            if w is not None:
                w.config(state=state)

    # ------------------------------------------------------
    # Open files
    # ------------------------------------------------------
    def open_files(self):
        try:
            data_list = read_multil_data()
            if len(data_list) < 2:
                raise ValueError("至少需要两条数据")

            self.data_list = data_list
            self.wavelength_axis = data_list[0][0].astype(float)

            self.listbox.config(state="normal")
            self.listbox.delete(0, tk.END)

            for w in self.wavelength_axis:
                self.listbox.insert(tk.END, f"{w:.2f}")

            self.file_label.config(
                text=f"Loaded {len(data_list)} files",
                foreground="green"
            )

            self.set_ui_state("normal")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ------------------------------------------------------
    # Run
    # ------------------------------------------------------
    def run(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Select at least one wavelength")
            return

        peak_list = [float(self.listbox.get(i)) for i in sel]

        self.set_ui_state("disabled")
        self.master.update_idletasks()

        try:
            process_multi_wavelength_delta(
                data_list=self.data_list,
                peak_list=peak_list,
                basename=self.basename,
                path=self.output_path,
                curve_plt=self.curve_plt,
                save_csv=self.save_csv.get(),
            )
            messagebox.showinfo("Done", "Analysis completed successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.set_ui_state("normal")

# ==========================================================
# Main
# ==========================================================
if __name__ == "__main__":
    root = tk.Tk()
    DataDeltaGUI(root, curve_plt=curve_plt)
    root.mainloop()
