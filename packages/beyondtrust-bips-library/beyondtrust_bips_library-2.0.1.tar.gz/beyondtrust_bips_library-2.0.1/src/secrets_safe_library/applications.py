"""Applications module, all the logic to manage applications from PS API"""

import logging

from secrets_safe_library import utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import GetByIdMixin, ListMixin


class Application(APIObject, GetByIdMixin, ListMixin):
    """
    Application class for managing applications via Password Safe API.

    This class provides functionality to:
    - Get a list of applications
      (requires Password Safe Account Management (Read) permission)
    - Get an application by ID
      (requires Password Safe Account Management (Read) permission)
    """

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/applications")

    def get_managed_account_apps(self, account_id: int) -> list:
        """
        Returns a list of applications assigned to a managed account.

        Args:
            account_id (int): ID of the managed account.

        Returns:
            list: List of applications assigned to the managed account.
        """
        endpoint = f"/managedaccounts/{account_id}/applications"

        utils.print_log(
            self._logger,
            "Calling get_managed_account_apps endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint, include_api_version=False)

        return response.json()

    def assign_app_to_managed_account(
        self, account_id: int, application_id: int
    ) -> dict:
        """
        Assigns an application to a managed account.

        Args:
            account_id (int): ID of the managed account.
            application_id (int): ID of the application.

        Returns:
            dict: Response from the API.
        """
        endpoint = f"/managedaccounts/{account_id}/applications/{application_id}"

        utils.print_log(
            self._logger,
            "Calling assign_app_to_managed_account endpoint",
            logging.DEBUG,
        )
        response = self._run_post_request(endpoint, {}, include_api_version=False)

        return response.json()

    def remove_app_from_managed_account(
        self, account_id: int, application_id: int
    ) -> None:
        """
        Removes an application from a managed account.

        Args:
            account_id (int): ID of the managed account.
            application_id (int): ID of the application.

        Returns:
            None
        """
        endpoint = f"/managedaccounts/{account_id}/applications/{application_id}"

        utils.print_log(
            self._logger,
            "Calling remove_app_from_managed_account endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint, expected_status_code=200)

    def unassign_all_apps_from_managed_account(self, account_id: int) -> None:
        """
        Unassigns all applications from a managed account.

        Args:
            account_id (int): ID of the managed account.

        Returns:
            None
        """
        endpoint = f"/managedaccounts/{account_id}/applications"

        utils.print_log(
            self._logger,
            "Calling unassign_all_apps_from_managed_account endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint, expected_status_code=200)
