import cv2, queue, threading, traceback
from camera import create_camera
from config import *
from door import DoorClassifier
from tracker import CentroidTracker
from face_worker import FaceWorker
from event_logic import EventLogic
from firebase_writer import FirebaseWriter

def main():
    home_now = input("Who is currently home? (comma-separated, or Enter): ")
    initially_home = [n.strip() for n in home_now.split(",") if n.strip()] if home_now.strip() else []

    frame_q = queue.Queue(maxsize=2)
    face_q  = queue.Queue(maxsize=FACE_QUEUE_MAXSIZE)
    write_q = queue.Queue(maxsize=WRITE_QUEUE_MAXSIZE)

    tracker     = CentroidTracker()
    door_clf    = DoorClassifier()
    event_logic = EventLogic(write_q)

    FirebaseWriter(write_q).start()
    for name in initially_home:
        write_q.put({"name": name, "isHome": True})
    FaceWorker(face_q, tracker).start()

    cam = create_camera(CAPTURE_WIDTH, CAPTURE_HEIGHT)

    def capture_loop():
        while True:
            try: frame_q.put_nowait(cam.capture_bgr())
            except queue.Full: pass

    threading.Thread(target=capture_loop, daemon=True).start()

    bg_sub    = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)
    no_motion = 0
    motion_on = False

    while True:
        try:
            frame_bgr = frame_q.get()

            # Motion detection (always on, cheap)
            fg = bg_sub.apply(frame_bgr)
            if cv2.countNonZero(fg) > MOTION_THRESHOLD:
                no_motion = 0; motion_on = True
            else:
                no_motion += 1
                if no_motion > MOTION_COOLDOWN_FRAMES:
                    motion_on = False
                    tracker.update([])   # age out tracks while hallway is empty

            # Feed FaceWorker when motion active (non-blocking; drops if worker busy)
            if motion_on:
                try: face_q.put_nowait(frame_bgr)
                except queue.Full: pass

            # Door state (always on, cheap, never blocked by face inference)
            door_state, _ = door_clf.predict(frame_bgr)
            event_logic.update(tracker.snapshot(), door_state)

        except Exception:
            traceback.print_exc()

if __name__ == "__main__":
    main()