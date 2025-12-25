"""Auth Manager, Used to authenticate with the BeyondTrust PS API."""

# flake8: noqa: E402
# -*- coding: utf-8 -*-
# (c) 2025 BeyondTrust Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
try:
    from secrets_safe_library import authentication
except ImportError:
    pass


class AuthManager:
    """
    Auth Manager, Used to authenticate with the BeyondTrust PS API.
    """

    def __init__(self, session, params: dict, logger=None) -> None:
        """
        Initialize a new AuthManager instance.

        Args:
            session (Session): Request session to make API calls.
            params (dict):  Mapping with fields related to authentication.
            logger (str): Logger object
        """
        self.session = session
        self.params = params
        self.logger = logger

    def authenticate(self):
        """
        Authenticate with the BeyondTrust PS API.
        """

        auth_obj = authentication.Authentication(
            req=self.session,
            timeout_connection=30,
            timeout_request=30,
            api_url=self.params["api_url"],
            client_id=self.params["client_id"],
            client_secret=self.params["client_secret"],
            verify_ca=self.params.get("verify_ca", True),
            logger=self.logger,
            api_version=self.params["api_version"],
        )

        response = auth_obj.get_api_access()

        if response.status_code != 200:
            return None

        return auth_obj
