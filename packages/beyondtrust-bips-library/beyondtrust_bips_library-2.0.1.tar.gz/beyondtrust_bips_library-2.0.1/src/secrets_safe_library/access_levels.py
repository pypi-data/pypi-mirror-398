"""Access levels module, all the logic to manage Access levels from BeyondInsight API"""

import logging

from secrets_safe_library import utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject


class AccessLevels(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/accesslevels")

    def get_access_levels(self) -> list:
        """
        Returns all access levels.

        API: GET AccessLevels

        Returns:
            list: List of access levels.
        """
        utils.print_log(
            self._logger,
            "Calling get_access_levels endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(self.endpoint, include_api_version=False)

        return response.json()

    def post_access_levels_usergroupid_smartruleid(
        self, usergroupid: int, smartruleid: int, accesslevelid: int
    ) -> None:
        """
        Assigns an access level to a user group and smart rule.

        API: POST UserGroups/{usergroupid}/SmartRules/{smartruleid}/AccessLevels

        Args:
            usergroupid (int): The user group ID.
            smartruleid (int): The smart rule ID.
            accesslevelid (int): The access level ID.

        Returns:
            dict: Response from the API.
        """

        endpoint = f"/usergroups/{usergroupid}/smartrules/{smartruleid}/accesslevels"

        payload = {"AccessLevelID": accesslevelid}

        utils.print_log(
            self._logger,
            "Calling post_access_levels_usergroupid_smartruleid endpoint",
            logging.DEBUG,
        )

        self._run_post_request(
            endpoint,
            payload,
            include_api_version=False,
            expected_status_code=200,
        )
