from mat3ra.utils import matrix as utils

REFERENCE_MATRIX_2X2 = [[1, 2], [3, 4]]
REFERENCE_MATRIX_3X3 = [[1, 2, 0], [3, 4, 0], [0, 0, 1]]


def test_convert_2x2_to_3x3():
    matrix_3x3 = utils.convert_2x2_to_3x3(REFERENCE_MATRIX_2X2)
    assert matrix_3x3 == REFERENCE_MATRIX_3X3
