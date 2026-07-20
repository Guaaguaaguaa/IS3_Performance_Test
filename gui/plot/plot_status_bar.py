# plot_status_bar.py
from tkinter import ttk


class StatusBar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        import inspect
        print("StatusBar loaded from:", inspect.getfile(inspect.currentframe()))
        self.label = ttk.Label(self, text="x: -, y: -")
        self.label.grid(row=0, column=0, sticky="w", padx=5)

        self.columnconfigure(0, weight=1)

    def update_xy(self, x, y, label=None):
        if x is None or y is None:
            self.label.config(text="λ: -, I: -")
        else:
            if label:
                self.label.config(
                    text=f"λ: {x:.2f} nm | I: {y:.5f} | curve: {label}"
                )
            else:
                self.label.config(
                    text=f"λ: {x:.2f} nm | I: {y:.5f}"
                )

