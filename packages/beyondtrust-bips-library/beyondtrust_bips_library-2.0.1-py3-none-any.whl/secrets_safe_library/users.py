"""Users module, all the logic to manage users from BeyondInsight API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import (
    POST_USERS_AD,
    POST_USERS_APP,
    POST_USERS_BI,
    POST_USERS_LDAP,
    POST_USERS_USERGROUPID,
    PUT_USERS_ID_APP,
    PUT_USERS_ID_BI,
)
from secrets_safe_library.constants.users import UserType
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.users import fields as users_fields


class User(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger)

        # Schema rules used for validations
        self._schema = {
            "user_name": {"type": "string", "maxlength": 64, "nullable": True},
            "first_name": {"type": "string", "maxlength": 64, "nullable": True},
            "last_name": {"type": "string", "maxlength": 64, "nullable": True},
            "email_address": {"type": "string", "maxlength": 255, "nullable": True},
            "user_id": {"type": "integer", "nullable": True},
            "forest_name": {"type": "string", "maxlength": 300, "nullable": True},
            "domain_name": {"type": "string", "maxlength": 250, "nullable": True},
            "usergroup_id": {"type": "integer", "nullable": True},
            "distinguished_name": {
                "type": "string",
                "maxlength": 255,
                "nullable": True,
            },
        }
        self._validator = Validator(self._schema)

    def get_users(self, username: str = None, include_inactive: bool = False) -> list:
        """
        Returns a list of users.

        API: GET Users

        Args:
            username (str, optional): The user to return, in one of following formats:
                - username: returns the BeyondInsight users.
                - domain\\username or universal principal name: returns Active Directory
                                                                or LDAP users.
            include_inactive (bool, optional): Include inactive users. Default=False.

        Returns:
            list: List of users.
        """

        params = {"username": username, "includeInactive": include_inactive}

        query_string = self.make_query_string(params)

        endpoint = f"/users?{query_string}"

        utils.print_log(
            self._logger,
            "Calling get_users endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_user_by_id(self, user_id: int) -> dict:
        """
        Returns a user by ID.

        API: GET Users/{id}

        Args:
            user_id (int): The user ID.

        Returns:
            dict: User.
        """

        attributes = {"user_id": user_id}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/users/{user_id}"

        utils.print_log(
            self._logger,
            "Calling get_user_by_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_users_by_usergroup_id(self, usergroup_id: int) -> list:
        """
        Returns a list of users by User Group ID.

        API: GET UserGroups/{usergroupid}/Users

        Args:
            usergroup_id (int): The User Group ID.

        Returns:
            list: List of users.
        """

        attributes = {"usergroup_id": usergroup_id}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/usergroups/{usergroup_id}/users"

        utils.print_log(
            self._logger,
            "Calling get_users_by_usergroup_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def post_user_beyondinsight(
        self,
        user_name: str,
        first_name: str,
        email_address: str,
        password: str,
        last_name: str = None,
    ) -> dict:
        """
        Creates a new user with UserType "BeyondInsight".

        API: POST Users

        Args:
            user_name (str): The user name.
            first_name (str): The user's first name.
            email_address (str): The user's email address.
            password (str): The user's password.
            last_name (str, optional): The user's last name. Defaults to None.

        Returns:
            dict: Created user.
        """

        attributes = {
            "user_name": user_name,
            "first_name": first_name,
            "last_name": last_name,
            "email_address": email_address,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            users_fields, POST_USERS_BI, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            user_type=UserType.USER_TYPE_BI.value,
            user_name=user_name,
            first_name=first_name,
            last_name=last_name,
            email_address=email_address,
            password=password,
        )

        endpoint = "/users"

        utils.print_log(
            self._logger,
            "Calling post_user_beyondinsight endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def post_user_active_directory(
        self,
        user_name: str,
        forest_name: str = None,
        domain_name: str = None,
        bind_user: str = None,
        bind_password: str = None,
        use_ssl: bool = False,
    ) -> dict:
        """
        Creates a new user with UserType "ActiveDirectory".

        API: POST Users

        Args:
            user_name (str): The user name.
            forest_name (str, optional): The forest name. Defaults to None.
            domain_name (str, optional): The domain name. Defaults to None.
            bind_user (str, optional): The bind user. Defaults to None.
            bind_password (str, optional): The bind password. Defaults to None.
            use_ssl (bool, optional): Use SSL. Defaults to False.

        Returns:
            dict: Created user.
        """

        attributes = {
            "user_name": user_name,
            "forest_name": forest_name,
            "domain_name": domain_name,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            users_fields, POST_USERS_AD, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            user_type=UserType.USER_TYPE_AD.value,
            user_name=user_name,
            forest_name=forest_name,
            domain_name=domain_name,
            bind_user=bind_user,
            bind_password=bind_password,
            use_ssl=use_ssl,
        )

        endpoint = "/users"

        utils.print_log(
            self._logger,
            "Calling post_user_active_directory endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def post_user_ldap(
        self,
        host_name: str,
        distinguished_name: str,
        account_name_attribute: str,
        bind_user: str = None,
        bind_password: str = None,
        port: int = None,
        use_ssl: bool = False,
    ) -> dict:
        """
        Creates a new user with UserType "LDAP".

        API: POST Users

        Args:
            host_name (str): The LDAP host name.
            distinguished_name (str): The LDAP distinguished name.
            account_name_attribute (str): The LDAP account name attribute.
            bind_user (str, optional): The bind user.
            bind_password (str, optional): The bind password.
            port (int, optional): The LDAP port.
            use_ssl (bool, optional): Use SSL.

        Returns:
            dict: Created user.
        """

        attributes = {
            "distinguished_name": distinguished_name,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            users_fields, POST_USERS_LDAP, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            user_type=UserType.USER_TYPE_LDAP.value,
            host_name=host_name,
            distinguished_name=distinguished_name,
            account_name_attribute=account_name_attribute,
            bind_user=bind_user,
            bind_password=bind_password,
            port=port,
            use_ssl=use_ssl,
        )

        endpoint = "/users"

        utils.print_log(
            self._logger,
            "Calling post_user_ldap endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def post_user_application(
        self,
        user_name: str,
        access_policy_id: int = None,
    ) -> dict:
        """
        Creates a new user with UserType "Application".

        API: POST Users

        Args:
            user_name (str): The user name.
            access_policy_id (int, optional): The access policy ID.

        Returns:
            dict: Created user.
        """

        attributes = {"user_name": user_name}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            users_fields, POST_USERS_APP, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            user_type=UserType.USER_TYPE_APP.value,
            user_name=user_name,
            access_policy_id=access_policy_id,
        )

        endpoint = "/users"

        utils.print_log(
            self._logger,
            "Calling post_user_application endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def post_user_quarantine(self, user_id: int) -> dict:
        """
        Quarantines a user by ID.

        API: POST Users/{user_id}/quarantine

        Args:
            user_id (int): The user ID.

        Returns:
            dict: Quarantined user.
        """

        endpoint = f"/users/{user_id}/quarantine"

        utils.print_log(
            self._logger,
            "Calling post_user_quarantine endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint, payload={}, include_api_version=False
        )

        return response.json()

    def post_user_usergroupid(
        self,
        user_group_id: int,
        user_name: str,
        first_name: str,
        email_address: str,
        password: str,
        last_name: str = None,
    ) -> dict:
        """
        Creates a user in a BeyondInsight-type user group.

        API: UserGroups/{userGroupId}/Users

        Args:
            user_group_id (int): ID of the user group.
            user_name (str): The user name.
            first_name (str): The user's first name.
            email_address (str): The user's email address.
            password (str): The user's password.
            last_name (str, optional): The user's last name. Defaults to None.

        Returns:
            dict: Created user.
        """

        attributes = {
            "user_name": user_name,
            "first_name": first_name,
            "last_name": last_name,
            "email_address": email_address,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            users_fields, POST_USERS_USERGROUPID, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            user_name=user_name,
            first_name=first_name,
            last_name=last_name,
            email_address=email_address,
            password=password,
        )

        endpoint = f"/usergroups/{user_group_id}/users"

        utils.print_log(
            self._logger,
            "Calling post_user_usergroupid endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def post_user_recycleclient_secret(self, user_id: int) -> dict:
        """
        Recycles the client secret for an application user.

        API: POST Users/{user_id}/recycleclientsecret

        Args:
            user_id (int): The user ID.

        Returns:
            dict: User with recycled client secret.
        """

        endpoint = f"/users/{user_id}/recycleclientsecret"

        utils.print_log(
            self._logger,
            "Calling post_user_recycleclient_secret endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint, payload={}, include_api_version=False
        )

        return response.json()

    def put_user_beyondinsight(
        self,
        user_id: int,
        user_name: str,
        first_name: str,
        email_address: str,
        password: str,
        last_name: str = None,
    ) -> dict:
        """
        Updates a user with UserType "BeyondInsight" referenced by ID.

        API: PUT Users/{user_id}

        Args:
            user_id (int): ID of the BeyondInsight user.
            user_name (str): The user name.
            first_name (str): The user's first name.
            email_address (str): The user's email address.
            password (str): The user's password.
            last_name (str, optional): The user's last name. Defaults to None.

        Returns:
            dict: Updated user.
        """
        attributes = {
            "user_name": user_name,
            "first_name": first_name,
            "last_name": last_name,
            "email_address": email_address,
        }

        if not self._validator.validate(attributes):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            users_fields, PUT_USERS_ID_BI, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            user_name=user_name,
            first_name=first_name,
            last_name=last_name,
            email_address=email_address,
            password=password,
        )

        endpoint = f"/users/{user_id}"

        utils.print_log(
            self._logger,
            "Calling put_user_beyondinsight endpoint",
            logging.DEBUG,
        )

        response = self._run_put_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def put_user_application(
        self,
        user_id: int,
        user_name: str,
        access_policy_id: int = None,
    ) -> dict:
        """
        Updates a user with UserType "Application" referenced by ID.

        API: PUT Users/{user_id}

        Args:
            user_id (int): ID of the application user.
            user_name (str): The user name.
            access_policy_id (int, optional): The access policy ID.

        Returns:
            dict: Updated user.
        """

        attributes = {"user_name": user_name}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            users_fields, PUT_USERS_ID_APP, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            user_name=user_name,
            access_policy_id=access_policy_id,
        )

        endpoint = f"/users/{user_id}"

        utils.print_log(
            self._logger,
            "Calling put_user_application endpoint",
            logging.DEBUG,
        )
        response = self._run_put_request(endpoint, req_body, include_api_version=False)

        return response.json()

    def delete_user(self, user_id: int) -> None:
        """
        Deletes a user by ID.

        API: DELETE Users/{user_id}

        Args:
            user_id (int): The user ID.
        """

        attributes = {"user_id": user_id}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/users/{user_id}"

        utils.print_log(
            self._logger,
            "Calling delete_user endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)
        utils.print_log(
            self._logger,
            f"User with ID {user_id} deleted successfully.",
            logging.INFO,
        )
