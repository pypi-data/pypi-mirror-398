"""ManagedAccount Module, all the logic to retrieve managed accounts from PS API"""

import logging
from typing import Tuple

import requests

from secrets_safe_library import exceptions, utils
from secrets_safe_library.constants.endpoints import (
    POST_MANAGED_SYSTEMS_SYSTEM_ID_MANAGED_ACCOUNTS,
    PUT_MANAGED_ACCOUNTS_CREDENTIALS,
)
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.managed_accounts import (
    fields as managed_accounts_fields,
)
from secrets_safe_library.mixins import DeleteByIdMixin, GetByIdMixin
from secrets_safe_library.validators.managed_accounts import ManagedAccountValidator


class ManagedAccount(APIObject, DeleteByIdMixin, GetByIdMixin, ManagedAccountValidator):
    """
    Class to interact with managed accounts in PS API.
    """

    _separator = None
    _sign_app_out_error_message = "Error in sign_app_out"

    def __init__(self, authentication, logger=None, separator="/"):
        APIObject.__init__(self, authentication, logger, endpoint="/managedaccounts")

        ManagedAccountValidator.__init__(self)

        if len(separator.strip()) != 1:
            raise exceptions.LookupError(f"Invalid separator: {separator}")
        self._separator = separator

    def get_secret(self, path):
        """
        Get Managed account by path
        Arguments:
            path
        Returns:
            Retrieved managed account string
        """

        utils.print_log(
            self._logger,
            "Running get_secret method in ManagedAccount class",
            logging.DEBUG,
        )
        managed_account_dict = self.managed_account_flow([path])
        return managed_account_dict[path]

    def get_secret_with_metadata(self, path):
        """
        Get Managed account with metadata by path
        Arguments:
            path
        Returns:
             Retrieved managed account in dict format
        """

        utils.print_log(
            self._logger,
            "Running get_secret method in ManagedAccount class",
            logging.DEBUG,
        )
        managed_account_dict = self.managed_account_flow([path], get_metadata=True)
        return managed_account_dict

    def get_secrets(self, paths):
        """
        Get Managed accounts by paths
        Arguments:
            paths list
        Returns:
            Retrieved managed account in dict format
        """

        utils.print_log(
            self._logger,
            "Running get_secrets method in ManagedAccount class",
            logging.INFO,
        )
        managed_account_dict = self.managed_account_flow(paths)
        return managed_account_dict

    def get_secrets_with_metadata(self, paths):
        """
        Get Managed accounts with metadata by paths
        Arguments:
            paths list
        Returns:
            Retrieved managed account in dict format
        """

        utils.print_log(
            self._logger,
            "Running get_secrets method in ManagedAccount class",
            logging.INFO,
        )
        managed_account_dict = self.managed_account_flow(paths, get_metadata=True)
        return managed_account_dict

    def get_request_id(self, system_id, account_id):
        create_request_response = self.create_request(system_id, account_id)
        request_id = create_request_response.json()
        return request_id

    def managed_account_flow(self, paths, get_metadata=False):
        """
        Managed account by path flow
        Arguments:
            paths list
        Returns:
            Response (Dict)
        """

        response = {}

        for path in paths:

            utils.print_log(
                self._logger,
                f"************** managed account path len: {len(path)} **************",
                logging.INFO,
            )
            data = path.split(self._separator)

            if len(data) != 2:
                raise exceptions.LookupError(
                    f"Invalid managed account path: {path}. Use '{self._separator}' as "
                    f"a delimiter: system_name{self._separator}managed_account_name"
                )

            system_name = data[0]
            managed_account_name = data[1]

            manage_account = self.get_managed_accounts(
                system_name=system_name, account_name=managed_account_name
            )

            if get_metadata:
                response[f"{path}-metadata"] = manage_account

            utils.print_log(
                self._logger, "Managed account info retrieved", logging.DEBUG
            )

            request_id = self.get_request_id(
                manage_account["SystemId"], manage_account["AccountId"]
            )

            utils.print_log(
                self._logger,
                f"Request id retrieved: {'*' * len(str(request_id))}",
                logging.DEBUG,
            )

            if not request_id:
                raise exceptions.LookupError("Request Id not found")

            credential = self.get_credential_by_request_id(request_id)

            response[path] = credential

            utils.print_log(
                self._logger, "Credential was successfully retrieved", logging.INFO
            )

            self.request_check_in(request_id)
        return response

    def create_request(self, system_id: int, account_id: int) -> requests.Response:
        """
        Create request by system ID and account ID.

        API: POST Requests

        Args:
            system_id (int): ID of the managed system to request.
            account_id (int): ID of the managed account to request.

        Returns:
            request.Response: Response object.
        """
        payload = {
            "SystemID": system_id,
            "AccountID": account_id,
            "DurationMinutes": 5,
            "Reason": "Secrets Safe Integration",
            "ConflictOption": "reuse",
        }

        endpoint = "/Requests"
        utils.print_log(self._logger, "Calling create_request endpoint", logging.DEBUG)
        response = self._run_post_request(
            endpoint,
            payload=payload,
            expected_status_code=[200, 201],
            include_api_version=False,
        )
        return response

    def get_credential_by_request_id(self, request_id: int):
        """
        Retrieves the credentials for an approved and active (not expired) credentials
        release request.

        API: GET Credentials/{requestId}

        Args:
            request_id (int): The request ID.

        Returns:
            requests.Response: The response object containing the credential details.
        """

        endpoint = f"/Credentials/{request_id}"
        print_url = (
            f"{self._authentication._api_url}/Credentials/{'*' * len(str(request_id))}"
        )

        utils.print_log(
            self._logger,
            f"Calling get_credential_by_request_id endpoint: {print_url}",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        credential = response.json()
        return credential

    def request_check_in(self, request_id: int, reason: str = "") -> None:
        """
        Checks-in/releases a request before it has expired.

        API: PUT Requests/{id}/checkin.

        Args:
            request_id (int): The ID of the request to check-in/release.
            reason (str, optional): A reason or comment why the request is being
                approved. Max string length is 1000.

        Returns:
            None
        """
        endpoint = f"/Requests/{request_id}/checkin"
        print_url = (
            f"{self._authentication._api_url}/Requests/"
            f"{'*' * len(str(request_id))}/checkin"
        )

        utils.print_log(
            self._logger,
            f"Calling request_check_in endpoint: {print_url}",
            logging.DEBUG,
        )
        payload = {"Reason": reason} if reason else {}
        _ = self._run_put_request(
            endpoint,
            payload=payload,
            expected_status_code=204,
        )

        utils.print_log(self._logger, "Request checked in", logging.DEBUG)

    def list_by_managed_system(self, managed_system_id: int) -> list:
        """
        Returns a list of managed accounts by managed system ID.

        API: GET ManagedSystems/{systemID}/ManagedAccounts

        Args:
            managed_system_id (int): Managed system ID.

        Returns:
            list: List of managed accounts.
        """

        endpoint = f"/managedsystems/{managed_system_id}/managedaccounts"

        utils.print_log(
            self._logger,
            "Calling list_by_managed_system endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint)

        return response.json()

    def get_managed_accounts(
        self,
        *,
        system_name: str = None,
        account_name: str = None,
        system_id: str = None,
        workgroup_name: str = None,
        application_display_name: str = None,
        ip_address: str = None,
        type: str = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list | dict:
        """
        Get managed account(s) by system name, account name and other fields.

        API: GET ManagedAccounts.

        Args:
            system_name (str): The name of the system where the account is managed.
            account_name (str): The name of the account to retrieve.
            system_id (str): The ID of the managed system.
            workgroup_name (str): The name of the workgroup.
            application_display_name (str): The display name of the application.
            ip_address (str): The IP address of the managed asset.
            type (str): The type of the managed account to return. Options are:
                system, recent, domainlinked, database, cloud, application.
            limit (int): The number of records to return. Default is 1000.
            offset (int): The number of records to skip before returning records.
                Default is 0.

        Returns:
            list | dict: List of managed accounts if multiple accounts are found,
                otherwise, a dictionary containing a single accound data will be
                returned.

        Raises:
            exceptions.OptionsError: If provided arguments are not valid.
        """
        attributes = {
            "system_name": system_name,
            "account_name": account_name,
            "system_id": system_id,
            "workgroup_name": workgroup_name,
            "application_display_name": application_display_name,
            "ip_address": ip_address,
            "type": type,
            "limit": limit,
            "offset": offset,
        }

        params = {key.replace("_", ""): value for key, value in attributes.items()}

        self.validate(attributes, operation="list")

        query_string = self.make_query_string(params)
        endpoint = f"/managedaccounts?{query_string}"
        utils.print_log(
            self._logger,
            "Calling get_managed_accounts endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)
        return response.json()

    def list_by_smart_rule_id(self, smart_rule_id: int) -> list:
        """
        Returns a list of managed accounts by Smart Rule ID.

        API: GET SmartRules/{smartRuleID}/ManagedAccounts

        Args:
            smart_rule_id (int): Smart Rule ID.

        Returns:
            list: List of managed accounts.
        """

        endpoint = f"/smartrules/{smart_rule_id}/managedaccounts"

        utils.print_log(
            self._logger,
            "Calling list_by_smart_rule_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint)

        return response.json()

    def list_by_quick_rule_id(self, quick_rule_id: int) -> list:
        """
        Returns a list of managed accounts by Quick Rule ID.

        API: GET QuickRules/{quickRuleID}/ManagedAccounts

        Args:
            quick_rule_id (int): Quick rule ID.

        Returns:
            list: List of managed accounts.
        """

        endpoint = f"/quickrules/{quick_rule_id}/managedaccounts"

        utils.print_log(
            self._logger,
            "Calling list_by_quick_rule_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint)

        return response.json()

    def create_managed_account(
        self,
        *,
        system_id: int,
        account_name: str,
        password: str = None,
        domain_name: str = None,
        user_principal_name: str = None,
        sam_account_name: str = None,
        distinguished_name: str = None,
        private_key: str = None,
        passphrase: str = None,
        password_fallback_flag: bool = False,
        login_account_flag: bool = None,
        description: str = None,
        password_rule_id: int = 0,
        api_enabled: bool = False,
        release_notification_email: str = None,
        change_services_flag: bool = False,
        restart_services_flag: bool = False,
        change_tasks_flag: bool = False,
        release_duration: int = 120,
        max_release_duration: int = 525600,
        isa_release_duration: int = 120,
        max_concurrent_requests: int = 1,
        auto_management_flag: bool = False,
        dss_auto_management_flag: bool = False,
        check_password_flag: bool = False,
        reset_password_on_mismatch_flag: bool = False,
        change_password_after_any_release_flag: bool = False,
        change_frequency_type: str = "first",
        change_frequency_days: int = None,
        change_time: str = "23:30",
        next_change_date: str = None,
        use_own_credentials: bool = None,
        change_iis_app_pool_flag: bool = None,
        restart_iis_app_pool_flag: bool = None,
        workgroup_id: int = None,
        change_windows_auto_logon_flag: bool = False,
        change_com_plus_flag: bool = False,
        change_dcom_flag: bool = False,
        change_scom_flag: bool = False,
        object_id: str = None,
    ) -> Tuple[dict, int]:
        """
        Creates a new managed account in the managed system referenced by ID.

        API: POST ManagedSystems/{systemID}/ManagedAccounts

        Args:
            system_id (int): ID of the managed system where the account will be created.
            account_name (str): Name of the managed account.
            password (str): Password for the managed account.
            domain_name (str): Domain name of the managed account.
            user_principal_name (str): User principal name of the managed account.
            sam_account_name (str): SAM account name of the managed account.
            distinguished_name (str): Distinguished name of the managed account.
            private_key (str): Private key for the managed account, if applicable.
            passphrase (str): Passphrase for the private key, if applicable.
            password_fallback_flag (bool): True if password fallback is enabled,
                otherwise False.
            login_account_flag (bool): True if this is a login account, otherwise False.
            description (str): Description of the managed account.
            password_rule_id (int): ID of the password rule to apply to this account.
            api_enabled (bool): True if API access is enabled for this account,
                otherwise False.
            release_notification_email (str): Email address for release notifications.
            change_services_flag (bool): True if services should be updated with new
                credentials, otherwise False.
            restart_services_flag (bool): True if services should be restarted after a
                password change, otherwise False.
            change_tasks_flag (bool): True if tasks should be updated with new
                credentials, otherwise False.
            release_duration (int): Default release duration in minutes.
            max_release_duration (int): Maximum release duration in minutes.
            isa_release_duration (int): Default ISA release duration in minutes.
            max_concurrent_requests (int): Maximum number of concurrent requests
                allowed for this account.
            auto_management_flag (bool): True if auto-management is enabled, otherwise
                False.
            dss_auto_management_flag (bool): True if DSS key auto-management is enabled,
                otherwise False.
            check_password_flag (bool): True to enable password testing, otherwise
                False.
            reset_password_on_mismatch_flag (bool): True to reset password on mismatch,
                otherwise False.
            change_password_after_any_release_flag (bool): True to change password
                after any release, otherwise False.
            change_frequency_type (str): Type of change frequency ('first', 'last',
                'xdays').
            change_frequency_days (int): Number of days for scheduled changes when
                using 'xdays'.
            change_time (str): Time of day for scheduled changes 24hr format ('HH:MM').
            next_change_date (str): Next change date in 'YYYY-MM-DD' format.
            use_own_credentials (bool): True if the account should use its own
                credentials, otherwise False.
            change_iis_app_pool_flag (bool): True if IIS app pool should be changed,
                otherwise False.
            restart_iis_app_pool_flag (bool): True if IIS app pool should be restarted,
                otherwise False.
            workgroup_id (int, optional): ID of the workgroup to which the account
                belongs.
            change_windows_auto_logon_flag (bool): True if Windows auto logon should be
                changed, otherwise False.
            change_com_plus_flag (bool): True if COM+ settings should be changed,
                otherwise False.
            change_dcom_flag (bool): True if DCOM settings should be changed, otherwise
                False.
            change_scom_flag (bool): True if SCOM settings should be changed, otherwise
                False.
            object_id (str): Object ID of the managed account, if applicable.

        Returns:
            Tuple[dict, int]: A tuple containing the created managed account data and
                the HTTP status code.

        Raises:
            exceptions.OptionsError: If the provided attributes do not pass validation.
        """

        attributes = {
            "system_id": system_id,
            "account_name": account_name,
            "password": password,
            "domain_name": domain_name,
            "user_principal_name": user_principal_name,
            "sam_account_name": sam_account_name,
            "distinguished_name": distinguished_name,
            "private_key": private_key,
            "passphrase": passphrase,
            "password_fallback_flag": password_fallback_flag,
            "login_account_flag": login_account_flag,
            "description": description,
            "password_rule_id": password_rule_id,
            "api_enabled": api_enabled,
            "release_notification_email": release_notification_email,
            "change_services_flag": change_services_flag,
            "restart_services_flag": restart_services_flag,
            "change_tasks_flag": change_tasks_flag,
            "release_duration": release_duration,
            "max_release_duration": max_release_duration,
            "isa_release_duration": isa_release_duration,
            "max_concurrent_requests": max_concurrent_requests,
            "auto_management_flag": auto_management_flag,
            "dss_auto_management_flag": dss_auto_management_flag,
            "check_password_flag": check_password_flag,
            "reset_password_on_mismatch_flag": reset_password_on_mismatch_flag,
            "change_password_after_any_release_flag": (
                change_password_after_any_release_flag
            ),
            "change_frequency_type": change_frequency_type,
            "change_frequency_days": change_frequency_days,
            "change_time": change_time,
            "next_change_date": next_change_date,
            "use_own_credentials": use_own_credentials,
            "change_iis_app_pool_flag": change_iis_app_pool_flag,
            "restart_iis_app_pool_flag": restart_iis_app_pool_flag,
            "workgroup_id": workgroup_id,
            "change_windows_auto_logon_flag": change_windows_auto_logon_flag,
            "change_com_plus_flag": change_com_plus_flag,
            "change_dcom_flag": change_dcom_flag,
            "change_scom_flag": change_scom_flag,
            "object_id": object_id,
        }

        validated_data = self.validate(
            attributes, operation="create", allow_unknown=False
        )

        endpoint = f"/managedsystems/{system_id}{self.endpoint}"

        req_structure = self.get_request_body_version(
            managed_accounts_fields, POST_MANAGED_SYSTEMS_SYSTEM_ID_MANAGED_ACCOUNTS
        )

        req_body = self.generate_request_body(req_structure, **validated_data)

        utils.print_log(
            self._logger,
            "Calling create_managed_account endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint,
            payload=req_body,
            expected_status_code=[201],
            include_api_version=True,
        )
        managed_account = response.json()
        utils.print_log(
            self._logger, "Managed account created successfully", logging.INFO
        )
        return managed_account, response.status_code

    def assign_attribute(self, managed_account_id: int, attribute_id: int) -> dict:
        """
        Assigns an attribute to a managed account.

        API: POST ManagedAccounts/{managedAccountID}/Attributes/{attributeID}

        Args:
            managed_account_id (int): ID of the managed account.
            attribute_id (int): ID of the attribute to assign.

        Returns:
            dict: Response from the API
        """

        endpoint = f"{self.endpoint}/{managed_account_id}/attributes/{attribute_id}"
        utils.print_log(
            self._logger,
            "Calling assign_attribute endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint, payload={}, include_api_version=False
        )
        return response.json()

    def delete_attribute(self, managed_account_id: int, attribute_id: int) -> None:
        """
        Deletes an attribute to a managed account.

        API: DELETE ManagedAccounts/{managedAccountID}/Attributes/{attributeID}

        Args:
            managed_account_id (int): ID of the managed account.
            attribute_id (int): ID of the attribute to assign.

        Returns:
            None.
        """

        endpoint = f"{self.endpoint}/{managed_account_id}/attributes/{attribute_id}"
        utils.print_log(
            self._logger,
            "Calling delete_attribute endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)

    def delete_all_attributes(self, managed_account_id: int) -> dict:
        """
        Deletes all managed account attributes by managed account ID.

        API: DELETE ManagedAccounts/{managedAccountID}/Attributes

        Args:
            managed_account_id (int): ID of the managed account.

        Returns:
            None.
        """

        endpoint = f"{self.endpoint}/{managed_account_id}/attributes"
        utils.print_log(
            self._logger,
            "Calling delete_all_attributes endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)

    def update_credentials(
        self,
        managed_account_id: int,
        private_key: str = None,
        public_key: str = None,
        password: str = None,
        passphrase: str = None,
        update_system: bool = True,
    ) -> None:
        """
        Updates the credentials of a managed account,
        optionally applying the change to the managed system.

        API: PUT ManagedAccounts/{managedAccountID}/Credentials

        Args:
            managed_account_id (int): ID of the managed account.
            private_key (str, optional): New private key for the managed account.
            public_key (str, optional): Required if private_key is provided and
                                        update_system is True.
                                        The new public key to set on the host.
            password (str, optional): New password for the managed account. If not
                                      given, generates a new random password.
            passphrase (str, optional): New passphrase for the private key.
            update_system (bool): True to update the system with new credentials,
                                  otherwise False.
        Returns:
            None.
        """

        attributes = {
            "password": password,
            "public_key": public_key,
            "private_key": private_key,
            "passphrase": passphrase,
            "update_system": update_system,
        }

        validated_data = self.validate(
            attributes, operation="update", allow_unknown=False
        )

        req_structure = self.get_request_body_version(
            managed_accounts_fields,
            PUT_MANAGED_ACCOUNTS_CREDENTIALS,
            Version.DEFAULT.value,
        )

        req_body = self.generate_request_body(req_structure, **validated_data)

        endpoint = f"{self.endpoint}/{managed_account_id}/credentials"
        utils.print_log(
            self._logger,
            "Calling update_credentials endpoint",
            logging.DEBUG,
        )
        self._run_put_request(
            endpoint,
            req_body,
            include_api_version=False,
            expected_status_code=204,
        )
