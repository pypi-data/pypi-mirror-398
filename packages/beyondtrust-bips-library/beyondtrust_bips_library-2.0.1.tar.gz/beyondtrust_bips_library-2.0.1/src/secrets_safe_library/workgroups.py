"""Workgroups module, all the logic to manage workgroups from BeyondInsight API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import POST_WORKGROUPS
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.workgroups import fields as workgroups_fields


class Workgroup(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/workgroups")

        # Schema rules used for validations
        self._schema = {
            "name": {"type": "string", "maxlength": 256, "nullable": True},
            "workgroup_id": {"type": "integer", "nullable": True},
        }
        self._validator = Validator(self._schema)

    def get_workgroup_by_id(self, workgroup_id: int) -> dict:
        """
        Returns a Workgroup by ID.

        API: GET Workgroups/{id}

        Args:
            workgroup_id (int): The Workgroup ID.

        Returns:
            dict: Workgroup.
        """

        attributes = {"workgroup_id": workgroup_id}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"{self.endpoint}/{workgroup_id}"

        utils.print_log(
            self._logger,
            "Calling get_workgroup_by_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_workgroup_by_name(self, workgroup_name: str) -> dict:
        """
        Returns a Workgroup by name.

        API: GET Workgroups?name={name}

        Args:
            workgroup_name (str): The Workgroup name.

        Returns:
            dict: Workgroup.
        """

        attributes = {"name": workgroup_name}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"{self.endpoint}?name={workgroup_name}"

        utils.print_log(
            self._logger,
            "Calling get_workgroup_by_name endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_workgroups(self) -> list:
        """
        Returns all Workgroups.

        API: GET Workgroups

        Returns:
            list: List of Workgroups.
        """

        utils.print_log(
            self._logger,
            "Calling get_workgroups endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(self.endpoint, include_api_version=False)

        return response.json()

    def post_workgroup(self, name: str, organization_id: str) -> dict:
        """
        Creates a new Workgroup.

        API: POST Workgroups

        Args:
            name (str): The Workgroup name.
            organization_id (str, optional): The Organization GUID.

        Returns:
            dict: Created Workgroup.
        """

        attributes = {"name": name}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            workgroups_fields, POST_WORKGROUPS, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            organization_id=organization_id,
            name=name,
        )

        utils.print_log(
            self._logger,
            "Calling post_workgroup endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            self.endpoint, req_body, include_api_version=False
        )

        return response.json()
