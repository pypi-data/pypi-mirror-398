from typing import Any

from apppy.fastql.annotation import fastql_type_error
from apppy.fastql.errors import GraphQLClientError, GraphQLServerError


@fastql_type_error
class UserSessionInvalidDataError(GraphQLServerError):
    """Error raised when user session data does not have the correct shape"""

    session_data: dict[str, Any]

    def __init__(self, session_data: dict[str, Any]) -> None:
        super().__init__("invalid_user_session_data")
        self.session_data = session_data


@fastql_type_error
class UserSessionRefreshMissingSessionError(GraphQLClientError):
    """Error raised when a user session refresh is attempted against a missing session"""

    def __init__(self) -> None:
        super().__init__("user_session_refresh_missing_session")


@fastql_type_error
class UserSignInInvalidCredentialsError(GraphQLClientError):
    """Error raised when a user has provided invalid credentials for sign in"""

    def __init__(self) -> None:
        super().__init__("user_sign_in_invalid_credentials")


@fastql_type_error
class UserSignInServerError(GraphQLServerError):
    """Error raised when there's a user sign in error on the server side"""

    def __init__(self, code: str) -> None:
        super().__init__(code)


@fastql_type_error
class UserSignOutInvalidScopeError(GraphQLClientError):
    """Error raised when a user has provided an invalid scope for sign out"""

    scope: str

    def __init__(self, scope: str) -> None:
        super().__init__("user_sign_out_invalid_scope")
        self.scope = scope


@fastql_type_error
class UserSignOutServerError(GraphQLServerError):
    """Error raised when there's a user sign out error on the server side"""

    def __init__(self, code: str) -> None:
        super().__init__(code)


@fastql_type_error
class UserSignUpInvalidCredentialsError(GraphQLClientError):
    """Error raised when a user has provided invalid credentials for sign up"""

    def __init__(self) -> None:
        super().__init__("user_sign_up_invalid_credentials")


@fastql_type_error
class UserSignUpTooManyRetriesError(GraphQLServerError):
    """Error raised when there have been too many user sign up attempts"""

    def __init__(self) -> None:
        super().__init__("user_sign_up_too_many_retries")


@fastql_type_error
class UserSignUpAlreadyExistsError(GraphQLClientError):
    """Error raised when a user already exists during user sign up"""

    def __init__(self) -> None:
        super().__init__("user_already_exists")


@fastql_type_error
class UserSignUpServerError(GraphQLServerError):
    """Error raised when there's a user sign up error on the server side"""

    def __init__(self, code: str) -> None:
        super().__init__(code)
