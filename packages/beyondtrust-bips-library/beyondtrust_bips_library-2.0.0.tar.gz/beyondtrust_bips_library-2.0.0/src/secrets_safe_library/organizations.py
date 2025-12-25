"""Organizations module, all the logic to manage organizations from BeyondInsight API"""

import logging

from secrets_safe_library import utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject


class Organization(APIObject):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/organizations")

    def get_organization_by_id(self, organization_id: str) -> dict:
        """
        Find an organization by ID.

        API: GET Organizations/{id}

        Args:
            organization_id (str): The organization ID (GUID).

        Returns:
            dict: Organization object.
        """

        endpoint = f"{self.endpoint}/{organization_id}"

        utils.print_log(
            self._logger,
            "Calling get_organization_by_id endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def list_organizations(self) -> list:
        """
        Returns a list of organizations to which the current user has permission.

        API: GET Organizations

        Returns:
            list: List of organizations.
        """

        utils.print_log(
            self._logger,
            "Calling list_organizations endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(self.endpoint, include_api_version=False)

        return response.json()

    def get_organization_by_name(self, organization_name: str) -> dict:
        """
        Returns an Organization by name.

        API: GET Organizations?name={name}

        Args:
            organization_name (str): Name of the organization.

        Returns:
            dict: Organization.
        """

        endpoint = f"{self.endpoint}?name={organization_name}"

        utils.print_log(
            self._logger,
            "Calling get_organization_by_name endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()
