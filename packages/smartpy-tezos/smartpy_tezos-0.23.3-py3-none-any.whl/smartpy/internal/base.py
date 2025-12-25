from abc import ABC

"""
This file contains the abstract base classes of the smartpy library.
These empty classes can be detected by `isinstance` while the actual classes are
defined later in other files. This is useful to avoid circular imports.
"""


class BaseParsedExpr(ABC):
    pass


class BaseExpr(ABC):
    pass


class BaseTypeRef(ABC):
    pass


class BaseRef(ABC):
    pass


class BaseTestAccount(ABC):
    pass
