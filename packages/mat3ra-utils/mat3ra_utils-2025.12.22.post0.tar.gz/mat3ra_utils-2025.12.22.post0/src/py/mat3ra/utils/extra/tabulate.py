import json

from tabulate import tabulate


def pretty_print(table, headers, tablefmt="simple", stralign="left"):
    """
    Pretty-prints tabular data.
        https://pypi.python.org/pypi/tabulate

    Args:
        table (List of Lists): data to be printed.
        headers (List): a list of column headers to be used.
        stralign (str): text alignment. Can be right, center and left. Defaults to left
        tablefmt (str): output format. Can be plain, simple, json, grid, fancy_grid,
            pipe, orgtbl, rst, mediawiki, html, latex and latex_booktabs. Defaults to simple.
    """
    if tablefmt == "json":
        print(json.dumps([dict(zip(headers, row)) for row in table], sort_keys=True, indent=4, separators=(",", ": ")))
    else:
        print(tabulate(table, headers, tablefmt=tablefmt, stralign=stralign))
