from typing import Any

import strawberry


def fastql_type_error(cls: type[Any]):
    """
    Custom field decorator that marks error types (i.e. response errors from APIs)
    """
    cls._fastql_type_error = True  # type: ignore[attr-defined]
    return strawberry.type(cls)


def valid_fastql_type_error(cls: Any) -> bool:
    return hasattr(cls, "_fastql_type_error")
