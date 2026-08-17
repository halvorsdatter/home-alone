# door.py
import os
import pickle

import cv2
import numpy as np

from config import DOOR_ROI


class DoorClassifier:
    def __init__(self, path="models/door_classifier.pkl"):
        if not os.path.exists(path):
            print("[WARN] door_classifier.pkl not found — run calibrate_door.py on Pi first")
            self.model = None
        else:
            with open(path, "rb") as f: self.model = pickle.load(f)

    def predict(self, bgr_frame) -> tuple[str, float]:
        """Returns (state, confidence) where confidence = P(open), range [0,1]."""
        if self.model is None: return "closed", 0.0
        x, y, w, h = DOOR_ROI
        gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        roi  = gray[y:y+h, x:x+w]
        br   = float(np.mean(gray)) + 1e-6
        # Normalise by frame brightness — robust to day/night lighting changes
        prob = float(self.model.predict_proba([[np.mean(roi)/br, np.std(roi)/br]])[0][1])
        return ("open" if prob > 0.5 else "closed"), prob