from pathlib import Path

import pytest
from fastapi_lifespan_manager import LifespanManager

from apppy.auth.jwks import JwksAuthStorage, JwksAuthStorageSettings
from apppy.env import DictEnv, Env
from apppy.env.fixtures import current_test_file, current_test_name, current_test_time
from apppy.fs import FileSystem


@pytest.fixture
def jwks_auth_storage(local_fs: FileSystem):
    env: Env = DictEnv(
        prefix="APP",
        name=current_test_name(),
        d={
            "APP_JWKS_AUTH_ENABLED": True,
            # Create a unique jwks directory for each test to avoid collisions
            "APP_JWKS_AUTH_ROOT_DIR": f"{current_test_file()}/{current_test_name()}",
        },
    )
    jwks_auth_settings = JwksAuthStorageSettings(env)
    jwks_auth_storage: JwksAuthStorage = JwksAuthStorage(
        settings=jwks_auth_settings,
        fs=local_fs,
        lifespan=LifespanManager(),
    )
    yield jwks_auth_storage


##### ##### ##### Pem Files ##### ##### #####
parent_dir = Path(__file__).parent


@pytest.fixture(scope="session")
def pem_file_bytes_private():
    pem_file_private = Path(f"{parent_dir}/test_examples", "test.key.pem")
    pem_file_bytes = pem_file_private.read_bytes()

    yield pem_file_bytes


@pytest.fixture(scope="session")
def pem_file_bytes_public():
    pem_file_public = Path(f"{parent_dir}/test_examples", "test.pub.pem")
    pem_file_bytes = pem_file_public.read_bytes()

    yield pem_file_bytes


@pytest.fixture(scope="session")
def pem_file_bytes_unauthorized():
    pem_file_unregistered = Path(f"{parent_dir}/test_examples", "unauthorized.key.pem")
    pem_file_bytes = pem_file_unregistered.read_bytes()

    yield pem_file_bytes


##### ##### ##### Services ##### ##### #####
@pytest.fixture
def service_name_unique():
    service_name = f"{current_test_name()}_{current_test_time()}"
    yield service_name
