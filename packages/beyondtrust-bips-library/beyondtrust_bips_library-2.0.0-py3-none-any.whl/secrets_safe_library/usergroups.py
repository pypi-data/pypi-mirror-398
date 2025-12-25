"""UserGroups module, all the logic to manage users from BeyondInsight API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import (
    POST_USERGROUPS_AD,
    POST_USERGROUPS_BI,
    POST_USERGROUPS_ENTRAID,
    POST_USERGROUPS_LDAP,
)
from secrets_safe_library.constants.users import UserType
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.usergroups import fields as usergroups_fields


class Usergroups(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger)

        # Schema rules used for validations
        self._schema = {
            "group_name": {"type": "string", "maxlength": 200, "nullable": True},
            "description": {"type": "string", "maxlength": 255, "nullable": True},
            "domain_name": {"type": "string", "maxlength": 250, "nullable": True},
            "group_distinguished_name": {
                "type": "string",
                "maxlength": 500,
                "nullable": True,
            },
            "membership_attribute": {
                "type": "string",
                "maxlength": 255,
                "nullable": True,
            },
            "account_attribute": {
                "type": "string",
                "maxlength": 255,
                "nullable": True,
            },
        }
        self._validator = Validator(self._schema)

    def get_usergroups(self) -> list:
        """
        Returns a list of active and inactive user groups.

        API: GET Usergroups

        Returns:
            list: List of Usergroups.
        """

        endpoint = "/usergroups"

        utils.print_log(
            self._logger,
            "Calling get_usergroups endpoint",
            logging.DEBUG,
        )

        response = self._run_get_request(endpoint, include_api_version=False)
        return response.json()

    def get_usergroup_by_id(self, usergroup_id: int) -> dict:
        """
        Returns a user group by ID.

        API: GET Usergroups/{usergroup_id}

        Args:
            usergroup_id (int): The Usergroup ID.

        Returns:
            dict: Usergroup.
        """

        endpoint = f"/usergroups/{usergroup_id}"

        utils.print_log(
            self._logger,
            "Calling get_usergroup_by_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_usergroups_by_name(self, name: str) -> list:
        """
        Returns a list of user groups by name.

        API: GET Usergroups?name={name}

        Args:
            name (str): The Usergroup name.

        Returns:
            list: List of Usergroups.
        """

        endpoint = f"/usergroups?name={name}"

        utils.print_log(
            self._logger,
            "Calling get_usergroups_by_name endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def post_usergroups_beyondinsight(
        self,
        group_name: str,
        description: str,
        is_active: bool = None,
        permissions: list = None,
        smart_rule_access: list = None,
        application_registration_ids: list = None,
    ) -> dict:
        """
        Creates a new user group, groupType = "BeyondInsight"

        API: POST Usergroups

        Args:
            group_name (str): The Usergroup name.
            description (str): The Usergroup description.
            is_active (bool, optional): Indicates if the Usergroup is active.
            permissions (list, optional): List of permissions.
                [ { PermissionID: int, AccessLevelID: int }, ... ]
            smart_rule_access (str, optional): List of smart rule access.
                [ { SmartRuleID: int, AccessLevelID: int }, ... ]
            application_registration_ids (list, optional): List of application
                                                           registration IDs.
                                                        [ int, … ]

        Returns:
            dict: Created Usergroup.
        """

        attributes = {
            "group_name": group_name,
            "description": description,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            usergroups_fields, POST_USERGROUPS_BI, Version.DEFAULT.value
        )

        # Convert string representation of dicts to actual dicts
        permissions = utils.convert_as_literal(permissions)
        smart_rule_access = utils.convert_as_literal(smart_rule_access)

        req_body = self.generate_request_body(
            req_structure,
            groupType=UserType.USER_TYPE_BI.value,
            group_name=group_name,
            description=description,
            is_active=is_active,
            permissions=permissions,
            smart_rule_access=smart_rule_access,
            application_registration_ids=application_registration_ids,
        )

        endpoint = "/usergroups"

        utils.print_log(
            self._logger,
            "Calling post_usergroups_beyondinsight endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def post_usergroups_entraid(
        self,
        description: str,
        group_name: str,
        client_id: str,
        tenant_id: str,
        client_secret: str,
        azure_instance: str = None,
        is_active: bool = None,
        permissions: list = None,
        smart_rule_access: list = None,
        application_registration_ids: list = None,
    ) -> dict:
        """
        Creates a new user group, groupType = "EntraId"

        API: POST Usergroups

        Args:
            description (str): The Usergroup description.
            group_name (str): The Usergroup name.
            client_id (str): The Entra ID.
            tenant_id (str): The Entra Tenant ID.
            client_secret (str): The Entra Client Secret.
            azure_instance (str, optional): The Entra Azure Instance.
            is_active (bool, optional): Indicates if the Usergroup is active.
            permissions (list, optional): List of permissions.
                [ { PermissionID: int, AccessLevelID: int }, ... ]
            smart_rule_access (str, optional): List of smart rule access.
                [ { SmartRuleID: int, AccessLevelID: int }, ... ]
            application_registration_ids (list, optional): List of application
                                                           registration IDs.
                                                        [ int, … ]

        Returns:
            dict: Created Usergroup.
        """

        attributes = {
            "description": description,
            "group_name": group_name,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            usergroups_fields, POST_USERGROUPS_ENTRAID, Version.DEFAULT.value
        )
        # Convert string representation of dicts to actual dicts
        permissions = utils.convert_as_literal(permissions)
        smart_rule_access = utils.convert_as_literal(smart_rule_access)

        req_body = self.generate_request_body(
            req_structure,
            groupType=UserType.USER_TYPE_ENTRAID.value,
            description=description,
            group_name=group_name,
            client_id=client_id,
            tenant_id=tenant_id,
            client_secret=client_secret,
            azure_instance=azure_instance,
            is_active=is_active,
            permissions=permissions,
            smart_rule_access=smart_rule_access,
            application_registration_ids=application_registration_ids,
        )

        endpoint = "/usergroups"

        utils.print_log(
            self._logger,
            "Calling post_usergroups_entraid endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def post_usergroups_ad(
        self,
        group_name: str,
        domain_name: str,
        description: str,
        forest_name: str = None,
        bind_user: str = None,
        bind_password: str = None,
        use_ssl: bool = None,
        is_active: bool = None,
        excluded_from_global_sync: bool = None,
        override_global_sync_settings: bool = None,
        permissions: list = None,
        smart_rule_access: list = None,
        application_registration_ids: list = None,
    ) -> dict:
        """
        Creates a new user group, groupType = "ActiveDirectory"

        API: POST Usergroups

        Args:
            group_name (str): The Usergroup name.
            domain_name (str): The Active Directory domain name.
            description (str): The Usergroup description.
            forest_name (str, optional): The Active Directory forest name.
            bind_user (str, optional): The Active Directory bind user.
            bind_password (str, optional): The Active Directory bind password.
            use_ssl (bool, optional): Use SSL.
            is_active (bool, optional): Indicates if the Usergroup is active.
            excluded_from_global_sync (bool, optional): Exclude from global sync.
            override_global_sync_settings (bool, optional): Override global sync
                                                            settings.
            permissions (list, optional): List of permissions.
                [ { PermissionID: int, AccessLevelID: int }, ... ]
            smart_rule_access (str, optional): List of smart rule access.
                [ { SmartRuleID: int, AccessLevelID: int }, ... ]
            application_registration_ids (list, optional): List of application
                                                        registration IDs.
                                                        [ int, … ]

        Returns:
            dict: Created Usergroup.
        """

        attributes = {
            "group_name": group_name,
            "domain_name": domain_name,
            "description": description,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            usergroups_fields, POST_USERGROUPS_AD, Version.DEFAULT.value
        )

        # Convert string representation of dicts to actual dicts
        permissions = utils.convert_as_literal(permissions)
        smart_rule_access = utils.convert_as_literal(smart_rule_access)

        req_body = self.generate_request_body(
            req_structure,
            groupType=UserType.USER_TYPE_AD.value,
            group_name=group_name,
            domain_name=domain_name,
            description=description,
            forest_name=forest_name,
            bind_user=bind_user,
            bind_password=bind_password,
            use_ssl=use_ssl,
            is_active=is_active,
            excluded_from_global_sync=excluded_from_global_sync,
            override_global_sync_settings=override_global_sync_settings,
            permissions=permissions,
            smart_rule_access=smart_rule_access,
            application_registration_ids=application_registration_ids,
        )

        endpoint = "/usergroups"

        utils.print_log(
            self._logger,
            "Calling post_usergroups_ad endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def post_usergroups_ldap(
        self,
        group_name: str,
        group_distinguished_name: str,
        host_name: str,
        membership_attribute: str,
        account_attribute: str,
        bind_user: str = None,
        bind_password: str = None,
        port: int = None,
        use_ssl: bool = None,
        is_active: bool = None,
        permissions: list = None,
        smart_rule_access: list = None,
        application_registration_ids: list = None,
    ) -> dict:
        """
        Creates a new user group, groupType = "LdapDirectory"

        API: POST Usergroups

        Args:
            group_name (str): The Usergroup name.
            group_distinguished_name (str): The LDAP group distinguished name.
            host_name (str): The LDAP host name.
            membership_attribute (str): The LDAP membership attribute.
            account_attribute (str): The LDAP account attribute.
            bind_user (str, optional): The LDAP bind user.
            bind_password (str, optional): The LDAP bind password.
            port (int, optional): The LDAP port.
            use_ssl (bool, optional): Use SSL.
            is_active (bool, optional): Indicates if the Usergroup is active.
            permissions (list, optional): List of permissions.
                [ { PermissionID: int, AccessLevelID: int }, ... ]
            smart_rule_access (str, optional): List of smart rule access.
                [ { SmartRuleID: int, AccessLevelID: int }, ... ]
            application_registration_ids (list, optional): List of application
                                                        registration IDs.
                                                        [ int, … ]

        Returns:
            dict: Created Usergroup.
        """

        attributes = {
            "group_name": group_name,
            "group_distinguished_name": group_distinguished_name,
            "membership_attribute": membership_attribute,
            "account_attribute": account_attribute,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            usergroups_fields, POST_USERGROUPS_LDAP, Version.DEFAULT.value
        )

        # Convert string representation of dicts to actual dicts
        permissions = utils.convert_as_literal(permissions)
        smart_rule_access = utils.convert_as_literal(smart_rule_access)

        req_body = self.generate_request_body(
            req_structure,
            groupType=UserType.USER_TYPE_LDAP.value,
            group_name=group_name,
            group_distinguished_name=group_distinguished_name,
            host_name=host_name,
            membership_attribute=membership_attribute,
            account_attribute=account_attribute,
            bind_user=bind_user,
            bind_password=bind_password,
            port=port,
            use_ssl=use_ssl,
            is_active=is_active,
            permissions=permissions,
            smart_rule_access=smart_rule_access,
            application_registration_ids=application_registration_ids,
        )

        endpoint = "/usergroups"

        utils.print_log(
            self._logger,
            "Calling post_usergroups_ldap endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def delete_usergroup_by_name(self, name: str) -> None:
        """
        Deletes a user group by name.

        API: DELETE Usergroups?name={name}

        Args:
            name (str): The Usergroup name.

        Returns:
            None
        """

        endpoint = f"/usergroups?name={name}"

        utils.print_log(
            self._logger,
            "Calling delete_usergroup_by_name endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)

        utils.print_log(
            self._logger,
            f"Usergroup with name {name} deleted successfully.",
            logging.INFO,
        )

    def delete_usergroup_by_id(self, usergroup_id: int) -> None:
        """
        Deletes a user group by ID.

        API: DELETE Usergroups/{usergroup_id}

        Args:
            usergroup_id (int): The Usergroup ID.

        Returns:
            None
        """

        endpoint = f"/usergroups/{usergroup_id}"

        utils.print_log(
            self._logger,
            "Calling delete_usergroup_by_id endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)

        utils.print_log(
            self._logger,
            f"Usergroup with ID {usergroup_id} deleted successfully.",
            logging.INFO,
        )
