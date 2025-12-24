import abc
from typing import Any

from strawberry.permission import BasePermission

from apppy.fastql.errors import GraphQLClientError, GraphQLServerError


class GraphQLPermission(BasePermission):
    """
    A generic base class which represents a graphql permission.
    """

    # In GraphQL, there are strongly typed errors returned.
    # Here, we allow an permission class to declare the GraphQL
    # errors that are to be returned on either a server-side error
    # or a client-side error
    graphql_client_error_class: type[GraphQLClientError]
    graphql_server_error_class: type[GraphQLServerError]

    def on_unauthorized(self) -> None:
        error = self.graphql_client_error_class(self.graphql_client_error_args())  # type: ignore[arg-type]
        raise error

    @abc.abstractmethod
    def graphql_client_error_args(self) -> tuple[Any, ...]:
        pass
