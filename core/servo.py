"""
servo.py  –  Pan‑tilt driver (PCA9685)

Mapping
  • Channel 7  (pan)  : 30 ° = right ... 150 ° = left
  • Channel 6  (tilt) : 100 ° = level ... 150 ° = up
"""

import busio, board, time
from adafruit_pca9685 import PCA9685

def angle_to_duty(angle, freq=50, min_us=1000, max_us=2000):
    angle = max(0, min(180, angle))
    us = min_us + (angle/180)*(max_us-min_us)
    return int(us / (1_000_000/freq) * 0xFFFF)

class PanTilt:
    def __init__(self,
                 pan_ch=7, tilt_ch=6,
                 pan_rng=(30,150), tilt_rng=(100,150),
                 step=1.0, freq=50):
        self._pan_ch, self._tilt_ch = pan_ch, tilt_ch
        self._pan_min, self._pan_max = pan_rng
        self._tilt_min, self._tilt_max = tilt_rng
        self._step = step

        self._pca = PCA9685(busio.I2C(board.SCL, board.SDA))
        self._pca.frequency = freq

        self._current_pan  = (self._pan_min + self._pan_max)/2
        self._current_tilt = (self._tilt_min+ self._tilt_max)/2
        self._apply()

    # ------------ I/O helpers ----------
    def _apply(self):
        self._pca.channels[self._pan_ch ].duty_cycle = angle_to_duty(self._current_pan)
        self._pca.channels[self._tilt_ch].duty_cycle = angle_to_duty(self._current_tilt)

    # ------------ absolute -------------
    def set_pan(self, a):  self._current_pan  = max(self._pan_min,  min(self._pan_max,  a)); self._apply()
    def set_tilt(self,a):  self._current_tilt = max(self._tilt_min, min(self._tilt_max, a)); self._apply()

    # ------------ relative (1 ° default) ----------
    def pan_left (self, s=None): self.set_pan (self._current_pan + (s or self._step))
    def pan_right(self, s=None): self.set_pan (self._current_pan - (s or self._step))
    def tilt_up  (self, s=None): self.set_tilt(self._current_tilt+ (s or self._step))
    def tilt_down(self, s=None): self.set_tilt(self._current_tilt- (s or self._step))

    # ------------ cleanup -------------
    def deinit(self): self._pca.deinit()

