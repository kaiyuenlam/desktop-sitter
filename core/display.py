# display.py
import tkinter as tk
from PIL import Image, ImageTk
import os
import subprocess
import threading
import sys
from threading import Lock

class TextRedirector:
    def __init__(self, widget, stream=None):
        self.widget = widget
        # Forward to whatever stream was current (e.g. the file handle)
        self.stream = stream or sys.__stdout__
        self.lock = Lock()

    def write(self, message):
        with self.lock:
            # 1) Insert into the Tk debug console
            self.widget.configure(state="normal")
            self.widget.insert("end", message)
            self.widget.configure(state="disabled")
            self.widget.see("end")
            # 2) Also echo to the underlying stream (→ output.txt)
            try:
                self.stream.write(message)
                self.stream.flush()
            except Exception:
                pass

    def flush(self):
        try:
            self.stream.flush()
        except Exception:
            pass

class AnimatedGIFPlayer(tk.Tk):
    def __init__(self, gif_mapping):
        super().__init__()
        self.title("Desktop Sitter Display")
        self.attributes("-fullscreen", True)
        self.configure(background="black")
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("g", lambda e: self.toggle_debug())
        self.bind("G", lambda e: self.toggle_debug())
        self.config(cursor="none")

        # Layout
        self.container = tk.Frame(self, bg="black"); self.container.pack(fill=tk.BOTH, expand=True)
        self.left_frame = tk.Frame(self.container, bg="black"); self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right_frame = tk.Frame(self.container, bg="black")
        self.right_frame_visible = False

        # GIF + status
        self.gif_label = tk.Label(self.left_frame, bg="black"); self.gif_label.pack(fill=tk.BOTH, expand=True)
        self.status_label = tk.Label(self.left_frame, text="", fg="white", bg="black", font=("Helvetica", 18))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Debug console plumbing
        self.console_text     = None
        self.original_stdout  = sys.stdout
        self.original_stderr  = sys.stderr
        self.tracker_process  = None

        # Animation state
        self.gif_mapping = gif_mapping
        self.frames      = []
        self.durations   = []
        self.current_frame = 0
        self._animation_job = None

    def play_gif(self, gif_file):
        if self._animation_job:
            self.after_cancel(self._animation_job)
        self.frames, self.durations = [], []
        self.current_frame = 0

        if not os.path.exists(gif_file):
            print(f"[Error] File not found: {gif_file}")
            return

        gif = Image.open(gif_file)
        try:
            while True:
                frame = ImageTk.PhotoImage(gif.copy())
                self.frames.append(frame)
                self.durations.append(gif.info.get("duration", 100))
                gif.seek(len(self.frames))
        except EOFError:
            pass

        if self.frames:
            self.update_frame()

    def update_frame(self):
        if self.frames:
            frame = self.frames[self.current_frame]
            delay = self.durations[self.current_frame]
            self.gif_label.config(image=frame)
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self._animation_job = self.after(delay, self.update_frame)

    def display_emotion(self, keyword):
        if keyword in self.gif_mapping:
            self.play_gif(self.gif_mapping[keyword])
        else:
            print(f"[Error] No GIF mapped to keyword: {keyword}")

    def update_status(self, text):
        self.status_label.config(text=text)

    def toggle_debug(self):
        import sys
        real_out = sys.stdout
        real_err = sys.stderr

        if not self.right_frame_visible:
            # show debug pane
            self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
            self.console_text = tk.Text(self.right_frame, bg="black", fg="white", font=("Courier",12))
            self.console_text.pack(fill=tk.BOTH, expand=True)

            sys.stdout = TextRedirector(self.console_text, stream=real_out)
            sys.stderr = TextRedirector(self.console_text, stream=real_err)

            if hasattr(self, 'tracker'):
                self.tracker.enable_debug_window(True)

            self.right_frame_visible = True
        else:
            # hide debug pane
            if self.tracker_process:
                self.tracker_process.terminate()
                self.tracker_process = None
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            self.right_frame.pack_forget()
            self.right_frame_visible = False

    def _steam_subprocess(self):
        for line in self.tracker_process.stdout:
            print(line, end="")
            
    def start(self):
        self.mainloop()
