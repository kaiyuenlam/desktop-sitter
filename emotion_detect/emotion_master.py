import cv2
import numpy as np
from deepface import DeepFace
import threading
import time
import os
import requests
import tkinter as tk
from PIL import Image, ImageTk

# ========== Hugging Face Chatbot API ==========
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
HF_API_KEY = "hf_FmuBSizXbQfVHZGFwhkHdjiWNzidDKHID"  # <-- Replace with your token

def get_chatbot_response(emotion):
    try:
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt = (f"You are my AI companion. I am feeling {emotion}. "
                  "What should I do? Please respond warmly and in first-person.")
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 100,
                "num_return_sequences": 1,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and result:
            return result[0].get("generated_text", "No response from chatbot")
        else:
            return "Error in response format"
    except Exception as e:
        return f"Chatbot error: {str(e)}"

# ========== Emotion Detection ==========
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
if face_cascade.empty():
    print("Error: Could not load Haar Cascade classifier.")
    exit()

def preprocess_image(image):
    image = cv2.resize(image, (300, 300))
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    enhanced_image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    return enhanced_image

def analyze_emotion(image_path):
    try:
        results = DeepFace.analyze(img_path=image_path, actions=['emotion'],
                                   enforce_detection=False, detector_backend='opencv')
        # Standardize output
        if results and isinstance(results, list) and len(results) > 0:
            dominant_emotion = results[0]['dominant_emotion']
            emotion_scores = results[0]['emotion']
        elif results and not isinstance(results, list):
            dominant_emotion = results['dominant_emotion']
            emotion_scores = results['emotion']
        else:
            return None, None
        return dominant_emotion, emotion_scores
    except Exception as e:
        print(f"Emotion analysis failed: {str(e)}")
        return None, None

# ========== Thread-Safe State ==========
class SharedState:
    def __init__(self, initial_emotion='neutral', initial_response='Hello!'):
        self.lock = threading.Lock()
        self.emotion = initial_emotion
        self.response = initial_response
        self.changed = threading.Event()

    def set(self, emotion, response):
        with self.lock:
            if emotion != self.emotion or response != self.response:
                self.emotion = emotion
                self.response = response
                self.changed.set()

    def get(self):
        with self.lock:
            return self.emotion, self.response

    def wait_for_change(self):
        self.changed.wait()
        self.changed.clear()

# ========== Animated GIF Player (Tkinter GUI) ==========
class AnimatedGIFPlayer(tk.Tk):
    def __init__(self, gif_mapping, shared_state):
        super().__init__()
        self.title("Animated GIF + Chatbot")
        self.geometry("500x400")
        self.gif_mapping = gif_mapping
        self.shared_state = shared_state

        # Layout
        self.label = tk.Label(self, bg="black")
        self.label.pack(fill=tk.BOTH, expand=True)

        self.chatbot_label = tk.Label(self, text="", wraplength=490, justify="left", font=("Arial", 12), bg="#222", fg="#fff")
        self.chatbot_label.pack(fill=tk.X, side=tk.BOTTOM, padx=2, pady=4)

        self.frames = []
        self.current_frame = 0

        # Start with neutral
        self.current_gif_keyword = "neutral"
        self.play_gif(self.gif_mapping["neutral"])

        # Start background emotion listener
        threading.Thread(target=self.listen_for_emotion, daemon=True).start()

    def play_gif(self, gif_file):
        self.frames = []
        self.current_frame = 0
        if not os.path.exists(gif_file):
            print(f"GIF file {gif_file} not found!")
            return
        try:
            gif = Image.open(gif_file)
            while True:
                frame = ImageTk.PhotoImage(gif.copy())
                self.frames.append(frame)
                gif.seek(len(self.frames))
        except EOFError:
            pass
        self.update_frame()

    def update_frame(self):
        if self.frames:
            frame = self.frames[self.current_frame]
            self.label.config(image=frame)
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.after(100, self.update_frame)

    def listen_for_emotion(self):
        while True:
            self.shared_state.wait_for_change()
            emotion, response = self.shared_state.get()
            gif_file = self.gif_mapping.get(emotion, self.gif_mapping["neutral"])
            self.play_gif(gif_file)
            self.set_chatbot_response(response)

    def set_chatbot_response(self, text):
        # Tkinter text updates must be run from the main thread
        self.after(0, lambda: self.chatbot_label.config(text=text))

# ========== Webcam & Emotion Detection Thread ==========
def webcam_emotion_thread(shared_state):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    analysis_interval = 10  # seconds
    last_analysis_time = 0
    last_emotion = "neutral"

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display status text overlays
        cv2.putText(frame, "Press ESC to exit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        if len(faces) > 0:
            cv2.putText(frame, "Face Detected", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "No Face Detected", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        current_time = time.time()
        if current_time - last_analysis_time >= analysis_interval and len(faces) > 0:
            processed_frame = preprocess_image(frame)
            timestamp = int(current_time)
            image_path = f"captured_face_{timestamp}.jpg"
            cv2.imwrite(image_path, processed_frame)
            while not os.path.exists(image_path):
                time.sleep(0.1)
            dominant_emotion, emotion_scores = analyze_emotion(image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
            if dominant_emotion:
                # Format and print scores to terminal
                if emotion_scores:
                    emotion_str = ", ".join([f"{k}: {v:.2f}%" for k, v in emotion_scores.items()])
                    print(f"[Webcam] Detected Emotion: {dominant_emotion}")
                    print(f"[Webcam] Emotion Scores: {emotion_str}")
                else:
                    print(f"[Webcam] Detected Emotion: {dominant_emotion}")
                # Only trigger update if different or it's the first run
                if dominant_emotion != last_emotion or last_analysis_time == 0:
                    chatbot_response = get_chatbot_response(dominant_emotion)
                    print(f"[Webcam] Chatbot: {chatbot_response}")
                    shared_state.set(dominant_emotion, chatbot_response)
                    last_emotion = dominant_emotion
            last_analysis_time = current_time

        cv2.imshow('Webcam - Real-Time Emotion Detection (ESC to exit)', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            print("Exiting webcam thread...")
            break

    cap.release()
    cv2.destroyAllWindows()
    os._exit(0)  # Ensure all threads kill (tkinter mainloop will hang otherwise)

# ========== MAIN ==========
if __name__ == "__main__":
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

    shared_state = SharedState(initial_emotion='neutral', initial_response="Hello! I'm here to chat.")

    # Start webcam detection in a new thread
    webcam_thread = threading.Thread(target=webcam_emotion_thread, args=(shared_state,), daemon=True)
    webcam_thread.start()

    # Start the Tkinter GUI (main thread)
    app = AnimatedGIFPlayer(gif_mapping, shared_state)
    app.mainloop()