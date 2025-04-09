#!/usr/bin/env python3
"""
Face Tracking with Servo Control (Updated Horizontal Inversion)

This script uses OpenCV’s Haar cascade classifier to detect a face 
and adjusts two servos via the PCA9685 to keep the face centered.
Configuration:
  - Vertical servo on channel 6: Range 70° (down) to 150° (up).
    Default center is 110°.
  - Horizontal servo on channel 7: Range 30° (left) to 150° (right).
    Default center is 90°.
    
Control Adjustments:
  - For vertical servo: if face is above center (offset_y negative), 
    we subtract offset_y so that the vertical angle increases (looking up).
  - For horizontal servo: now the logic is inverted. If the face is to the 
    right (offset_x positive), we decrease the horizontal angle to turn right.
    
A proportional controller is used for both servos.
"""

import cv2
import time
import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685

# --- Servo Configuration ---
# Horizontal servo (channel 7): range from 30° (left) to 150° (right)
HORIZ_MIN = 30
HORIZ_MAX = 150
# Vertical servo (channel 6): range from 70° (down) to 150° (up)
VERT_MIN = 70
VERT_MAX = 150

# Control factors (adjust these to tune responsiveness)
# For horizontal servo, we now subtract the offset to invert direction.
HORIZ_FACTOR = 0.01   # horizontal adjustment (degrees per pixel)
VERT_FACTOR  = 0.01   # vertical adjustment (degrees per pixel)

# Default initial angles (calculated midpoints)
default_horiz_angle = (HORIZ_MIN + HORIZ_MAX) // 2  # (30 + 150) / 2 = 90°
default_vert_angle = (VERT_MIN + VERT_MAX) // 2       # (70 + 150) / 2 = 110°

def angle_to_duty(angle):
    """
    Convert an angle (0° to 180°) to a 16-bit PWM duty cycle value.
    Standard servos usually need ~500µs for 0° and ~2500µs for 180°,
    given a 20ms period.
    """
    pulse = 500 + (angle / 180.0) * 2000  # pulse width in microseconds
    duty = int(pulse / 20000 * 0xFFFF)    # convert to a 16-bit duty cycle value
    return duty

def clamp(value, min_value, max_value):
    """Clamp the value to lie between min_value and max_value."""
    return max(min(value, max_value), min_value)

def main():
    # Set initial servo angles
    horiz_angle = default_horiz_angle  # horizontal servo on channel 7 (initial: 90°)
    vert_angle = default_vert_angle    # vertical servo on channel 6 (initial: 110°)

    # Initialize I2C and PCA9685
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50  # Standard frequency for servos

    # Set initial servo positions
    pca.channels[7].duty_cycle = angle_to_duty(horiz_angle)
    pca.channels[6].duty_cycle = angle_to_duty(vert_angle)

    # Open the USB camera (set resolution to 640x480)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print("Error: Unable to open camera")
        return

    # Load the Haar cascade for face detection
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print("Error: Failed to load Haar cascade from", cascade_path)
        return

    print("Face tracking with servo started. Press 'q' to quit.")
    time.sleep(2)  # Allow time for the camera to adjust

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame")
                break

            # Convert the frame to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

            if len(faces) > 0:
		# Use the first detected face
                (x, y, w, h) = faces[0]
                face_center_x = x + w // 2
                face_center_y = y + h // 2

                # Compute frame center
                frame_center_x = frame.shape[1] // 2
                frame_center_y = frame.shape[0] // 2

                # Calculate offsets
                offset_x = face_center_x - frame_center_x
                offset_y = face_center_y - frame_center_y

                # Adjust horizontal servo (channel 7)
                # If face is to the right (offset_x positive), decrease the angle (turn right).
                if abs(offset_x) > 10:  # apply deadzone threshold to avoid jitter
                    horiz_angle -= offset_x * HORIZ_FACTOR
                    horiz_angle = clamp(horiz_angle, HORIZ_MIN, HORIZ_MAX)
                    pca.channels[7].duty_cycle = angle_to_duty(horiz_angle)

                # Adjust vertical servo (channel 6)
                # If face is above center (offset_y negative), then increase the angle to look up.
                if abs(offset_y) > 10:
                    vert_angle -= offset_y * VERT_FACTOR
                    vert_angle = clamp(vert_angle, VERT_MIN, VERT_MAX)
                    pca.channels[6].duty_cycle = angle_to_duty(vert_angle)

                # Draw a rectangle around the detected face and display its center coordinates
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, f"({face_center_x}, {face_center_y})", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Show the frame for visual feedback
            cv2.imshow("Face Tracking with Servo", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Tracking interrupted by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        pca.deinit()
        print("Face tracking stopped; servos released.")

if __name__ == "__main__":
    main()
