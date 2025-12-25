import pytest
from mat3ra.utils import search as utils


class ElementMock:
    def __init__(self, symbol, name, atomic_number, group=None):
        self.symbol = symbol
        self.name = name
        self.atomic_number = atomic_number
        self.group = group


ELEMENTS = [
    ElementMock("H", "Hydrogen", 1, "nonmetal"),
    ElementMock("He", "Helium", 2, "noble_gas"),
    ElementMock("C", "Carbon", 6, "nonmetal"),
    ElementMock("Fe", "IRON", 26, "transition_metal"),
]

ELEMENTS_WITH_NONE = [
    ElementMock("X", "Unknown", 999, None),
]

EMPTY_LIST = []

KEY_SYMBOL = "symbol"
KEY_NAME = "name"
KEY_ATOMIC_NUMBER = "atomic_number"
KEY_GROUP = "group"
KEY_NONEXISTENT = "mass"

VALUE_HYDROGEN = "Hydrogen"
VALUE_IRON_LOWER = "iron"
VALUE_NONEXISTENT = "Oxygen"

REGEX_STARTS_WITH_H = "^H"
REGEX_ENDS_WITH_ON = "on$"
REGEX_NUMERIC = r"\d+"

EXPECTED_SYMBOL_H = "H"
EXPECTED_SYMBOL_C = "C"
EXPECTED_SYMBOL_FE = "Fe"


@pytest.mark.parametrize(
    "items,key,value,value_regex,expected_symbol,should_raise",
    [
        (ELEMENTS, KEY_NAME, VALUE_HYDROGEN, None, EXPECTED_SYMBOL_H, False),
        (ELEMENTS, KEY_NAME, VALUE_IRON_LOWER, None, EXPECTED_SYMBOL_FE, False),
        (ELEMENTS, KEY_NAME, None, REGEX_ENDS_WITH_ON, EXPECTED_SYMBOL_C, False),
        (ELEMENTS, KEY_ATOMIC_NUMBER, "6", None, EXPECTED_SYMBOL_C, False),
        (ELEMENTS, KEY_NAME, VALUE_HYDROGEN, REGEX_STARTS_WITH_H, None, True),
        (EMPTY_LIST, KEY_NAME, VALUE_HYDROGEN, None, None, False),
        (ELEMENTS_WITH_NONE, KEY_GROUP, "nonmetal", None, None, False),
    ],
)
def test_find_by_key_or_regex(items, key, value, value_regex, expected_symbol, should_raise):
    if should_raise:
        with pytest.raises(ValueError, match="Cannot specify both 'value' and 'value_regex'"):
            utils.find_by_key_or_regex(items, key=key, value=value, value_regex=value_regex)
    else:
        result = utils.find_by_key_or_regex(items, key=key, value=value, value_regex=value_regex)
        if expected_symbol is None:
            assert result is None
        else:
            assert result.symbol == expected_symbol

