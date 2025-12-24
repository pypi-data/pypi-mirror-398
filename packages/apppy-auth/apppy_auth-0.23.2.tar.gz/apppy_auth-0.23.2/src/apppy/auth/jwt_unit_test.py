import datetime

from apppy.auth.jwt import JwtAuthContext


class FakeJWT:
    """
    Minimal stub for the JWT class used by JwtAuthContext.
    - Accepts _token to simulate "has token" vs not.
    - Returns the provided claims from get_raw_jwt().
    """

    def __init__(self, *, _token=None, claims=None, **kwargs):
        self._token = _token
        self._claims = claims

    def get_raw_jwt(self):
        return self._claims


def _claims_base(exp=1111111111, iat=1111110000, **extra):
    c = {"exp": exp, "iat": iat}
    c.update(extra)
    return c


def test_jwt_empty():
    ctx = JwtAuthContext()
    assert ctx.has_token is False
    assert ctx.is_token_well_formed is False
    assert ctx.expires_at == 0
    assert ctx.issued_at == 0
    # sanity: optional fields default to None
    assert ctx.auth_session_id is None
    assert ctx.auth_subject_id is None
    assert ctx.auth_subject_type is None
    assert ctx.iam_enabled is False

    assert ctx.iam_revoked_at is None
    assert ctx.iam_role is None
    assert ctx.iam_scopes is None

    assert ctx.raw_claims is None


def test_jwt_is_unauthenticated_when_no_token():
    jwt = FakeJWT(_token=None, claims=None)
    ctx = JwtAuthContext.from_jwt(jwt)  # type: ignore[invalid-argument-type]
    assert ctx.has_token is False
    assert ctx.is_token_well_formed is False
    assert ctx.iam_enabled is False


def test_jwt_is_unauthenticated_when_no_claims():
    jwt = FakeJWT(_token="token", claims=None)
    ctx = JwtAuthContext.from_jwt(jwt)  # type: ignore[invalid-argument-type]
    assert ctx.has_token is False
    assert ctx.is_token_well_formed is False
    assert ctx.iam_enabled is False


def test_jwt_is_unauthenticated_when_missing_user_metadata():
    claims = _claims_base()  # no "user_metadata" key
    jwt = FakeJWT(_token="token", claims=claims)
    ctx = JwtAuthContext.from_jwt(jwt)  # type: ignore[invalid-argument-type]
    assert ctx.has_token is True
    assert ctx.is_token_well_formed is False
    assert ctx.iam_enabled is False


def test_service_jwt_is_unauthenticated_when_iam_is_disabled():
    claims = _claims_base(
        user_metadata={
            "subject_type": "service",
            "iam_metadata": {
                "enabled": False,
            },
        }
    )
    jwt = FakeJWT(_token="token", claims=claims)
    ctx = JwtAuthContext.from_jwt(jwt)  # type: ignore[invalid-argument-type]
    assert ctx.has_token is True
    assert ctx.is_token_well_formed is True
    assert ctx.iam_enabled is False


def test_service_jwt_is_unauthenticated_when_iam_is_revoked():
    claims = _claims_base(
        user_metadata={
            "subject_type": "service",
            "iam_metadata": {"enabled": True, "revoked_at": datetime.datetime.now()},
        }
    )
    jwt = FakeJWT(_token="token", claims=claims)
    ctx = JwtAuthContext.from_jwt(jwt)  # type: ignore[invalid-argument-type]
    assert ctx.has_token is True
    assert ctx.is_token_well_formed is True
    assert ctx.iam_enabled is True
    assert ctx.iam_revoked_at is not None


def test_service_jwt_subject_type():
    claims = _claims_base(
        service_metadata={
            "subject_type": "service",
            "iam_metadata": {
                "enabled": True,
            },
        }
    )
    jwt = FakeJWT(_token="token", claims=claims)

    ctx = JwtAuthContext.from_jwt(jwt)  # type: ignore[invalid-argument-type]
    assert ctx.auth_subject_type == "service"


def test_user_jwt_is_unauthenticated_when_iam_is_disabled():
    claims = _claims_base(
        user_metadata={
            "subject_type": "user",
            "iam_metadata": {
                "enabled": False,
            },
        }
    )
    jwt = FakeJWT(_token="token", claims=claims)
    ctx = JwtAuthContext.from_jwt(jwt)  # type: ignore[invalid-argument-type]
    assert ctx.has_token is True
    assert ctx.is_token_well_formed is True
    assert ctx.iam_enabled is False


def test_user_jwt_is_unauthenticated_when_iam_is_revoked():
    claims = _claims_base(
        user_metadata={
            "subject_type": "user",
            "iam_metadata": {"enabled": True, "revoked_at": datetime.datetime.now()},
        }
    )
    jwt = FakeJWT(_token="token", claims=claims)
    ctx = JwtAuthContext.from_jwt(jwt)  # type: ignore[invalid-argument-type]
    assert ctx.has_token is True
    assert ctx.is_token_well_formed is True
    assert ctx.iam_enabled is True
    assert ctx.iam_revoked_at is not None


def test_user_jwt_subject_type():
    claims = _claims_base(
        user_metadata={
            "subject_type": "user",
            "iam_metadata": {
                "enabled": True,
            },
        }
    )
    jwt = FakeJWT(_token="token", claims=claims)

    ctx = JwtAuthContext.from_jwt(jwt)  # type: ignore[invalid-argument-type]
    assert ctx.auth_subject_type == "user"
