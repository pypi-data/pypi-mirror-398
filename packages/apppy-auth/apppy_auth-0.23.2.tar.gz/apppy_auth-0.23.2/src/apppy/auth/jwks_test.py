import pytest

from apppy.auth.errors.service import ServiceKeyMissingError
from apppy.auth.fixtures import (
    jwks_auth_storage,  # noqa: F401
)
from apppy.auth.jwks import JwksAuthStorage
from apppy.env.fixtures import (
    current_test_time,
)


async def test_write_public_key(jwks_auth_storage: JwksAuthStorage, pem_file_bytes_public):  # noqa: F811
    jwks_auth_storage.clear_all_jwks()

    service_name = f"test_write_public_key_{current_test_time()}"
    jwk_info = await jwks_auth_storage.write_public_key(service_name, pem_file_bytes_public)

    assert jwk_info is not None
    assert jwk_info.pem.service_name == service_name
    assert jwk_info.pem.version == 0
    assert jwk_info.pem.generated_at is not None

    assert jwks_auth_storage.current_service_version(service_name) == 0

    jwk_info0 = jwks_auth_storage.get_jwk(f"{service_name}.v0")
    assert jwk_info0 is not None
    assert jwk_info0.pem == jwk_info.pem

    with pytest.raises(ServiceKeyMissingError):
        jwks_auth_storage.get_jwk(f"{service_name}.v1")


async def test_rotate_public_key(jwks_auth_storage: JwksAuthStorage, pem_file_bytes_public):  # noqa: F811
    jwks_auth_storage.clear_all_jwks()

    service_name = f"test_rotate_public_key_{current_test_time()}"
    jwk_info_v0 = await jwks_auth_storage.write_public_key(service_name, pem_file_bytes_public)

    assert jwk_info_v0 is not None
    assert jwk_info_v0.pem.version == 0
    assert jwks_auth_storage.current_service_version(service_name) == 0

    jwk_info_v1 = await jwks_auth_storage.write_public_key(service_name, pem_file_bytes_public)
    assert jwk_info_v1 is not None
    assert jwk_info_v1.pem.version == 1
    assert jwks_auth_storage.current_service_version(service_name) == 1

    jwk_info0 = jwks_auth_storage.get_jwk(f"{service_name}.v0")
    assert jwk_info0 is not None
    assert jwk_info0.pem == jwk_info_v0.pem

    jwk_info1 = jwks_auth_storage.get_jwk(f"{service_name}.v1")
    assert jwk_info1 is not None
    assert jwk_info1.pem == jwk_info_v1.pem
