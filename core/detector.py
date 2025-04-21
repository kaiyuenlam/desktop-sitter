# detector.py

import cv2
import numpy as np

_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
_cascade = cv2.CascadeClassifier(_CASCADE_PATH)
if _cascade.empty():
    raise RuntimeError(f"Failed to load Haar cascade at {_CASCADE_PATH}")


def find_faces(
    gray_img,
    scaleFactor: float = 1.1,
    minNeighbors: int = 5,
    minSize: tuple = (30, 30),
    flags: int = cv2.CASCADE_SCALE_IMAGE,
    *,
    min_area_ratio: float = 0.02,
    aspect_ratio_tol: float = 0.25,
):
    """
    Detect faces with extra post‑filters to reduce noise.

    Parameters
    ----------
    gray_img : uint8 ndarray
        Single‑channel (grayscale) image.
    scaleFactor, minNeighbors, minSize, flags
        Same as cv2.CascadeClassifier.detectMultiScale.
    min_area_ratio : float, optional
        Reject faces with area < (ratio × frame area). 0.02 = 2 %.
    aspect_ratio_tol : float, optional
        Accept faces whose width/height is within
        [1 ‑ tol, 1 + tol]. Default 0.25 keeps 0.75–1.25.
    Returns
    -------
    list[(x, y, w, h)]  largest‑first
    """
    faces = _cascade.detectMultiScale(
        gray_img,
        scaleFactor=scaleFactor,
        minNeighbors=minNeighbors,
        minSize=minSize,
        flags=flags,
    )

    if len(faces) == 0:
        return []

    frame_area = gray_img.shape[0] * gray_img.shape[1]
    min_area = frame_area * min_area_ratio
    min_ar, max_ar = 1.0 - aspect_ratio_tol, 1.0 + aspect_ratio_tol

    filtered = []
    for (x, y, w, h) in faces:
        area = w * h
        ar = w / h if h else 0
        if area < min_area:
            continue
        if not (min_ar <= ar <= max_ar):
            continue
        filtered.append((x, y, w, h))

    # largest faces first
    filtered.sort(key=lambda r: r[2] * r[3], reverse=True)
    return filtered


