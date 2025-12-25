"""Safes module, all the logic to manage safes from PS API"""

import logging
from typing import Tuple

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import DeleteByIdMixin, GetByIdMixin, ListMixin


class Safe(APIObject, GetByIdMixin, DeleteByIdMixin, ListMixin):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/secrets-safe/safes")

        # Schema rules used for validations
        self._schema = {
            "name": {"type": "string", "maxlength": 256, "nullable": True},
            "description": {"type": "string", "maxlength": 256, "nullable": True},
        }
        self._validator = Validator(self._schema)

    def create_safe(
        self,
        name: str,
        description: str = "",
    ) -> dict:
        """
        Creates a new Safe.

        API: POST Secrets-Safe/Safes/

        Args:
            name (str): The safe name.
            description (str, optional): The safe description.

        Returns:
            dict: Created Safe object.
        """

        attributes = {"name": name, "description": description}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Name": name,
            "Description": description,
        }
        endpoint = "/secrets-safe/safes"

        utils.print_log(self._logger, "Calling create safe endpoint", logging.DEBUG)
        response = self._run_post_request(endpoint, payload, include_api_version=False)

        return response.json()

    def update_safe(
        self,
        safe_id: str,
        name: str,
        description: str = "",
    ) -> Tuple[str, int]:
        """
        Update an existing Safe using its ID.

        API: PUT secrets-safe/safes/{id}

        Args:
            safe_id (str): The safe ID (GUID).
            name (str): The safe name.
            description (str, optional): The safe description.

        Returns:
            Tuple[str, int]: Tuple containing raw response and int response status code.
        """

        attributes = {"name": name, "description": description}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Name": name,
            "Description": description,
        }
        endpoint = f"/secrets-safe/safes/{safe_id}"

        utils.print_log(self._logger, "Calling update safe endpoint", logging.DEBUG)
        response = self._run_put_request(
            endpoint,
            payload,
            include_api_version=False,
            expected_status_code=[204, 409],
        )

        return response.text, response.status_code
