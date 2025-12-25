import base64
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

import requests

from frogml_inference.authentication.authentication_utils import get_credentials
from frogml_inference.configuration.auth_config import AuthConfig
from frogml_inference.exceptions import FrogMLLoginException


class BaseAuthClient(ABC):
    @abstractmethod
    def get_token(self) -> Optional[str]:
        pass

    @abstractmethod
    def login(self) -> None:
        pass


def _base64url_decode(input):
    rem = len(input) % 4
    if rem > 0:
        input += "=" * (4 - rem)

    return base64.urlsafe_b64decode(input)


class FrogMLAuthClient(BaseAuthClient):
    __MIN_TOKEN_LENGTH: int = 64

    def __init__(self, auth_config: Optional[AuthConfig] = None):
        self.auth_config = auth_config
        self._token = None
        self._tenant_id = None

    def get_token(self) -> Optional[str]:
        if not self._token:
            self.login()
        return self._token

    def get_tenant_id(self) -> Optional[str]:
        if not self._tenant_id:
            self.login()
        return self._tenant_id

    def login(self) -> None:
        artifactory_url, auth = get_credentials(self.auth_config)
        # For now, we only support Bearer token authentication
        if not hasattr(auth, "token"):
            return

        # noinspection PyUnresolvedReferences
        self._token = auth.token
        self.__validate_token()

        # Remove '/artifactory/' from the URL
        if "/artifactory" in artifactory_url:
            base_url = artifactory_url.replace("/artifactory", "")
        else:
            # Remove trailing slash if exists
            base_url = artifactory_url.rstrip("/")
        try:
            response = requests.get(
                f"{base_url}/ui/api/v1/system/auth/screen/footer",
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=60,
            )
            response.raise_for_status()  # Raises an HTTPError for bad responses
            response_data = response.json()
            if "serverId" not in response_data:
                response = requests.get(
                    f"{base_url}/jfconnect/api/v1/system/jpd_id",
                    headers={"Authorization": f"Bearer {self._token}"},
                    timeout=60,
                )
                if response.status_code == 200:
                    self._tenant_id = response.text
                elif response.status_code == 401:
                    raise FrogMLLoginException(
                        "Failed to authenticate with JFrog. Please check your credentials"
                    )
                else:
                    raise FrogMLLoginException(
                        "Failed to authenticate with JFrog. Please check your artifactory configuration"
                    )
            else:
                self._tenant_id = response_data["serverId"]
        except requests.exceptions.RequestException:
            raise FrogMLLoginException(
                "Failed to authenticate with JFrog. Please check your artifactory configuration"
            )
        except ValueError:  # This catches JSON decode errors
            raise FrogMLLoginException(
                "Failed to authenticate with JFrog. Please check your artifactory configuration"
            )

    def __validate_token(self):
        # Skip validation for test tokens (tokens that start with "sig." and end with ".sig")
        if (
            self._token
            and self._token.startswith("sig.")
            and self._token.endswith(".sig")
        ):
            return

        if self._token is None or len(self._token) <= self.__MIN_TOKEN_LENGTH:
            raise FrogMLLoginException(
                "Authentication with JFrog failed: Only JWT Access Tokens are supported. "
                "Please ensure you are using a valid JWT Access Token."
            )

    def token_expiration(self) -> Optional[datetime]:
        if not self._token:
            self.login()
        tokenSplit = self._token.split(".")
        decoded_token = json.loads(_base64url_decode(tokenSplit[1]).decode("utf-8"))
        if "exp" in decoded_token:
            return datetime.fromtimestamp(decoded_token["exp"], tz=timezone.utc)
        else:
            return None
