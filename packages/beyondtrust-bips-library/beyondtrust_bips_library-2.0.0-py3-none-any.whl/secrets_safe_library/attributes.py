"""
Attributes module, all the logic to manage attributes from BeyondInsight and
Password Safe API
"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import POST_ATTRIBUTE_ATTRIBUTE_TYPE_ID
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.attributes import fields as attributes_fields
from secrets_safe_library.mixins import DeleteByIdMixin, GetByIdMixin


class Attributes(APIObject, DeleteByIdMixin, GetByIdMixin):
    """
    Attributes class to manage attributes in BeyondInsight and Password Safe API
    """

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/attributes")

        # Schema rules used for validations
        self._schema = {
            "attribute_type_id": {"type": "integer", "nullable": False},
            "managed_account_id": {"type": "integer", "nullable": False},
            "managed_system_id": {"type": "integer", "nullable": False},
            "attribute_id": {"type": "integer", "nullable": False},
            "short_name": {
                "type": "string",
                "minlength": 1,
                "maxlength": 64,
                "nullable": False,
            },
            "long_name": {
                "type": "string",
                "minlength": 1,
                "maxlength": 64,
                "nullable": False,
            },
            "description": {
                "type": "string",
                "minlength": 1,
                "maxlength": 255,
                "nullable": False,
            },
        }
        self._validator = Validator(self._schema)

    def get_attributes_by_attribute_type_id(self, attribute_type_id: int) -> dict:
        """
        Returns a list of attribute definitions by attribute type.

        API: GET AttributeTypes/{attributeTypeID}/Attributes

        Args:
            attribute_type_id (int): The ID of the attribute type.

        Returns:
            dict: Attributes associated with the specified attribute type.
        """

        attributes = {"attribute_type_id": attribute_type_id}

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/attributetypes/{attribute_type_id}{self.endpoint}"

        utils.print_log(
            self._logger,
            "Calling get attributes by attribute type ID endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def post_attribute_by_attribute_type_id(
        self,
        attribute_type_id: int,
        short_name: str,
        long_name: str,
        description: str,
        parent_attribute_id: int = None,
        value_int: int = None,
    ) -> dict:
        """
        Creates a new attribute definition by attribute type ID.

        API: POST AttributeTypes/{attributeTypeID}/Attributes

        Args:
            attribute_type_id (int): The ID of the attribute type.
            short_name (str): The short name of the attribute.
            long_name (str): The long name of the attribute.
            description (str): The description of the attribute.
            parent_attribute_id (int, optional): The ID of the parent attribute.
            value_int (int, optional): The integer value of the attribute.

        Returns:
            dict: The created attribute.
        """

        attributes = {
            "attribute_type_id": attribute_type_id,
            "short_name": short_name,
            "long_name": long_name,
            "description": description,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            attributes_fields, POST_ATTRIBUTE_ATTRIBUTE_TYPE_ID, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            short_name=short_name,
            long_name=long_name,
            description=description,
            parent_attribute_id=parent_attribute_id,
            value_int=value_int,
        )

        endpoint = f"/attributetypes/{attribute_type_id}{self.endpoint}"

        utils.print_log(
            self._logger,
            "Calling post attribute by attribute type ID endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def get_attributes_by_managed_account_id(self, managed_account_id: int) -> dict:
        """
        Returns a list of attribute definitions by managed account ID.

        API: GET ManagedAccounts/{managedAccountID}/Attributes

        Args:
            managed_account_id (int): The ID of the managed account.

        Returns:
            dict: Attributes associated with the specified managed account.
        """

        attributes = {"managed_account_id": managed_account_id}

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/managedaccounts/{managed_account_id}{self.endpoint}"

        utils.print_log(
            self._logger,
            "Calling get attributes by managed account ID endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(
            endpoint, include_api_version=False, expected_status_code=[200, 201]
        )

        return response.json()

    def get_attributes_by_managed_system_id(self, managed_system_id: int) -> dict:
        """
        Returns a list of attribute definitions by managed system ID.

        API: GET ManagedSystems/{managedSystemID}/Attributes

        Args:
            managed_system_id (int): The ID of the managed system.

        Returns:
            dict: Attributes associated with the specified managed system.
        """

        attributes = {"managed_system_id": managed_system_id}

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/managedsystems/{managed_system_id}{self.endpoint}"

        utils.print_log(
            self._logger,
            "Calling get attributes by managed system ID endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def post_attribute_by_managed_account_id(
        self, managed_account_id: int, attribute_id: int
    ) -> dict:
        """
        Assigns an attribute to a managed account.

        API: POST ManagedAccounts/{managedAccountID}/Attributes/{attributeID}

        Args:
            managed_account_id (int): The ID of the managed account.
            attribute_id (int): The ID of the attribute.

        Returns:
            dict: The created attribute.
        """

        attributes = {
            "managed_account_id": managed_account_id,
            "attribute_id": attribute_id,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = (
            f"/managedaccounts/{managed_account_id}{self.endpoint}/{attribute_id}"
        )

        utils.print_log(
            self._logger,
            "Calling post attribute by managed account ID endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint, payload={}, include_api_version=False
        )

        return response.json()

    def post_attribute_by_managed_system_id(
        self, managed_system_id: int, attribute_id: int
    ) -> dict:
        """
        Assigns an attribute to a managed system.

        API: POST ManagedSystems/{managedSystemID}/Attributes/{attributeID}

        Args:
            managed_system_id (int): The ID of the managed system.
            attribute_id (int): The ID of the attribute.

        Returns:
            dict: The created attribute.
        """

        attributes = {
            "managed_system_id": managed_system_id,
            "attribute_id": attribute_id,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/managedsystems/{managed_system_id}{self.endpoint}/{attribute_id}"

        utils.print_log(
            self._logger,
            "Calling post attribute by managed system ID endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint, payload={}, include_api_version=False
        )

        return response.json()

    def delete_attributes_by_managed_account_id(self, managed_account_id: int) -> None:
        """
        Deletes all managed account attributes by managed account ID.

        API: DELETE ManagedAccounts/{managedAccountID}/Attributes

        Args:
            managed_account_id (int): The ID of the managed account.
        """

        attributes = {"managed_account_id": managed_account_id}

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/managedaccounts/{managed_account_id}{self.endpoint}"

        utils.print_log(
            self._logger,
            "Calling delete attributes by managed account ID endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)

    def delete_attributes_by_managed_account_id_attribute_id(
        self, managed_account_id: int, attribute_id: int
    ) -> None:
        """
        Deletes a managed account attribute by managed account ID and attribute ID.

        API: DELETE ManagedAccounts/{managedAccountID}/Attributes/{attributeID}

        Args:
            managed_account_id (int): The ID of the managed account.
            attribute_id (int): The ID of the attribute.
        """

        attributes = {
            "managed_account_id": managed_account_id,
            "attribute_id": attribute_id,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = (
            f"/managedaccounts/{managed_account_id}{self.endpoint}/{attribute_id}"
        )

        utils.print_log(
            self._logger,
            "Calling delete attributes by managed account ID"
            " and attribute ID endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)

    def delete_attributes_by_managed_system_id(self, managed_system_id: int) -> None:
        """
        Deletes all managed system attributes by managed system ID.

        API: DELETE ManagedSystems/{managedSystemID}/Attributes

        Args:
            managed_system_id (int): The ID of the managed system.
        """

        attributes = {"managed_system_id": managed_system_id}

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/managedsystems/{managed_system_id}{self.endpoint}"

        utils.print_log(
            self._logger,
            "Calling delete attributes by managed system ID endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)

    def delete_attributes_by_managed_system_id_attribute_id(
        self, managed_system_id: int, attribute_id: int
    ) -> None:
        """
        Deletes a managed system attribute by managed system ID and attribute ID.

        API: DELETE ManagedSystems/{managedSystemID}/Attributes/{attributeID}

        Args:
            managed_system_id (int): The ID of the managed system.
            attribute_id (int): The ID of the attribute.
        """

        attributes = {
            "managed_system_id": managed_system_id,
            "attribute_id": attribute_id,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/managedsystems/{managed_system_id}{self.endpoint}/{attribute_id}"

        utils.print_log(
            self._logger,
            "Calling delete attributes by managed system ID"
            " and attribute ID endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)
