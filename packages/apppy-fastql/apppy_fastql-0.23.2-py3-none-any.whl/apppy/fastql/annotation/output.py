from types import UnionType
from typing import Any, Union, get_args, get_origin

import strawberry
from strawberry.types.scalar import ScalarWrapper


def extract_concrete_type(typ: Any) -> Any:
    """
    Given something like Optional[MyType] or List[MyType], return MyType.
    """
    # Handle types that may come already wrapped in Strawberry
    if isinstance(typ, ScalarWrapper):
        return extract_concrete_type(typ.wrap)

    origin = get_origin(typ)
    if origin in {Union, UnionType, list, tuple}:
        args = get_args(typ)
        for arg in args:
            if arg is not type(None):  # skip NoneType
                return extract_concrete_type(arg)

    return typ


def fastql_type_output(cls: type[Any]):
    """
    Custom field decorator that marks output types (i.e. response types from APIs)
    """
    cls._fastql_type_output = True  # type: ignore[attr-defined]
    return strawberry.type(cls)


def valid_fastql_type_output(cls: Any) -> bool:
    cls = extract_concrete_type(cls)
    return hasattr(cls, "_fastql_type_output")
