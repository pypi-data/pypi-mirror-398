"""Credentials module, all the logic to manage Credentials from Password Safe API"""

import logging

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject


class Credentials(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/credentials")

        # Schema rules used for validations
        self._schema = {
            "request_id": {"type": "integer", "nullable": True},
            "alias_id": {"type": "integer", "nullable": True},
            "type": {
                "type": "string",
                "allowed": ["password", "dsskey"],
                "nullable": True,
            },
        }
        self._validator = self._validator = utils.Validator(self._schema)

    def get_credentials_by_request_id(self, request_id: int, type: str = None) -> dict:
        """
        Returns credentials by request ID.

        API: GET Credentials/{requestid}

        Args:
            request_id (int): The request ID.
            type (str, optional): The type of credentials to return. Options are:
                - password (default): Returns the password in the response body.
                - dsskey: Returns the DSS private key in the response body.
        Returns:
            dict: Credentials.
        """

        attributes = {"request_id": request_id, "type": type}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        params = {"type": type}

        query_string = self.make_query_string(params)

        endpoint = f"{self.endpoint}/{request_id}?{query_string}"

        utils.print_log(
            self._logger,
            "Calling get_credentials_by_request_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_credentials_by_alias_id(
        self, alias_id: int, request_id: int, type: str = None
    ) -> dict:
        """
        Returns credentials by alias ID.

        API: GET Aliases/{aliasId}/Credentials/{requestId}

        Args:
            alias_id (int): The alias ID.
            request_id (int): The request ID.
            type (str, optional): The type of credentials to return. Options are:
                - password (default): Returns the password in the response body.
                - dsskey: Returns the DSS private key in the response body.
        Returns:
            dict: Credentials.
        """

        attributes = {"alias_id": alias_id, "request_id": request_id, "type": type}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        params = {"type": type}

        query_string = self.make_query_string(params)

        endpoint = f"/aliases/{alias_id}/credentials/{request_id}?{query_string}"

        utils.print_log(
            self._logger,
            "Calling get_credentials_by_alias_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()
