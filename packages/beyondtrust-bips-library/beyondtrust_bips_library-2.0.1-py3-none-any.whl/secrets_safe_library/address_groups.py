"""
Address groups module, all the logic to manage address groups from BeyondInsight API
"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import DeleteByIdMixin, ListMixin


class AddressGroup(APIObject, DeleteByIdMixin, ListMixin):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/addressgroups")

        # Schema rules used for validations
        self._schema = {
            "name": {"type": "string", "maxlength": 256, "nullable": False},
        }
        self._validator = Validator(self._schema)

    def get_address_group_by_id(self, address_group_id: int) -> dict:
        """
        Find an address group by ID.

        API: GET AddressGroups/{id}

        Args:
            address_group_id (int): The address group ID.

        Returns:
            dict: Address group object according requested API version.
        """

        endpoint = f"{self.endpoint}/{address_group_id}"

        utils.print_log(
            self._logger,
            "Calling get_address_group_by_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_address_group_by_name(self, address_group_name: str) -> dict:
        """
        Returns an address group by name.

        API: GET AddressGroups/?name={name}

        Args:
            address_group_name (str): Name of the address group.

        Returns:
            dict: Address group.
        """

        endpoint = f"{self.endpoint}?name={address_group_name}"

        utils.print_log(
            self._logger,
            "Calling get_address_group_by_name endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def create_address_group(self, name: str) -> dict:
        """
        Creates a new address group.

        API: POST AddressGroups

        Args:
            name (str): Name of the address group.

        Returns:
            dict: Created address group object.
        """

        attributes = {"name": name}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Name": name,
        }

        utils.print_log(
            self._logger,
            f"Calling create_address_group endpoint: {self.endpoint}",
            logging.DEBUG,
        )
        response = self._run_post_request(self.endpoint, payload)

        return response.json()

    def update_address_group(self, address_group_id: int, name: str) -> dict:
        """
        Updates an address group by ID.

        API: PUT AddressGroups/{id}

        Args:
            address_group_id (int): The address group ID.
            name (str): Name of the address group.

        Returns:
            dict: Updated address group object.
        """

        attributes = {"name": name}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Name": name,
        }

        endpoint = f"{self.endpoint}/{address_group_id}"

        utils.print_log(
            self._logger,
            "Calling update_address_group endpoint",
            logging.DEBUG,
        )
        response = self._run_put_request(endpoint, payload)

        return response.json()
