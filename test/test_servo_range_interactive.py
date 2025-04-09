#!/usr/bin/env python3
"""
Interactive Servo Range Test

This script allows you to input parameters to test the moving range of a servo.
It uses the PCA9685 to control the servo. You will be prompted to enter:
  - Servo channel number (e.g., 6)
  - Minimum angle (default: 30°)
  - Maximum angle (default: 150°)
  - Step size (default: 10°)
  - Delay between steps in seconds (default: 0.5 seconds)

The script then sweeps the servo from the minimum angle to the maximum angle and then back.
"""

import time
import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685

def angle_to_duty(angle):
    """
    Convert an angle (0-180°) to a 16-bit duty cycle value for the PCA9685.
    Typically, 0° corresponds to ~500µs pulse and 180° to ~2500µs pulse,
    using a 20ms period.
    """
    pulse = 500 + (angle / 180.0) * 2000  # pulse width in microseconds
    duty = int(pulse / 20000 * 0xFFFF)    # convert to a 16-bit value
    return duty

def clamp(value, min_value, max_value):
    """Clamp the value between min_value and max_value."""
    return max(min(value, max_value), min_value)

def sweep_servo(pca, channel, min_angle, max_angle, step, delay):
    """
    Sweep the servo on the specified channel from min_angle to max_angle and back,
    printing each angle and its corresponding duty cycle.
    """
    print(f"Sweeping servo on channel {channel} from {min_angle}° to {max_angle}°")
    # Sweep upward from min_angle to max_angle
    for angle in range(min_angle, max_angle + 1, step):
        duty = angle_to_duty(angle)
        pca.channels[channel].duty_cycle = duty
        print(f"Channel {channel}: {angle}° (duty cycle: {duty})")
        time.sleep(delay)
    print(f"Sweeping servo on channel {channel} back from {max_angle}° to {min_angle}°")
    # Sweep downward from max_angle to min_angle
    for angle in range(max_angle, min_angle - 1, -step):
        duty = angle_to_duty(angle)
        pca.channels[channel].duty_cycle = duty
        print(f"Channel {channel}: {angle}° (duty cycle: {duty})")
        time.sleep(delay)

def main():
    # Initialize I2C and the PCA9685 controller
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50  # Standard frequency for servos

    print("Interactive Servo Range Test")
    
    try:
        # Prompt user for parameters with defaults if input is blank.
        ch_input = input("Enter servo channel number (e.g., 6): ").strip()
        channel = int(ch_input) if ch_input else 6

        min_input = input("Enter minimum angle (default 30): ").strip()
        min_angle = int(min_input) if min_input else 30

        max_input = input("Enter maximum angle (default 150): ").strip()
        max_angle = int(max_input) if max_input else 150

        step_input = input("Enter step size (default 10): ").strip()
        step = int(step_input) if step_input else 10

        delay_input = input("Enter delay in seconds between steps (default 0.5): ").strip()
        delay = float(delay_input) if delay_input else 0.5

        # Set initial servo position to the midpoint
        mid_angle = (min_angle + max_angle) // 2
        pca.channels[channel].duty_cycle = angle_to_duty(mid_angle)
        print(f"Setting servo on channel {channel} to midpoint {mid_angle}°")
        time.sleep(1)

        # Perform the sweep test
        sweep_servo(pca, channel, min_angle, max_angle, step, delay)

    except KeyboardInterrupt:
        print("Servo range test interrupted by the user.")
    except Exception as e:
        print("Error:", e)
    finally:
        pca.deinit()
        print("Test complete. PCA9685 deinitialized.")

if __name__ == "__main__":
    main()
