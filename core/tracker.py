"""
tracker.py – Face tracking module with automatic reinitialization on lost face

Provides:
- Continuous pan/tilt face tracking
- Automatic INIT sweep if no face detected for a timeout
- Optional GUI display for debugging
- Optional frame callback for integration
"""
import math, time, cv2
from camera import Camera
from servo import PanTilt
from detector import find_faces

# ---------- FOV (50° diagonal, 4:3 sensor) ----------
THETA_D = 50
THETA_H = 2 * math.degrees(math.atan(math.tan(math.radians(THETA_D/2)) * 4/5))
THETA_V = 2 * math.degrees(math.atan(math.tan(math.radians(THETA_D/2)) * 3/5))

# ---------- knobs -----------------------------------
SCALE             = 0.5   # 320×240 detector
ALPHA_PAN         = 0.35
ALPHA_TILT        = 0.25
MAX_PAN_DELTA     = 1.0   # ° per frame
MAX_TILT_DELTA    = 0.5
STEP_DELAY        = 0.075
SETTLE_EXTRA      = 0.04
MIN_AREA_RATIO    = 0.1   # 10 % @ half-res
ASPECT_TOL        = 0.25
INIT_PAN_STEP     = 15
INIT_TILT_STEP    = 10
FONT              = cv2.FONT_HERSHEY_SIMPLEX
TIMEOUT_NO_FACE   = 30.0  # seconds without face → reinit
# -----------------------------------------------------

class Mode:
    INIT, TRACK = range(2)
MODE_NAMES = ["INIT", "TRACK"]

class FaceTracker:
    def __init__(
        self,
        device_index: int = 0,
        res=(320, 240),
        debug=True,
        headless=False,
        frame_callback=None
    ):
        """
        headless: skip GUI if True
        frame_callback: function(frame) for external use
        """
        self.cam = Camera(device_index=device_index, resolution=res)
        self.pt = PanTilt(step=1.0)
        self.debug = debug
        self.headless = headless
        self.frame_callback = frame_callback

        self.w, self.h = res
        self.deg_px_x = THETA_H / self.w
        self.deg_px_y = THETA_V / self.h
        
        self.show_window = False

        # dynamic dead-zone
        self.dead_x = 40
        self.dead_y = 40
        self.mode = Mode.INIT

        # timeout tracking
        self.last_face_time = time.time()
        
        # FPS
        self._prev_t = time.time()
        self._fps = 0.0
        self._avg_n = 10
        self._frame_no = 0
        
    def enable_debug_window(self, enable: bool):
        self.show_window = enable

    def _centre(self, cx, cy):
        dx = cx - self.w/2
        dy = cy - self.h/2
        if abs(dx) < self.dead_x and abs(dy) < self.dead_y:
            return
        goal_pan  = self.pt._current_pan  - dx * self.deg_px_x
        goal_tilt = self.pt._current_tilt - dy * self.deg_px_y

        sp = self.pt._current_pan  + ALPHA_PAN  * (goal_pan  - self.pt._current_pan)
        st = self.pt._current_tilt + ALPHA_TILT * (goal_tilt - self.pt._current_tilt)

        tp = max(self.pt._current_pan - MAX_PAN_DELTA, min(self.pt._current_pan + MAX_PAN_DELTA, sp))
        tt = max(self.pt._current_tilt - MAX_TILT_DELTA, min(self.pt._current_tilt + MAX_TILT_DELTA, st))

        moved = abs(tp - self.pt._current_pan) > 1e-2 or abs(tt - self.pt._current_tilt) > 1e-2
        self.pt.set_pan(tp)
        self.pt.set_tilt(tt)
        if moved:
            time.sleep(SETTLE_EXTRA)

    def _initial_scan(self):
        best = 0
        best_ang = None
        best_wh = (0, 0)
        for tilt in range(150, 99, -INIT_TILT_STEP):
            self.pt.set_tilt(tilt)
            for pan in range(30, 151, INIT_PAN_STEP):
                self.pt.set_pan(pan)
                time.sleep(0.08)
                gray = cv2.cvtColor(self.cam.get_frame(), cv2.COLOR_BGR2GRAY)
                small = cv2.resize(gray, (0,0), fx=SCALE, fy=SCALE)
                faces = find_faces(small, min_area_ratio=MIN_AREA_RATIO, aspect_ratio_tol=ASPECT_TOL)
                if faces:
                    _,_,w,h = faces[0]
                    area = w*h
                    if area > best:
                        best = area
                        best_ang = (pan, tilt)
                        best_wh = (int(w/SCALE), int(h/SCALE))
        if best_ang:
            self.pt.set_pan(best_ang[0])
            self.pt.set_tilt(best_ang[1])
            self.dead_x = best_wh[0] // 2
            self.dead_y = best_wh[1] // 2
            if self.debug:
                print(f"[INIT] dead-zone ±{self.dead_x}×±{self.dead_y} px")
        self.mode = Mode.TRACK
        self.last_face_time = time.time()

    def run(self):
        if self.debug:
            print("[INFO] tracker start")
        self._initial_scan()
        try:
            while True:
                tic = time.time()
                frame = self.cam.get_frame()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                small = cv2.resize(gray, (0,0), fx=SCALE, fy=SCALE)
                faces = find_faces(small, min_area_ratio=MIN_AREA_RATIO, aspect_ratio_tol=ASPECT_TOL)

                if faces:
                    x,y,w,h = faces[0]
                    x,y,w,h = [int(v/SCALE) for v in (x,y,w,h)]
                    cx,cy = x + w/2, y + h/2
                    cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
                    cv2.circle(frame, (int(cx),int(cy)), 4, (0,0,255), -1)
                    self._centre(cx, cy)
                    self.last_face_time = time.time()
                else:
                    # no face: check timeout
                    if time.time() - self.last_face_time > TIMEOUT_NO_FACE:
                        if self.debug:
                            print("[INFO] No face for 30s, reinitializing scan...")
                        self._initial_scan()

                # callback integration
                if self.frame_callback:
                    self.frame_callback(frame)

                # optional GUI
                if not self.headless:
                    if self.debug:
                        cv2.putText(frame, MODE_NAMES[self.mode], (10,25), FONT, 0.7, (0,255,255), 2)
                        cv2.putText(frame, f'FPS: {self._fps:4.1f}', (10, 50), FONT, 0.7, (0,255,0), 2)
                    cv2.imshow("Tracker Debug", frame)
                    if cv2.waitKey(1) & 0xFF in (27, ord('q')):
                        break
                    
                if self.show_window:
                    cv2.putText(frame, MODE_NAMES[self.mode], (10,25), FONT, 0.7, (0,255,255), 2)
                    cv2.putText(frame, f'FPS: {self._fps:4.1f}', (10, 50), FONT, 0.7, (0,255,0), 2)
                    cv2.imshow("Camera Debug", frame)
                    if cv2.waitKey(1) & 0xFF in (27, ord('q')):
                        break
                
                toc = time.time()
                self._frame_no += 1
                inst = 1.0 / max(toc - tic, 1e-6)
                w = 1.0 / self._avg_n
                self._fps = (1 - w) * self._fps + w * inst
                
                time.sleep(STEP_DELAY)
        finally:
            self.pt.deinit()
            self.cam.stop()
            if not self.headless:
                cv2.destroyAllWindows()


if __name__ == "__main__":
    FaceTracker(
        device_index=0,
        debug=True,
        headless=False,
        frame_callback=None
    ).run()
