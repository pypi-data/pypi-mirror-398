import strawberry

from apppy.fastql.typed_id import TypedId


def fastql_type_id(cls: type[TypedId]):
    """
    Decorator for TypedId subclasses that automatically registers them as GraphQL scalars.
    """
    if not issubclass(cls, TypedId):
        raise TypeError(f"{cls.__name__} must subclass TypedId to use @fastql_type_id")

    cls._fastql_type_id = True  # type: ignore[attr-defined]

    return strawberry.scalar(
        serialize=lambda value: str(value),
        parse_value=lambda raw: cls.from_str(raw),
    )(cls)
