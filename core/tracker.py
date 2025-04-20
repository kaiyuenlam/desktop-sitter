"""
tracker.py  –  smooth Desktop‑Sitter face‑tracking loop
-------------------------------------------------------

Modes
  INIT   : start‑up coarse sweep, lock largest face
  TRACK  : face visible  – smooth absolute‑angle centring
  HOLD   : lost <10 s    – stay still
  MICRO  : lost 10‑60 s  – ±15°/±10° local grid
  SWEEP  : lost ≥60 s    – full pan sweep, tilt 150↔100°

"""

import math, time, cv2
from camera   import Camera
from servo    import PanTilt
from detector import find_faces

# ---------- FOV constants (50° diagonal) ----------
THETA_D=50
THETA_H=2*math.degrees(math.atan(math.tan(math.radians(THETA_D/2))*4/5))
THETA_V=2*math.degrees(math.atan(math.tan(math.radians(THETA_D/2))*3/5))

# ---------- behaviour knobs -----------------------
DEAD_X,DEAD_Y =40,40
ALPHA =0.35
STEP_DELAY   =0.075
SETTLE_EXTRA =0.04
MAX_DELTA    =1.0          # 1 °/frame
MICRO_AFTER  =10.0
FULL_AFTER   =60.0
NOISE_RATIO  =0.5
LOCAL_PAN_RANGE,LOCAL_TILT_RANGE=15,10
LOCAL_STEP   =1            # MICRO moves 1 °
SEARCH_TILT_MIN=100
FONT=cv2.FONT_HERSHEY_SIMPLEX

class Mode: INIT,TRACK,HOLD,MICRO,SWEEP=range(5)
MODE_NAMES=["INIT","TRACK","HOLD","MICRO","SWEEP"]

class FaceTracker:
    def __init__(self,res=(640,480),debug=True):
        self.cam, self.pt = Camera(resolution=res), PanTilt()
        self.debug=debug
        self.w,self.h=res
        self.deg_px_x, self.deg_px_y = THETA_H/self.w, THETA_V/self.h
        self.mode=Mode.INIT; self.last_seen=0
        self.last_pan,self.last_tilt=self.pt._current_pan,self.pt._current_tilt
        self.last_area=None; self._pan_dir,self._tilt_dir=-1,1; self._micro_iter=iter(())

    # ------------- utilities ----------
    def _log(self,m): print(m) if self.debug else None
    @property
    def _pan(self):  return self.pt._current_pan
    @property
    def _tilt(self): return self.pt._current_tilt

    # ------------- centring -----------
    def _centre(self,cx,cy):
        dx,dy=cx-self.w/2,cy-self.h/2
        raw_pan  = self._pan  - dx*self.deg_px_x       # 30°→150°
        raw_tilt = self._tilt - dy*self.deg_px_y       # 100°→150°

        sp = self._pan  + ALPHA*(raw_pan -self._pan)
        st = self._tilt + ALPHA*(raw_tilt-self._tilt)

        tp = max(self._pan- MAX_DELTA, min(self._pan+ MAX_DELTA, sp))
        tt = max(self._tilt-MAX_DELTA, min(self._tilt+MAX_DELTA, st))

        moved= abs(tp-self._pan)>1e-2 or abs(tt-self._tilt)>1e-2
        self.pt.set_pan(tp); self.pt.set_tilt(tt)
        if moved: time.sleep(SETTLE_EXTRA)
        self.last_pan,self.last_tilt=self._pan,self._tilt

    # ------------- MICRO grid ---------
    def _init_micro(self):
        pans  = range(int(max(30 ,self.last_pan-LOCAL_PAN_RANGE)),
                      int(min(150,self.last_pan+LOCAL_PAN_RANGE))+1, LOCAL_STEP)
        tilts = range(int(max(SEARCH_TILT_MIN,self.last_tilt-LOCAL_TILT_RANGE)),
                      int(min(150,             self.last_tilt+LOCAL_TILT_RANGE))+1, LOCAL_STEP)
        order=[(p,t) for p in pans for t in tilts]
        self._micro_iter=iter(order)

    def _micro_step(self):
        try:
            p,t=next(self._micro_iter)
            self.pt.set_pan(p); self.pt.set_tilt(t)
        except StopIteration: self.mode=Mode.SWEEP
        time.sleep(STEP_DELAY)

    # ------------- SWEEP --------------
    def _tilt_bounce(self):
        if self._tilt_dir>0:
            if self._tilt-1>=SEARCH_TILT_MIN: self.pt.tilt_down()
            else: self._tilt_dir=-1
        else:
            if self._tilt+1<=150: self.pt.tilt_up()
            else: self._tilt_dir=1

    def _sweep_step(self):
        if self._pan_dir<0:
            self.pt.pan_left()
            if self._pan>=150: self._pan_dir=1; self._tilt_bounce()
        else:
            self.pt.pan_right()
            if self._pan<=30:  self._pan_dir=-1; self._tilt_bounce()
        time.sleep(STEP_DELAY)

    # ------------- initial scan -------
    def _initial_scan(self):
        best=0; best_ang=None
        for tilt in range(150, SEARCH_TILT_MIN-1,-10):
            self.pt.set_tilt(tilt)
            for pan in range(30,151,15):
                self.pt.set_pan(pan); time.sleep(0.1)
                gray=cv2.cvtColor(self.cam.get_frame(),cv2.COLOR_BGR2GRAY)
                faces=find_faces(gray)
                if faces:
                    _,_,w,h=max(faces,key=lambda r:r[2]*r[3]); area=w*h
                    if area>best: best,best_ang=area,(pan,tilt)
        if best_ang:
            self.pt.set_pan(best_ang[0]); self.pt.set_tilt(best_ang[1])
            self.last_pan,self.last_tilt=best_ang
            self.last_seen=time.time(); self.mode=Mode.TRACK
        else: self.mode=Mode.SWEEP

    # ------------- main loop ----------
    def run(self):
        self._log("[INFO] tracker start"); self._initial_scan()
        try:
            while True:
                frame=self.cam.get_frame(); gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
                faces=find_faces(gray)

                ok=False
                if faces:
                    x,y,w,h=max(faces,key=lambda r:r[2]*r[3]); area=w*h
                    if self.last_area is None or area>=NOISE_RATIO*self.last_area:
                        ok=True; self.last_area=area; cx,cy=x+w/2,y+h/2
                        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                        cv2.circle(frame,(int(cx),int(cy)),4,(0,0,255),-1)

                if ok:
                    self.mode=Mode.TRACK; self.last_seen=time.time(); self._centre(cx,cy)
                else:
                    dt=time.time()-self.last_seen
                    if dt<MICRO_AFTER: self.mode=Mode.HOLD
                    elif dt<FULL_AFTER:
                        if self.mode!=Mode.MICRO: self._init_micro()
                        self.mode=Mode.MICRO
                    else: self.mode=Mode.SWEEP

                    if self.mode==Mode.MICRO: self._micro_step()
                    elif self.mode==Mode.SWEEP: self._sweep_step()

                cv2.putText(frame, MODE_NAMES[self.mode],(10,25),FONT,0.7,(0,255,255),2)
                cv2.imshow("Desktop‑Sitter", frame)
                if cv2.waitKey(1)&0xFF in (27, ord('q')): break
        finally:
            self.pt.deinit(); self.cam.stop(); cv2.destroyAllWindows()

if __name__=="__main__":
    FaceTracker(debug=True).run()
