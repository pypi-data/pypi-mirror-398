"""Request Sets module, all the logic to manage requests from Password Safe API"""

import logging

from cerberus import Validator

from secrets_safe_library import utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import POST_REQUEST_SETS
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.request_sets import fields as requests_fields


class RequestSets(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/requestsets")

        # Schema rules used for validations
        self._schema = {
            "reason": {"type": "string", "maxlength": 1000, "nullable": True},
        }
        self._validator = Validator(self._schema)

    def get_request_sets(self, status: str = None) -> list:
        """
        Returns all Request Sets.

        API: GET RequestSets

        Args:
            status (str, optional): Status of requests to return. Options:
                    - all (default): Both active and pending requests.
                    - pending:  Requests that have not yet been approved.
                    - active: Requests approved (including auto-approved).

        Returns:
            list: List of Request Sets.
        """
        params = {"status": status}
        query_string = self.make_query_string(params)

        endpoint = f"{self.endpoint}?{query_string}"

        utils.print_log(
            self._logger,
            "Calling get_request_sets endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def post_request_sets(
        self,
        access_types: list,
        system_id: int,
        account_id: int,
        duration_minutes: int,
        application_id: int = None,
        reason: str = None,
        ticket_system_id: int = None,
        ticket_number: str = None,
    ) -> dict:
        """
        Creates a new Request Set.

        API: POST RequestSets

        Args:
            access_types (list): (at least two are required) A list of the types
                                of access requested (View, RDP, SSH, App).
            system_id (int): System ID.
            account_id (int): Account ID.
            duration_minutes (int, optional): Duration in minutes.
            application_id (int, optional): Application ID.
            reason (str, optional): Reason for the request.
            ticket_system_id (int, optional): Ticket system ID.
            ticket_number (str, optional): Ticket number.

        Returns:
            dict: Response from the API.
        """
        attributes = {
            "reason": reason,
        }

        if not self._validator.validate(attributes):
            raise utils.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            requests_fields, POST_REQUEST_SETS, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            access_types=access_types,
            system_id=system_id,
            account_id=account_id,
            duration_minutes=duration_minutes,
            application_id=application_id,
            reason=reason,
            ticket_system_id=ticket_system_id,
            ticket_number=ticket_number,
        )

        utils.print_log(
            self._logger,
            f"Calling post_request_sets endpoint: {self.endpoint}",
            logging.DEBUG,
        )
        response = self._run_post_request(
            self.endpoint, req_body, include_api_version=False
        )

        return response.json()
