"""UserGroupRoles module, all the logic to manage user group roles from PS API"""

import logging
from typing import List

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import POST_USERGROUPS_ID_SMARTRULES_ROLES
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.user_group_roles import fields as roles_fields


class UserGroupRoles(APIObject):
    """
    Class to manage Password Safe roles for User Groups and Smart Rules.

    This class provides methods to get, set, and delete roles for specific
    User Group and Smart Rule combinations.
    """

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/usergroups")

        # Schema rules used for validations
        self._schema = {
            "roles": {
                "type": "list",
                "schema": {"type": "integer", "required": True},
                "required": False,
                "nullable": True,
            },
            "access_policy_id": {"type": "integer", "nullable": True},
        }
        self._validator = Validator(self._schema)

    def get_roles(self, user_group_id: int, smart_rule_id: int) -> List[dict]:
        """
        Returns a list of roles for the user group and Smart Rule referenced by ID.

        API: GET UserGroups/{userGroupId}/SmartRules/{smartRuleId}/Roles

        Args:
            user_group_id (int): ID of the user group.
            smart_rule_id (int): ID of the Smart Rule.

        Returns:
            List[dict]: List of roles with RoleID and Name.
        """
        endpoint = f"{self.endpoint}/{user_group_id}/smartrules/{smart_rule_id}/roles"

        utils.print_log(self._logger, "Calling get roles endpoint", logging.DEBUG)
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def set_roles(
        self,
        user_group_id: int,
        smart_rule_id: int,
        roles: List[int],
        access_policy_id: int = None,
    ) -> None:
        """
        Sets Password Safe roles for the user group and Smart Rule referenced by ID.

        API: POST UserGroups/{userGroupId}/SmartRules/{smartRuleId}/Roles

        Args:
            user_group_id (int): ID of the user group.
            smart_rule_id (int): ID of the Smart Rule.
            roles (List[int]): Zero or more roles to set on the UserGroup-SmartRule.
                Each role should be an integer representing the RoleID.
            access_policy_id (int, optional): The access policy ID to set on the
                UserGroup-SmartRule. Required when the Requestor or Requestor/Approver
                role is set.

        Returns:
            None.

        Raises:
            exceptions.OptionsError: If validation fails.
            exceptions.CreationError: If the API request fails.
        """

        # Validate input
        attributes = {"roles": roles}
        if access_policy_id is not None:
            attributes["access_policy_id"] = access_policy_id

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        # Convert roles to the required format for the API
        roles_dict = [{"RoleID": role_id} for role_id in roles]
        attributes["roles"] = roles_dict

        req_structure = self.get_request_body_version(
            roles_fields, POST_USERGROUPS_ID_SMARTRULES_ROLES, Version.DEFAULT.value
        )
        req_body = self.generate_request_body(
            req_structure,
            **attributes,
        )

        endpoint = f"{self.endpoint}/{user_group_id}/smartrules/{smart_rule_id}/roles"

        utils.print_log(self._logger, "Calling set roles endpoint", logging.DEBUG)
        self._run_post_request(
            endpoint, req_body, include_api_version=False, expected_status_code=204
        )

    def delete_roles(self, user_group_id: int, smart_rule_id: int) -> None:
        """
        Deletes all Password Safe roles for the user group and Smart Rule
        referenced by ID.

        API: DELETE UserGroups/{userGroupId}/SmartRules/{smartRuleId}/Roles

        Args:
            user_group_id (int): ID of the user group.
            smart_rule_id (int): ID of the Smart Rule.

        Returns:
            None.

        Raises:
            exceptions.DeletionError: If the API request fails.
        """
        endpoint = f"{self.endpoint}/{user_group_id}/smartrules/{smart_rule_id}/roles"

        utils.print_log(self._logger, "Calling delete roles endpoint", logging.DEBUG)
        self._run_delete_request(endpoint, expected_status_code=200)
