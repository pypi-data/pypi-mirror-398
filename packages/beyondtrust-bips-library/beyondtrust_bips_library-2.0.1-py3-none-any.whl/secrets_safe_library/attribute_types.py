"""
Attribute Types module, all the logic to manage attribute types from BeyondInsight API
"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import DeleteByIdMixin, GetByIdMixin, ListMixin

# Maximum length for attribute type name
ATTRIBUTE_TYPE_NAME_MAX_LENGTH = 64


class AttributeType(APIObject, GetByIdMixin, DeleteByIdMixin, ListMixin):
    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/attributetypes")

        # Schema rules used for validations
        self._schema = {
            "name": {
                "type": "string",
                "maxlength": ATTRIBUTE_TYPE_NAME_MAX_LENGTH,
                "empty": False,
            },
        }

        self._validator = Validator(self._schema)

    def create_attribute_type(self, name: str) -> dict:
        """
        Creates a new Attribute Type.

        API: POST /AttributeTypes

        Args:
            name (str): The name of the attribute type.

        Returns:
            dict: Created Attribute Type object.
        """

        attributes = {"name": name}

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Name": name,
        }

        utils.print_log(
            self._logger,
            f"Calling create attribute type endpoint: {self.endpoint}",
            logging.DEBUG,
        )
        response = self._run_post_request(
            self.endpoint, payload, include_api_version=False
        )

        return response.json()
