import logging
import os

from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject


def configure_logging() -> None:
    propagate_setting = os.getenv("URLLIB3_PROPAGATE", "False").lower() in [
        "true",
        "1",
        "t",
    ]
    logging.getLogger("urllib3").propagate = propagate_setting


class Configuration(APIObject):
    """
    Class to manage configuration related operations from PS API.
    """

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/configuration")

    def get_version(self) -> dict:
        """
        Returns the current system version.

        API: GET configuration/version

        Returns:
            dict: Version information containing Version field.
        """
        endpoint = f"{self.endpoint}/version"

        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()
