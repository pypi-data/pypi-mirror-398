from typing import Any

import strawberry


def fastql_type_interface(cls: type[Any]):
    """
    Decorator to wrap strawberry.interface
    """
    cls._fastql_type_interface = True  # type: ignore[attr-defined]
    return strawberry.interface(cls)


def valid_fastql_type_interface(cls: type) -> bool:
    return hasattr(cls, "_fastql_type_interface")
