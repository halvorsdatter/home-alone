import json, numpy as np, itertools
from utils import cosine_distance

db = json.load(open("data/enrollments.json"))
print("ArcFace cosine distances between prototypes:")
for a, b in itertools.combinations(db.keys(), 2):
    d = cosine_distance(np.array(db[a]["prototype"]), np.array(db[b]["prototype"]))
    print(f"  {a} vs {b}: {d:.3f}")