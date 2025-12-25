import json

import numpy as np
from mat3ra.utils import object as utils

REFERENCE_OBJECT_1 = {"key1": "value1", "key2": "value2"}
REFERENCE_OBJECT_1_WITHOUT_KEY1 = {"key2": "value2"}
REFERENCE_OBJECT_1_WITH_KEY3 = {"key1": "value1", "key2": "value2", "key3": "value3"}
# Using 3 different objects to avoid clashes between tests
REFERENCE_OBJECT_2_CLONE_SHALLOW = {"key2": {"nested_key1": "nested_value1"}}
REFERENCE_OBJECT_2_CLONE_DEEP = {"key2": {"nested_key1": "nested_value1"}}
REFERENCE_OBJECT_2_GET = {"key2": {"nested_key1": "nested_value1"}}
REFERENCE_OBJECT_WITH_NONES = {
    "key1": "value1",
    "key2": None,
    "key3": {
        "nested_key1": "nested_value1",
        "nested_key2": None,
    },
    "key4": [1, 2, None, 4],
    "key5": None
}
REFERENCE_OBJECT_WITH_SOME_NONES_FILTERED = {
    "key1": "value1",
    "key3": {
        "nested_key1": "nested_value1",
        "nested_key2": None,
    },
    "key4": [1, 2, 4],
    "key5": None
}


def test_omit():
    object_without_key1 = utils.omit(REFERENCE_OBJECT_1, ["key1"])
    assert object_without_key1 == REFERENCE_OBJECT_1_WITHOUT_KEY1


def test_set_object_key():
    object_with_key3 = utils.clone_deep(REFERENCE_OBJECT_1)
    utils.set_object_key(object_with_key3, "key3", "value3")
    assert object_with_key3 == REFERENCE_OBJECT_1_WITH_KEY3


def test_clone_shallow():
    object_2_clone_shallow = utils.clone_shallow(REFERENCE_OBJECT_2_CLONE_SHALLOW)
    REFERENCE_OBJECT_2_CLONE_SHALLOW["key2"]["nested_key1"] = "nested_value2"
    assert object_2_clone_shallow["key2"]["nested_key1"] == "nested_value2"


def test_clone_deep():
    object_2_clone_deep = utils.clone_deep(REFERENCE_OBJECT_2_CLONE_DEEP)
    REFERENCE_OBJECT_2_CLONE_DEEP["key2"]["nested_key1"] = "nested_value2"
    assert object_2_clone_deep["key2"]["nested_key1"] == "nested_value1"


def test_get():
    nested_value1 = utils.get(REFERENCE_OBJECT_2_GET, "key2/nested_key1")
    assert nested_value1 == "nested_value1"
    assert nested_value1 == utils.get(REFERENCE_OBJECT_2_GET, "/key2/nested_key1")
    assert nested_value1 == utils.get(REFERENCE_OBJECT_2_GET, "key2.nested_key1", ".")


def test_filter_out_none_values():
    filtered_object = utils.filter_out_none_values(REFERENCE_OBJECT_WITH_NONES, keep_as_none=["key5", "nested_key2"])

    assert filtered_object == REFERENCE_OBJECT_WITH_SOME_NONES_FILTERED


def test_attribute_dict():
    attribute_dict = utils.AttributeDict(REFERENCE_OBJECT_1)
    assert attribute_dict.key1 == "value1"
    assert attribute_dict.key2 == "value2"
    assert attribute_dict["key1"] == "value1"
    assert attribute_dict["key2"] == "value2"


def test_numpy_ndarray_round_encoder():
    example_object = {"key1": np.array([1.1, 2.2, 3.3])}
    json_object = json.dumps(example_object, cls=utils.NumpyNDArrayRoundEncoder)
    assert json_object == '{"key1": [1.1, 2.2, 3.3]}'
    example_object = {"key1": np.array([1.1, 2.2, 3.3]), "key2": np.array([1.1, 2.2, 3.3])}
    json_object = json.dumps(example_object, cls=utils.NumpyNDArrayRoundEncoder)
    assert json_object == '{"key1": [1.1, 2.2, 3.3], "key2": [1.1, 2.2, 3.3]}'
