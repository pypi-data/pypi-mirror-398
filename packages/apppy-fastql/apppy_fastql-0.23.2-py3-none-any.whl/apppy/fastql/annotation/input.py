from typing import Any

import strawberry


def fastql_type_input(cls: type[Any]):
    """
    Custom field decorator that marks input types (i.e. request types in APIs)
    """
    cls._fastql_type_input = True  # type: ignore[attr-defined]
    return strawberry.input(cls)


def valid_fastql_type_input(cls: Any) -> bool:
    return hasattr(cls, "_fastql_type_input")
