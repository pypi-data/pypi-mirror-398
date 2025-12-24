from fastapi import Request
from fastapi_another_jwt_auth import AuthJWT as JWT


def convert_token_to_jwt(token: str) -> JWT:
    # The JWT infrastructure only deals with http requests
    # and responses so we'll emulate an http request in
    # order to run the JWT parsing
    scope = {
        "type": "http",
        "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
    }
    req = Request(scope=scope)
    return extract_jwt_from_request(req)


def extract_jwt_from_request(request: Request) -> JWT:
    jwt = JWT(req=request, res=None)  # type: ignore[invalid-argument-type]
    return jwt
