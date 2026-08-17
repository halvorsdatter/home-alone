import itertools
import json

import numpy as np

from utils import cosine_distance

with open("data/enrollments.json") as f:
    db = json.load(f)
print("ArcFace cosine distances between prototypes:")
for a, b in itertools.combinations(db.keys(), 2):
    d = cosine_distance(np.array(db[a]["prototype"]), np.array(db[b]["prototype"]))
    print(f"  {a} vs {b}: {d:.3f}")