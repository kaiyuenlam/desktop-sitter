#!/usr/bin/env python3
import cv2

# --- Setup Camera ---
# Open the default camera (index 0 for the Pi Camera V2.1)
cap = cv2.VideoCapture(0)

# Set the desired frame dimensions.
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# --- Load the LBPCascade classifier ---
# Make sure to place lbpcascade_frontalface.xml inside a folder named 'cascades'
cascade_path = "/home/pi/Desktop/desktop-sitter/cascades/lbpcascade_frontalface.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)

# Check if the cascade file was loaded correctly.
if face_cascade.empty():
    print("Error loading cascade file. Please check the path:", cascade_path)
    exit(1)

print("Press 'q' to quit the program.")

# --- Main Loop for Face Detection ---
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame. Exiting...")
        break

    # Convert the frame to grayscale (LBP works on grayscale images).
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Perform face detection.
    # The scaleFactor determines how much the image size is reduced at each image scale.
    # The minNeighbors parameter specifies how many neighbors each candidate rectangle should have to retain it.
    # Adjust these parameters as needed for your lighting and detection requirements.
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # For every detected face, draw a rectangle on the original frame.
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Display the resulting frame with detected faces.
    cv2.imshow("Face Detection", frame)

    # Break out of the loop if 'q' is pressed.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- Cleanup ---
cap.release()
cv2.destroyAllWindows()
