# face_worker.py
import threading, json, numpy as np
from insightface.app import FaceAnalysis
from utils import cosine_distance
from config import (INSIGHTFACE_MODEL, ARCFACE_MATCH_THRESHOLD, FACE_TRACK_ASSOC_DIST)

class FaceWorker(threading.Thread):
    """
    T3: detection + recognition in a single thread.

    Receives full frames. Calls face_app.get() once per frame to get all face
    bounding boxes and ArcFace embeddings. Updates the tracker with detections,
    then runs recognition for each detected face against its nearest unidentified
    track. claimed_tids prevents two faces from being assigned to the same track.

    When no faces are detected, tracker.update([]) is still called so that track
    disappeared counts increment correctly — required for exit events to fire.
    """
    def __init__(self, face_queue, tracker):
        super().__init__(daemon=True)
        self.queue   = face_queue
        self.tracker = tracker
        if not __import__("os").path.exists("data/enrollments.json"):
            raise FileNotFoundError(
                "data/enrollments.json not found. "
                "Run `python enroll.py` for each roommate first."
            )
        raw = json.load(open("data/enrollments.json"))
        self.names      = list(raw.keys())
        self.prototypes = {nm: np.array(raw[nm]["prototype"]) for nm in self.names}
        # InsightFace expects BGR — same as OpenCV, same as what camera.py returns
        self.app = FaceAnalysis(name=INSIGHTFACE_MODEL, providers=["CPUExecutionProvider"])
        self.app.prepare(ctx_id=0, det_size=(640, 480))

    def _identify(self, embedding: np.ndarray) -> str | None:
        dists = {nm: cosine_distance(embedding, self.prototypes[nm]) for nm in self.names}
        best  = min(dists, key=dists.get)
        return best if dists[best] < ARCFACE_MATCH_THRESHOLD else None

    def run(self):
        while True:
            frame_bgr = self.queue.get()
            faces = self.app.get(frame_bgr)   # one call: detection + all embeddings, BGR

            if not faces:
                self.tracker.update([])   # no faces detected — age out disappeared tracks
                continue

            # Update tracker with detected bounding boxes
            detections = []
            for face in faces:
                b = face.bbox.astype(int)
                x1, y1, x2, y2 = b[0], b[1], b[2], b[3]
                cx, cy = (x1+x2)//2, (y1+y2)//2
                detections.append(((cx, cy), (x1, y1, x2, y2)))
            self.tracker.update(detections)

            # Recognition: associate each face with its nearest unidentified track.
            # claimed_tids ensures each track is matched by at most one face per pass.
            unidentified = self.tracker.unidentified_tracks()
            if not unidentified: continue

            claimed_tids = set()
            for face in faces:
                b = face.bbox.astype(int)
                face_cx = (b[0] + b[2]) // 2
                face_cy = (b[1] + b[3]) // 2

                best_track   = None
                best_px_dist = FACE_TRACK_ASSOC_DIST
                for t in unidentified:
                    if t.id in claimed_tids: continue
                    d = np.sqrt((t.centroid[0] - face_cx)**2 + (t.centroid[1] - face_cy)**2)
                    if d < best_px_dist:
                        best_px_dist = d; best_track = t

                if best_track is None: continue

                claimed_tids.add(best_track.id)
                name = self._identify(face.embedding)
                if name:
                    self.tracker.report_identity(best_track.id, name)