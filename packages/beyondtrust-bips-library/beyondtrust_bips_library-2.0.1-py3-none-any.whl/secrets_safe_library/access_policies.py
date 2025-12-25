"""Access Policies module, all the logic to read and test access policies from PS API"""

import logging
from typing import Tuple

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import ListMixin


class AccessPolicy(APIObject, ListMixin):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/accesspolicies")

        # Schema rules used for validations
        self._schema = {
            "system_id": {"type": "integer", "min": 1, "required": True},
            "account_id": {"type": "integer", "min": 1, "required": True},
            "duration_minutes": {"type": "integer", "min": 1, "default": 60},
        }
        self._validator = Validator(self._schema)

    def test_access_policy(
        self,
        system_id: int,
        account_id: int,
        duration_minutes: int = 60,
    ) -> Tuple[dict, int]:
        """
        Tests access to a managed account and returns a list of Password Safe access
        policies that are available in the request window.

        API: POST AccessPolicies/Test

        Args:
            system_id (int): The ID of the system.
            account_id (int): The ID of the account.
            duration_minutes (int, optional): The duration in minutes for which the
                access is requested. Defaults to 60.

        Returns:
            Tuple[dict, int]: Tuple containing the JSON response and the HTTP status
                code.
        """
        attributes = {
            "system_id": system_id,
            "account_id": account_id,
            "duration_minutes": duration_minutes,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "SystemId": system_id,
            "AccountId": account_id,
            "DurationMinutes": duration_minutes,
        }
        endpoint = f"{self.endpoint}/test"

        utils.print_log(
            self._logger,
            "Calling test access policy endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint, payload, include_api_version=False, expected_status_code=200
        )

        return response.json(), response.status_code
