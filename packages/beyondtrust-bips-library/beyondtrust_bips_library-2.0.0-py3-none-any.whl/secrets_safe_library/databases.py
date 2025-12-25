"""Databases module, all the logic to manage databases from BeyondInsight API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import (
    POST_DATABASES_ASSET_ID,
    PUT_DATABASES_ID,
)
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.databases import fields as databases_fields


class Database(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger)

        # Schema rules used for validations
        self._schema = {
            "instance_name": {"type": "string", "maxlength": 100, "nullable": True},
            "database_id": {"type": "integer"},
            "asset_id": {"type": "integer"},
            "platform_id": {"type": "integer"},
            "port": {"type": "integer", "nullable": True},
            "version": {"type": "string", "maxlength": 20, "nullable": True},
        }
        self._validator = Validator(self._schema)

    def get_databases(self) -> list:
        """
        Returns all Databases.

        API: GET Databases

        Returns:
            list: List of Databases.
        """

        endpoint = "/databases"

        utils.print_log(
            self._logger,
            "Calling get_databases endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_database_by_id(self, database_id: int) -> dict:
        """
        Returns a Database by ID.

        API: GET Databases/{id}

        Args:
            database_id (int): The Database ID.

        Returns:
            dict: Database.
        """

        attributes = {"database_id": database_id}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/databases/{database_id}"

        utils.print_log(
            self._logger,
            "Calling get_database_by_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_databases_by_asset_id(self, asset_id: int) -> list:
        """
        Returns all Databases by Asset ID.

        API: GET Assets/{assetId}/Databases

        Args:
            asset_id (int): The Asset ID.

        Returns:
            list: List of Databases.
        """

        attributes = {"asset_id": asset_id}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/assets/{asset_id}/databases"

        utils.print_log(
            self._logger,
            "Calling get_databases_by_asset_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def post_database_by_asset_id(
        self,
        asset_id: int,
        platform_id: int,
        port: int,
        instance_name: str = None,
        is_default_instance: bool = None,
        version: str = None,
        template: str = None,
    ) -> dict:
        """
        Creates a new Database by Asset ID.

        API: POST Assets/{assetId}/Databases

        Args:
            asset_id (int): The Asset ID.
            platform_id (int): The Platform ID.
            port (int): The Port.
            instance_name (str, optional): The Instance Name.
            is_default_instance (bool, optional): Is Default Instance.
            version (str, optional): The Version.
            template (str, optional): The Template.

        Returns:
            dict: Database.
        """

        attributes = {
            "asset_id": asset_id,
            "platform_id": platform_id,
            "instance_name": instance_name,
            "port": port,
            "version": version,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            databases_fields, POST_DATABASES_ASSET_ID, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            platform_id=platform_id,
            instance_name=instance_name,
            is_default_instance=is_default_instance,
            port=port,
            version=version,
            template=template,
        )

        endpoint = f"/assets/{asset_id}/databases"

        utils.print_log(
            self._logger,
            "Calling post_database_by_asset_id endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def put_database_by_id(
        self,
        database_id: int,
        platform_id: int,
        instance_name: str = None,
        is_default_instance: bool = None,
        port: int = None,
        version: str = None,
        template: str = None,
    ) -> dict:
        """
        Updates a Database by ID.

        API: PUT Databases/{id}

        Args:
            database_id (int): The Database ID.
            platform_id (int): The Platform ID.
            instance_name (str, optional): The Instance Name.
            is_default_instance (bool, optional): Is Default Instance.
            port (int, optional): The Port.
            version (str, optional): The Version.
            template (str, optional): The Template.

        Returns:
            dict: Database.
        """

        attributes = {
            "database_id": database_id,
            "platform_id": platform_id,
            "instance_name": instance_name,
            "port": port,
            "version": version,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            databases_fields, PUT_DATABASES_ID, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            platform_id=platform_id,
            instance_name=instance_name,
            is_default_instance=is_default_instance,
            port=port,
            version=version,
            template=template,
        )

        endpoint = f"/databases/{database_id}"

        utils.print_log(
            self._logger,
            "Calling put_database_by_id endpoint",
            logging.DEBUG,
        )
        response = self._run_put_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def delete_database_by_id(self, database_id: int) -> None:
        """
        Deletes a Database by ID.

        API: DELETE Databases/{id}

        Args:
            database_id (int): The Database ID.

        Returns:
            None: If deletion is successful no exceptions.DeletionError is raised.
        """

        attributes = {"database_id": database_id}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/databases/{database_id}"

        utils.print_log(
            self._logger,
            "Calling delete_database_by_id endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)
