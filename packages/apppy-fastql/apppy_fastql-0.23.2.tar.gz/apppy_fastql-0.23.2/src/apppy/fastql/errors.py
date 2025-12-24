from apppy.fastql.annotation.error import fastql_type_error
from apppy.fastql.annotation.interface import fastql_type_interface
from apppy.generic.errors import ApiClientError, ApiError, ApiServerError


# NOTE: Do not use GraphQLError directly
# instead use GraphQLClientError or GraphQLServerError
@fastql_type_interface
class GraphQLError(ApiError):
    """Generic base class for any error raised in a GraphQL API"""

    # NOTE -- We need to restate the fields here even though
    # they are defined in the base ApiError class so that the
    # GraphQL framework picks them up
    code: str
    status: int

    def __init__(self, code: str, status: int):
        super().__init__(code, status)


@fastql_type_interface
class GraphQLClientError(GraphQLError, ApiClientError):
    """Base class for any GraphQL error raised related to bad client input"""

    def __init__(self, code: str = "generic_graphql_client_error", status: int = 400):
        super().__init__(code, status)


@fastql_type_interface
class GraphQLServerError(GraphQLError, ApiServerError):
    """Base class for any GraphQL error raised related to internal server processing"""

    def __init__(self, code: str = "generic_graphql_server_error", status: int = 500):
        super().__init__(code, status)


@fastql_type_error
class TypedIdInvalidPrefixError(GraphQLClientError):
    """Raised when a TypedId encounters an invalid prefix"""

    id: str
    id_type: str

    def __init__(self, id: str, id_type: str):
        super().__init__("typed_id_invalid_prefix")
        self.id = id
        self.id_type = id_type
