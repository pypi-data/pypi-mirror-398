"""Replay module, all the logic to manage replay sessions from PS API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import DeleteByIdMixin, GetByIdMixin


class Replay(APIObject, GetByIdMixin, DeleteByIdMixin):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/pbsm/replay")

        # Schema rules used for validations
        self._schema = {
            "id": {"type": "string", "nullable": False, "empty": False},
            "record_key": {"type": "string", "nullable": False, "empty": False},
            "protocol": {"type": "string", "nullable": False, "empty": False},
            "headless": {"type": "boolean", "nullable": False},
            "speed": {"type": "integer", "nullable": True, "min": 1},
            "offset": {"type": "integer", "nullable": True, "min": 0},
            "next": {"type": "integer", "nullable": True, "min": 0},
        }
        self._validator = Validator(self._schema)

    def create_replay_session(
        self,
        session_id: str,
        record_key: str,
        protocol: str,
        headless: bool = True,
    ) -> dict:
        """
        Creates a new replay session for a specified session token.

        API: POST pbsm/replay

        Args:
            session_id (str): Session Token from query to <base>/Sessions endpoint.
            record_key (str): RecordKey from query to <base>/Sessions endpoint.
            protocol (str): When session Type is 0 this should be RDP or for type 1 SSH.
            headless (bool): Must be set to true. Defaults to True.

        Returns:
            dict: Response containing:
                - id (str): ReplayID for this replay session
                - token (str): ReplayID for this replay session
                - ticket (str): Ticket value used internally

        Raises:
            exceptions.OptionsError: If validation fails.
            exceptions.CreationError: If the request fails (403, 404, etc).
        """

        attributes = {
            "id": session_id,
            "record_key": record_key,
            "protocol": protocol,
            "headless": headless,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "id": session_id,
            "record_key": record_key,
            "protocol": protocol,
            "headless": headless,
        }

        utils.print_log(
            self._logger,
            f"Calling create replay session endpoint: {self.endpoint}",
            logging.DEBUG,
        )
        response = self._run_post_request(
            self.endpoint,
            payload,
            include_api_version=False,
            expected_status_code=[200],
        )

        return response.json()

    def get_replay_session(
        self,
        replay_id: str,
        jpeg_scale: str | None = None,
        png_scale: str | None = None,
        screen: bool | None = None,
    ) -> dict:
        """
        Displays the replay session details.

        API: GET pbsm/replay/{replayId}

        Args:
            replay_id (str): ID of the replay session returned from POST pbsm/replay.
            jpeg_scale (str, optional): Requests a JPEG image scaled by the given scale.
            png_scale (str, optional): Requests a PNG image scaled by the given scale.
            screen (bool, optional): If True, requests a text representation
                of the current SSH session.

        Returns:
            dict: Response containing:
                - tstamp (int): Start time of the session in seconds
                - end (int): End time of the session in seconds
                - offset (int): Current offset of replay session in ms
                - next (int): Offset of next activity of replay session in ms
                - speed (int): Speed of replay session as a %
                - eof (bool): Set to true when the end of the replay has been reached
                - duration (int): Duration in ms of the replay session

        Raises:
            exceptions.LookupError: If the request fails (403, 404, etc).
        """

        endpoint = f"{self.endpoint}/{replay_id}"

        # Build query parameters
        query_params = {}
        if jpeg_scale is not None:
            query_params["jpeg"] = jpeg_scale
        if png_scale is not None:
            query_params["png"] = png_scale
        if screen:
            query_params["screen"] = "1"

        if query_params:
            query_string = self.make_query_string(query_params)
            endpoint = f"{endpoint}?{query_string}"

        utils.print_log(
            self._logger,
            "Calling get replay session endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(
            endpoint, include_api_version=False, expected_status_code=[200]
        )

        return response.json()

    def control_replay_session(
        self,
        replay_id: str,
        speed: int | None = None,
        offset: int | None = None,
        next_frame: int | None = None,
    ) -> dict:
        """
        Controls the replay session status.

        API: PUT pbsm/replay/{replayId}

        Args:
            replay_id (str): ID of the replay session returned from POST pbsm/replay.
            speed (int, optional): Sets the replay speed of this session as a %.
            offset (int, optional): Sets the offset of the replay cursor
                for this session in ms.
            next_frame (int, optional): Requests the next changed frame
                based on the given % change.

        Returns:
            dict: Response containing:
                - tstamp (int): Start time of the session in seconds
                - end (int): End time of the session in seconds
                - offset (int): Current offset of replay session in ms
                - next (int): Offset of next activity of replay session in ms
                - speed (int): Speed of replay session as a %
                - eof (bool): Set to true when the end of the replay has been reached
                - duration (int): Duration in ms of the replay session

        Raises:
            exceptions.OptionsError: If validation fails.
            exceptions.UpdateError: If the request fails (403, 404, etc).
        """

        # Build attributes for validation
        attributes = {}
        if speed is not None:
            attributes["speed"] = speed
        if offset is not None:
            attributes["offset"] = offset
        if next_frame is not None:
            attributes["next"] = next_frame

        if attributes and not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        # Build payload
        payload = {}
        if speed is not None:
            payload["speed"] = speed
        if offset is not None:
            payload["offset"] = offset
        if next_frame is not None:
            payload["next"] = next_frame

        endpoint = f"{self.endpoint}/{replay_id}"

        utils.print_log(
            self._logger,
            "Calling control replay session endpoint",
            logging.DEBUG,
        )
        response = self._run_put_request(
            endpoint, payload, include_api_version=False, expected_status_code=[200]
        )

        return response.json()
