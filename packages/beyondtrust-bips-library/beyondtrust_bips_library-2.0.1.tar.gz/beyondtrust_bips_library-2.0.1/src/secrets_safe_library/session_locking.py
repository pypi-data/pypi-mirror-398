"""Session Locking module, all the logic to lock sessions from PS API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject


class SessionLocking(APIObject):
    """
    Class to interact with session locking in PS API.
    """

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/sessions")

        # Schema rules used for validations
        self._schema = {
            "session_id": {"type": "integer", "nullable": True},
            "managed_account_id": {"type": "integer", "nullable": True},
            "managed_system_id": {"type": "integer", "nullable": True},
        }
        self._validator = Validator(self._schema)

    def post_session_lock_sessionid(
        self,
        session_id: int,
    ) -> None:
        """
        Locks a session by session ID.

        API: POST Sessions/{sessionid}/lock

        Args:
            session_id (int): The session ID.

        Returns:
            None
        """

        attributes = {
            "session_id": session_id,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"{self.endpoint}/{session_id}/lock"

        utils.print_log(
            self._logger,
            "Calling post_session_lock_sessionid endpoint",
            logging.DEBUG,
        )

        self._run_post_request(
            endpoint, payload={}, include_api_version=False, expected_status_code=204
        )

        utils.print_log(
            self._logger,
            f"Session with ID {session_id} locked successfully.",
            logging.INFO,
        )

    def post_session_lock_managed_account_id(
        self,
        managed_account_id: int,
    ) -> None:
        """
        Locks all active sessions by managed account ID.

        API: POST ManagedAccounts/{managedaccountid}/sessions/lock

        Args:
            managed_account_id (int): The managed account ID.

        Returns:
            None
        """

        attributes = {
            "managed_account_id": managed_account_id,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/managedaccounts/{managed_account_id}{self.endpoint}/lock"

        utils.print_log(
            self._logger,
            "Calling post_session_lock_managed_account_id endpoint",
            logging.DEBUG,
        )

        self._run_post_request(
            endpoint, payload={}, include_api_version=False, expected_status_code=204
        )

        utils.print_log(
            self._logger,
            f"Session with managed account ID {managed_account_id} "
            "locked successfully.",
            logging.INFO,
        )

    def post_session_lock_managed_system_id(
        self,
        managed_system_id: int,
    ) -> None:
        """
        Locks all active sessions by managed system ID.

        API: POST ManagedSystems/{managedsystemid}/sessions/lock

        Args:
            managed_system_id (int): The managed system ID.

        Returns:
            None
        """

        attributes = {
            "managed_system_id": managed_system_id,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/managedsystems/{managed_system_id}{self.endpoint}/lock"

        utils.print_log(
            self._logger,
            "Calling post_session_lock_managed_system_id endpoint",
            logging.DEBUG,
        )

        self._run_post_request(
            endpoint, payload={}, include_api_version=False, expected_status_code=204
        )

        utils.print_log(
            self._logger,
            f"Session with managed system ID {managed_system_id} locked successfully.",
            logging.INFO,
        )
