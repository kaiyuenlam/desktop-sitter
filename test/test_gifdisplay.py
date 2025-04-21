import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import os

class AnimatedGIFPlayer(tk.Tk):

    def __init__(self, gif_mapping):
        super().__init__()
        self.title("Animated GIF Player")
        self.geometry("432x324")  # Set window size

        # Map keywords to GIF files
        self.gif_mapping = gif_mapping

        # Create a label to display the GIF
        self.label = tk.Label(self, bg="black")
        self.label.pack(expand=True)

        # Set a default GIF to display
        default_keyword = list(self.gif_mapping.keys())[0]
        self.play_gif(self.gif_mapping[default_keyword])

        # Start a thread to listen for terminal input
        self.input_thread = threading.Thread(target=self.handle_terminal_input, daemon=True)
        self.input_thread.start()

    def play_gif(self, gif_file):
        """Play the given GIF file."""
        self.frames = []
        self.current_frame = 0

        try:
            # Load the GIF using PIL
            gif = Image.open(gif_file)

            # Extract frames and store them
            while True:
                frame = ImageTk.PhotoImage(gif.copy())
                self.frames.append(frame)
                time.sleep(0.02)
                gif.seek(len(self.frames))  # Move to the next frame
        except EOFError:
            pass  # End of GIF reached

        # Start the animation
        self.update_frame()

    def update_frame(self):
        """Update the label with the next frame."""
        if self.frames:
            frame = self.frames[self.current_frame]
            self.label.config(image=frame)
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            # Schedule the next frame update
            self.after(100, self.update_frame)

    def handle_terminal_input(self):
        """Handle user input from the terminal."""
        while True:
            user_input = input()
            print(f"Displaying GIF for keyword: {user_input}")
            self.play_gif(self.gif_mapping[user_input])


# Map keywords to GIF file paths
gif_mapping = {
    "happy": r"C:\Users\lewis\Documents\GitHub\desktop-sitter\emotion_detect\HappyTalk.gif",
    "surprise": r"C:\Users\lewis\Documents\GitHub\desktop-sitter\emotion_detect\HappyTalk.gif",
    "angry": r"C:\Users\lewis\Documents\GitHub\desktop-sitter\emotion_detect\SadTalk.gif",
    "sad": r"C:\Users\lewis\Documents\GitHub\desktop-sitter\emotion_detect\SadTalk.gif",
    "neutral": r"C:\Users\lewis\Documents\GitHub\desktop-sitter\emotion_detect\Idle.gif",
    "fear": r"C:\Users\lewis\Documents\GitHub\desktop-sitter\emotion_detect\HappyTalk.gif",
    "disgust": r"C:\Users\lewis\Documents\GitHub\desktop-sitter\emotion_detect\SadTalk.gif",
    "sleepy": r"C:\Users\lewis\Documents\GitHub\desktop-sitter\emotion_detect\Sleep.gif"
}

# Create and run the app
app = AnimatedGIFPlayer(gif_mapping)
app.mainloop()
