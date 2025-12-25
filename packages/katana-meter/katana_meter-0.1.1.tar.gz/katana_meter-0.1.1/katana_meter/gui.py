import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from .core import analyze_file, DEFAULT_TARGET_LUFS

def main():
    class KatanaGUI(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Katana Meter")
            self.geometry("560x360")
            self.configure(bg="#0b1a2e")
            self.file = None

            tk.Label(self, text="Katana Meter",
                     font=("Arial",16,"bold"),
                     fg="white", bg="#0b1a2e").pack(pady=12)

            btns = tk.Frame(self, bg="#0b1a2e")
            btns.pack(pady=6)

            tk.Button(btns, text="Dosya Seç", command=self.pick).grid(row=0,column=0,padx=8)
            tk.Button(btns, text="Analiz Et", command=self.run).grid(row=0,column=1,padx=8)

            self.status = tk.Label(self, text="Bekleniyor",
                                   fg="#c8d6ea", bg="#0b1a2e")
            self.status.pack(pady=6)

            self.out = tk.Label(self, text="-",
                                font=("Consolas",12),
                                fg="white", bg="#0b1a2e",
                                justify="left")
            self.out.pack(pady=10)

        def pick(self):
            p = filedialog.askopenfilename(
                filetypes=[("Audio","*.wav *.mp3 *.flac *.aac *.ogg")]
            )
            if p:
                self.file = p
                self.status.config(text=p)

        def run(self):
            if not self.file:
                messagebox.showwarning("Uyarı","Dosya seç")
                return
            self.status.config(text="Analiz ediliyor...")
            threading.Thread(target=self.worker, daemon=True).start()

        def worker(self):
            try:
                r = analyze_file(self.file, target_lufs=DEFAULT_TARGET_LUFS)
                self.after(0, lambda: self.show(r))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Hata", str(e)))

        def show(self, r):
            txt = (
                f"LUFS : {r['lufs']}\n"
                f"Gain : {r['gain_to_target_db']} dB\n"
                f"Peak : {r['peak_dbtp_approx']} dBTP\n"
                f"ΔE   : {r['delta_e']}"
            )
            self.out.config(text=txt)
            self.status.config(text="Tamam ✓")

    KatanaGUI().mainloop()
