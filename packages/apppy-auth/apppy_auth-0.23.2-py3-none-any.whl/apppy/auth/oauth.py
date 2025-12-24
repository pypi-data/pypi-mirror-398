from authlib.integrations.starlette_client import OAuth

from apppy.auth.errors.oauth import UnknownOAuthProviderError
from apppy.env import EnvSettings
from apppy.logger import WithLogger


class OAuthRegistrySettings(EnvSettings):
    pass


class OAuthRegistry(OAuth, WithLogger):
    """
    Wrapper about the Starlette OAuth integration to allow for
    any custom settings or logic to be added.
    """

    def __init__(self, settings: OAuthRegistrySettings) -> None:
        super().__init__()
        self._settings = settings

    def load_client(self, provider: str) -> OAuth:
        oauth_client = self.create_client(provider)
        if oauth_client is None:
            raise UnknownOAuthProviderError(provider)

        return oauth_client

    def register(self, name, overwrite=False, **kwargs):
        self._logger.info("Registering OAuth provider", extra={"provider": name})
        super().register(name, overwrite=overwrite, **kwargs)
