# tracker.py
import threading
from collections import deque

import numpy as np

from config import (
    CENTROID_MATCH_DIST,
    DIRECTION_HISTORY_LEN,
    DIRECTION_MIN_FRAMES,
    DIRECTION_MOVEMENT_THRESHOLD,
    DOOR_ZONE,
    IDENTITY_LOCK_VOTES,
    MAX_DISAPPEARED_FRAMES,
)

_ZX, _ZY, _ZW, _ZH = DOOR_ZONE
DOOR_ZONE_CX = _ZX + _ZW // 2
DOOR_ZONE_CY = _ZY + _ZH // 2

def _dist_to_door(cx: int, cy: int) -> float:
    return float(np.sqrt((cx - DOOR_ZONE_CX)**2 + (cy - DOOR_ZONE_CY)**2))


class Track:
    def __init__(self, tid, centroid, bbox):
        self.id = tid; self.centroid = centroid; self.bbox = bbox
        self.history = deque(maxlen=DIRECTION_HISTORY_LEN)
        self.history.append(centroid)
        self.name = None; self.name_votes = {}
        self.identity_locked = False; self.disappeared = 0

    def update(self, centroid, bbox):
        self.centroid = centroid; self.bbox = bbox
        self.history.append(centroid); self.disappeared = 0

    def direction(self) -> str:
        """Whether centroid is moving toward or away from door zone centre.
        Works for any door position in the frame (left, right, or centre).
        """
        if len(self.history) < DIRECTION_MIN_FRAMES: return "unknown"
        delta = _dist_to_door(*self.history[-1]) - _dist_to_door(*self.history[0])
        if abs(delta) < DIRECTION_MOVEMENT_THRESHOLD: return "unknown"
        return "approaching_door" if delta < 0 else "entering_apartment"

    def in_door_zone(self) -> bool:
        zx, zy, zw, zh = DOOR_ZONE
        cx, cy = self.centroid
        return zx <= cx <= zx+zw and zy <= cy <= zy+zh


class CentroidTracker:
    def __init__(self):
        self.next_id = 0; self.tracks = {}; self._lock = threading.Lock()

    def update(self, detections):
        """detections: list of ((cx, cy), (x1, y1, x2, y2)), or [] to age out tracks."""
        with self._lock:
            if not detections:
                for t in list(self.tracks.values()):
                    t.disappeared += 1
                    if t.disappeared > MAX_DISAPPEARED_FRAMES: del self.tracks[t.id]
                return
            if not self.tracks:
                for c, b in detections:
                    self.tracks[self.next_id] = Track(self.next_id, c, b); self.next_id += 1
                return
            tids = list(self.tracks.keys())
            tc   = np.array([self.tracks[i].centroid for i in tids])
            dc   = np.array([d[0] for d in detections])
            D    = np.linalg.norm(tc[:, None] - dc[None, :], axis=2)
            used_t, used_d = set(), set()
            for row, col in zip(*np.where(D < CENTROID_MATCH_DIST)):
                tid = tids[row]
                if tid not in used_t and col not in used_d:
                    self.tracks[tid].update(detections[col][0], detections[col][1])
                    used_t.add(tid); used_d.add(col)
            for i, tid in enumerate(tids):
                if tid not in used_t:
                    self.tracks[tid].disappeared += 1
                    if self.tracks[tid].disappeared > MAX_DISAPPEARED_FRAMES: del self.tracks[tid]
            for i, (c, b) in enumerate(detections):
                if i not in used_d:
                    self.tracks[self.next_id] = Track(self.next_id, c, b); self.next_id += 1

    def report_identity(self, track_id, name):
        with self._lock:
            if track_id not in self.tracks or not name: return
            t = self.tracks[track_id]
            t.name_votes[name] = t.name_votes.get(name, 0) + 1
            if t.name_votes[name] >= IDENTITY_LOCK_VOTES:
                t.name = name; t.identity_locked = True

    def unidentified_tracks(self):
        with self._lock: return [t for t in self.tracks.values() if not t.identity_locked]

    def snapshot(self):
        with self._lock: return list(self.tracks.values())