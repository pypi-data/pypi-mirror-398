import threading
import time
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from frogml.core.exceptions import FrogmlLoginException
from frogml.storage.authentication.models import BearerAuth
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from requests import Response


class TokenMaintainer(BaseModel):
    model_config = ConfigDict(frozen=True)

    token_rotation_interval_seconds: int = Field(ge=0)
    token_rotation_grace_period_seconds: int = Field(ge=0)
    token_rotation_generation_timeout_seconds: int = Field(ge=0)
    base_token: str
    base_url: str
    __token_scope: str = ""
    __curr_token: Optional[str] = None
    __curr_token_cache_expiration: float
    __lock: threading.RLock = PrivateAttr(default_factory=threading.RLock)
    __refreshing: bool = False

    def model_post_init(self, context: Any, /) -> None:
        self.__curr_token_cache_expiration = (
            -2
            * (
                self.token_rotation_interval_seconds
                + self.token_rotation_grace_period_seconds
            )
            - 1.0
        )

        self.__extract_token_scope()

    def get_token(self) -> str:
        curr_time = time.monotonic()

        if curr_time > self.__curr_token_cache_expiration:
            # need to refresh (either because it's about to expire it was never loaded)
            # note that this does not necessarily mean the current value can't be used
            self.trigger_background_load()

        if (
            curr_time
            > self.__curr_token_cache_expiration
            + self.token_rotation_grace_period_seconds
        ):
            # the current value is either no longer valid (passed its grace) or was never loaded, return the base token
            return self.base_token

        return self.__curr_token

    def __refresh(self):
        next_curr_value_expiration: float = (
            time.monotonic() + self.token_rotation_interval_seconds
        )
        try:
            token = self.__generate_token()
            with self.__lock:
                self.__curr_token = token
                self.__curr_token_cache_expiration = next_curr_value_expiration
        finally:
            with self.__lock:
                self.__refreshing = False

    def __generate_token(self) -> str:
        try:
            url: str = urljoin(self.base_url, "/access/api/v1/tokens")
            token_life_duration: int = int(
                self.token_rotation_interval_seconds
                + self.token_rotation_grace_period_seconds
            )
            resp: Response = requests.post(
                url,
                data={"expires_in": token_life_duration, "scope": self.__token_scope},
                auth=BearerAuth(self.base_token),
                timeout=self.token_rotation_generation_timeout_seconds,
            )
            resp.raise_for_status()
            return resp.json()["access_token"]
        except Exception as e:
            raise FrogmlLoginException("Failed to generate token: {}".format(e)) from e

    def trigger_background_load(self):
        with self.__lock:
            if self.__refreshing:
                # another refresh is ongoing, do not disturb it
                return
            # first start a thread for refreshing the token,
            # then mark self as refreshing (to prevent a phantom refresh)
            threading.Thread(target=self.__refresh, daemon=True).start()
            self.__refreshing = True

    def __extract_token_scope(self):
        # parsing the base token to get its scope (which is used for generating new ones)
        # note that here it does not matter whether the token is valid or not, we care
        # only about the scope
        try:
            import jwt

            parsed_token = jwt.decode(
                self.base_token,
                options={
                    "verify_signature": False
                },  # NOSONAR(S5659) we only parse the token, no authentication happens here
            )
        except Exception as e:
            raise FrogmlLoginException(
                "Failed to decode JWT token: {}".format(e)
            ) from e

        if "scp" not in parsed_token:
            raise FrogmlLoginException("Invalid token - missing scp claim")

        self.__token_scope = parsed_token["scp"]
