#!/usr/bin/env python3
"""
User Tracking Script

This script uses OpenCV to detect a user's face from a USB camera.
It calculates the offset of the detected face from the center of the frame
and adjusts two servos via the PCA9685:
  - Channel 6: Vertical movement
  - Channel 7: Horizontal movement

Servo positions are updated by converting a desired angle (0° to 180°)
to the corresponding 16-bit duty cycle value required by the PCA9685.
"""

import cv2
import time
import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685

# ----------------------------
# Servo Configuration Settings
# ----------------------------

# Define valid angle ranges for the servos (tune these based on your mechanical limits)
HORIZ_MIN, HORIZ_MAX = 30, 150   # Horizontal servo limits (channel 7)
VERT_MIN, VERT_MAX = 30, 150     # Vertical servo limits (channel 6)

# Starting angles (typically the center position)
horiz_angle = 90  # Horizontal servo initial angle (channel 7)
vert_angle = 90   # Vertical servo initial angle (channel 6)

def angle_to_duty(angle):
    """
    Convert a servo angle (0-180) to the corresponding 16-bit duty cycle value.
    The PCA9685 expects a pulse width between about 500µs (0°) and 2500µs (180°)
    over a 20ms period.
    """
    pulse = 500 + (angle / 180.0) * 2000  # in microseconds
    duty = int(pulse / 20000 * 0xFFFF)    # convert to 16-bit value
    return duty

def clamp(value, min_value, max_value):
    """Clamp the value between min_value and max_value."""
    return max(min(value, max_value), min_value)

def main():
    global horiz_angle, vert_angle

    # ----------------------------
    # Initialize PCA9685
    # ----------------------------
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50  # Standard frequency for servos

    # Set initial positions for the servos
    pca.channels[6].duty_cycle = angle_to_duty(vert_angle)
    pca.channels[7].duty_cycle = angle_to_duty(horiz_angle)

    # ----------------------------
    # Initialize OpenCV Face Detector
    # ----------------------------
    face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    if face_cascade.empty():
        print("Error loading cascade classifier from:", face_cascade_path)
        return

    # ----------------------------
    # Open USB Camera
    # ----------------------------
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return
    # Optionally set resolution for faster processing
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    print("User tracking started. Press 'q' to quit.")
    time.sleep(2)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame from camera.")
                break

            # Convert frame to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

            # If a face is detected, handle it
            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                face_center_x = x + w // 2
                face_center_y = y + h // 2

                frame_center_x = frame.shape[1] // 2
                frame_center_y = frame.shape[0] // 2

                # Calculate offsets between face center and frame center
                offset_x = face_center_x - frame_center_x
                offset_y = face_center_y - frame_center_y

                # Simple proportional control: adjust servos based on the offsets

                # Adjust horizontal servo (channel 7)
                if abs(offset_x) > 10:  # dead zone threshold to avoid jitter
                    horiz_angle -= offset_x * 0.05
                    horiz_angle = clamp(horiz_angle, HORIZ_MIN, HORIZ_MAX)
                    pca.channels[7].duty_cycle = angle_to_duty(horiz_angle)

                # Adjust vertical servo (channel 6)
                if abs(offset_y) > 10:
                    # Increase vertical angle to move the camera upward if face is lower in frame
                    vert_angle += offset_y * 0.05
                    vert_angle = clamp(vert_angle, VERT_MIN, VERT_MAX)
                    pca.channels[6].duty_cycle = angle_to_duty(vert_angle)

                # Draw a rectangle around the detected face for visual feedback
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Show the frame with tracking (optional; press 'q' to quit)
            cv2.imshow("User Tracking", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    except KeyboardInterrupt:
        print("Tracking interrupted by the user.")

    finally:
        # Clean up resources
        cap.release()
        cv2.destroyAllWindows()
        pca.deinit()
        print("User tracking stopped, resources released.")

if __name__ == "__main__":
    main()
