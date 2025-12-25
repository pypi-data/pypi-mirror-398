import os

from ..internal.modules import load_module

STDLIB_MODULES = [
    "address_utils",
    "fp",
    "list_utils",
    "math",
    "rational",
    "statistics",
    "string_utils",
    "utils",
]


class Stdlib:
    utils = None
    statistics = None
    math = None
    rational = None
    fp = None
    list_utils = None
    string_utils = None
    address_utils = None


def load_library_if_needed():
    if os.environ.get("SMARTPY_NEW_TYPE_CHECKER"):
        return
    if Stdlib.utils is None:
        Stdlib.utils = load_module("smartpy/stdlib/utils.spy", STDLIB_MODULES)
        Stdlib.statistics = load_module("smartpy/stdlib/statistics.spy", STDLIB_MODULES)
        Stdlib.math = load_module("smartpy/stdlib/math.spy", STDLIB_MODULES)
        Stdlib.rational = load_module("smartpy/stdlib/rational.spy", STDLIB_MODULES)
        Stdlib.fp = load_module("smartpy/stdlib/fixed_point.spy", STDLIB_MODULES)
        Stdlib.list_utils = load_module("smartpy/stdlib/list_utils.spy", STDLIB_MODULES)
        Stdlib.string_utils = load_module(
            "smartpy/stdlib/string_utils.spy", STDLIB_MODULES
        )
        Stdlib.address_utils = load_module(
            "smartpy/stdlib/address_utils.spy", STDLIB_MODULES
        )


def __getattr__(name):
    """The dynamic loading of the standard library modules upon attribute access
    is needed because Jupyter cannot call load_module in the
    `import smartpy as sp` cell.
    """
    # Handle stdlib attributes dynamically
    if name in STDLIB_MODULES:
        load_library_if_needed()

        return getattr(Stdlib, name)
    raise AttributeError(f"The SmartPy standard library has no attribute '{name}'")
