import cv2
import numpy as np
from deepface import DeepFace
import requests
import os
import time

# Hugging Face API configuration
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
HF_API_KEY = "hf_xxxxxxxxxxxx"  # Replace with your actual token

def analyze_emotion(image_path):
    """Analyze emotion using DeepFace with default model."""
    try:
        result = DeepFace.analyze(img_path=image_path, actions=['emotion'], enforce_detection=True, detector_backend='opencv')
        # Handle different result types if necessary:
        if isinstance(result, list):
            dominant_emotion = result[0]['dominant_emotion']
            emotion_scores = result[0]['emotion']
        else:
            dominant_emotion = result['dominant_emotion']
            emotion_scores = result['emotion']
        return dominant_emotion, emotion_scores
    except Exception as e:
        return None, f"Emotion analysis failed: {str(e)}"

def get_chatbot_response(emotion):
    """Send emotion to Hugging Face chatbot and get a conversational response."""
    try:
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt = (f"I detected that you're feeling {emotion}. How can I make your day even better?" 
                  if emotion == "happy" else f"I noticed you're feeling {emotion}. Want to share what's going on? I'm here for you!")
        
        payload = {
            "inputs": prompt,
            "parameters": {"max_length": 50, "num_return_sequences": 1}
        }
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        # Expecting result to be a list containing a dictionary
        if isinstance(result, list) and result:
            return result[0].get("generated_text", "No response from chatbot")
        else:
            return "Unexpected response format from chatbot API"
    except Exception as e:
        return f"Chatbot error: {str(e)}"

def main():
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Load Haar Cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("Error: Could not load Haar Cascade classifier.")
        return

    print("Starting webcam. Analyzing emotions in real-time. Press 'esc' to exit.")
    last_analysis_time = 0
    analysis_interval = 10  # seconds

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        # Convert frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Real-time emotion analysis every few seconds when a face is detected
        current_time = time.time()
        if current_time - last_analysis_time >= analysis_interval and len(faces) > 0:
            timestamp = int(time.time())
            image_path = f"captured_face_{timestamp}.jpg"
            cv2.imwrite(image_path, frame)
            print(f"\nImage saved as {image_path}")

            print("Analyzing emotion...")
            dominant_emotion, emotion_data = analyze_emotion(image_path)
            
            if dominant_emotion:
                emotion_str = ", ".join([f"{k}: {v:.2f}%" for k, v in emotion_data.items()])
                print(f"Detected Emotion: {dominant_emotion}")
                print(f"Emotion Scores: {emotion_str}")

                print("Getting chatbot response...")
                chatbot_response = get_chatbot_response(dominant_emotion)
                print(f"Chatbot Response: {chatbot_response}")
            else:
                print(f"Error: {emotion_data}")

            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"Deleted temporary image: {image_path}")

            last_analysis_time = current_time

        # Display the frame
        cv2.imshow('Webcam - Real-Time Emotion Detection (esc to exit)', frame)

        # Exit on 'esc'
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC key
            print("Exiting...")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
