"""Oracle Internet Directories module, logic to manage Oracle Internet Directories
from PS API"""

import logging

from secrets_safe_library import utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import GetByIdMixin, ListMixin


class OracleInternetDirectories(APIObject, GetByIdMixin, ListMixin):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/oracleinternetdirectories")

    def query_services(self, oid_id: str) -> dict:
        """
        Queries and returns DB Services for an Oracle Internet Directory by ID (GUID).

        API: POST OracleInternetDirectories/{id}/Services/Query

        Args:
            oid_id (str): The Oracle Internet Directory GUID.

        Returns:
            dict: Response containing Success, Message, and Services fields.
                Success (bool): Whether the query was successful
                Message (str): Response message
                Services (list): List of services with Name field
        """
        endpoint = f"{self.endpoint}/{oid_id}/Services/Query"

        utils.print_log(
            self._logger, f"Calling query services endpoint: {endpoint}", logging.DEBUG
        )
        response = self._run_post_request(
            endpoint, {}, include_api_version=False, expected_status_code=200
        )

        return response.json()

    def test_connection(self, oid_id: str) -> dict:
        """
        Tests the connection to an Oracle Internet Directory by ID.

        API: POST OracleInternetDirectories/{id}/Test

        Args:
            oid_id (str): The Oracle Internet Directory ID.

        Returns:
            dict: Response containing Success field.
                Success (bool): Whether the connection test was successful
        """
        endpoint = f"{self.endpoint}/{oid_id}/Test"

        utils.print_log(
            self._logger, f"Calling test connection endpoint: {endpoint}", logging.DEBUG
        )
        response = self._run_post_request(
            endpoint, {}, include_api_version=False, expected_status_code=200
        )

        return response.json()

    def list_by_organization(self, organization_id: str) -> list:
        """
        Gets Oracle Internet Directories for a given Organization ID.

        API: GET Organizations/{id}/OracleInternetDirectories

        Args:
            organization_id (str): The Organization GUID.

        Returns:
            list: Response containing Oracle Internet Directories.
        """
        endpoint = f"/organizations/{organization_id}/oracleinternetdirectories"

        utils.print_log(
            self._logger,
            f"Calling get by organization ID endpoint: {endpoint}",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()
