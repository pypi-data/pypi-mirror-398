from apppy.fastql.annotation import fastql_type_error
from apppy.fastql.errors import GraphQLServerError


@fastql_type_error
class IllegalJwksPemFileError(GraphQLServerError):
    """Error raised when a JWKS PEM file is not well-formed"""

    def __init__(self, code: str) -> None:
        super().__init__(code)
