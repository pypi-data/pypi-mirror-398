"""API registrations module, all the logic to manage API registrations from BI API"""

import logging

from secrets_safe_library import utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import POST_API_REGISTRATIONS
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.api_registrations import (
    fields as api_registrations_fields,
)
from secrets_safe_library.mixins import DeleteByIdMixin, GetByIdMixin, ListMixin
from secrets_safe_library.validators.api_registrations import APIRegistrationValidator


class APIRegistration(
    APIObject, GetByIdMixin, DeleteByIdMixin, ListMixin, APIRegistrationValidator
):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        APIObject.__init__(self, authentication, logger, endpoint="/apiregistrations")
        APIRegistrationValidator.__init__(self)

    def get_key_by_id(self, api_registration_id: int) -> str:
        """
        Retrieves the API key for an API Key policy API Registration.

        Args:
            api_registration_id (int): The ID of the API Registration to retrieve the
                key for.

        Returns:
            str: The API key content.
        """
        _ = self.validate(
            {"api_registration_id": api_registration_id},
            operation="get_key",
            allow_unknown=False,
        )
        endpoint = f"{self.endpoint}/{api_registration_id}/key"

        utils.print_log(self._logger, "Calling get_key_by_id endpoint", logging.DEBUG)
        response = self._run_get_request(
            endpoint, include_api_version=False, expected_status_code=[200, 201]
        )

        return response.text

    def rotate_api_key(self, api_registration_id: int) -> str:
        """
        Rotates the API key for an API Key policy API Registration.

        Args:
            api_registration_id (int): The ID of the API Registration to rotate the key
                for.

        Returns:
            str: The new API key content.
        """
        _ = self.validate(
            {"api_registration_id": api_registration_id},
            operation="rotate_key",
            allow_unknown=False,
        )

        endpoint = f"{self.endpoint}/{api_registration_id}/rotate"

        utils.print_log(self._logger, "Calling rotate_api_key endpoint", logging.DEBUG)

        response = self._run_post_request(
            endpoint, payload={}, include_api_version=False
        )

        return response.text

    def create_api_registration(
        self,
        name: str,
        registration_type: str,
        access_token_duration: int = 60,
        active: bool = True,
        visible: bool = True,
        multi_factor_authentication_enforced: bool = False,
        client_certificate_required: bool = False,
        user_password_required: bool = False,
        verify_psrun_signature: bool = False,
        ip_authentication_rules: list = None,
        psrun_rules: list = None,
        x_forwarded_for_authentication_rules: list = None,
    ) -> dict:
        """
        Creates a new API registration.

        API: POST ApiRegistrations

        Args:
            name (str): The registration name.
            registration_type (str): The type of registration, "ApiKeyPolicy" or
                "ApiAccessPolicy".
            access_token_duration (int, optional): Duration of the access token in
                minutes. Defaults to 60. Used with "ApiAccessPolicy" type.
            active (bool, optional): Whether the registration is active. Defaults to
                True.
            visible (bool, optional): Whether the registration is visible. Defaults to
                True.
            multi_factor_authentication_enforced (bool, optional): Whether MFA is
                enforced. Defaults to False.
            client_certificate_required (bool, optional): Whether a client certificate
                is required. Defaults to False.
            user_password_required (bool, optional): Whether a user password is
                required. Defaults to False.
            verify_psrun_signature (bool, optional): Whether to verify PSRun signature.
                Defaults to False.
            ip_authentication_rules (list, optional): List of IP authentication rules.
                Defaults to None, should be in this format: [{"Type": str,
                "Value": str, "Description": str}].
            psrun_rules (list, optional): List of PSRun rules. Defaults to None. Should
                be in this format: [{"Id": int, "IPAddress": str, "MacAddress": str,
                "SystemName": str, "FQDN": str, "DomainName": str, "UserId": str,
                "RootVolumeId": str, "OSVersion": str}]. Used with "ApiKeyPolicy" type.
            x_forwarded_for_authentication_rules (list, optional): List of
                X-Forwarded-For authentication rules. Defaults to None. should be in
                this format: [{"Type": str, "Value": str, "Description": str}].

        Returns:
            dict: The created API registration.
        """
        attributes = {
            "name": name,
            "registration_type": registration_type,
            "access_token_duration": access_token_duration,
            "active": active,
            "visible": visible,
            "multi_factor_authentication_enforced": (
                multi_factor_authentication_enforced
            ),
            "client_certificate_required": client_certificate_required,
            "user_password_required": user_password_required,
            "verify_psrun_signature": verify_psrun_signature,
            "ip_authentication_rules": utils.convert_as_literal(
                ip_authentication_rules
            ),
            "psrun_rules": utils.convert_as_literal(psrun_rules),
            "x_forwarded_for_authentication_rules": utils.convert_as_literal(
                x_forwarded_for_authentication_rules
            ),
        }

        validated_data = self.validate(
            attributes, operation="create", allow_unknown=False
        )

        req_structure = self.get_request_body_version(
            api_registrations_fields, POST_API_REGISTRATIONS, Version.DEFAULT.value
        )
        req_body = self.generate_request_body(
            req_structure,
            **validated_data,
        )

        utils.print_log(
            self._logger,
            f"Calling create API registration endpoint: {self.endpoint}",
            logging.DEBUG,
        )
        response = self._run_post_request(
            self.endpoint, req_body, include_api_version=False
        )

        return response.json()

    def update_api_registration(
        self,
        registration_id: int,
        name: str = None,
        registration_type: str = None,
        access_token_duration: int = 60,
        active: bool = True,
        visible: bool = True,
        multi_factor_authentication_enforced: bool = False,
        client_certificate_required: bool = False,
        user_password_required: bool = False,
        verify_psrun_signature: bool = False,
        ip_authentication_rules: list = None,
        psrun_rules: list = None,
        x_forwarded_for_authentication_rules: list = None,
    ) -> dict:
        """
        Update an existing API registration.

        API: PUT ApiRegistrations/{id}

        Args:
            registration_id (int): The ID of the API registration to update.
            name (str): The registration name.
            registration_type (str): The type of registration, "ApiKeyPolicy" or
                "ApiAccessPolicy".
            access_token_duration (int, optional): Duration of the access token in
                minutes. Defaults to 60. Used with "ApiAccessPolicy" type.
            active (bool, optional): Whether the registration is active. Defaults to
                True.
            visible (bool, optional): Whether the registration is visible. Defaults to
                True.
            multi_factor_authentication_enforced (bool, optional): Whether MFA is
                enforced. Defaults to False.
            client_certificate_required (bool, optional): Whether a client certificate
                is required. Defaults to False.
            user_password_required (bool, optional): Whether a user password is
                required. Defaults to False.
            verify_psrun_signature (bool, optional): Whether to verify PSRun signature.
                Defaults to False.
            ip_authentication_rules (list, optional): List of IP authentication rules.
                Defaults to None, should be in this format: [{"Type": str,
                "Value": str, "Description": str}].
            psrun_rules (list, optional): List of PSRun rules. Defaults to None. Should
                be in this format: [{"Id": int, "IPAddress": str, "MacAddress": str,
                "SystemName": str, "FQDN": str, "DomainName": str, "UserId": str,
                "RootVolumeId": str, "OSVersion": str}]. Used with "ApiKeyPolicy" type.
            x_forwarded_for_authentication_rules (list, optional): List of
                X-Forwarded-For authentication rules. Defaults to None. should be in
                this format: [{"Type": str, "Value": str, "Description": str}].

        Returns:
            dict: The updated API registration.
        """
        attributes = {
            "registration_id": registration_id,
            "name": name,
            "registration_type": registration_type,
            "access_token_duration": access_token_duration,
            "active": active,
            "visible": visible,
            "multi_factor_authentication_enforced": (
                multi_factor_authentication_enforced
            ),
            "client_certificate_required": client_certificate_required,
            "user_password_required": user_password_required,
            "verify_psrun_signature": verify_psrun_signature,
            "ip_authentication_rules": utils.convert_as_literal(
                ip_authentication_rules
            ),
            "psrun_rules": utils.convert_as_literal(psrun_rules),
            "x_forwarded_for_authentication_rules": utils.convert_as_literal(
                x_forwarded_for_authentication_rules
            ),
        }

        validated_data = self.validate(
            attributes, operation="update", allow_unknown=False
        )

        req_structure = self.get_request_body_version(
            api_registrations_fields, POST_API_REGISTRATIONS, Version.DEFAULT.value
        )
        req_body = self.generate_request_body(
            req_structure,
            **validated_data,
        )

        endpoint = f"{self.endpoint}/{registration_id}"

        utils.print_log(
            self._logger,
            "Calling update API registration endpoint",
            logging.DEBUG,
        )
        response = self._run_put_request(endpoint, req_body, include_api_version=False)

        return response.json()
