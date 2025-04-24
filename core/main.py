"""
main.py – Orchestrates Desktop-Sitter workflow:
1. Face tracking
2. Conditional Cloud AI emotion API (after stable detections)
3. Display + TTS

Writes any unhandled traceback to core/error.txt
"""
import os
import threading
import traceback
import time
import cv2

from tracker import FaceTracker
from display import AnimatedGIFPlayer
from emotion_api import send_image_to_api
from tts import TextToSpeech
from detector import find_faces

# Constants for detection stability and API throttle
DETECTION_WINDOW = 10.0      # seconds to accumulate detections
DETECTION_THRESHOLD = 5      # number of detections required
API_THROTTLE      = 30.0      # seconds between API calls
# Mirror tracker detection params
SCALE             = 0.5
MIN_AREA_RATIO    = 0.1
ASPECT_TOL        = 0.25

# Path for error logging
def error_log_path():
    return os.path.join(os.path.dirname(__file__), 'error.txt')

# Initialize TTS and Display
tts = TextToSpeech()
src = os.path.join(os.path.dirname(__file__), 'src')
gif_mapping = {
    'happy': os.path.join(src, 'HappyTalk.gif'),
    'sad':   os.path.join(src, 'SadTalk.gif'),
    'sleep': os.path.join(src, 'Sleep.gif'),
    'idle':  os.path.join(src, 'Idle.gif'),
}
display = AnimatedGIFPlayer(gif_mapping)
display.display_emotion('idle')  # default state

# State for detection stability
on_frame.detections    = []
on_frame.last_api_time = 0.0

# Callback receives each new frame from tracker
def on_frame(frame):
    try:
        now = time.time()
        # Check for face in this frame
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (0,0), fx=SCALE, fy=SCALE)
        faces = find_faces(small, min_area_ratio=MIN_AREA_RATIO, aspect_ratio_tol=ASPECT_TOL)
        if faces:
            # Record detection timestamp
            on_frame.detections.append(now)
            # Purge old entries
            on_frame.detections = [t for t in on_frame.detections if now - t <= DETECTION_WINDOW]

        # Show camera feed in debug pane if active
        if display.right_frame_visible:
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            display.show_camera_frame(img_rgb)

        # Only call API if we have enough stable detections
        if len(on_frame.detections) >= DETECTION_THRESHOLD and now - on_frame.last_api_time >= API_THROTTLE:
            ret, buf = cv2.imencode('.jpg', frame)
            if not ret:
                return
            result = send_image_to_api(buf.tobytes())
            on_frame.last_api_time = now
            on_frame.detections.clear()

            status = result.get('status')
            if status == 'ok':
                dom = result['result'].get('dominant_emotion')
                msg = result['result'].get('gemini_interpretation','')
                display.display_emotion(dom)
                display.update_status(msg)
                tts.speak(msg)
            elif status == 'reinit_required':
                fallback = result.get('gemini_interpretation','')
                display.update_status('No face detected, retrying...')
                tts.speak(fallback)
            else:
                err = result.get('error','Unknown API error')
                display.update_status(f'Error: {err}')

    except Exception:
        tb = traceback.format_exc()
        with open(error_log_path(), 'w') as ef:
            ef.write(tb)
        raise

# Entrypoint: start tracker thread + UI loop
def start():
    try:
        tracker = FaceTracker(debug=True, headless=True, frame_callback=on_frame)
        threading.Thread(target=tracker.run, daemon=True).start()
        display.start()
    except Exception:
        tb = traceback.format_exc()
        with open(error_log_path(), 'w') as ef:
            ef.write(tb)
        print(tb)
        raise

if __name__ == '__main__':
    start()

