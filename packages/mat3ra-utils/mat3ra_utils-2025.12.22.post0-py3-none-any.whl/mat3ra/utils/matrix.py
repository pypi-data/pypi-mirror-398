from typing import List


def convert_2x2_to_3x3(matrix: List[List[float]]) -> List[List[float]]:
    """
    Convert a 2x2 matrix to a 3x3 matrix by adding a third unitary orthogonal basis vector.

    Args:
        matrix (list): A 2x2 matrix.

    Returns:
        list: A 3x3 matrix.
    """
    return [[matrix[0][0], matrix[0][1], 0], [matrix[1][0], matrix[1][1], 0], [0, 0, 1]]
