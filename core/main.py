"""
main.py – Orchestrates Desktop-Sitter workflow:
1. Face tracking via FaceTracker
2. Conditional Cloud AI emotion API (after stable detections)
3. Display + TTS, using display.py

On any unexpected exception, writes full traceback and debug output to core/output.txt.
"""
# main.py

import os
import threading
import traceback
import time
import cv2
import sys

from tracker     import FaceTracker
from display     import AnimatedGIFPlayer
from emotion_api import send_image_to_api
from tts         import TextToSpeech
from detector    import find_faces

# — Redirect everything into output.txt (overwrite each run) —
log_path = os.path.join(os.path.dirname(__file__), 'output.txt')
log_file  = open(log_path, 'w')
sys.stdout = log_file
sys.stderr = log_file

# Detection & throttle settings
DETECTION_WINDOW     = 10.0
DETECTION_THRESHOLD  = 5
API_THROTTLE         = 30.0
SCALE                = 0.5
MIN_AREA_RATIO       = 0.1
ASPECT_TOL           = 0.25

# Initialize TTS & Display
tts = TextToSpeech()
src = os.path.join(os.path.dirname(__file__), 'src')
gif_mapping = {
    'happy': os.path.join(src, 'HappyTalk.gif'),
    'sad':   os.path.join(src, 'SadTalk.gif'),
    'sleep': os.path.join(src, 'Sleep.gif'),
    'idle':  os.path.join(src, 'Idle.gif'),
}
display = AnimatedGIFPlayer(gif_mapping)
display.display_emotion('idle')

display.device_index = 0

tracker = FaceTracker(
            device_index=0,
            debug=True,
            headless=True,
            frame_callback=None
        )
display.tracker = tracker

# Frame callback
def on_frame(frame):
    try:
        now = time.time()
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (0,0), fx=SCALE, fy=SCALE)
        faces = find_faces(small, min_area_ratio=MIN_AREA_RATIO, aspect_ratio_tol=ASPECT_TOL)
        if faces:
            on_frame.detections.append(now)
            on_frame.detections = [t for t in on_frame.detections if now - t <= DETECTION_WINDOW]

        # Once stable, send to emotion API
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
        traceback.print_exc()
        raise

# Attach persistent state
on_frame.detections    = []
on_frame.last_api_time = 0.0
tracker.frame_callback = on_frame

def start():
    # Launch tracker thread + UI
    threading.Thread(target=tracker.run, daemon=True).start()
    display.start()

if __name__ == '__main__':
    start()
    log_file.flush()
    log_file.close()

