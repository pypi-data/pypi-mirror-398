from importlib.util import find_spec
from functools import cache

@cache
def check_dependency(name: str) -> bool:
    """
    Check if a specified dependency is available on the system.

    This function verifies the availability of a Python module or package by
    checking if it can be located using the Python runtime's import system.

    :param name: The name of the dependency to check.
    :type name: str
    :return: True if the dependency is available, False otherwise.
    :rtype: bool
    """
    return find_spec(name) is not None
