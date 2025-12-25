"""ISA Requests module, all the logic to manage ISA Requests from PS API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject


class ISARequest(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/isarequests")

        self._schema = {
            "system_id": {"type": "integer", "nullable": False},
            "reason": {"type": "string", "maxlength": 256, "nullable": True},
            "account_id": {"type": "integer", "nullable": False},
            "duration_minutes": {"type": "integer", "nullable": True},
            "type": {
                "type": "string",
                "allowed": ["password", "dsskey", "passphrase"],
                "nullable": True,
            },
        }
        self._validator = Validator(self._schema)

    def create_isa_request(
        self,
        system_id: int,
        account_id: int,
        duration_minutes: int = None,
        reason: str = None,
        type: str = "password",
    ) -> dict:
        """
        Creates a new Information Systems Administrator (ISA) release request.

        API: POST ISARequests

        Args:
            system_id (int): ID of the managed system to request.
            account_id (int): ID of the managed account to request.
            duration_minutes (int, optional): The request duration in minutes. Defaults
                to None.
            reason (str, optional): The reason for the request. Defaults to None.
            type (str, optional): Type of credentials to retrieve. Options are:
                                  - password (default): Returns the password in
                                    the response body.
                                  - dsskey: Returns the DSS private key in the
                                    response body.
                                  - passphrase: Returns the DSS key passphrase in
                                    the response body.

        Returns:
            dict: Response containing requested credentials.
        """

        attributes = {
            "system_id": system_id,
            "reason": reason,
            "account_id": account_id,
            "duration_minutes": duration_minutes,
            "type": type,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "SystemID": system_id,
            "AccountID": account_id,
            "DurationMinutes": duration_minutes,
            "Reason": reason,
        }

        params = {
            "type": type,
        }

        query_string = self.make_query_string(params)

        endpoint = f"{self.endpoint}?{query_string}"

        utils.print_log(
            self._logger,
            f"Calling create_isa_request endpoint: {endpoint}",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, payload, include_api_version=False)

        return response.json()
