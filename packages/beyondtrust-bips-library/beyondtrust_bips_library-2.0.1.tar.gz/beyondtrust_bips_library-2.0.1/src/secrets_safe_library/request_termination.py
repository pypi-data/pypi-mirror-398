"""Request Termination module, all the logic to manage requests from PasswordSafe API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import (
    POST_REQUEST_TERMINATION_MANAGED_ACCOUNT_ID,
    POST_REQUEST_TERMINATION_MANAGED_SYSTEM_ID,
    POST_REQUEST_TERMINATION_USER_ID,
)
from secrets_safe_library.core import APIObject


class RequestTermination(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger)

        # Schema rules used for validations
        self._schema = {
            "reason": {
                "type": "string",
                "maxlength": 1000,
                "nullable": True,
            },
        }
        self._validator = Validator(self._schema)

    def post_request_termination_managed_account_id(
        self,
        managed_account_id: int,
        reason: str = None,
    ) -> None:
        """
        Terminates a managed account request.

        API: POST Requests/{managedaccountid}/requests/terminate
        Args:
            managed_account_id (int): The managed account ID.
            reason (str, optional): The reason for the termination.
        """

        attibute = {
            "reason": reason,
        }
        if not self._validator.validate(attibute, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Reason": reason,
        }

        endpoint = "/" + POST_REQUEST_TERMINATION_MANAGED_ACCOUNT_ID.format(
            managedaccountid=managed_account_id
        ).replace("post:", "")

        utils.print_log(
            self._logger,
            "Calling post_request_termination_managed_account_id endpoint",
            logging.DEBUG,
        )
        self._run_post_request(
            endpoint, payload, include_api_version=False, expected_status_code=204
        )

    def post_request_termination_managed_system_id(
        self,
        managed_system_id: int,
        reason: str = None,
    ) -> None:
        """
        Terminates a managed system request.

        API: POST Requests/{managedsystemid}/requests/terminate
        Args:
            managed_system_id (int): The managed system ID.
            reason (str, optional): The reason for the termination.
        """

        attibute = {
            "reason": reason,
        }
        if not self._validator.validate(attibute, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Reason": reason,
        }

        endpoint = "/" + POST_REQUEST_TERMINATION_MANAGED_SYSTEM_ID.format(
            managedsystemid=managed_system_id
        ).replace("post:", "")

        utils.print_log(
            self._logger,
            "Calling post_request_termination_managed_system_id endpoint",
            logging.DEBUG,
        )
        self._run_post_request(
            endpoint, payload, include_api_version=False, expected_status_code=204
        )

    def post_request_termination_user_id(
        self,
        userid: int,
        reason: str = None,
    ) -> None:
        """
        Terminates a user request.

        API: POST Requests/{userid}/requests/terminate
        Args:
            userid (int): The user ID.
            reason (str, optional): The reason for the termination.
        """

        attibute = {
            "reason": reason,
        }
        if not self._validator.validate(attibute, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "Reason": reason,
        }

        endpoint = "/" + POST_REQUEST_TERMINATION_USER_ID.format(userid=userid).replace(
            "post:", ""
        )

        utils.print_log(
            self._logger,
            "Calling post_request_termination_user_id endpoint",
            logging.DEBUG,
        )
        self._run_post_request(
            endpoint, payload, include_api_version=False, expected_status_code=204
        )
