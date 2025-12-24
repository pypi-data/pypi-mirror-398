import datetime
import logging
from collections.abc import Sequence
from typing import Any

from apppy.auth.jwt import JwtAuthContext
from apppy.fastql.annotation import fastql_type_error
from apppy.fastql.errors import GraphQLClientError, GraphQLServerError
from apppy.fastql.permissions import GraphQLPermission
from apppy.logger import WithLogger


def _check_preprocessing_errors(
    permission: GraphQLPermission,
    auth_ctx: JwtAuthContext,
    logger: logging.Logger,
) -> None:
    if auth_ctx.preprocessing_error is not None:
        if isinstance(auth_ctx.preprocessing_error, GraphQLClientError):
            permission._error_code = auth_ctx.preprocessing_error.code  # type: ignore[attr-defined]
            raise permission.graphql_client_error_class(*permission.graphql_client_error_args())
        else:
            raise permission.graphql_server_error_class(auth_ctx.preprocessing_error.code)


def _extract_auth_context(permission: GraphQLPermission, info, **kwargs) -> JwtAuthContext:
    auth_ctx: JwtAuthContext = kwargs.get("auth_ctx")  # type: ignore[assignment]
    if auth_ctx is not None:
        return auth_ctx

    if not info:
        permission._logger.error(
            "No context or info provided while attempting to check permission",
            extra={"permission": type(permission).__name__},
        )
        raise permission.graphql_server_error_class("missing_context_and_info")

    return info.context.auth


@fastql_type_error
class AuthenticationServerError(GraphQLServerError):
    """Error raised when authentication fails due to an error on the server side"""

    def __init__(self, code) -> None:
        super().__init__(code)


@fastql_type_error
class AuthenticatedServiceOrUserRequiredError(GraphQLClientError):
    """Error raised when authentication is required but it is missing"""

    def __init__(self, code) -> None:
        super().__init__(code)


class IsServiceOrUser(GraphQLPermission, WithLogger):
    graphql_client_error_class = AuthenticatedServiceOrUserRequiredError
    graphql_server_error_class = AuthenticationServerError

    def __init__(self):
        self._error_code: str | None = None

    def has_permission(self, source, info, **kwargs) -> bool:
        auth_ctx: JwtAuthContext = _extract_auth_context(self, info, **kwargs)
        _check_preprocessing_errors(self, auth_ctx, self._logger)

        is_authenticated, self._error_code = IsServiceOrUser.is_context_authenticated(auth_ctx)
        return is_authenticated

    @staticmethod
    def is_context_authenticated(auth_ctx: JwtAuthContext) -> tuple[bool, str | None]:
        if not auth_ctx.has_token:
            return (False, "token_is_missing")
        if not auth_ctx.is_token_well_formed:
            return (False, "token_is_not_well_formed")

        now = int(datetime.datetime.now().timestamp())
        if now > auth_ctx.expires_at:
            return (False, "token_is_expired")
        if not auth_ctx.iam_enabled:
            return (False, "iam_is_disabled")
        if auth_ctx.iam_revoked_at is not None:
            return (False, "iam_is_revoked")

        return (True, None)

    def graphql_client_error_args(self) -> tuple[Any, ...]:
        return (self._error_code,)


@fastql_type_error
class AuthenticatedUserRequiredError(GraphQLClientError):
    """Error raised when a user authentication is required but it is missing"""

    def __init__(self, code: str, status: int = 401) -> None:
        super().__init__(code, status)


class IsUser(GraphQLPermission, WithLogger):
    graphql_client_error_class = AuthenticatedUserRequiredError
    graphql_server_error_class = AuthenticationServerError

    def __init__(self):
        self._error_code: str | None = None

    def has_permission(self, source, info, **kwargs) -> bool:
        auth_ctx: JwtAuthContext = _extract_auth_context(self, info, **kwargs)
        _check_preprocessing_errors(self, auth_ctx, self._logger)

        is_authenticated, self._error_code = IsUser.is_context_user_authenticated(auth_ctx)
        return is_authenticated

    @staticmethod
    def is_context_user_authenticated(auth_ctx: JwtAuthContext) -> tuple[bool, str | None]:
        is_authenticated, error_code = IsServiceOrUser.is_context_authenticated(auth_ctx)
        if not is_authenticated:
            return (is_authenticated, error_code)

        if auth_ctx.auth_subject_type != "user":
            return (False, "not_authenticated_as_user")

        return (True, None)

    def graphql_client_error_args(self) -> tuple[Any, ...]:
        return (self._error_code,)


@fastql_type_error
class AuthenticatedServiceRequiredError(GraphQLClientError):
    """Error raised when a service authentication is required but it is missing"""

    def __init__(self, code: str, status: int = 401) -> None:
        super().__init__(code, status)


class IsService(GraphQLPermission, WithLogger):
    graphql_client_error_class = AuthenticatedServiceRequiredError
    graphql_server_error_class = AuthenticationServerError

    def __init__(self):
        self._error_code: str | None = None

    def has_permission(self, source, info, **kwargs) -> bool:
        auth_ctx: JwtAuthContext = _extract_auth_context(self, info, **kwargs)
        _check_preprocessing_errors(self, auth_ctx, self._logger)

        is_authenticated, self._error_code = IsService.is_context_service_authenticated(auth_ctx)
        return is_authenticated

    @staticmethod
    def is_context_service_authenticated(auth_ctx: JwtAuthContext) -> tuple[bool, str | None]:
        is_authenticated, error_code = IsServiceOrUser.is_context_authenticated(auth_ctx)
        if not is_authenticated:
            return (is_authenticated, error_code)

        if auth_ctx.auth_subject_type != "service":
            return (False, "not_authenticated_as_service")

        return (True, None)

    def graphql_client_error_args(self) -> tuple[Any, ...]:
        return (self._error_code,)


@fastql_type_error
class AuthorizationServerError(GraphQLServerError):
    """Error raised when authorization fails due to an error on the server side"""

    def __init__(self, code) -> None:
        super().__init__(code)


@fastql_type_error
class AuthorizedRoleRequiredError(GraphQLClientError):
    """Error raised when an authorization role is required but it is missing"""

    permitted_role: str

    def __init__(self, permitted_role: str) -> None:
        super().__init__("authorization_role_required", status=403)
        self.permitted_role = permitted_role


class HasRole(GraphQLPermission, WithLogger):
    graphql_client_error_class = AuthorizedRoleRequiredError
    graphql_server_error_class = AuthorizationServerError

    def __init__(self, role: str):
        self._role = role

    def has_permission(self, source, info, **kwargs) -> bool:
        auth_ctx: JwtAuthContext = _extract_auth_context(self, info, **kwargs)
        _check_preprocessing_errors(self, auth_ctx, self._logger)

        return bool(auth_ctx.iam_role and self._role == auth_ctx.iam_role)

    def graphql_client_error_args(self) -> tuple[Any, ...]:
        return (self._role,)


@fastql_type_error
class AuthorizedScopeRequiredError(GraphQLClientError):
    """Error raised when an authorization scope is required but it is missing"""

    permitted_scope: str

    def __init__(self, permitted_scope: str) -> None:
        super().__init__("authorization_scope_required", status=403)
        self.permitted_scope = permitted_scope


class HasScope(GraphQLPermission, WithLogger):
    graphql_client_error_class = AuthorizedScopeRequiredError
    graphql_server_error_class = AuthorizationServerError

    def __init__(self, scope: str):
        self._scope = scope

    def has_permission(self, source, info, **kwargs) -> bool:
        auth_ctx: JwtAuthContext = _extract_auth_context(self, info, **kwargs)
        _check_preprocessing_errors(self, auth_ctx, self._logger)

        return self._check_scope(auth_ctx)

    def graphql_client_error_args(self) -> tuple[Any, ...]:
        return (self._scope,)

    def _check_scope(self, auth_ctx: JwtAuthContext) -> bool:
        # Allow hierarchical scopes like "users:read" implied by "users:*"
        if not auth_ctx.iam_scopes:
            return False
        if self._scope in auth_ctx.iam_scopes:
            return True

        prefix = self._scope.split(":")[0] + ":*"
        return prefix in auth_ctx.iam_scopes


@fastql_type_error
class AuthorizedRoleOrScopeRequiredError(GraphQLClientError):
    """Error raised when an authorization role is required but it is missing"""

    permitted_roles: list[str]
    permitted_scopes: list[str]

    def __init__(self, permitted_roles: list[str], permitted_scopes: list[str]) -> None:
        super().__init__("authorization_role_or_scope_required", status=403)
        self.permitted_roles = permitted_roles
        self.permitted_scopes = permitted_scopes


class HasRoleOrScope(GraphQLPermission, WithLogger):
    graphql_client_error_class = AuthorizedRoleOrScopeRequiredError
    graphql_server_error_class = AuthorizationServerError

    def __init__(self, roles: Sequence[str | HasRole] = (), scopes: Sequence[str | HasScope] = ()):
        self._roles = roles
        self._role_permissions: list[HasRole] = [
            role if isinstance(role, HasRole) else HasRole(role) for role in roles
        ]
        self._scopes = scopes
        self._scope_permissions: list[HasScope] = [
            scope if isinstance(scope, HasScope) else HasScope(scope) for scope in scopes
        ]

    def has_permission(self, source, info, **kwargs) -> bool:
        auth_ctx: JwtAuthContext = _extract_auth_context(self, info, **kwargs)
        _check_preprocessing_errors(self, auth_ctx, self._logger)

        has_role: bool = any(
            perm.has_permission(source, info, auth_ctx=auth_ctx) for perm in self._role_permissions
        )
        has_scope: bool = False
        if not has_role:
            has_scope = any(
                perm.has_permission(source, info, auth_ctx=auth_ctx)
                for perm in self._scope_permissions
            )
        return bool(has_role or has_scope)

    def graphql_client_error_args(self) -> tuple[Any, ...]:
        return (
            self._roles,
            self._scopes,
        )
