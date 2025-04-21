#!/usr/bin/env python3
import cv2
import time
from pantilthat import pan, tilt  # Functions to control the pan/tilt hat servos

# --------------------------------------------------------------------
# CONFIGURATION OF SERVO RANGES (ABSOLUTE ANGLES: 0 to 180°)
# Vertical servo (channel 6): 70° = looking up, 150° = looking down
VERT_MIN = 70
VERT_MAX = 150

# Horizontal servo (channel 7): 30° = left, 150° = right
HORZ_MIN = 30
HORZ_MAX = 150

# For the Pan-Tilt HAT functions, angles are expected as "relative" angles in the range -90° to +90°
# Thus, conversion: relative_angle = absolute_angle - 90.

# Set the initial servo positions to the center of the allowed ranges:
current_vert = (VERT_MIN + VERT_MAX) // 2  # For example, (70 + 150) // 2 = 110°
current_horz = (HORZ_MIN + HORZ_MAX) // 2    # For example, (30 + 150) // 2 = 90°

# Set the frame dimensions for the Pi Camera:
FRAME_W = 640
FRAME_H = 480

# --------------------------------------------------------------------
# Initialize the servos on the pan–tilt hat using the relative angle values:
# For the horizontal servo: pan() controls channel 7.
# For the vertical servo: tilt() controls channel 6.
pan(current_horz - 90)   # (e.g. 90 - 90 = 0° => center)
tilt(current_vert - 90)  # (e.g. 110 - 90 = 20°)

# --------------------------------------------------------------------
# Load the cascade classifier for face detection.
# Update the cascade path to point to your cascade XML file if needed.
cascade_path = "cascades/haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)
if face_cascade.empty():
    print("Error: Could not load cascade classifier at", cascade_path)
    exit(1)

# --------------------------------------------------------------------
# Initialize the video capture.
# With the Raspberry Pi Camera (in legacy V4L2 mode), VideoCapture(0) should work.
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
time.sleep(2)  # Allow the camera time to warm up

print("Face tracking started. Press 'q' to quit.")

# Sensitivity factor for servo adjustment (tune this if needed)
sensitivity = 0.1

# --------------------------------------------------------------------
# Main loop for face detection and servo tracking
while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame. Exiting...")
        break

    # For better detection, convert the captured frame to grayscale:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # You can also use histogram equalization if desired:
    # gray = cv2.equalizeHist(gray)

    # Detect faces in the frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # If at least one face is detected, use the first face for tracking:
    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        # Draw a rectangle around the detected face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Calculate the center of the detected face:
        face_center_x = x + w / 2.0
        face_center_y = y + h / 2.0

        # Calculate error (offset) between the face center and the frame center:
        error_x = face_center_x - (FRAME_W / 2.0)
        error_y = face_center_y - (FRAME_H / 2.0)

        # Convert errors into adjustments (delta) for the servos.
        # You may need to tune the sensitivity factor:
        delta_horz = -error_x * sensitivity  # Negative sign: to move horizontally correctly
        delta_vert = error_y * sensitivity

        # Update servo positions (absolute angles), then clamp them to our specified ranges:
        new_horz = current_horz + delta_horz
        new_vert = current_vert + delta_vert

        new_horz = max(HORZ_MIN, min(HORZ_MAX, new_horz))
        new_vert = max(VERT_MIN, min(VERT_MAX, new_vert))

        # Only update if the change is significant (e.g. > 1 degree)
        if abs(new_horz - current_horz) > 1 or abs(new_vert - current_vert) > 1:
            current_horz = new_horz
            current_vert = new_vert
            # Update the servos (convert absolute to relative)
            pan(int(current_horz - 90))   # Horizontal servo update
            tilt(int(current_vert - 90))  # Vertical servo update
            print("Updated servo positions -> Horizontal:", int(current_horz), "Vertical:", int(current_vert))

    # Show the frame with drawn rectangle (for debugging/visual feedback)
    cv2.imshow("Face Tracking", frame)
    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up resources
cap.release()
cv2.destroyAllWindows()
