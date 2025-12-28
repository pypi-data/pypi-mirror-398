import os
from typing import Callable, Optional, Union
from urllib.parse import urljoin

import requests
from cachetools import LRUCache, TTLCache, cached, cachedmethod
from frogml.core.exceptions import FrogmlLoginException
from frogml.core.exceptions.frogml_token_exception import FrogMLTokenException
from frogml.core.inner.tool.auth.token_maintainer import TokenMaintainer
from frogml.storage.authentication.models import AuthConfig, BearerAuth, EmptyAuth
from frogml.storage.authentication.utils import get_credentials
from frogml.storage.constants import (
    JF_ACCESS_TOKEN_RELOAD_INTERVAL_SECONDS,
    JF_SHORT_TOKEN_ROTATION_GENERATION_TIMEOUT_SECONDS,
    JF_SHORT_TOKEN_ROTATION_GENERATION_TIMEOUT_SECONDS_DEFAULT,
    JF_SHORT_TOKEN_ROTATION_GRACE_PERIOD_SECONDS,
    JF_SHORT_TOKEN_ROTATION_GRACE_PERIOD_SECONDS_DEFAULT,
    JF_SHORT_TOKEN_ROTATION_INTERVAL_SECONDS,
    JF_SHORT_TOKEN_ROTATION_INTERVAL_SECONDS_DEFAULT,
    JF_USE_SHORT_TOKEN_ROTATION,
    JF_USE_SHORT_TOKEN_ROTATION_DEFAULT,
)
from requests import Response
from requests.exceptions import RequestException


class FrogMLAuthClient:
    __MIN_TOKEN_LENGTH: int = 64

    def __init__(self, auth_config: Optional[AuthConfig] = None):
        self.__auth_config: Optional[AuthConfig] = auth_config
        self.__token: Optional[str] = None
        self.__tenant_id: Optional[str] = None

        # Initialize instance-level caches
        self.__token_maintainer_cache = LRUCache(maxsize=1)
        self.__tenant_id_cache = LRUCache(maxsize=1)
        self.__jpd_id_cache = LRUCache(maxsize=10)

        self.__base_token_retriever: Callable[[], str] = (
            self.__get_base_token_retriever()
        )
        self.__use_token_maintainer: bool = self.__should_use_token_maintainer()

        # best-effort to prime the token maintainer (if used)
        if self.__use_token_maintainer:
            self.get_token()

    def __should_use_token_maintainer(self) -> bool:
        return (
            str(
                os.getenv(
                    JF_USE_SHORT_TOKEN_ROTATION, JF_USE_SHORT_TOKEN_ROTATION_DEFAULT
                )
            ).upper()
            == "TRUE"
        )

    def get_token(self) -> str:
        base_token: str = self.__base_token_retriever()

        if not self.__use_token_maintainer:
            return base_token

        return self._get_token_maintainer(base_token).get_token()

    @cachedmethod(
        cache=lambda self: self.__token_maintainer_cache,
    )
    def _get_token_maintainer(self, base_token: str) -> TokenMaintainer:
        token_rotation_interval_seconds: int = int(
            os.getenv(
                JF_SHORT_TOKEN_ROTATION_INTERVAL_SECONDS,
                JF_SHORT_TOKEN_ROTATION_INTERVAL_SECONDS_DEFAULT,
            )
        )
        token_rotation_grace_period_seconds: int = int(
            os.getenv(
                JF_SHORT_TOKEN_ROTATION_GRACE_PERIOD_SECONDS,
                JF_SHORT_TOKEN_ROTATION_GRACE_PERIOD_SECONDS_DEFAULT,
            )
        )
        token_rotation_generation_timeout_seconds: int = int(
            os.getenv(
                JF_SHORT_TOKEN_ROTATION_GENERATION_TIMEOUT_SECONDS,
                JF_SHORT_TOKEN_ROTATION_GENERATION_TIMEOUT_SECONDS_DEFAULT,
            )
        )

        return TokenMaintainer(
            base_token=base_token,
            base_url=self.get_base_url(),
            token_rotation_interval_seconds=token_rotation_interval_seconds,
            token_rotation_grace_period_seconds=token_rotation_grace_period_seconds,
            token_rotation_generation_timeout_seconds=token_rotation_generation_timeout_seconds,
        )

    def get_base_token(self) -> str:
        auth: Union[EmptyAuth, BearerAuth] = self.get_auth()

        if isinstance(auth, BearerAuth):
            self.validate_token(auth.token)
            self.__token = auth.token

        else:
            raise FrogMLTokenException(
                message="Token not found in the authentication configurations."
            )

        return self.__token

    @cachedmethod(lambda self: self.__tenant_id_cache)
    def get_tenant_id(self) -> str:
        base_url: str = self.get_base_url()
        url: str = urljoin(base_url, "/ui/api/v1/system/auth/screen/footer")

        try:
            response: Response = requests.get(url, timeout=15, auth=self.get_auth())
            response.raise_for_status()  # Raises an HTTPError for bad responses
            response_data: dict = response.json()

            if "serverId" in response_data:
                self.__tenant_id = response_data["serverId"]
            else:
                self.__tenant_id = self.__get_jpd_id(base_url)

            return self.__tenant_id

        except (RequestException, ValueError) as exc:
            raise FrogmlLoginException(
                "Failed to authenticate with JFrog. Please check your credentials"
            ) from exc

    def get_base_url(self) -> str:
        artifactory_url, _ = get_credentials(self.__auth_config)
        return self.__remove_artifactory_path_from_url(artifactory_url)

    def get_auth(self) -> Union[EmptyAuth, BearerAuth]:
        return get_credentials(self.__auth_config)[1]

    def validate_token(self, token: Optional[str]):
        if token is None or len(token) <= self.__MIN_TOKEN_LENGTH or token.isspace():
            raise FrogmlLoginException(
                "Authentication with JFrog failed: Only JWT Access Tokens are supported. "
                "Please ensure you are using a valid JWT Access Token."
            )

    @cachedmethod(cache=lambda self: self.__jpd_id_cache)
    def __get_jpd_id(self, base_url: str) -> str:
        url: str = urljoin(base_url, "/jfconnect/api/v1/system/jpd_id")
        response: Response = requests.get(url=url, timeout=15, auth=self.get_auth())

        if response.status_code == 200:
            return response.text

        if response.status_code == 401:
            raise FrogmlLoginException(
                "Failed to authenticate with JFrog. Please check your credentials"
            )
        else:
            raise FrogmlLoginException(
                "Failed to authenticate with JFrog. Please check your artifactory configuration"
            )

    def __get_base_token_retriever(self) -> Callable[[], str]:
        if JF_ACCESS_TOKEN_RELOAD_INTERVAL_SECONDS not in os.environ:
            # no reload interval configured, preserve the original behavior of reading each time
            return self.get_base_token

        # base token reload interval is configured, wrap the basic retrieval with a cache
        try:
            ttl: int = int(os.getenv(JF_ACCESS_TOKEN_RELOAD_INTERVAL_SECONDS))
        except ValueError:
            raise FrogmlLoginException(
                f"Value of {JF_ACCESS_TOKEN_RELOAD_INTERVAL_SECONDS} should be an integer"
            )

        cache: TTLCache = TTLCache(ttl=ttl, maxsize=1)

        # Use a constant key since this is a nested function with no parameters
        @cached(cache=cache)
        def get_token() -> str:
            return self.get_base_token()

        return get_token

    @staticmethod
    def __remove_artifactory_path_from_url(artifactory_url: str) -> str:
        # Remove '/artifactory' from the URL
        base_url: str = artifactory_url.replace("/artifactory", "", 1)
        # Remove trailing slash if exists
        return base_url.rstrip("/")
