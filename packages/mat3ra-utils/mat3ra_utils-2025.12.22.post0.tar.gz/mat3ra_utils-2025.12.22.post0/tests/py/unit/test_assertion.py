import pytest
from mat3ra.utils.assertion import assert_almost_equal_numbers, assert_deep_almost_equal, assert_equal

TEST_STRUCTURE_A = {
    "a": 1.00001,
    "b": [1.00002, 2, {"c": 3.00001, "d": [4.00001, "test"]}],
    "e": {"f": 5.00001, "g": [6.00001, {"h": 7.00001, "i": "test"}]},
}

TEST_STRUCTURE_ALMOST_A = {
    "a": 1.00002,
    "b": [1.00001, 2, {"c": 3.00002, "d": [4.00002, "test"]}],
    "e": {"f": 5.00002, "g": [6.00002, {"h": 7.00002, "i": "test"}]},
}

TEST_STRUCTURE_NOT_A = {
    "a": 1.0001,
    "b": [1.0002, 2, {"c": 3.0001, "d": [4.0001, "test"]}],
    "e": {"f": 5.00002, "g": [6.00002, {"h": 7.00002, "i": "test"}]},
}

ATOL = 1e-5


def test_assert_almost_equal_numbers():
    assert_almost_equal_numbers(1.00001, 1.00002, atol=ATOL)
    # test negative outcome
    with pytest.raises(AssertionError):
        assert_almost_equal_numbers(1.0001, 1.0002, atol=ATOL)


def test_assert_equal():
    assert_equal("test", "test")
    with pytest.raises(AssertionError):
        assert_equal("test", "test1")


def test_assert_deep_almost_equal():
    assert_deep_almost_equal(TEST_STRUCTURE_A, TEST_STRUCTURE_ALMOST_A, atol=ATOL)
    # Test with not almost equal complex structures
    with pytest.raises(AssertionError):
        assert_deep_almost_equal(TEST_STRUCTURE_A, TEST_STRUCTURE_NOT_A, atol=ATOL)
