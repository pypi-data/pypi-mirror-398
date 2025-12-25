"""Entitlements module, all the logic to manage entitlements from BeyondInsight API"""

import logging

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject


class Entitlement(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger)

    def list_entitlements(self, group_ids: list = None) -> list:
        """
        Returns user entitlements.
        Optionally filter by group IDs.

        API: GET Entitlements

        Args:
            group_ids (list, optional): List of group IDs to filter entitlements.
                If provided, only entitlements for these groups will be returned.

        Returns:
            list: List of user entitlements.
        """

        endpoint = "/entitlements"

        if group_ids:
            if not isinstance(group_ids, list):
                raise exceptions.OptionsError("group_ids must be a list.")
            group_ids_str = ",".join(map(str, group_ids))
            endpoint += f"?groupIds={group_ids_str}"

        utils.print_log(
            self._logger,
            "Calling list_entitlements endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint)

        return response.json()
