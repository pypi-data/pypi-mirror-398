"""Permissions module, all the logic to manage safes from BI API"""

import logging

from cerberus import Validator

from secrets_safe_library import utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import ListMixin
from secrets_safe_library.utils import convert_as_literal


class Permission(APIObject, ListMixin):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/permissions")

        # Schema rules used for validations
        self._schema = {
            "name": {"type": "string", "nullable": False},
        }
        self._validator = Validator(self._schema)

    def get_usergroup_permissions(self, usergroup_id: int) -> list:
        """
        Gets all permissions for the user group referenced by ID.

        API: GET UserGroups/{userGroupID}/Permissions

        Args:
            usergroup_id (int): The Usergroup ID.

        Returns:
            list: List of permissions.
        """

        endpoint = f"/usergroups/{usergroup_id}/permissions"

        utils.print_log(
            self._logger,
            "Calling get_usergroup_permissions endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def set_usergroup_permissions(
        self,
        usergroup_id: int,
        permissions: list,
    ) -> int:
        """
        Sets permissions for the user group referenced by ID.

        API: POST UserGroups/{userGroupId}/Permissions

        Args:
            usergroup_id (int): The Usergroup ID.
            permissions (list): List of permissions to set. Expected format:
                [
                    {
                        "PermissionID": int,
                        "AccessLevelID": int
                    },
                    ...
                ]

        Returns:
            int: Response status code.
        """

        permissions = convert_as_literal(permissions)

        endpoint = f"/usergroups/{usergroup_id}/permissions"

        utils.print_log(
            self._logger,
            "Calling post_usergroup_permissions endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint, permissions, include_api_version=False, expected_status_code=204
        )

        return response.status_code

    def delete_usergroup_permissions(self, usergroup_id: int) -> None:
        """
        Deletes all permissions for the user group referenced by ID.

        API: DELETE UserGroups/{userGroupId}/Permissions

        Args:
            usergroup_id (int): The Usergroup ID.

        Returns:
            None
        """

        endpoint = f"/usergroups/{usergroup_id}/permissions"

        utils.print_log(
            self._logger,
            "Calling delete_usergroup_permissions endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)

        utils.print_log(
            self._logger,
            f"Permissions for user group with ID {usergroup_id} deleted successfully.",
            logging.INFO,
        )
