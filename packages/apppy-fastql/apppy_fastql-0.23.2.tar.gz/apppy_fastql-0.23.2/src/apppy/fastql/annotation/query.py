from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import get_type_hints

from apppy.fastql.annotation.output import valid_fastql_type_output
from apppy.fastql.errors import GraphQLError
from apppy.fastql.permissions import GraphQLPermission


def fastql_query():
    """
    Custom class decorator that marks query classes for inclusion in FastQL
    """

    def decorator(cls):
        cls._fastql_is_query = True  # type: ignore[attr-defined]
        return cls

    return decorator


def fastql_query_field(
    *,
    error_types: Sequence[type[GraphQLError]] = (),
    auth_check: type[GraphQLPermission] | None = None,
    iam_check: GraphQLPermission | None = None,
    skip_permission_checks: bool = False,
):
    """
    Custom field decorator that marks query fields for inclusion in FastQL.

    Args
    error_types: Possible error types raised by the query
    auth_check: GraphQLPermission authentication class guarding this field
    iam_check: GraphQLPermission authorization guarding this field
    skip_permission_checks: Flag indicating that no authentication nor
                            authorization permissions will be checked for
                            this field (i.e. it is an open API)
    """

    def decorator(resolver: Callable):
        all_error_types: set[type[GraphQLError]] = set()
        all_error_types.update(error_types)
        all_permission_instances: set[GraphQLPermission] = set()
        if not skip_permission_checks:
            # Process auth_check
            auth_check_cls = auth_check
            if auth_check_cls is None:
                raise ValueError("No auth_check permission provided")

            all_error_types.add(auth_check_cls.graphql_client_error_class)
            all_error_types.add(auth_check_cls.graphql_server_error_class)
            all_permission_instances.add(auth_check_cls())
            # Process iam_check
            if iam_check is not None:
                iam_check_cls = type(iam_check)
                all_error_types.add(iam_check_cls.graphql_client_error_class)
                all_error_types.add(iam_check_cls.graphql_server_error_class)
                all_permission_instances.add(iam_check)

        # Sort all error types for stable code generation
        all_error_types_sorted: list[type[GraphQLError]] = sorted(
            all_error_types, key=lambda t: t.__name__
        )

        return_type = get_type_hints(resolver).get("return")
        resolver_name = getattr(resolver, "__name__", "<unknown>")

        if return_type is None:
            raise TypeError(f"Missing return type hint for resolver: {resolver_name}")

        if not valid_fastql_type_output(return_type):
            raise TypeError(
                f"Return type of {resolver_name} must be a valid @fastql_type_output type."  # noqa: E501
            )

        resolver._fastql_query_field = True  # type: ignore[attr-defined]
        resolver._fastql_return_type = return_type  # type: ignore[attr-defined]
        resolver._fastql_error_types = tuple(all_error_types_sorted)  # type: ignore[attr-defined]
        resolver._fastql_permission_instances = tuple(all_permission_instances)  # type: ignore[attr-defined]
        resolver._skip_permission_checks = skip_permission_checks  # type: ignore[attr-defined]

        return resolver

    return decorator
