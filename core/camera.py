# camera.py

import cv2

class Camera:
    """
    USB camera wrapper using OpenCV.
    Opens a single device index (default 0).
    Supports optional rotation and mirroring.
    """
    def __init__(self,
                 device_index: int = 0,
                 resolution=(640, 480),
                 rotation: int = 0,
                 hflip: bool = False,
                 vflip: bool = False):
        """
        :param device_index: index for cv2.VideoCapture (e.g. 0)
        :param resolution: (width, height)
        :param rotation: degrees, one of {0, 90, 180, 270}, default 0 (no rotation)
        :param hflip: mirror left↔right, default False
        :param vflip: mirror top↔bottom, default False
        """
        self.cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera at index {device_index}")

        width, height = resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.rotation = rotation
        self.hflip   = hflip
        self.vflip   = vflip

    def start(self):
        """No-op for USB camera (already opened)."""
        pass

    def get_frame(self):
        """
        Capture a frame, apply optional rotation/flips, and return a BGR image.
        :return: uint8 NumPy array, shape (H, W, 3)
        """
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("Failed to read frame from USB camera")

        # Apply rotation if requested
        if self.rotation == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif self.rotation == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Apply flips if requested
        if self.hflip:
            frame = cv2.flip(frame, 1)
        if self.vflip:
            frame = cv2.flip(frame, 0)

        return frame

    def stop(self):
        """Release the camera device."""
        if self.cap and self.cap.isOpened():
            self.cap.release()


if __name__ == "__main__":
    # USB camera test harness at index 0
    cam = Camera(
        device_index=0,
        resolution=(640, 480),
        rotation=0,   # no rotation
        hflip=False,
        vflip=False
    )
    print("[INFO] Press 'q' to quit")
    while True:
        frame = cam.get_frame()
        cv2.imshow("USB Camera Test", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
            break
    cam.stop()
    cv2.destroyAllWindows()
