from typing import Any, List, Optional, Sequence, Union

import numpy as np


def filter_by_slice_or_index_or_indices(
    array: List, slice_or_index_or_indices: Optional[Union[slice, int, List[int]]] = None
):
    if isinstance(slice_or_index_or_indices, list):
        return list(map(lambda x: array[x], slice_or_index_or_indices))
    if isinstance(slice_or_index_or_indices, slice):
        return array[slice_or_index_or_indices]
    if isinstance(slice_or_index_or_indices, int):
        return [array[slice_or_index_or_indices]]
    return array


def convert_to_array_if_not(array_or_item: Union[List, Any]):
    return array_or_item if isinstance(array_or_item, list) else [array_or_item]


def jaccard_similarity_for_strings(array_a: Sequence[str], array_b: Sequence[str]) -> float:
    """
    Compute the Jaccard similarity coefficient between two sequences of elements.

    The Jaccard coefficient measures the similarity between two sets A and B as:
        J(A, B) = |A ∩ B| / |A ∪ B|

    where |A ∩ B| is the number of shared elements, and |A ∪ B| is the total number
    of unique elements across both sets. The score ranges from 0.0 (no overlap) to 1.0
    (identical sets). Empty layers are treated specially:
      - Both empty → score = 1.0
      - One empty → score = 0.0

    Args:
        array_a: Sequence of element symbols for the first layer
        array_b: Sequence of element symbols for the second layer

    Returns:
        float: Jaccard similarity coefficient between 0.0 and 1.0
    """
    intersection = np.intersect1d(array_a, array_b)
    union = np.union1d(array_a, array_b)

    if union.size == 0:
        return 1.0

    return float(intersection.size / union.size)
