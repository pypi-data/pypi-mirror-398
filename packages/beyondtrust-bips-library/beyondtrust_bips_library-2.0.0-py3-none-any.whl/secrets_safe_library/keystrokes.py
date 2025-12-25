"""Keystrokes module, all the logic to manage Keystrokes from PS API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import POST_KEYSTROKES_SEARCH
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.keystrokes import fields as keystrokes_fields
from secrets_safe_library.mixins import GetByIdMixin


class Keystroke(APIObject, GetByIdMixin):
    """Class to interact with Keystrokes in PS API."""

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/keystrokes")

        # Schema rules used for validations
        self._schema = {
            "session_id": {"type": "integer", "nullable": True},
            "data": {"type": "string", "nullable": False},
            "type": {
                "type": "integer",
                "min": 0,
                "max": 5,
                "default": 0,
                "nullable": True,
            },
        }
        self._validator = Validator(self._schema)

    def get_keystrokes_by_session_id(self, session_id: int) -> list:
        """
        Returns a list of keystrokes for the given session ID.

        API: GET Sessions/{sessionId:int}/Keystrokes

        Args:
            session_id (int): The Session ID.

        Returns:
            list: List of keystrokes for the specified session_id.
        """

        attributes = {"session_id": session_id}

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        endpoint = f"/sessions/{session_id}/keystrokes"

        utils.print_log(
            self._logger,
            "Calling get_keystrokes_by_session_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint)

        return response.json()

    def search_keystrokes(self, data: str, type: int = 0) -> list:
        """
        Searches for keystrokes based on data and type criteria.

        API: POST Keystrokes/Search

        Args:
            data (str): Keyword(s) for which to search.
            type (int, optional): Type of keystrokes:
                0: All (default)
                1: StdIn
                2: StdOut
                4: Window Event
                5: User Event

        Returns:
            list: List of keystrokes matching the search criteria.
        """

        attributes = {
            "data": data,
            "type": type,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            keystrokes_fields, POST_KEYSTROKES_SEARCH, Version.DEFAULT.value
        )
        req_body = self.generate_request_body(req_structure, **attributes)

        endpoint = f"{self.endpoint}/search"

        utils.print_log(
            self._logger, "Calling search keystrokes endpoint", logging.DEBUG
        )
        response = self._run_post_request(
            endpoint,
            payload=req_body,
            include_api_version=False,
            expected_status_code=200,
        )

        return response.json()
