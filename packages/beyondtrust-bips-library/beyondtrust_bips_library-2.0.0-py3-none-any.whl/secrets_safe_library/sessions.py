"""Sessions Module, all the logic to retrieve sessions from PS API"""

import logging

from cerberus import Validator

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import POST_SESSIONS_ADMIN
from secrets_safe_library.constants.versions import Version
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.sessions import fields as sessions_fields
from secrets_safe_library.mixins import GetByIdMixin


class Session(APIObject, GetByIdMixin):
    """
    Class to interact with sessions in PS API.
    """

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/sessions")

        # Schema rules used for validations
        self._schema = {
            "session_type": {"type": "string", "maxlength": 32, "nullable": True},
            "node_id": {"type": "integer", "nullable": True},
            "request_id": {"type": "integer", "nullable": True},
            "host_name": {"type": "string", "maxlength": 128, "nullable": True},
            "domain_name": {"type": "string", "maxlength": 50, "nullable": True},
            "user_name": {"type": "string", "maxlength": 200, "nullable": True},
        }
        self._validator = Validator(self._schema)

    def get_sessions(self, status: int = None, user_id: int = None) -> list:
        """
        Returns a list of sessions.

        API: GET Sessions

        Args:
            status (int, optional): A single value or comma-delimited list of values:
                - 0: Not Started
                - 1: In Progress
                - 2: Completed
                - 5: Locked
                - 7: Terminated (deprecated)
                - 8: Logged Off
                - 9: Disconnected (RDP only)
            user_id (int, optional): ID of the user that requested the session.

        Returns:
            list: List of sessions.
        """
        params = {"status": status, "userID": user_id}
        query_string = self.make_query_string(params)
        endpoint = f"{self.endpoint}?{query_string}"

        utils.print_log(
            self._logger,
            "Calling get_sessions endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def post_sessions_request_id(
        self, request_id: int, session_type: str, node_id: int = None
    ) -> dict:
        """
        Posts a session request by ID.

        API: POST Sessions RequestID

        Args:
            request_id (int): The ID of the session request.
            session_type (str): The type of session to create.
                Options: SSH or sshticket, RDP or rdpticket, rdpfile, app, or appfile.
            node_id (int, optional):  ID of the node that should be used to establish
                    the session. If NodeID is not given or if the Remote Session Proxy
                    feature is disabled, uses the local node.

        Returns:
            dict: The response from the API.
        """

        attributes = {
            "request_id": request_id,
            "session_type": session_type,
            "node_id": node_id,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        payload = {
            "SessionType": session_type,
            "NodeID": node_id,
        }

        endpoint = f"/requests/{request_id}/sessions"
        utils.print_log(
            self._logger,
            "Calling post_sessions_request_id endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, payload, include_api_version=False)

        return response.json()

    def post_sessions_admin(
        self,
        session_type: str,
        host_name: str,
        user_name: str,
        password: str,
        port: int = None,
        domain_name: str = None,
        reason: str = None,
        resolution: str = None,
        rdp_admin_switch: bool = None,
        smart_sizing: bool = None,
        node_id: int = None,
        record: bool = None,
    ) -> dict:
        """
        Posts a session request as an admin.

        API: POST Sessions Admin

        Args:
            session_type (str): The type of session to create.
                Options: SSH or sshticket, RDP or rdpticket, rdpfile, app, or appfile.
            host_name (str): The hostname or IP address of the target system.
            user_name (str): The username for the session.
            port (int, optional): The port number for the session. Defaults to None.
            domain_name (str, optional): The domain name for session. Defaults to None.
            password (str): The password for the session.
            reason (str, optional): Reason for the session request. Defaults to None.
            resolution (str, optional): Resolution for the session. Defaults to None.
            rdp_admin_switch (bool, optional): Whether to use RDP admin switch.
                                               Defaults None.
            smart_sizing (bool, optional): Whether to enable smart sizing.
                                            Defaults None.
            node_id (int, optional): ID of the node that should be used to establish
                    the session. If NodeID is not given or if the Remote Session Proxy
                    feature is disabled, uses the local node.
            record (bool, optional): Whether to record the session. Defaults to None.

        Returns:
            dict: The response from the API.
        """

        attributes = {
            "session_type": session_type,
            "node_id": node_id,
            "host_name": host_name,
            "domain_name": domain_name,
            "user_name": user_name,
        }

        if not self._validator.validate(attributes, update=True):
            raise exceptions.OptionsError(f"Please check: {self._validator.errors}")

        req_structure = self.get_request_body_version(
            sessions_fields, POST_SESSIONS_ADMIN, Version.DEFAULT.value
        )

        req_body = self.generate_request_body(
            req_structure,
            session_type=session_type,
            host_name=host_name,
            domain_name=domain_name,
            user_name=user_name,
            password=password,
            port=port,
            reason=reason,
            resolution=resolution,
            rdp_admin_switch=rdp_admin_switch,
            smart_sizing=smart_sizing,
            node_id=node_id,
            record=record,
        )

        endpoint = "/sessions/admin"
        utils.print_log(
            self._logger,
            "Calling post_sessions_admin endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, req_body, include_api_version=False)

        return response.json()
