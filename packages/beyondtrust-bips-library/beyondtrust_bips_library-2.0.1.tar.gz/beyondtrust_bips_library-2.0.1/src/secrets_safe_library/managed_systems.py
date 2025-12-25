"""ManagedSystems Module, all the logic to retrieve managed systems from PS API"""

import logging

from secrets_safe_library import utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import (
    POST_MANAGED_SYSTEMS_ASSETID,
    POST_MANAGED_SYSTEMS_DATABASEID,
    POST_MANAGED_SYSTEMS_WORKGROUPID,
    PUT_MANAGED_SYSTEMS_MANAGEDSYSTEMID,
)
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.managed_systems import fields as managed_system_fields
from secrets_safe_library.validators.managed_systems import ManagedSystemValidator


class ManagedSystem(APIObject, ManagedSystemValidator):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        # Initialize the APIObject parent class
        APIObject.__init__(self, authentication, logger)

        # Initialize the ManagedSystemValidator parent class
        ManagedSystemValidator.__init__(self)

    def get_managed_systems(
        self, limit: int = None, offset: int = None, type: int = None, name: str = None
    ) -> list:
        """
        Returns a list of managed systems.

        API: GET ManagedSystems/

        Args:
            limit (int, optional): Number of records to return. (default: 100000)
            offset (int, optional): Records to skip before returning results
                                    (use with limit). (default: 0)
            type (int, optional): The entity type of the managed system.
            name (str, optional): The managed system name.

        Returns:
            list: List of managed systems.
        """

        params = {"limit": limit, "offset": offset, "type": type, "name": name}
        query_string = self.make_query_string(params)
        endpoint = f"/managedsystems?{query_string}"

        utils.print_log(
            self._logger,
            "Calling get_managed_systems endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_managed_system_by_id(self, managed_system_id: int) -> dict:
        """
        Find a managed system by ID.

        API: GET ManagedSystems/{id}

        Args:
            managed_system_id (int): The managed system ID.

        Returns:
            dict: Managed system object.
        """

        endpoint = f"/managedsystems/{managed_system_id}"

        utils.print_log(
            self._logger,
            "Calling get_managed_system_by_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_managed_system_by_asset_id(self, asset_id: int) -> dict:
        """
        Find a managed system by asset ID.

        API: GET Assets/{assetId}/ManagedSystems

        Args:
            assetId (int): The asset ID.

        Returns:
            dict: Managed system object.
        """

        endpoint = f"/assets/{asset_id}/managedsystems"

        utils.print_log(
            self._logger,
            "Calling get_managed_system_by_asset_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_managed_system_by_database_id(self, database_id: int) -> dict:
        """
        Find a managed system by database ID.

        API: GET Databases/{databaseID}/ManagedSystems

        Args:
            databaseID (int): The database ID.
        Returns:
            dict: Managed system object.
        """

        endpoint = f"/databases/{database_id}/managedsystems"

        utils.print_log(
            self._logger,
            "Calling get_managed_system_by_database_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_managed_system_by_functional_account_id(
        self,
        functional_account_id: int,
        limit: int = None,
        offset: int = None,
        type: int = None,
        name: str = None,
    ) -> list:
        """
        Returns a list of managed systems auto-managed by the functional
        account referenced by ID.

        API: GET FunctionalAccounts/{id}/ManagedSystems

        Args:
            id (int): The functional account ID.
            limit (int, optional): Number of records to return. (default: 100000)
            offset (int, optional): Records to skip before returning results
                                    (use with limit). (default: 0)
            type (int, optional): The entity type of the managed system.
            name (str, optional): The managed system name.

        Returns:
            list: List of managed systems by functional account id.
        """
        params = {
            "limit": limit,
            "offset": offset,
            "type": type,
            "name": name,
        }
        query_string = self.make_query_string(params)
        endpoint = (
            f"/functionalaccounts/{functional_account_id}/managedsystems?"
            f"{query_string}"
        )

        utils.print_log(
            self._logger,
            "Calling get_managed_system_by_functional_account_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def get_managed_system_by_workgroup_id(
        self, workgroup_id: int, limit: int = None, offset: int = None
    ) -> list:
        """
        Returns a list of managed systems by Workgroup ID.

        API: GET Workgroups/{id}/ManagedSystems

        Args:
            id (int): The workgroup ID.
            limit (int, optional): Number of records to return. (default: 100000)
            offset (int, optional): Records to skip before returning results
                                    (use with limit). (default: 0)

        Returns:
            list: List of managed systems by workgroup id.
        """

        params = {"limit": limit, "offset": offset}
        query_string = self.make_query_string(params)
        endpoint = f"/workgroups/{workgroup_id}/managedsystems?{query_string}"

        utils.print_log(
            self._logger,
            "Calling get_managed_system_by_workgroup_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def post_managed_system_by_asset_id(
        self,
        *,
        asset_id: int,
        platform_id: int,
        contact_email: str,
        description: str,
        release_duration: int,
        max_release_duration: int,
        isa_release_duration: int,
        password_rule_id: int,
        check_password_flag: bool,
        change_password_after_any_release_flag: bool,
        reset_password_on_mismatch_flag: bool,
        change_frequency_type: str,
        change_frequency_days: int,
        change_time: str,
        is_application_host: bool,
        timeout: int = 30,
        port: int = None,
        ssh_key_enforcement_mode: int = None,
        dss_key_rule_id: int = None,
        login_account_id: int = None,
        auto_management_flag: bool = None,
        functional_account_id: int = None,
        elevation_command: str = None,
        remote_client_type: str = None,
        application_host_id: int = None,
    ) -> dict:
        """
        Creates a managed system for the asset referenced by ID.

        API: POST Assets/{assetId}/ManagedSystems

        Args:
            asset_id (int): The asset ID.
            platform_id (int): ID of the managed system platform..
            contact_email (str): Contact email (max 1000 characters).
            description (str): Decription (max 255 characters).
            timeout (int): Connection timeout. Length of time in seconds before a slow
                           or unresponsive connection to the system fails.
            release_duration (int):  Default release duration (default: 120).
            max_release_duration (int): Maximum release duration (default: 525600).
            isa_release_duration (int): ISA release duration (default: 120).
            password_rule_id (int): ID of the password rule (Default: 0).
            check_password_flag (bool): True to enable pswrd testing, otherwise false.
            change_password_after_any_release_flag(bool): True to change pswd on release
                                                      of a request, otherwise false.
            reset_password_on_mismatch_flag (bool): True to reset password on mismatch,
                                                otherwise false.
            change_frequency_type (str): The change frequency for scheduled password
                                       changes (default: first)
                            first: Changes scheduled for the first day of the month.
                            last: Changes scheduled for the last day of the month.
                            xdays: Changes scheduled every x days(change_frequency_days)
            change_frequency_days (int): if change_frequency_type is xdays, password
                                     changes take place this configured number of days.
            change_time (str): UTC time of day scheduled password changes take place.
                             (default: 23:30).
            is_application_host (bool): True if the managed system can be used as an
                                      application host, otherwise false (default:false)
                                      Cannot be set if application_host_id has a value.
            port (int, optional): The port used to connect to the host.
            ssh_key_enforcement_mode (int, optional): Enforcement mode for SSH host
                                                      keys.
                                        0: None.
                                        1: Auto. Auto accept initial key.
                                        2: Strict. Manually accept keys.
            dss_key_rule_id (int, optional): ID of the default DSS key rule assigned
                                to managed accounts created under this managed system.
            login_account_id (int, optional): ID of the functional account for
                                            SSH Session logins.
            auto_management_flag (bool, optional): Auto management flag
                                                   (default: False).
            functional_account_id (int, optional): ID functional account used for
                                       local managed account password changes.
            elevation_command (str, optional): Elevation command used to elevate
                                              privileges. (sudo, pbrun, pmrun)
            remote_client_type (str, optional): The remote client type (default: None).
                                        None: No remote client.
                                        EPM: Endpoint Privilege Management.
            application_host_id (int, optional): Managed system ID of the target
                                                application host (default: null).
                                                Must be an ID of a managed system
                                                whose is_application_host = true.

        Returns:
            dict: Managed system object.
        """
        attributes = {
            "platform_id": platform_id,
            "contact_email": contact_email,
            "description": description,
            "port": port,
            "timeout": timeout,
            "ssh_key_enforcement_mode": ssh_key_enforcement_mode,
            "password_rule_id": password_rule_id,
            "dss_key_rule_id": dss_key_rule_id,
            "login_account_id": login_account_id,
            "release_duration": release_duration,
            "max_release_duration": max_release_duration,
            "isa_release_duration": isa_release_duration,
            "auto_management_flag": auto_management_flag,
            "functional_account_id": functional_account_id,
            "elevation_command": elevation_command,
            "check_password_flag": check_password_flag,
            "change_password_after_any_release_flag": (
                change_password_after_any_release_flag
            ),
            "reset_password_on_mismatch_flag": reset_password_on_mismatch_flag,
            "change_frequency_type": change_frequency_type,
            "change_frequency_days": change_frequency_days,
            "change_time": change_time,
            "remote_client_type": remote_client_type,
            "application_host_id": application_host_id,
            "is_application_host": is_application_host,
        }

        validated_data = self.validate(
            attributes,
            operation="create_by_asset",
            version=self._authentication._api_version,
        )

        req_structure = self.get_request_body_version(
            managed_system_fields, POST_MANAGED_SYSTEMS_ASSETID
        )

        req_body = self.generate_request_body(
            req_structure,
            **validated_data,
        )

        endpoint = f"/assets/{asset_id}/managedsystems"

        utils.print_log(
            self._logger,
            "Calling post_managed_system_by_asset_id endpoint",
            logging.DEBUG,
        )

        response = self._run_post_request(
            endpoint, req_body, expected_status_code=[200, 201]
        )
        status_code = response.status_code

        return response.json(), status_code

    def post_managed_system_by_database_id(
        self,
        database_id: int,
        contact_email: str,
        description: str,
        timeout: int,
        password_rule_id: int,
        release_duration: int,
        max_release_duration: int,
        isa_release_duration: int,
        auto_management_flag: bool,
        check_password_flag: bool,
        change_password_after_any_release_flag: bool,
        reset_password_on_mismatch_flag: bool,
        change_frequency_type: str,
        change_frequency_days: int,
        change_time: str,
        functional_account_id: int = None,
    ) -> dict:
        """
        Creates a managed system for the database referenced by ID.

        API: POST Databases/{databaseID}/ManagedSystems

        Args:
            database_id (int): The database ID.
            contact_email (str): Contact email (max 1000 characters).
            description (str): Decription (max 255 characters).
            timeout (int): Connection timeout. Length of time in seconds before a slow
                           or unresponsive connection to the system fails.
            password_rule_id (int): ID of the password rule (Default: 0).
            release_duration (int):  Default release duration (default: 120).
            max_release_duration (int): Maximum release duration (default: 525600).
            isa_release_duration (int): ISA release duration (default: 120).
            auto_management_flag (bool): Auto management flag (default: False).
            check_password_flag (bool): True to enable pswrd testing, otherwise false.
            change_password_after_any_release_flag(bool): True to change pswd on release
                                                      of a request, otherwise false.
            reset_password_on_mismatch_flag (bool): True to reset password on mismatch,
                                                otherwise false.
            change_frequency_type (str): The change frequency for scheduled password
                                       changes (default: first)
                            first: Changes scheduled for the first day of the month.
                            last: Changes scheduled for the last day of the month.
                            xdays: Changes scheduled every x days(change_frequency_days)
            change_frequency_days (int): if change_frequency_type is xdays, password
                                     changes take place this configured number of days.
            change_time (str): UTC time of day scheduled password changes take place.
                             (default: 23:30).
            functional_account_id (int, optional): ID functional account used for local
                                        managed account password changes.

        Returns:
            dict: Managed system object.
        """

        attributes = {
            "contact_email": contact_email,
            "description": description,
            "timeout": timeout,
            "password_rule_id": password_rule_id,
            "release_duration": release_duration,
            "max_release_duration": max_release_duration,
            "isa_release_duration": isa_release_duration,
            "auto_management_flag": auto_management_flag,
            "functional_account_id": functional_account_id,
            "check_password_flag": check_password_flag,
            "change_password_after_any_release_flag": (
                change_password_after_any_release_flag
            ),
            "reset_password_on_mismatch_flag": reset_password_on_mismatch_flag,
            "change_frequency_type": change_frequency_type,
            "change_frequency_days": change_frequency_days,
            "change_time": change_time,
        }

        validated_data = self.validate(attributes, operation="create_by_database")

        req_structure = self.get_request_body_version(
            managed_system_fields,
            POST_MANAGED_SYSTEMS_DATABASEID,
            Version.DEFAULT.value,
        )

        req_body = self.generate_request_body(
            req_structure,
            **validated_data,
        )

        endpoint = f"/databases/{database_id}/managedsystems"

        utils.print_log(
            self._logger,
            "Calling post_managed_system_by_database_id endpoint",
            logging.DEBUG,
        )

        response = self._run_post_request(
            endpoint, req_body, expected_status_code=[200, 201]
        )
        status_code = response.status_code

        return response.json(), status_code

    def post_managed_system_by_workgroup_id(
        self,
        workgroup_id: int,
        entity_type_id: int,
        host_name: str,
        ip_address: str,
        dns_name: str,
        instance_name: str,
        template: str,
        forest_name: str,
        platform_id: int,
        net_bios_name: str,
        contact_email: str,
        description: str,
        timeout: int,
        password_rule_id: int,
        account_name_format: int,
        oracle_internet_directory_service_name: str,
        release_duration: int,
        max_release_duration: int,
        isa_release_duration: int,
        auto_management_flag: bool,
        check_password_flag: bool,
        change_password_after_any_release_flag: bool,
        reset_password_on_mismatch_flag: bool,
        change_frequency_type: str,
        change_frequency_days: int,
        change_time: str,
        remote_client_type: str,
        is_application_host: bool,
        access_url: str,
        is_default_instance: bool = None,
        use_ssl: bool = None,
        port: int = None,
        ssh_key_enforcement_mode: int = None,
        dss_key_rule_id: int = None,
        login_account_id: int = None,
        oracle_internet_directory_id: str = None,
        functional_account_id: int = None,
        elevation_command: str = None,
        application_host_id: int = None,
    ) -> dict:
        """
        Creates a managed system for the workgroup referenced by ID.

        API: POST Workgroups/{workgroupID}/ManagedSystems

        Args:
            workgroup_id (int): The workgroup ID.
            entity_type_id (int): The entity type ID.
            host_name (str): The host name.
            ip_address (str): The IP address.
            dns_name (str): The DNS name.
            instance_name (str): The instance name.
            template (str): The template."
            forest_name (str): The forest name.
            platform_id (int): The platform ID.
            net_bios_name (str): The NetBIOS name.
            contact_email (str): The contact email.
            description (str): The description.
            timeout (int): The timeout.
            password_rule_id (int): The password rule ID.
            account_name_format (int): The account name format.
            oracle_internet_directory_service_name (str): The Oracle Internet Directory
                                                         service name.
            release_duration (int): The release duration.
            max_release_duration (int): The maximum release duration.
            isa_release_duration (int): The ISA release duration.
            auto_management_flag (bool): True if auto management is enabled.
            check_password_flag (bool): True if password checking is enabled.
            change_password_after_any_release_flag (bool): True if password change
                                                           after any release is enabled.
            reset_password_on_mismatch_flag (bool): True if password reset on
                                                    mismatch is enabled.
            change_frequency_type (str): The change frequency type.
            change_frequency_days (int): The change frequency days.
            change_time (str): The change time.
            remote_client_type (str): The remote client type.
            is_application_host (bool): True if the managed system is an
                                        application host.
            access_url (str): The access URL.
            is_default_instance (bool, optional): True if the instance is the
                                                default instance.
            use_ssl (bool, optional): True if SSL is used.
            port (int, optional): The port number.
            ssh_key_enforcement_mode (int, optional): The SSH key enforcement mode.
            dss_key_rule_id (int): The DSS key rule ID.
            login_account_id (int, optional): The login account ID.
            oracle_internet_directory_id (str, optional): The Oracle Internet
                                                          Directory GUID.
            functional_account_id (int, optional): The functional account ID.
            elevation_command (str, optional): The elevation command.
            application_host_id (int, optional): The application host ID.

        Returns:
            dict: Managed system object.
        """
        attributes = {
            "entity_type_id": entity_type_id,
            "host_name": host_name,
            "ip_address": ip_address,
            "dns_name": dns_name,
            "instance_name": instance_name,
            "is_default_instance": is_default_instance,
            "template": template,
            "forest_name": forest_name,
            "use_ssl": use_ssl,
            "platform_id": platform_id,
            "net_bios_name": net_bios_name,
            "contact_email": contact_email,
            "description": description,
            "port": port,
            "timeout": timeout,
            "ssh_key_enforcement_mode": ssh_key_enforcement_mode,
            "password_rule_id": password_rule_id,
            "dss_key_rule_id": dss_key_rule_id,
            "login_account_id": login_account_id,
            "account_name_format": account_name_format,
            "oracle_internet_directory_id": oracle_internet_directory_id,
            "oracle_internet_directory_service_name": (
                oracle_internet_directory_service_name
            ),
            "release_duration": release_duration,
            "max_release_duration": max_release_duration,
            "isa_release_duration": isa_release_duration,
            "auto_management_flag": auto_management_flag,
            "functional_account_id": functional_account_id,
            "elevation_command": elevation_command,
            "check_password_flag": check_password_flag,
            "change_password_after_any_release_flag": (
                change_password_after_any_release_flag
            ),
            "reset_password_on_mismatch_flag": reset_password_on_mismatch_flag,
            "change_frequency_type": change_frequency_type,
            "change_frequency_days": change_frequency_days,
            "change_time": change_time,
            "remote_client_type": remote_client_type,
            "application_host_id": application_host_id,
            "is_application_host": is_application_host,
            "access_url": access_url,
        }

        validated_data = self.validate(
            attributes,
            operation="create_by_workgroup",
            version=self._authentication._api_version,
        )

        req_structure = self.get_request_body_version(
            managed_system_fields, POST_MANAGED_SYSTEMS_WORKGROUPID
        )

        req_body = self.generate_request_body(
            req_structure,
            **validated_data,
        )

        endpoint = f"/workgroups/{workgroup_id}/managedsystems"

        utils.print_log(
            self._logger,
            "Calling post_managed_system_by_workgroup_id endpoint",
            logging.DEBUG,
        )

        response = self._run_post_request(
            endpoint, req_body, expected_status_code=[200, 201]
        )
        status_code = response.status_code

        return response.json(), status_code

    def delete_managed_system_by_id(self, managed_system_id: int) -> None:
        """
        Deletes a managed system by ID.

        API: DELETE ManagedSystems/{id}

        Args:
            managed_system_id (int): The managed system ID.

        Returns:
            None: If deletion is successful no exceptions.DeletionError is raised.
        """

        endpoint = f"/managedsystems/{managed_system_id}"

        utils.print_log(
            self._logger,
            "Calling delete_managed_system_by_id endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)

    def put_managed_system_by_id(
        self,
        managed_system_id: int,
        workgroup_id: int,
        host_name: str,
        ip_address: str,
        dns_name: str,
        instance_name: str,
        template: str,
        forest_name: str,
        platform_id: int,
        net_bios_name: str,
        contact_email: str,
        description: str,
        timeout: int,
        password_rule_id: int,
        release_duration: int,
        max_release_duration: int,
        isa_release_duration: int,
        auto_management_flag: bool,
        check_password_flag: bool,
        change_password_after_any_release_flag: bool,
        reset_password_on_mismatch_flag: bool,
        change_frequency_type: str,
        change_frequency_days: int,
        change_time: str,
        remote_client_type: str,
        is_application_host: bool,
        access_url: str,
        is_default_instance: bool = None,
        use_ssl: bool = None,
        port: int = None,
        ssh_key_enforcement_mode: int = None,
        dss_key_rule_id: int = None,
        login_account_id: int = None,
        functional_account_id: int = None,
        elevation_command: str = None,
        application_host_id: int = None,
    ) -> dict:
        """
        Updates a managed system by ID.

        API: PUT ManagedSystems/{id}
        Args:
            managed_system_id (int): The managed system ID.
            workgroup_id (int): The workgroup ID.
            host_name (str): The host name.
            ip_address (str): The IP address.
            dns_name (str): The DNS name.
            instance_name (str): The instance name.
            template (str): The template.
            forest_name (str): The forest name.
            platform_id (int): The platform ID.
            net_bios_name (str): The NetBIOS name.
            contact_email (str): The contact email.
            description (str): The description.
            timeout (int): The timeout.
            password_rule_id (int): The password rule ID.
            release_duration (int): The release duration.
            max_release_duration (int): The maximum release duration.
            isa_release_duration (int): The ISA release duration.
            auto_management_flag (bool): True if auto management is enabled.
            check_password_flag (bool): True if password checking is enabled.
            change_password_after_any_release_flag (bool): True if password change
                                                           after any release is enabled.
            reset_password_on_mismatch_flag (bool): True if password reset on
                                                    mismatch is enabled.
            change_frequency_type (str): The change frequency type.
            change_frequency_days (int): The change frequency days.
            change_time (str): The change time.
            remote_client_type (str): The remote client type.
            is_application_host (bool): True if the managed system is an
                                        application host.
            access_url (str): The access URL.
            is_default_instance (bool, optional): True if the instance is the
                                                default instance.
            use_ssl (bool, optional): True if SSL is used.
            port (int, optional): The port number.
            ssh_key_enforcement_mode (int, optional): The SSH key enforcement mode.
            dss_key_rule_id (int, optional): The DSS key rule ID.
            login_account_id (int, optional): The login account ID.
            functional_account_id (int, optional): The functional account ID.
            elevation_command (str, optional): The elevation command.
            application_host_id (int, optional): The application host ID.

        Returns:
            dict: Managed system object.
        """
        attributes = {
            "workgroup_id": workgroup_id,
            "host_name": host_name,
            "ip_address": ip_address,
            "dns_name": dns_name,
            "instance_name": instance_name,
            "template": template,
            "forest_name": forest_name,
            "platform_id": platform_id,
            "net_bios_name": net_bios_name,
            "contact_email": contact_email,
            "description": description,
            "timeout": timeout,
            "password_rule_id": password_rule_id,
            "release_duration": release_duration,
            "max_release_duration": max_release_duration,
            "isa_release_duration": isa_release_duration,
            "auto_management_flag": auto_management_flag,
            "check_password_flag": check_password_flag,
            "change_password_after_any_release_flag": (
                change_password_after_any_release_flag
            ),
            "reset_password_on_mismatch_flag": reset_password_on_mismatch_flag,
            "change_frequency_type": change_frequency_type,
            "change_frequency_days": change_frequency_days,
            "change_time": change_time,
            "remote_client_type": remote_client_type,
            "is_application_host": is_application_host,
            "access_url": access_url,
            "is_default_instance": is_default_instance,
            "use_ssl": use_ssl,
            "port": port,
            "ssh_key_enforcement_mode": ssh_key_enforcement_mode,
            "dss_key_rule_id": dss_key_rule_id,
            "login_account_id": login_account_id,
            "functional_account_id": functional_account_id,
            "elevation_command": elevation_command,
            "application_host_id": application_host_id,
        }

        validated_data = self.validate(
            attributes,
            operation="update",
            version=self._authentication._api_version,
            update=True,
        )

        req_structure = self.get_request_body_version(
            managed_system_fields, PUT_MANAGED_SYSTEMS_MANAGEDSYSTEMID
        )

        req_body = self.generate_request_body(
            req_structure,
            **validated_data,
        )

        endpoint = f"/managedsystems/{managed_system_id}"

        utils.print_log(
            self._logger,
            "Calling put_managed_system_by_id endpoint",
            logging.DEBUG,
        )

        response = self._run_put_request(endpoint, req_body)

        return response.json()
