from frogml_inference.authentication.authentication_utils import get_credentials
from frogml_inference.configuration import FrogMLAuthClient, Session
from frogml_inference.constants import FrogMLConstants
from frogml_inference.exceptions import FrogMLLoginException


class UserAccountConfiguration:
    API_KEY_FIELD = "api_key"

    def __init__(
        self,
        config_file=None,
        auth_client: FrogMLAuthClient = None,
    ):
        if config_file:
            self._config_file = config_file
        else:
            self._config_file = FrogMLConstants.FROGML_CONFIG_FILE

        self._auth_client = auth_client
        self._environment = Session().get_environment()

        if not self._auth_client:
            self._auth_client = FrogMLAuthClient

    def configure_user(self) -> None:
        """
        Write user account to the given config file in an ini format. Configuration will be written under the 'default'
        section
        :param user_account: user account properties to be written
        """
        # Use FrogML's login flow
        _url, _ = get_credentials(None)

        if not _url:
            raise FrogMLLoginException("Failed to authenticate with JFrog")
        # Validate access token
        # TODO: Remove once we support reference token
        token = self._auth_client().get_token()
        if not token or len(token) <= 64:
            raise FrogMLLoginException(
                "Authentication with JFrog failed: Only Access Tokens are supported. Please ensure you are using a valid Access Token."
            )
