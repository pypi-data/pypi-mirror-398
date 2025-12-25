import re


def convert_js_flags_to_python(flags: str) -> int:
    """
    Convert JavaScript regex flags to Python regex flags.

    :param flags: String containing JavaScript regex flags.
    :return: Python flags for re.compile.
    """
    python_flags = 0

    if "i" in flags:
        python_flags |= re.IGNORECASE
    if "m" in flags:
        python_flags |= re.MULTILINE
    if "s" in flags:
        python_flags |= re.DOTALL

    # Note: JavaScript 'g' flag has no direct equivalent in Python, as Python inherently performs global searches.
    # Note: JavaScript 'u' flag (unicode) is inherently supported in Python 3's re module.
    # Note: JavaScript 'y' flag (sticky) has no direct equivalent in Python.

    return python_flags
