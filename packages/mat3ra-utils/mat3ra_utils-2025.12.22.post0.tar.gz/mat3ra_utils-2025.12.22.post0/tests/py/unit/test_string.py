from mat3ra.utils import string as utils


def test_snake_to_camel():
    """
    test_camel_to_snake should be converted to testCamelToSnake
    """
    print(utils.snake_to_camel("test_camel_to_snake"))
    assert utils.snake_to_camel("test_camel_to_snake") == "TestCamelToSnake"


def test_camel_to_snake():
    """
    testCamelToSnake should be converted to test_camel_to_snake
    """
    print(utils.camel_to_snake("testCamelToSnake"))
    assert utils.camel_to_snake("TestCamelToSnake") == "test_camel_to_snake"
