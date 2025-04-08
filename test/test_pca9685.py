# test/test_pca9685.py
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio
import time

def set_angle(pca, channel, angle):
    # Convert angle to pulse width (µs)
    pulse = 500 + (angle / 180.0) * 2000
    # Convert to 16-bit duty cycle
    duty = int(pulse / 20000 * 0xFFFF)
    pca.channels[channel].duty_cycle = duty

def main():
    # Setup I2C
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50  # Standard servo PWM

    try:
        for ch in range(16):
            print(f"🔁 Sweeping Servo on Channel {ch}")
            for angle in range(0, 181, 60):
                print(f"  → Moving to {angle}°")
                set_angle(pca, ch, angle)
                time.sleep(0.4)
            for angle in range(180, -1, -60):
                print(f"  ← Moving to {angle}°")
                set_angle(pca, ch, angle)
                time.sleep(0.4)
            print(f"✅ Channel {ch} test complete\n")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("🛑 Test interrupted.")

    finally:
        pca.deinit()
        print("PCA9685 shutdown.")

if __name__ == "__main__":
    main()

