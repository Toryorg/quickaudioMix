import os, sys, subprocess
if "--child" not in sys.argv:
    subprocess.Popen([sys.executable, os.path.abspath(__file__), "--child"], creationflags=0x08000000)
    sys.exit()
import tkinter as tk
from pycaw.pycaw import AudioUtilities

try:
    import keyboard
except ImportError:
    keyboard = None


def get_sessions():
    result = {}
    for s in AudioUtilities.GetAllSessions():
        if s.Process is None:
            continue
        result.setdefault(s.Process.name(), []).append(s)
    return result


class Mixer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Швидкий мікшер")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.names = None
        self.mute_vars = {}
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        if keyboard:
            keyboard.add_hotkey("ctrl+alt+m", self.toggle_window)
        self.refresh()

    def toggle_window(self):
        def _t():
            if self.state() == "normal":
                self.withdraw()
            else:
                self.deiconify()
                self.lift()
        self.after(0, _t)

    def set_mute(self, name):
        muted = self.mute_vars[name].get()
        for s in get_sessions().get(name, []):
            s.SimpleAudioVolume.SetMute(1 if muted else 0, None)

    def set_volume(self, name, value):
        for s in get_sessions().get(name, []):
            s.SimpleAudioVolume.SetMasterVolume(float(value) / 100, None)

    def build_rows(self, sessions):
        for w in self.winfo_children():
            w.destroy()
        self.mute_vars = {}
        for name in self.names:
            row = tk.Frame(self, padx=8, pady=4)
            row.pack(fill="x")
            var = tk.BooleanVar()
            self.mute_vars[name] = var
            tk.Checkbutton(
                row, text=f"🔇 {name}", variable=var, width=24, anchor="w",
                command=lambda n=name: self.set_mute(n),
            ).pack(side="left")
            vol = sessions[name][0].SimpleAudioVolume.GetMasterVolume()
            scale = tk.Scale(
                row, from_=0, to=100, orient="horizontal", length=120,
                showvalue=False,
                command=lambda v, n=name: self.set_volume(n, v),
            )
            scale.set(int(vol * 100))
            scale.pack(side="left")
        if not self.names:
            tk.Label(self, text="Зараз ніщо не грає", padx=20, pady=20).pack()

    def refresh(self):
        sessions = get_sessions()
        names = sorted(sessions)
        if names != self.names:
            self.names = names
            self.build_rows(sessions)
        for name, var in self.mute_vars.items():
            var.set(bool(sessions[name][0].SimpleAudioVolume.GetMute()))
        self.after(2000, self.refresh)


if __name__ == "__main__":
    Mixer().mainloop()

