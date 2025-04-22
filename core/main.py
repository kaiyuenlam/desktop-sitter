# main.py
from gifdisplay import AnimatedGIFPlayer
import time

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

player = AnimatedGIFPlayer(gif_mapping)
player.start()
player.display_emotion("happy")  # to display "happy" gif
player.update()