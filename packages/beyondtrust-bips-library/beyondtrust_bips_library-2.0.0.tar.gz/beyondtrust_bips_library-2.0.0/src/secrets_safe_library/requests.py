"""Requests module, all the logic to manage requests from Password Safe API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import (
    POST_REQUESTS,
    POST_REQUESTS_ALIASES,
)
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.requests import fields as requests_fields


class Request(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger)

        # Schema rules used for validations
        self._schema = {
            "access_type": {
                "type": "string",
                "allowed": ["View", "RDP", "SSH", "App"],
                "nullable": True,
            },
            "duration_minutes": {
                "type": "integer",
                "min": 1,
                "max": 525600,
                "nullable": True,
            },
            "reason": {
                "type": "string",
                "maxlength": 1000,
                "nullable": True,
            },
        }
        self._validator = Validator(self._schema)

    def get_requests(self, status: str = None, queue: str = None) -> list:
        """
        Returns all Requests.

        API: GET Requests

        Args:
            status (str, optional): Status of requests to return. Options:
                    - all (default): Both active and pending requests.
                    - pending:  Requests that have not yet been approved.
                    - active: Requests approved (including auto-approved).
            queue (str, optional): Type of request queue to return. Options:
                    - req (default): Requestor queue, returns requests available to the
                                     user as a requestor.
                    - app: Approver queue, returns requests for an approver or
                           requestor/approver that have either been approved by the user
                           (active) or have not yet been approved (pending).

        Returns:
            list: List of Requests.
        """
        params = {"status": status, "queue": queue}

        query_string = self.make_query_string(params)
        endpoint = f"/requests?{query_string}"

        utils.print_log(
            self._logger,
            "Calling get_requests endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def post_request(
        self,
        system_id: int,
        account_id: int,
        duration_minutes: int,
        application_id: int = None,
        reason: str = None,
        access_type: str = None,
        access_policy_schedule_id: int = None,
        conflict_option: str = None,
        ticket_system_id: int = None,
        ticket_number: str = None,
        rotate_on_checkin: bool = False,
    ) -> tuple[dict, int]:
        """
        Creates a new Request.

        API: POST Requests

        Args:
            system_id (int): ID of the managed system to request.
            account_id (int): ID of the managed account to request.
            duration_minutes (int): The request duration (in minutes).
            application_id (int, optional): The Application ID.
                                            Required when AccessType=App
            reason (str, optional): Reason for the request.
            access_type (str, optional): Type of access requested.
                                         Options: View, RDP, SSH, App.
            access_policy_schedule_id (int, optional): Access Policy Schedule ID.
            conflict_option (str, optional): Conflict option for the request.
            ticket_system_id (int, optional): Ticket System ID.
            ticket_number (str, optional): Ticket number associated with the request.
            rotate_on_checkin (bool, optional): Whether to rotate the password
                                                 on check-in/expiry.
        Returns:
            dict: The created Request.
        """
        attributes = {
            "access_type": access_type,
            "duration_minutes": duration_minutes,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            requests_fields, POST_REQUESTS, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            system_id=system_id,
            account_id=account_id,
            duration_minutes=duration_minutes,
            application_id=application_id,
            reason=reason,
            access_type=access_type,
            access_policy_schedule_id=access_policy_schedule_id,
            conflict_option=conflict_option,
            ticket_system_id=ticket_system_id,
            ticket_number=ticket_number,
            rotate_on_checkin=rotate_on_checkin,
        )

        endpoint = "/requests"
        utils.print_log(
            self._logger,
            "Calling post_request endpoint",
            logging.DEBUG,
        )

        response = self._run_post_request(
            endpoint,
            req_body,
            include_api_version=False,
            expected_status_code=[200, 201],
        )

        status_code = response.status_code

        return response.json(), status_code

    def post_request_alias(
        self,
        alias_id: int,
        duration_minutes: int,
        access_type: str = None,
        reason: str = None,
        access_policy_schedule_id: int = None,
        conflict_option: str = None,
        ticket_system_id: int = None,
        ticket_number: str = None,
        rotate_on_checkin: bool = False,
    ) -> tuple[dict, int]:
        """
        Creates a new release request using an alias.

        API: POST Aliases/{aliasId}/Requests

        Args:
            alias_id (int): ID of the managed account alias.
            duration_minutes (int): The Request duration (in minutes).
            access_type (str, optional): Type of access requested.
                                         Options: View, RDP, SSH, App.
            reason (str, optional): Reason for the request.
            access_policy_schedule_id (int, optional): Access Policy Schedule ID.
            conflict_option (str, optional): Conflict option for the request.
            ticket_system_id (int, optional): Ticket System ID.
            ticket_number (str, optional): Ticket number associated with the request.
            rotate_on_checkin (bool, optional): Whether to rotate the password
                                                 on check-in/expiry.
        Returns:
            dict: The created Request.
        """
        attributes = {
            "duration_minutes": duration_minutes,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            requests_fields, POST_REQUESTS_ALIASES, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            access_type=access_type,
            reason=reason,
            access_policy_schedule_id=access_policy_schedule_id,
            conflict_option=conflict_option,
            ticket_system_id=ticket_system_id,
            ticket_number=ticket_number,
            rotate_on_checkin=rotate_on_checkin,
        )

        endpoint = f"/aliases/{alias_id}/requests"
        utils.print_log(
            self._logger,
            "Calling post_request endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(
            endpoint,
            req_body,
            include_api_version=False,
            expected_status_code=[200, 201],
        )

        status_code = response.status_code

        return response.json(), status_code

    def put_request_checkin(
        self,
        request_id: int,
        reason: str = None,
    ) -> None:
        """
        Checks-in/releases a request before it has expired.

        API: PUT Requests/{request_id}/checkin

        Args:
            request_id (int): The Request ID.
            reason (str, optional): Reason for the check-in.
        """

        attibute = {
            "reason": reason,
        }
        if not self._validator.validate(attibute, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Reason": reason,
        }

        endpoint = f"/requests/{request_id}/checkin"
        utils.print_log(
            self._logger,
            "Calling put_request_checkin endpoint",
            logging.DEBUG,
        )
        self._run_put_request(
            endpoint, payload, include_api_version=False, expected_status_code=204
        )

    def put_request_approve(
        self,
        request_id: int,
        reason: str = None,
    ) -> None:
        """
        Approves a pending request.

        API: PUT Requests/{request_id}/approve

        Args:
            request_id (int): The Request ID.
            reason (str, optional): Reason for the approval.
        """

        attibute = {
            "reason": reason,
        }
        if not self._validator.validate(attibute, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Reason": reason,
        }

        endpoint = f"/requests/{request_id}/approve"
        utils.print_log(
            self._logger,
            "Calling put_request_approve endpoint",
            logging.DEBUG,
        )
        self._run_put_request(
            endpoint, payload, include_api_version=False, expected_status_code=204
        )

    def put_request_deny(
        self,
        request_id: int,
        reason: str = None,
    ) -> None:
        """
        Denies/cancels an active or pending request.

        API: PUT Requests/{request_id}/deny

        Args:
            request_id (int): The Request ID.
            reason (str, optional): Reason for the denial.
        """

        attibute = {
            "reason": reason,
        }
        if not self._validator.validate(attibute, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Reason": reason,
        }

        endpoint = f"/requests/{request_id}/deny"
        utils.print_log(
            self._logger,
            "Calling put_request_deny endpoint",
            logging.DEBUG,
        )
        self._run_put_request(
            endpoint, payload, include_api_version=False, expected_status_code=204
        )

    def put_request_rotate_on_checkin(
        self,
        request_id: int,
    ) -> None:
        """
        Updates a request to rotate the credentials on check-in/expiry.

        API: PUT Requests/{request_id}/rotateoncheckin

        Args:
            request_id (int): The Request ID.

        Returns:
            None
        """

        endpoint = f"/requests/{request_id}/rotateoncheckin"
        utils.print_log(
            self._logger,
            "Calling put_requests_rotate_on_checkin endpoint",
            logging.DEBUG,
        )
        self._run_put_request(
            endpoint, payload={}, include_api_version=False, expected_status_code=204
        )
