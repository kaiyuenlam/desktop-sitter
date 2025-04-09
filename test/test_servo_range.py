#!/usr/bin/env python3
"""
Servo Range Test

This script tests the movement range of servos connected to a PCA9685.
It will sweep the servo on a specified channel from a minimum
to a maximum angle and then back to the minimum. In our setup:
  - Channel 6: Vertical servo
  - Channel 7: Horizontal servo

Adjust the min/max values, step size, and delay as needed.
"""

import time
import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685

def angle_to_duty(angle):
    """
    Convert an angle (0–180 degrees) into a 16-bit duty cycle value.
    Typically, 0° corresponds to about 500µs pulse and 180° to 2500µs
    (with a 20ms period).
    """
    pulse = 500 + (angle / 180.0) * 2000  # pulse in microseconds
    duty = int(pulse / 20000 * 0xFFFF)    # convert to 16-bit value
    return duty

def sweep_servo(pca, channel, min_angle, max_angle, step=10, delay=0.5):
    """
    Sweep the servo on `channel` from `min_angle` to `max_angle` and back,
    printing the angle and corresponding duty cycle.
    """
    print(f"Sweeping servo on channel {channel} from {min_angle}° to {max_angle}°")
    # Sweep up (min -> max)
    for angle in range(min_angle, max_angle + 1, step):
        duty = angle_to_duty(angle)
        pca.channels[channel].duty_cycle = duty
        print(f"Channel {channel}: {angle}° (duty cycle: {duty})")
        time.sleep(delay)
    # Sweep down (max -> min)
    print(f"Sweeping servo on channel {channel} back from {max_angle}° to {min_angle}°")
    for angle in range(max_angle, min_angle - 1, -step):
        duty = angle_to_duty(angle)
        pca.channels[channel].duty_cycle = duty
        print(f"Channel {channel}: {angle}° (duty cycle: {duty})")
        time.sleep(delay)

def main():
    # Initialize I2C and the PCA9685
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50  # 50 Hz is standard for servos

    # Define servo settings (adjust these values according to your hardware limits)
    servo_settings = [
        {"channel": 6, "min": 30, "max": 150},  # Vertical servo
        {"channel": 7, "min": 30, "max": 150},  # Horizontal servo
    ]

    try:
        for setting in servo_settings:
            channel = setting["channel"]
            min_angle = setting["min"]
            max_angle = setting["max"]

            # Set initial position (midpoint)
            mid_angle = (min_angle + max_angle) // 2
            pca.channels[channel].duty_cycle = angle_to_duty(mid_angle)
            time.sleep(0.5)

            # Perform the sweep test for this servo
            sweep_servo(pca, channel, min_angle, max_angle)

            # Pause between servo tests
            time.sleep(1)

    except KeyboardInterrupt:
        print("Servo test interrupted by the user.")
    finally:
        # Shutdown PCA9685 cleanly
        pca.deinit()
        print("Servo range test complete, PCA9685 shutdown.")

if __name__ == "__main__":
    main()
