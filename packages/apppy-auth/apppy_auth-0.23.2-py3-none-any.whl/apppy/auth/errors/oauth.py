from apppy.fastql.annotation import fastql_type_error
from apppy.fastql.errors import GraphQLClientError


@fastql_type_error
class IllegalNativeOAuthProviderError(GraphQLClientError):
    """Error raised when a non-native OAuth provider is treated as a native one"""

    provider: str

    def __init__(self, provider: str) -> None:
        super().__init__("illegal_native_oauth_provider")
        self.provider = provider


@fastql_type_error
class UnknownOAuthProviderError(GraphQLClientError):
    """Error raised when a client has provided an unknown OAuth client name"""

    provider: str

    def __init__(self, provider: str) -> None:
        super().__init__("unknown_oauth_provider")
        self.provider = provider
