# tracker.py

import time
import cv2

from camera import Camera
from servo import PanTilt
from detector import find_faces

class FaceTracker:
    """
    FaceTracker orchestrates continuous face centering and a 2D sweep search when no face is detected.
    """
    def __init__(self,
                 resolution=(640, 480),
                 dead_x=30,
                 dead_y=30,
                 step_delay=0.05):
        # Camera and servo
        self.cam        = Camera(resolution=resolution)
        self.pt         = PanTilt()
        # Dead-zone in pixels
        self.dead_x     = dead_x
        self.dead_y     = dead_y
        # Delay between servo steps
        self.step_delay = step_delay
        # Sweep state
        self._search_state     = 0  # 0=pan, 1=tilt
        self._pan_dir          = 1  # 1=right, -1=left
        self._tilt_dir         = 1  # 1=down, -1=up
        # Frame dimensions
        self.width, self.height = resolution

    def start(self):
        """Start camera capture."""
        self.cam.start()

    def stop(self):
        """Stop camera and cleanup."""
        self.pt.deinit()
        self.cam.stop()
        cv2.destroyAllWindows()

    def _center_face(self, cx, cy):
        """Nudge pan/tilt until face center is within dead-zone."""
        # Horizontal centering
        while abs(cx - self.width/2) > self.dead_x:
            if cx < self.width/2:
                self.pt.pan_left()
            else:
                self.pt.pan_right()
            time.sleep(self.step_delay)
            frame = self.cam.get_frame()
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = find_faces(gray)
            if not faces:
                return False
            x, y, w, h = max(faces, key=lambda r: r[2]*r[3])
            cx = x + w/2
        # Vertical centering
        while abs(cy - self.height/2) > self.dead_y:
            if cy < self.height/2:
                self.pt.tilt_down()
            else:
                self.pt.tilt_up()
            time.sleep(self.step_delay)
            frame = self.cam.get_frame()
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = find_faces(gray)
            if not faces:
                return False
            x, y, w, h = max(faces, key=lambda r: r[2]*r[3])
            cy = y + h/2
        return True

    def _search_sweep(self):
        """Perform a 2D sweep: pan then tilt when limits reached."""
        if self._search_state == 0:
            # Pan sweep
            if self._pan_dir > 0:
                self.pt.pan_right()
            else:
                self.pt.pan_left()
            # Check limits
            if (self._pan_dir > 0 and self.pt._current_pan >= self.pt._pan_max) or \
               (self._pan_dir < 0 and self.pt._current_pan <= self.pt._pan_min):
                self._pan_dir *= -1
                self._search_state = 1
        else:
            # Tilt sweep
            if self._tilt_dir > 0:
                self.pt.tilt_down()
            else:
                self.pt.tilt_up()
            # Check limits
            if (self._tilt_dir > 0 and self.pt._current_tilt >= self.pt._tilt_max) or \
               (self._tilt_dir < 0 and self.pt._current_tilt <= self.pt._tilt_min):
                self._tilt_dir *= -1
                self._search_state = 0
        time.sleep(self.step_delay)

    def track_forever(self):
        """Main loop: center face if found, else sweep search."""
        try:
            while True:
                frame = self.cam.get_frame()
                gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = find_faces(gray)

                if faces:
                    x, y, w, h = max(faces, key=lambda r: r[2]*r[3])
                    cx, cy = x + w/2, y + h/2
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                    cv2.circle(frame, (int(cx), int(cy)), 4, (0,0,255), -1)
                    self._center_face(cx, cy)
                else:
                    # No face: sweep search
                    self._search_sweep()

                cv2.imshow("FaceTracker", frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
        finally:
            self.stop()


if __name__ == "__main__":
    tracker = FaceTracker(resolution=(640,480))
    tracker.start()
    tracker.track_forever()

 
