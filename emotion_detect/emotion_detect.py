import cv2
import numpy as np
from deepface import DeepFace
import requests
import os
import time

# Delay to ensure webcam initializes before running the detection loop
print("Starting webcam. Please wait...")
time.sleep(3)  # Small delay for the camera to fully initialize

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
if face_cascade.empty():
    print("Error: Could not load Haar Cascade classifier.")
    exit()

# Hugging Face API configuration (replace the token with your actual valid token)
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
HF_API_KEY = "hf_XXXXXXX"

def preprocess_image(image):
    """Preprocess the image to improve face detection."""
    image = cv2.resize(image, (300, 300))
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    enhanced_image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    return enhanced_image

def analyze_emotion(image_path):
    """Analyze emotion using DeepFace with default model."""
    try:
        results = DeepFace.analyze(img_path=image_path, actions=['emotion'], 
                                   enforce_detection=False, detector_backend='opencv')
        
        if results and isinstance(results, list) and len(results) > 0:
            dominant_emotion = results[0]['dominant_emotion']
            emotion_scores = results[0]['emotion']
            return dominant_emotion, emotion_scores
        elif results and not isinstance(results, list):
            dominant_emotion = results['dominant_emotion']
            emotion_scores = results['emotion']
            return dominant_emotion, emotion_scores
        else:
            return None, "No valid results returned"
    except Exception as e:
        return None, f"Emotion analysis failed: {str(e)}"

def get_chatbot_response(emotion):
    """Generate a first-person response that directly engages with the user."""
    try:
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json"
        }

        # Make the AI chatbot speak in first-person, directly engaging with the user
        prompt = f"You are my AI companion. I am feeling {emotion}. What should I do? Please respond warmly and in first-person."

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 100,  # Increase for more detailed responses
                "num_return_sequences": 1,
                "temperature": 0.7,  # Controls creativity (0.7 is a good balance)
                "top_p": 0.9  # Adds diversity to responses
            }
        }
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and result:
            return result[0].get("generated_text", "No response from chatbot")
        else:
            return "Error in response format"
    except Exception as e:
        return f"Chatbot error: {str(e)}"

# Main loop for real-time processing
print("Webcam is ready. Analyzing emotions in real-time. Press 'ESC' to exit.")
last_analysis_time = 0
analysis_interval = 10  # Analyze every 10 seconds

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

    # Run emotion analysis at defined intervals if at least one face is found
    current_time = time.time()
    if current_time - last_analysis_time >= analysis_interval and len(faces) > 0:
        # Preprocess the frame
        processed_frame = preprocess_image(frame)
        
        # Save frame temporarily
        timestamp = int(current_time)
        image_path = f"captured_face_{timestamp}.jpg"
        cv2.imwrite(image_path, processed_frame)

        # Ensure the image file exists before proceeding
        while not os.path.exists(image_path):
            time.sleep(0.5)  # Wait for the file to be saved properly

        print(f"\nImage saved as {image_path}")

        # Analyze emotion using DeepFace
        print("Analyzing emotion...")
        dominant_emotion, emotion_data = analyze_emotion(image_path)
        
        if dominant_emotion:
            emotion_str = ", ".join([f"{k}: {v:.2f}%" for k, v in emotion_data.items()])
            print(f"Detected Emotion: {dominant_emotion}")
            print(f"Emotion Scores: {emotion_str}")

            # Get chatbot response via the Hugging Face API
            print("Getting chatbot response...")
            chatbot_response = get_chatbot_response(dominant_emotion)
            print(f"Chatbot Response: {chatbot_response}")
        else:
            print(f"Error: {emotion_data}")

        # Remove temporary image file after analysis
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"Deleted temporary image: {image_path}")

        last_analysis_time = current_time

    # Display the frame with an informative caption
    cv2.putText(frame, "Press ESC to exit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    if len(faces) > 0:
        cv2.putText(frame, "Face Detected", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "No Face Detected", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.imshow('Webcam - Real-Time Emotion Detection (ESC to exit)', frame)

    # Exit on 'Esc' key
    if cv2.waitKey(1) & 0xFF == 27:
        print("Exiting...")
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
