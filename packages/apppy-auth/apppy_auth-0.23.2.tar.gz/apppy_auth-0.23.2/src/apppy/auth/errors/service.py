from apppy.fastql.annotation import fastql_type_error
from apppy.fastql.errors import GraphQLClientError, GraphQLServerError


@fastql_type_error
class ServiceAuthenticationDisabledError(GraphQLServerError):
    """Error raised when a service trying to authenticate but service authentication is disabled"""

    def __init__(self) -> None:
        super().__init__("service_authenticaion_disabled")


@fastql_type_error
class ServiceKeyAlgorithmMissingError(GraphQLClientError):
    """Error raised when a service trying to authenticate does not include an algorithm header"""

    def __init__(self) -> None:
        super().__init__("service_key_algorithm_missing")


@fastql_type_error
class ServiceKeyMissingError(GraphQLServerError):
    """Error raised when a service trying to authenticate does not have a registered public key"""

    def __init__(self) -> None:
        super().__init__("service_key_missing")


@fastql_type_error
class ServiceUnknownError(GraphQLClientError):
    """Error raised when a service trying to authenticate cannot be found"""

    def __init__(self) -> None:
        super().__init__("service_unknown")
