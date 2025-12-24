import datetime
import re
from dataclasses import dataclass

from fastapi_lifespan_manager import LifespanManager
from jwcrypto.jwk import JWK
from pydantic import Field

from apppy.auth.errors.jwks import IllegalJwksPemFileError
from apppy.auth.errors.service import (
    ServiceAuthenticationDisabledError,
    ServiceKeyMissingError,
    ServiceUnknownError,
)
from apppy.env import Env, EnvSettings
from apppy.fs import FileSystem, FileUrl
from apppy.logger import WithLogger


@dataclass
class JwkPemFile:
    file_url: FileUrl

    is_public: bool
    service_name: str
    version: int
    generated_at: datetime.datetime

    @property
    def file_ext(self) -> str:
        return "pub.pem" if self.is_public else "key.pem"

    @property
    def kid(self) -> str:
        return f"{self.service_name}.v{self.version}"

    @staticmethod
    def file_name_private(service_name: str, version: int, generated_at: datetime.datetime) -> str:
        generated_ts = generated_at.strftime("%Y%m%d%H%M%S")
        return f"{service_name}.v{version}.{generated_ts}.key.pem"

    @staticmethod
    def file_name_public(service_name: str, version: int, generated_at: datetime.datetime) -> str:
        generated_ts = generated_at.strftime("%Y%m%d%H%M%S")
        return f"{service_name}.v{version}.{generated_ts}.pub.pem"

    @staticmethod
    def from_file_url(file_url: FileUrl) -> "JwkPemFile":
        if file_url.file_name is None:
            raise IllegalJwksPemFileError("unavailable_pem_file_name")

        service_name, version, generated_at = JwkPemFile._parse_file_name(file_url.file_name)
        return JwkPemFile(
            file_url=file_url,
            is_public=file_url.file_name.endswith("pub.pem"),
            service_name=service_name,
            version=version,
            generated_at=generated_at,
        )

    @staticmethod
    def _parse_file_name(file_name: str) -> tuple[str, int, datetime.datetime]:
        if not file_name.endswith(".pub.pem") and not file_name.endswith(".key.pem"):
            raise IllegalJwksPemFileError("unknown_pem_file_extension")

        pattern = (
            r"^(?P<service>[a-zA-Z0-9_-]+)\.v(?P<version>\d+)\.(?P<ts>\d{14})\.(pub|key)\.pem$"
        )
        m = re.match(pattern, file_name)
        if not m:
            raise ValueError(f"Invalid filename format: {file_name}")

        service_name = m.group("service")
        version = int(m.group("version"))
        ts_str = m.group("ts")
        generated_at = datetime.datetime.strptime(ts_str, "%Y%m%d%H%M%S")

        return (service_name, version, generated_at)

    @staticmethod
    def parse_kid(kid: str | None) -> tuple[str | None, int | None]:
        if kid is None:
            return (None, None)

        pattern = r"^(?P<service>[a-zA-Z0-9_-]+)\.v(?P<version>\d+)$"
        m = re.match(pattern, kid)
        if not m:
            return (None, None)

        service_name = m.group("service")
        version = int(m.group("version"))

        return (service_name, version)


@dataclass
class JwkInfo:
    key: dict
    jwk: JWK
    pem: JwkPemFile


class JwksAuthStorageSettings(EnvSettings):
    # NOTE: Some of these configuration values are general to all authentication
    # so those use the APP_AUTH prefix. Configuration values specific to jwks use
    # the APP_JWKS_AUTH prefix.

    # Control whether JWKS authenication is available.
    # If not available (the default), JwksAuth will not attempt to read
    # any files from the FileSystem.
    # Note that this is useful for integration tests. Some integration tests
    # run with an encrypted FileSystem and some without. So they cannot share
    # pem files.

    # JWKS_AUTH_ENABLED
    enabled: bool = Field(default=False)
    # JWKS_AUTH_FS_PARTITION
    fs_partition: str = Field(default="auth")
    # JWKS_AUTH_ROOT_DIR
    root_dir: str = Field(default=".jwks")

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="JWKS_AUTH")


class JwksAuthStorage(WithLogger):
    def __init__(
        self, settings: JwksAuthStorageSettings, lifespan: LifespanManager, fs: FileSystem
    ):
        self._settings = settings
        self._fs = fs

        self._jwks_root_file_url: FileUrl = self._fs.new_file_url_internal(
            protocol=self._fs.settings.default_protocol,
            partition=settings.fs_partition,
            directory=settings.root_dir,
            file_name=None,
        )
        self._jwks_full_cache: dict[str, list[JwkInfo]] = {}
        self._jwks_version_cache: dict[str, int] = {}

        self._keys: list[dict] = []
        self._keys_dict = {"keys": self._keys}
        if self._settings.enabled is True:
            lifespan.add(self.rebuild_caches)

    def _clear_cache(self):
        self._jwks_full_cache.clear()
        self._jwks_version_cache.clear()
        self._keys.clear()

    def add_jwk(self, pem_file_url: FileUrl) -> JwkInfo:
        if not self._fs.exists(self._jwks_root_file_url):
            self._fs.makedir(self._jwks_root_file_url, create_parents=True)

        pem_file: JwkPemFile = JwkPemFile.from_file_url(pem_file_url)
        pem_file_bytes: bytes = self._fs.read_bytes(pem_file_url)
        jwk_: JWK = JWK.from_pem(pem_file_bytes)
        key = jwk_.export_public(as_dict=True)
        key["use"] = "sig"
        key["alg"] = "EdDSA"
        key["kid"] = pem_file.kid

        if pem_file.service_name not in self._jwks_full_cache:
            self._jwks_full_cache[pem_file.service_name] = []

        jwk_info = JwkInfo(key=key, jwk=jwk_, pem=pem_file)
        self._jwks_full_cache[pem_file.service_name].append(jwk_info)

        if (
            pem_file.service_name not in self._jwks_version_cache
            or self._jwks_version_cache[pem_file.service_name] < pem_file.version
        ):
            self._jwks_version_cache[pem_file.service_name] = pem_file.version

        self._keys.append(key)
        return jwk_info

    def all_services(self) -> dict[str, list[JwkPemFile]]:
        if self._settings.enabled is False:
            raise ServiceAuthenticationDisabledError()

        return {s: [j.pem for j in jwk_infos] for s, jwk_infos in self._jwks_full_cache.items()}

    def clear_all_jwks(self) -> None:
        if self._fs.exists(self._jwks_root_file_url):
            self._fs.rm(self._jwks_root_file_url, recursive=True)

        self._clear_cache()

    def current_service_version(self, service_name: str) -> int | None:
        if self._settings.enabled is False:
            raise ServiceAuthenticationDisabledError()

        return self._jwks_version_cache.get(service_name)

    def get_jwk(self, kid: str) -> JwkInfo:
        if self._settings.enabled is False:
            raise ServiceAuthenticationDisabledError()

        service_name, _ = JwkPemFile.parse_kid(kid)
        if service_name is None or service_name not in self._jwks_full_cache:
            raise ServiceUnknownError()

        jwk_info = next(
            filter(
                lambda e: e.pem.kid == kid,
                self._jwks_full_cache[service_name],
            ),
            None,
        )
        if jwk_info is None:
            raise ServiceKeyMissingError()

        return jwk_info

    @property
    def is_enabled(self) -> bool:
        return self._settings.enabled

    @property
    def keys_dict(self) -> dict:
        if self._settings.enabled is False:
            raise ServiceAuthenticationDisabledError()

        return self._keys_dict

    async def rebuild_caches(self):
        if self._settings.enabled is False:
            raise ServiceAuthenticationDisabledError()

        if not self._fs.exists(self._jwks_root_file_url):
            self._fs.makedir(self._jwks_root_file_url, create_parents=True)

        self._clear_cache()

        for service_dir in self._fs.ls(self._jwks_root_file_url):
            service_dir_url = self._fs.parse_file_url(service_dir["url"])
            if self._fs.isdir(service_dir_url):
                self._jwks_full_cache[service_dir_url.directory] = []  # type: ignore[invalid-assignment]
                for pem_file in self._fs.ls(service_dir_url):
                    pem_file_url = self._fs.parse_file_url(pem_file["url"])
                    if self._fs.isfile(pem_file_url):
                        self.add_jwk(pem_file_url)

        yield {
            "jwks_full_cache": self._jwks_full_cache,
            "jwks_version_cache": self._jwks_version_cache,
            "keys": self._keys,
        }

    # IMPORTANT NOTE: Each server instance keeps an in-memory cache of
    # all jwks records. Thus if you are running multiple instances and
    # you write a new public key (e.g. due to regular rotation maintenance)
    # you will need to ensure that all server instances are rebooted.
    async def write_public_key(self, service_name: str, key_bytes: bytes) -> JwkInfo:
        if self._settings.enabled is False:
            raise ServiceAuthenticationDisabledError()

        version = (
            self._jwks_version_cache[service_name] + 1
            if service_name in self._jwks_version_cache
            else 0
        )
        generated_at = datetime.datetime.now(datetime.UTC)

        pem_file_url: FileUrl = self._jwks_root_file_url.join(
            directory=service_name,
            file_name=JwkPemFile.file_name_public(service_name, version, generated_at),
        )
        service_dir_url = pem_file_url.parent()
        if not self._fs.exists(service_dir_url):
            self._fs.makedir(url=pem_file_url.parent(), create_parents=True)

        pem_file_url, _ = await self._fs.write_bytes(pem_file_url, key_bytes)
        return self.add_jwk(pem_file_url)
