"""
tracker.py  –  INIT + TRACK
• Tilt 100‑150°, pan 30‑150°
• Half‑resolution detection for latency
• Dead‑zone is set dynamically from the largest INIT face
"""

import math, time, cv2
from camera   import Camera
from servo    import PanTilt
from detector import find_faces

# ---------- FOV (50° diagonal, 4:3 sensor) ----------
THETA_D=50
THETA_H=2*math.degrees(math.atan(math.tan(math.radians(THETA_D/2))*4/5))
THETA_V=2*math.degrees(math.atan(math.tan(math.radians(THETA_D/2))*3/5))

# ---------- knobs -----------------------------------
SCALE           = 0.5          # 320×240 detector
ALPHA_PAN       = 0.35
ALPHA_TILT      = 0.25
MAX_PAN_DELTA   = 1.0          # ° per frame
MAX_TILT_DELTA  = 0.5
STEP_DELAY      = 0.075
SETTLE_EXTRA    = 0.04
MIN_AREA_RATIO  = 0.1         # 10 % @ half‑res
ASPECT_TOL      = 0.25
INIT_PAN_STEP   = 15
INIT_TILT_STEP  = 10
FONT            = cv2.FONT_HERSHEY_SIMPLEX
# -----------------------------------------------------

class Mode: INIT, TRACK = range(2)
MODE_NAMES = ["INIT","TRACK"]

class FaceTracker:
    def __init__(self, res=(640,480), debug=True):
        self.cam  = Camera(resolution=res)
        self.pt   = PanTilt(step=1.0)
        self.debug= debug
        self.w, self.h = res
        self.deg_px_x, self.deg_px_y = THETA_H/self.w, THETA_V/self.h

        # default dead‑zone (will be overwritten after INIT)
        self.dead_x, self.dead_y = 40, 40
        self.mode = Mode.INIT

    # ---------- helper --------------------------------
    def _centre(self, cx, cy):
        dx, dy = cx - self.w/2, cy - self.h/2
        if abs(dx) < self.dead_x and abs(dy) < self.dead_y:
            return

        goal_pan  = self.pt._current_pan  - dx * self.deg_px_x
        goal_tilt = self.pt._current_tilt - dy * self.deg_px_y

        sp = self.pt._current_pan  + ALPHA_PAN  * (goal_pan  - self.pt._current_pan)
        st = self.pt._current_tilt + ALPHA_TILT * (goal_tilt - self.pt._current_tilt)

        tp = max(self.pt._current_pan -MAX_PAN_DELTA,
                 min(self.pt._current_pan +MAX_PAN_DELTA,  sp))
        tt = max(self.pt._current_tilt-MAX_TILT_DELTA,
                 min(self.pt._current_tilt+MAX_TILT_DELTA, st))

        moved = abs(tp-self.pt._current_pan)>1e-2 or abs(tt-self.pt._current_tilt)>1e-2
        self.pt.set_pan(tp); self.pt.set_tilt(tt)
        if moved: time.sleep(SETTLE_EXTRA)

    # ---------- INIT sweep ----------------------------
    def _initial_scan(self):
        best=0; best_ang=None; best_wh=(0,0)
        for tilt in range(150, 99, -INIT_TILT_STEP):
            self.pt.set_tilt(tilt)
            for pan in range(30, 151, INIT_PAN_STEP):
                self.pt.set_pan(pan); time.sleep(0.08)
                gray=cv2.cvtColor(self.cam.get_frame(),cv2.COLOR_BGR2GRAY)
                small=cv2.resize(gray,(0,0),fx=SCALE,fy=SCALE)
                faces=find_faces(small,min_area_ratio=MIN_AREA_RATIO,
                                       aspect_ratio_tol=ASPECT_TOL)
                if faces:
                    _,_,w,h=faces[0]; area=w*h
                    if area>best:
                        best, best_ang = area, (pan,tilt)
                        best_wh = (int(w/SCALE), int(h/SCALE))  # rescale
        if best_ang:
            self.pt.set_pan(best_ang[0]); self.pt.set_tilt(best_ang[1])
            # ----- dynamic dead‑zone -------------------
            self.dead_x = best_wh[0] // 2
            self.dead_y = best_wh[1] // 2
            if self.debug:
                print(f"[INIT] dead‑zone set to ±{self.dead_x} × ±{self.dead_y} px")
        self.mode = Mode.TRACK

    # ---------- main loop -----------------------------
    def run(self):
        if self.debug: print("[INFO] tracker start")
        self._initial_scan()
        try:
            while True:
                full = self.cam.get_frame()
                gray = cv2.cvtColor(full,cv2.COLOR_BGR2GRAY)
                small=cv2.resize(gray,(0,0),fx=SCALE,fy=SCALE)

                faces=find_faces(small,min_area_ratio=MIN_AREA_RATIO,
                                       aspect_ratio_tol=ASPECT_TOL)
                if faces:
                    x,y,w,h=faces[0]
                    x,y,w,h=[int(v/SCALE) for v in (x,y,w,h)]
                    cx,cy=x+w/2,y+h/2
                    cv2.rectangle(full,(x,y),(x+w,y+h),(0,255,0),2)
                    cv2.circle(full,(int(cx),int(cy)),4,(0,0,255),-1)
                    self._centre(cx,cy)

                if self.debug:
                    cv2.putText(full,MODE_NAMES[self.mode],(10,25),
                                FONT,0.7,(0,255,255),2)
                cv2.imshow("Desktop‑Sitter", full)
                if cv2.waitKey(1)&0xFF in (27, ord('q')): break
                time.sleep(STEP_DELAY)
        finally:
            self.pt.deinit(); self.cam.stop(); cv2.destroyAllWindows()

# -----------------------------------------------------
if __name__=="__main__":
    FaceTracker(debug=True).run()
