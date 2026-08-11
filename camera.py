import os, cv2, numpy as np

# CAMERA_BACKEND (set in .env or shell):
#   auto (default)        — detects Pi or falls back to webcam
#   pi                    — force picamera2
#   0                     — webcam at /dev/video0
#   path/to/video.mp4     — replay a recording (loops at original FPS)

def _is_pi() -> bool:
    try:
        with open("/proc/cpuinfo") as f: return "Raspberry Pi" in f.read()
    except FileNotFoundError: return False


class PiCamera:
    """picamera2 returns RGB. capture_bgr() converts to BGR for OpenCV/InsightFace."""
    def __init__(self, width, height):
        from picamera2 import Picamera2
        self._cam = Picamera2()
        self._cam.configure(
            self._cam.create_preview_configuration(main={"size": (width, height)})
        )
        self._cam.start()

    def capture_bgr(self) -> np.ndarray:
        return cv2.cvtColor(self._cam.capture_array(), cv2.COLOR_RGB2BGR)

    def stop(self): self._cam.stop()


class WebcamCamera:
    """OpenCV reads in BGR — no conversion needed."""
    def __init__(self, width, height, device=0):
        self._cap = cv2.VideoCapture(device)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open webcam at device {device}")

    def capture_bgr(self) -> np.ndarray:
        ret, frame = self._cap.read()
        if not ret: raise RuntimeError("Webcam read failed")
        return frame

    def stop(self): self._cap.release()


class VideoFileCamera:
    """
    Replay a video file. Loops at original FPS.
    Record your hallway on a phone, transfer it, set CAMERA_BACKEND=hallway.mp4.
    Direction/timing behave like a real camera because frame rate is preserved.
    """
    def __init__(self, path):
        if not os.path.exists(path): raise FileNotFoundError(f"Not found: {path}")
        self._path = path
        self._cap  = cv2.VideoCapture(path)
        fps = self._cap.get(cv2.CAP_PROP_FPS) or 30
        self._frame_delay = 1.0 / fps

    def capture_bgr(self) -> np.ndarray:
        import time
        time.sleep(self._frame_delay)
        ret, frame = self._cap.read()
        if not ret:
            self._cap = cv2.VideoCapture(self._path)
            ret, frame = self._cap.read()
        return frame

    def stop(self): self._cap.release()


def create_camera(width: int, height: int):
    backend = os.environ.get("CAMERA_BACKEND", "auto").strip()
    if backend == "pi":   return PiCamera(width, height)
    if backend == "auto": return PiCamera(width, height) if _is_pi() else WebcamCamera(width, height)
    if backend.isdigit(): return WebcamCamera(width, height, device=int(backend))
    return VideoFileCamera(backend)