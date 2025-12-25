from mat3ra.utils.extra import tabulate as utils

EXAMPLE_TABULAR_DATA = """name       age
-------  -----
Alice       24
Bob         19
Charlie     35"""


def test_tabulate():
    data = [
        ["Alice", 24],
        ["Bob", 19],
        ["Charlie", 35],
    ]
    headers = ["name", "age"]
    table = utils.tabulate(data, headers)
    assert table == EXAMPLE_TABULAR_DATA
