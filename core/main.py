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
import cProfile
import pstats
import asyncio
import logging
from functools import partial

from tracker     import FaceTracker
from display     import AnimatedGIFPlayer
from emotion_api import send_image_to_api
from tts         import TextToSpeech
from detector    import find_faces

# Setup logging
logging.basicConfig(
    filename='output.txt',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger()

# — Redirect everything into output.txt (overwrite each run) —
log_path = os.path.join(os.path.dirname(__file__), 'output.txt')
log_file  = open(log_path, 'a')
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
    'neutral':  os.path.join(src, 'Idle.gif'),
    'fear':  os.path.join(src, 'SadTalk.gif'), 
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

# Asyncio event loop
loop = asyncio.get_event_loop()

# Frame callback
async def on_frame(frame):
    logger.debug('Processing frame in on_frame')
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
            logger.debug('Sending image to API')
            ret, buf = cv2.imencode('.jpg', frame)
            if not ret:
                logger.error('Failed to encode frame to JPEG')
                return
            # Cache API result to reduce calls
            if hasattr(on_frame, 'last_result') and now - on_frame.last_api_time < 10:
                result = on_frame.last_result
            else:      
                result = send_image_to_api(buf.tobytes())
                on_frame.last_result = result
            
            logger.debug(f'API result: {result}')
            on_frame.last_api_time = now
            on_frame.detections.clear()

            status = result.get('status')
            if status == 'ok':
                dom = result['result'].get('dominant_emotion')
                msg = result['result'].get('gemini_interpretation','')
                loop.call_soon_threadsafe(display.display_emotion, dom)
                loop.call_soon_threadsafe(display.update_status, msg)
                loop.call_soon_threadsafe(tts.speak, msg)
            elif status == 'reinit_required':
                fallback = result.get('gemini_interpretation','')
                loop.call_soon_threadsafe(display.update_status, 'No face detected, retrying...')
                loop.call_soon_threadsafe(tts.speak, fallback)
            else:
                err = result.get('error','Unknown API error')
                loop.call_soon_threadsafe(display.update_status, f'Error: {err}')
    except Exception:
        logger.error(f'Error in on_frame: {str(e)}', exc_info=True)
        raise

# Attach persistent state
on_frame.detections    = []
on_frame.last_api_time = 0.0

def on_frame_wrapper(frame):
    try:
        logger.debug('Calling on_frame_wrapper')
        coro = on_frame(frame)
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        future.result()
    except Exception as e:
        logger.error(f'Error in on_frame_wrapper: {str(e)}', exc_info=True)

tracker.frame_callback = on_frame_wrapper

def start():
    logger.info('Starting Desktop-Sitter')
    threading.Thread(target=tracker.run, daemon=True).start()
    display.start()
    
def integrate_asyncio_tkinter():
    """
    Run asyncio tasks alongside Tkinter mainloop
    """
    try:
        loop.run_until_complete(loop.create_task(asyncio.sleep(0))) # Process async
        display.after(10, integrate_asyncio_tkinter) # Schedule next check
    except Exception as e:
        logger.error(f'Error in asyncio_tkinter integration: {str(e)}', exc_info=True)

if __name__ == '__main__':
    # Run with profiling
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        display.after(10, integrate_asyncio_tkinter)
        start()
    except Exception as e:
        logger.error(f'Main loop error: {str(e)}', exc_info=True)
    finally:
        profiler.disable()
        profiler.dump_stats('profile_stats.prof')
        ps = pstats.Stats(profiler, stream = log_file)
        ps.sort_stats('cumulative')
        ps.print_stats(20)
        log_file.flush()
        log_file.close()
        loop.close()

