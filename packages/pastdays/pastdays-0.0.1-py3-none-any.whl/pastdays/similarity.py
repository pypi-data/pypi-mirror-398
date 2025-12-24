import numpy as np


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    return np.sqrt(np.sum((a - b) ** 2))


def rank_similar_days(target: np.ndarray, history: dict) -> list:
    """
    history: {date: feature_vector}
    """
    distances = []

    for date, features in history.items():
        dist = euclidean_distance(target, features)
        distances.append((date, dist))

    distances.sort(key=lambda x: x[1])
    return distances
