"""
Mixin classes for Secrets Safe Library.
Optional classes to extend APIObject functionality.

These mixins need to be used with APIObject class.
"""

import logging

from secrets_safe_library import utils


class ListMixin:
    """
    Mixin class to add list functionality.
    """

    def list(self) -> list:
        """
        Generic listing function.

        Returns:
            list: List of elements for defined endpoint.
        """

        utils.print_log(
            self._logger, f"Calling list endpoint: {self.endpoint}", logging.DEBUG
        )
        response = self._run_get_request(self.endpoint)

        return response.json()


class GetByIdMixin:
    """
    Mixin class to add get by ID functionality.
    """

    def get_by_id(self, object_id: str | int, include_api_version=False) -> dict:
        """
        Generic method to get an object by ID.

        Args:
            object_id (str | int): The ID of the object to retrieve.
            include_api_version (bool, optional): Whether to include the API version
                in the request. Defaults to False.

        Returns:
            dict: The object retrieved by ID.
        """
        endpoint = f"{self.endpoint}/{object_id}"

        utils.print_log(self._logger, "Calling get_by_id endpoint", logging.DEBUG)
        response = self._run_get_request(
            endpoint, include_api_version=include_api_version
        )

        return response.json()


class ListByKeyMixin:
    """
    Mixin class to add list/retrieve by key functionality.
    """

    def list_by_key(self, key: str, value: str) -> list | dict:
        """
        Generic method to list objects by a specific key and value.

        Args:
            key (str): The key to filter by.
            value (str): The value to filter by.

        Returns:
            list | dict: List of objects or object matching the key-value pair query
                string.
        """
        endpoint = f"{self.endpoint}?{key}={value}"

        utils.print_log(self._logger, "Calling list_by_key endpoint", logging.DEBUG)
        response = self._run_get_request(endpoint)

        return response.json()


class DeleteByIdMixin:
    """
    Mixin class to add delete by ID functionality.
    """

    def delete_by_id(
        self, object_id: str | int, expected_status_code: int = 204
    ) -> None:
        """
        Generic method to delete an object by ID.

        Args:
            object_id (str | int): The ID of the object to delete.
            expected_status_code (int, optional): The expected status code for a
                successful deletion. Defaults to 204.

        Raises:
            exceptions.DeletionError: If the deletion fails.
        """
        endpoint = f"{self.endpoint}/{object_id}"

        utils.print_log(self._logger, "Calling delete_by_id endpoint", logging.DEBUG)
        self._run_delete_request(endpoint, expected_status_code=expected_status_code)


class DeleteByKeyMixin:
    """
    Mixin class to add delete by query parameter functionality.
    i.e.: DELETE QuickRules?title={title}, where key is "title" and value is the value
    to delete.
    """

    def delete_by_key(
        self, key: str, value: str, expected_status_code: int = 204
    ) -> None:
        """
        Generic method to delete objects by a specific key and value.

        Args:
            key (str): The key to delete by.
            value (str): The value to delete by.
            expected_status_code (int, optional): The expected status code for a
                successful deletion. Defaults to 204.

        Returns:
            None.
        """
        endpoint = f"{self.endpoint}?{key}={value}"

        utils.print_log(self._logger, "Calling delete_by_key endpoint", logging.DEBUG)
        _ = self._run_delete_request(
            endpoint, expected_status_code=expected_status_code
        )
