# servo.py

import time
import board
import busio
from adafruit_pca9685 import PCA9685

def angle_to_duty(angle: float,
                  min_pulse_us: float = 1000,
                  max_pulse_us: float = 2000,
                  freq: float = 50) -> int:
    """
    Convert an angle (0–180°) into a 16‑bit PCA9685 duty cycle.
    """
    # clamp
    angle = max(0.0, min(180.0, angle))
    pulse_range = max_pulse_us - min_pulse_us
    pulse = min_pulse_us + (angle / 180.0) * pulse_range
    period = 1_000_000.0 / freq
    return int((pulse / period) * 0xFFFF)

class PanTilt:
    """
    Pan/Tilt head controller using PCA9685:
      - pan servo   on channel 7, valid angles [30,150]
      - tilt servo  on channel 6, valid angles [70,150]
    
    New vertical setup: 
      • angle=70 → camera looks DOWN
      • angle=150 → camera looks UP
    """

    def __init__(self,
                 pan_ch: int = 7,
                 tilt_ch: int = 6,
                 pan_range: tuple = (30, 150),
                 tilt_range: tuple = (70, 150),
                 step: float = 5.0,
                 freq: float = 50):
        # init I2C & PCA9685
        i2c = busio.I2C(board.SCL, board.SDA)
        self._pca = PCA9685(i2c)
        self._pca.frequency = freq

        # channels & ranges
        self._pan_ch   = pan_ch
        self._tilt_ch  = tilt_ch
        self._pan_min,   self._pan_max   = pan_range
        self._tilt_min,  self._tilt_max  = tilt_range

        self._step = step

        # start centered
        self._current_pan  = (self._pan_min + self._pan_max) / 2.0
        self._current_tilt = (self._tilt_min + self._tilt_max) / 2.0
        self._apply()

    def _apply(self):
        """Write the current angles to the servos."""
        # pan
        duty = angle_to_duty(self._current_pan, freq=self._pca.frequency)
        self._pca.channels[self._pan_ch].duty_cycle = duty
        # tilt
        duty = angle_to_duty(self._current_tilt, freq=self._pca.frequency)
        self._pca.channels[self._tilt_ch].duty_cycle = duty

    # Pan controls (unchanged)
    def pan_left(self):
        self._current_pan = max(self._pan_min, self._current_pan - self._step)
        self._apply()

    def pan_right(self):
        self._current_pan = min(self._pan_max, self._current_pan + self._step)
        self._apply()

    # Tilt controls (inverted for new camera orientation)
    def tilt_up(self):
        """Tilt camera UP: increase angle toward tilt_max (150°)."""
        self._current_tilt = min(self._tilt_max, self._current_tilt + self._step)
        self._apply()

    def tilt_down(self):
        """Tilt camera DOWN: decrease angle toward tilt_min (70°)."""
        self._current_tilt = max(self._tilt_min, self._current_tilt - self._step)
        self._apply()

    # Direct setters, if needed
    def set_pan(self, angle: float):
        self._current_pan = max(self._pan_min, min(self._pan_max, angle))
        self._apply()

    def set_tilt(self, angle: float):
        self._current_tilt = max(self._tilt_min, min(self._tilt_max, angle))
        self._apply()

    def deinit(self):
        """Disable PCA9685 cleanly."""
        self._pca.deinit()


if __name__ == "__main__":
    # Quick test harness for your USB‑camera mount
    pt = PanTilt(step=10)
    try:
        print("Sweeping pan/tilt. Ctrl‑C to stop.")
        while True:
            # pan left→right
            pt.pan_left();  time.sleep(0.2)
            pt.pan_right(); time.sleep(0.2)
            # tilt down→up
            pt.tilt_down(); time.sleep(0.2)
            pt.tilt_up();   time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        pt.deinit()
        print("Done.")
