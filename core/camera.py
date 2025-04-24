# camera.py

import cv2

class Camera:
    """
    USB camera wrapper using OpenCV default backend.
    """
    def __init__(self,
                 device_index: int = 0,
                 resolution=(640, 480),
                 rotation: int = 0,
                 hflip: bool = False,
                 vflip: bool = False):
        """
        :param device_index: index for cv2.VideoCapture (e.g. 0)
        """
        cap = cv2.VideoCapture(device_index)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera at index {device_index}")

        width, height = resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.cap      = cap
        self.rotation = rotation
        self.hflip    = hflip
        self.vflip    = vflip

    def start(self):
        # no-op for default VideoCapture
        pass

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("Failed to read frame from camera")

        # Rotation
        if   self.rotation ==  90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif self.rotation == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Flips
        if self.hflip:
            frame = cv2.flip(frame, 1)
        if self.vflip:
            frame = cv2.flip(frame, 0)

        return frame

    def stop(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()


if __name__ == "__main__":
    # quick test
    cam = Camera(device_index=0, resolution=(640,480))
    print("[INFO] Press 'q' to quit")
    while True:
        f = cam.get_frame()
        cv2.imshow("USB Camera Test", f)
        if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
            break
    cam.stop()
    cv2.destroyAllWindows()

