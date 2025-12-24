import datetime

from apppy.auth.jwks import JwkPemFile


def test_jwk_parse_file_name_private():
    service_name, version, generated_at = JwkPemFile._parse_file_name(
        "test_jwk_pem_file_public.v0.20250905215639.key.pem"
    )
    assert service_name == "test_jwk_pem_file_public"
    assert version == 0
    assert generated_at == datetime.datetime(2025, 9, 5, 21, 56, 39, 0)


def test_jwk_parse_file_name_public():
    service_name, version, generated_at = JwkPemFile._parse_file_name(
        "test_jwk_pem_file_public.v0.20250905215639.pub.pem"
    )
    assert service_name == "test_jwk_pem_file_public"
    assert version == 0
    assert generated_at == datetime.datetime(2025, 9, 5, 21, 56, 39, 0)


def test_jwk_parse_kid_none():
    service_name, version = JwkPemFile.parse_kid(None)
    assert service_name is None
    assert version is None


def test_jwk_parse_kid_service():
    service_name, version = JwkPemFile.parse_kid("test_jwk_parse_kid_service.v0")
    assert service_name == "test_jwk_parse_kid_service"
    assert version == 0


def test_jwk_parse_kid_external():
    service_name, version = JwkPemFile.parse_kid("gdXuAFniUzd6iihb")
    assert service_name is None
    assert version is None
