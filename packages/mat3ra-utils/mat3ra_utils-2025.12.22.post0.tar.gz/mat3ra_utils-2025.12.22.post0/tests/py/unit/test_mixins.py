import numpy as np
from mat3ra.utils import mixins as mixins

ARRAY_TO_ROUND = [1.23456789101112, 2.34567899, 3.45678999, 4.56789999, -5.67899999]

ARRAY_TO_ROUND_WITH_NEGATIVE_ZERO = [3.0616852911453934e-17, 0, -3.0616852911453934e-17]


def test_RoundNumericValuesMixin():
    """
    Test the availability of the RoundNumericValuesMixin methods
    """

    class TestClass(mixins.RoundNumericValuesMixin):
        pass

    assert TestClass.round_array_or_number(ARRAY_TO_ROUND[0]) == 1.234567891
    assert TestClass.round_array_or_number(ARRAY_TO_ROUND) == [
        1.234567891,
        2.34567899,
        3.45678999,
        4.56789999,
        -5.67899999,
    ]


def test_RoundNumericValuesMixin_with_negative_zero():
    class TestClass(mixins.RoundNumericValuesMixin):
        pass

    rounded = TestClass.round_array_or_number(ARRAY_TO_ROUND_WITH_NEGATIVE_ZERO)

    signs = [bool(np.signbit(x)) for x in rounded]
    # Assert there is no negative zero
    assert signs == [False, False, False]
    assert rounded == [0.0, 0.0, 0.0]


def test_RoundNumericValuesMixin_inheritance():
    """
    Test the availability of the RoundNumericValuesMixin methods
    """

    class BaseClass(object):
        pass

    class TestClass(BaseClass, mixins.RoundNumericValuesMixin):
        __round_precision__ = 3

    assert TestClass.round_array_or_number(ARRAY_TO_ROUND[0]) == 1.235
    assert TestClass.round_array_or_number(ARRAY_TO_ROUND) == [
        1.235,
        2.346,
        3.457,
        4.568,
        -5.679,
    ]
