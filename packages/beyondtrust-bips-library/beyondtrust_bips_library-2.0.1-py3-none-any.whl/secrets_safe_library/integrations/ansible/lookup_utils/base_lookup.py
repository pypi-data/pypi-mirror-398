"""Plugin Base class"""

# flake8: noqa: E402
# -*- coding: utf-8 -*-
# (c) 2025 BeyondTrust Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import logging

from ansible.errors import AnsibleLookupError
from ansible.plugins.lookup import LookupBase

from secrets_safe_library.integrations.ansible.common_utils.logger import Logger


class BaseLookup(LookupBase):
    """
    Plugin Base class.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_data = {}
        self.log = None

    def validate_and_set_auth_parameters(self, params):
        """
        Validate required parameters and set them in the auth_data dictionary.
        Args:
            params (dict): Parameters to validate.
        """

        required_params = ["client_id", "client_secret", "api_url"]

        missing = [p for p in required_params if not params.get(p)]
        if missing:
            raise AnsibleLookupError(
                f"Missing required parameter(s): {', '.join(missing)}"
            )

        self.auth_data.update(
            {
                "client_id": params.get("client_id"),
                "client_secret": params.get("client_secret"),
                "api_url": params.get("api_url"),
                "api_version": params.get("api_version"),
                "verify_ca": params.get("verify_ca", True),
            }
        )

        self.log = Logger(
            getattr(logging, params.get("log_level", "DEBUG"), logging.DEBUG),
            params.get("log_file_name", "ansible-collection-lookups-logs"),
        )
