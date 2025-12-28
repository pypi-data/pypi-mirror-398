import math
from typing import Literal


def calc_score(
    distance: float,
    *,
    datatype: Literal["FLOAT32", "FLOAT64"],
    distance_metric: Literal["COSINE", "IP", "L2"],
) -> float:
    """
    Calculate relevance score from distance.
    """
    if datatype == "FLOAT32":
        distance = round(distance, 4)
    else:
        distance = round(distance, 7)

    if distance_metric == "COSINE":
        # Normalise the cosine distance to a score within the range [0, 1]
        return 1.0 - distance

    elif distance_metric == "IP":
        # Normalise the inner product distance to a score within the range [0, 1]
        if distance > 0:
            return 1.0 - distance
        else:
            return -1.0 * distance

    elif distance_metric == "L2":
        # Convert the Euclidean distance to a similarity score within the range [0, 1]
        return 1.0 - distance / math.sqrt(2)

    else:
        raise ValueError(f"Unsupported distance metric: {distance_metric}")
