import tkinter as tk
from PIL import Image, ImageTk
import os

class AnimatedGIFPlayer(tk.Tk):
    def __init__(self, gif_mapping):
        super().__init__()
        self.title("Animated GIF Player")
        self.geometry("432x324")
        self.gif_mapping = gif_mapping
        self.label = tk.Label(self, bg="black")
        self.label.pack(expand=True)
        self.frames = []
        self.current_frame = 0
        self._animation_job = None

    def play_gif(self, gif_file):
        """Load and play the given GIF file."""
        if self._animation_job:
            self.after_cancel(self._animation_job)
        self.frames = []
        self.current_frame = 0

        try:
            gif = Image.open(gif_file)
            # Extract frames
            while True:
                frame = ImageTk.PhotoImage(gif.copy())
                self.frames.append(frame)
                gif.seek(len(self.frames))
        except EOFError:
            pass  # End of GIF reached

        if self.frames:
            self.update_frame()

    def update_frame(self):
        """Update the label with the next frame."""
        if self.frames:
            frame = self.frames[self.current_frame]
            self.label.config(image=frame)
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self._animation_job = self.after(100, self.update_frame)

    def display_emotion(self, keyword):
        """Display a GIF based on the keyword."""
        if keyword in self.gif_mapping:
            self.play_gif(self.gif_mapping[keyword])
        else:
            raise ValueError(f"No GIF mapped to keyword: {keyword}")

    def start(self):
        """Start the Tkinter mainloop."""
        self.mainloop()