import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two L2-normalised vectors. Range [-1, 1]."""
    return float(np.dot(a, b))

def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine distance. Range [0, 2]."""
    return 1.0 - cosine_similarity(a, b)