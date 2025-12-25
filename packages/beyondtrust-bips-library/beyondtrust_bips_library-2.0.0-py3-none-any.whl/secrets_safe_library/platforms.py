"""Platforms module, all the logic to manage platforms from PS API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import GetByIdMixin, ListMixin


class Platform(APIObject, ListMixin, GetByIdMixin):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/platforms")

        self._schema = {
            "entity_type_id": {"type": "integer", "nullable": True},
        }
        self._validator = Validator(self._schema)

    def list_by_entity_type(self, entity_type_id: int) -> list:
        """
        Returns a list of Platforms by entity type ID.

        API: GET EntityTypes/{id}/Platforms

        Args:
            entity_type_id (int): The ID of the entity type.

        Returns:
            list: List of platforms associated with the specified entity type.
        """

        attributes = {"entity_type_id": entity_type_id}
        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/entitytypes/{entity_type_id}{self.endpoint}"

        utils.print_log(
            self._logger,
            "Calling list_by_entity_type endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()
