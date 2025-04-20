# detector.py

import cv2

# Path to OpenCV’s bundled frontal‑face Haar cascade
_CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

# Load the classifier once at import time
face_cascade = cv2.CascadeClassifier(_CASCADE_PATH)
if face_cascade.empty():
    raise RuntimeError(f"Failed to load Haar cascade from {_CASCADE_PATH}")

def find_faces(gray_img,
               scaleFactor: float = 1.1,
               minNeighbors: int  = 5,
               minSize: tuple     = (30, 30),
               # combine the flags you wanted:
               flags: int         = (
                   cv2.CASCADE_SCALE_IMAGE
                 | cv2.CASCADE_FIND_BIGGEST_OBJECT
                 | cv2.CASCADE_DO_ROUGH_SEARCH
               )
              ):
    """
    Detect faces in a grayscale image.

    :param gray_img: 8‑bit, single‑channel image (numpy array)
    :param scaleFactor: image pyramid scale factor
    :param minNeighbors: how many neighbors each candidate rectangle should have
    :param minSize: minimum possible face size (w,h) in pixels
    :param flags: detection flags (you can remove FIND_BIGGEST_OBJECT if you
                  want multiple faces)
    :return: list of (x, y, w, h) tuples
    """
    faces = face_cascade.detectMultiScale(
        gray_img,
        scaleFactor=scaleFactor,
        minNeighbors=minNeighbors,
        flags=flags,
        minSize=minSize
    )
    return faces.tolist() if hasattr(faces, 'tolist') else list(faces)
