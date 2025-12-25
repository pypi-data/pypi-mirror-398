import json
import logging
import os
from abc import ABC, abstractmethod
from typing import List
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication


class APIObjectInterface(ABC):
    @abstractmethod
    def _run_get_request(
        self, endpoint: str, include_api_version: bool, expected_status_code: int
    ) -> requests.Response:
        pass

    @abstractmethod
    def _run_post_request(
        self,
        endpoint: str,
        payload: dict,
        include_api_version: bool,
        expected_status_code: int,
    ) -> requests.Response:
        pass

    @abstractmethod
    def _run_post_file_request(
        self,
        endpoint: str,
        payload: dict,
        include_api_version: bool,
        expected_status_code: int,
        file_path: str = None,
    ) -> requests.Response:
        pass

    @abstractmethod
    def _run_put_request(
        self,
        endpoint: str,
        payload: dict,
        include_api_version: bool,
        expected_status_code: int,
    ) -> requests.Response:
        pass

    @abstractmethod
    def _run_put_file_request(
        self,
        endpoint: str,
        payload: dict,
        include_api_version: bool,
        expected_status_code: int,
        file_path: str = None,
    ) -> requests.Response:
        pass

    @abstractmethod
    def _run_delete_request(
        self, endpoint: str, expected_status_code: int
    ) -> requests.Response:
        pass

    @abstractmethod
    def make_query_string(self, params: dict) -> str:
        pass


class APIObject(APIObjectInterface):
    _authentication: Authentication
    _logger: logging.Logger
    endpoint: str

    def __init__(
        self,
        authentication: Authentication,
        logger: logging.Logger = None,
        endpoint: str = None,
    ):
        self._authentication = authentication
        self._logger = logger
        self.endpoint = endpoint

    def __is_successful_response(
        self, status_code: int, expected_status_code: int | List[int]
    ) -> bool:
        """
        Checks if the given status code matches the expected status code(s).

        Args:
            status_code (int): The actual status code to validate.
            expected_status_code (int | List[int]): The expected status code or a list
                of acceptable status codes.

        Returns:
            bool: True if the status code matches the expected value(s), False
            otherwise.
        """
        return (
            status_code == expected_status_code
            if isinstance(expected_status_code, int)
            else status_code in expected_status_code
        )

    def _get_headers(self) -> dict:
        """
        Get headers for requests.
        """
        if self._authentication._api_token:
            return {"Authorization": f"Bearer {self._authentication._api_token}"}
        elif self._authentication._api_key:
            return {"Authorization": f"PS-Auth key={self._authentication._api_key}"}
        return {}

    def _run_get_request(
        self,
        endpoint: str,
        include_api_version: bool = True,
        expected_status_code: int | List[int] = 200,
    ) -> requests.Response:
        """
        Shortcut function to make a GET request to the specified endpoint using
        Authentication object.

        Args:
            endpoint (str): The endpoint to call using GET HTTP verb.
            include_api_version (bool): Whether to include API version in request URL.
            expected_status_code (int | List[int], optional): Expected status code to
                consider the request was successful.

        Returns:
            request.Response: Response object.

        Raises:
            exceptions.LookupError: When get request fails.
        """
        url = self._create_url(endpoint, include_api_version)

        utils.print_log(self._logger, "GET request to URL", logging.DEBUG)

        response = self._authentication._req.get(
            url,
            headers=self._get_headers(),
            timeout=(
                self._authentication._timeout_connection_seconds,
                self._authentication._timeout_request_seconds,
            ),
        )

        if not self.__is_successful_response(
            response.status_code, expected_status_code
        ):
            if not self._authentication.sign_app_out():
                utils.print_log(
                    self._logger, "Error running get request", logging.ERROR
                )
            raise exceptions.LookupError(
                f"Error running get request, message: {response.text}, statuscode: "
                f"{response.status_code}"
            )

        return response

    def _run_post_request(
        self,
        endpoint: str,
        payload: dict,
        include_api_version: bool = True,
        expected_status_code: int | List[int] = 201,
    ) -> requests.Response:
        """
        Shortcut function to make a POST request to the specified endpoint using
        Authentication object.

        Args:
            endpoint (str): The endpoint to call using POST HTTP verb.
            payload (dict): Payload to send with the POST request.
            include_api_version (bool): Whether to include API version in request URL.
            expected_status_code (int | List[int], optional): Expected status code to
                consider the request was successful.

        Returns:
            request.Response: Response object.

        Raises:
            exceptions.CreationError: Raised when creation failed, because response
                status code is different to expected_status_code.
        """
        url = self._create_url(endpoint, include_api_version)

        utils.print_log(self._logger, "Calling URL", logging.DEBUG)

        response = self._authentication._req.post(
            url=url,
            json=payload,
            headers=self._get_headers(),
            timeout=(
                self._authentication._timeout_connection_seconds,
                self._authentication._timeout_request_seconds,
            ),
        )

        if not self.__is_successful_response(
            response.status_code, expected_status_code
        ):
            if not self._authentication.sign_app_out():
                utils.print_log(self._logger, "Error in post request", logging.ERROR)
            raise exceptions.CreationError(
                f"Error running post request, message: {response.text}, statuscode: "
                f"{response.status_code}"
            )

        return response

    def _run_post_file_request(
        self,
        endpoint: str,
        payload: dict,
        include_api_version: bool = True,
        expected_status_code: int | List[int] = 201,
        file_path: str = None,
    ) -> requests.Response:
        """
        Shortcut function to make a POST request to the specified endpoint, including
        a file and using Authentication object.

        Args:
            endpoint (str): The endpoint to call using POST HTTP verb.
            payload (dict): Payload to send with the POST request as secretmetadata.
            include_api_version (bool): Whether to include API version in request URL.
            expected_status_code (int | List[int], optional): Expected status code to
                consider the request was successful.
            file_path (str, optional): The path to the file to be uploaded. If not
                provided, no file will be uploaded. The FileName key is automatically
                included in request body using file_path.

        Returns:
            request.Response: Response object.

        Raises:
            exceptions.CreationError: Raised when creation failed, because response
                status code is different to expected_status_code.
            FileNotFoundError: If the provided file_path does not point to an existing
                file.
            requests.exceptions.RequestException: If there is an error during the file
                upload.
        """
        url = self._create_url(endpoint, include_api_version)

        utils.print_log(self._logger, "Calling URL", logging.DEBUG)

        with open(file_path, "rb") as file:
            file_name = os.path.basename(file_path)
            payload["FileName"] = file_name

            files = {
                # The None value is used as the filename, since it's not a file upload:
                "secretmetadata": (None, json.dumps(payload), "application/json"),
                "files": (file_name, file, "application/octet-stream"),
            }

            response = self._authentication._req.post(
                url=url,
                headers=self._get_headers(),
                files=files,
                timeout=(
                    self._authentication._timeout_connection_seconds,
                    self._authentication._timeout_request_seconds,
                ),
            )

            if not self.__is_successful_response(
                response.status_code, expected_status_code
            ):
                if not self._authentication.sign_app_out():
                    utils.print_log(
                        self._logger, "Error in post file request", logging.ERROR
                    )
                raise exceptions.CreationError(
                    f"Error running post file request, message: {response.text}"
                    f", statuscode: {response.status_code}"
                )

            return response

    def _run_delete_request(
        self,
        endpoint: str,
        expected_status_code: int | List[int] = 200,
    ) -> None:
        """
        Shortcut function to make a DELETE request to the specified endpoint using
        Authentication object.

        Args:
            endpoint (str): The endpoint to call using DELETE HTTP verb.
            include_api_version (bool): Whether to include API version in request URL.
            expected_status_code (int | List[int], optional): Expected status code to
                consider the request was successful.

        Returns:
            request.Response: Response object.

        Raises:
            exceptions.DeletionError: When delete request fails.
        """
        url = self._create_url(endpoint, include_api_version=False)

        utils.print_log(self._logger, "DELETE request to URL", logging.DEBUG)

        response = self._authentication._req.delete(
            url,
            headers=self._get_headers(),
            timeout=(
                self._authentication._timeout_connection_seconds,
                self._authentication._timeout_request_seconds,
            ),
        )

        if not self.__is_successful_response(
            response.status_code, expected_status_code
        ):
            if not self._authentication.sign_app_out():
                utils.print_log(
                    self._logger, "Error running delete request", logging.ERROR
                )
            raise exceptions.DeletionError(
                f"Error running delete request, message: {response.text}, statuscode: "
                f"{response.status_code}"
            )

    def _run_put_request(
        self,
        endpoint: str,
        payload: dict,
        include_api_version: bool = True,
        expected_status_code: int | List[int] = 200,
    ) -> requests.Response:
        """
        Shortcut function to make a PUT request to the specified endpoint using
        Authentication object.

        Args:
            endpoint (str): The endpoint to call using PUT HTTP verb.
            payload (dict): Payload to send with the PUT request.
            include_api_version (bool): Whether to include API version in request URL.
            expected_status_code (int | List[int], optional): Expected status code to
                consider the request was successful.

        Returns:
            request.Response: Response object.

        Raises:
            exceptions.UpdateError: Raised when update failed, because response
                status code is different to expected_status_code.
        """
        url = self._create_url(endpoint, include_api_version)

        utils.print_log(self._logger, "Calling URL", logging.DEBUG)

        response = self._authentication._req.put(
            url=url,
            headers=self._get_headers(),
            json=payload,
            timeout=(
                self._authentication._timeout_connection_seconds,
                self._authentication._timeout_request_seconds,
            ),
        )

        if not self.__is_successful_response(
            response.status_code, expected_status_code
        ):
            if not self._authentication.sign_app_out():
                utils.print_log(self._logger, "Error in put request", logging.ERROR)
            raise exceptions.UpdateError(
                f"Error running put request, message: {response.text}, statuscode: "
                f"{response.status_code}"
            )

        return response

    def _run_put_file_request(
        self,
        endpoint: str,
        payload: dict,
        include_api_version: bool = True,
        expected_status_code: int | List[int] = 204,
        file_path: str = None,
    ) -> requests.Response:
        """
        Shortcut function to make a PUT request to the specified endpoint, including
        a file and using Authentication object.

        Args:
            endpoint (str): The endpoint to call using PUT HTTP verb.
            payload (dict): Payload to send with the PUT request as secretmetadata.
            include_api_version (bool): Whether to include API version in request URL.
            expected_status_code (int | List[int], optional): Expected status code to
                consider the request was successful.
            file_path (str, optional): The path to the file to be uploaded. If not
                provided, no file will be uploaded. The FileName key is automatically
                included in request body using file_path.

        Returns:
            request.Response: Response object.

        Raises:
            exceptions.UpdateError: Raised when update failed, because response
                status code is different to expected_status_code.
            FileNotFoundError: If the provided file_path does not point to an existing
                file.
            requests.exceptions.RequestException: If there is an error during the file
                upload.
        """
        url = self._create_url(endpoint, include_api_version)

        utils.print_log(self._logger, "Calling URL", logging.DEBUG)

        with open(file_path, "rb") as file:
            file_name = os.path.basename(file_path)
            payload["FileName"] = file_name

            files = {
                # The None value is used as the filename, since it's not a file upload:
                "secretmetadata": (None, json.dumps(payload), "application/json"),
                "files": (file_name, file, "application/octet-stream"),
            }

            response = self._authentication._req.put(
                url=url,
                headers=self._get_headers(),
                files=files,
                timeout=(
                    self._authentication._timeout_connection_seconds,
                    self._authentication._timeout_request_seconds,
                ),
            )

            if not self.__is_successful_response(
                response.status_code, expected_status_code
            ):
                if not self._authentication.sign_app_out():
                    utils.print_log(
                        self._logger, "Error in put file request", logging.ERROR
                    )
                raise exceptions.UpdateError(
                    f"Error running put file request, message: {response.text}"
                    f", statuscode: {response.status_code}"
                )

            return response

    def _create_url(self, endpoint: str, include_api_version: bool = True) -> str:
        """
        Constructs a complete URL by appending the specified endpoint to the base API
        URL.
        Optionally includes the API version as a query parameter.

        Args:
            endpoint (str): The endpoint to be appended to the base API URL. This should
                start with a '/'.
            include_api_version (bool): Flag to determine whether to include the API
                version in the URL. Defaults to True. If True and the API version is
                specified in the authentication object, it will be included as a query
                parameter.

        Returns:
            str: The fully constructed URL.

        Example:
            If the base API URL is "http://api.example.com", the endpoint is "/data",
            and the API version is "v1", then the resulting URL will be
            "http://api.example.com/data?version=v1" if  include_api_version is True.
            If include_api_version is False, the resulting URL will be
            "http://api.example.com/data".
        """
        url = f"{self._authentication._api_url}{endpoint}"

        if self._authentication._api_version and include_api_version:
            params = {"version": self._authentication._api_version}
            url = self.add_api_version(url=url, new_params=params)
        return url

    def add_api_version(self, url: str, new_params: dict) -> str:
        """
        Appends or updates query parameters in the given URL.

        This function parses the provided URL, updates its query parameters with the new
        parameters provided, and reconstructs the URL.

        Args:
            url (str): The original URL to which parameters will be added or updated.
            new_params (dict): A dictionary of parameters to add or update in the URL.
                The dictionary should have parameter names as keys and parameter values
                as values.

        Returns:
            str: The new URL with updated query parameters.

        Example:
            Given the URL "http://example.com/data?filter=old" and new_params
            {"version": "v1", "filter": "new"}, the function returns
            "http://example.com/data?filter=new&version=v1".
        """
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        query_params.update(new_params)

        query_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
        query = urlencode(query_params, doseq=True)
        new_url = urlunparse(parsed_url._replace(query=query))
        return new_url

    def make_query_string(self, params: dict) -> str:
        """
        Constructs a query string from a dictionary of parameters, excluding any
        parameters with a value of None.

        This function filters out any key-value pairs in the input dictionary where the
        value is None, and then encodes the remaining parameters into a URL-encoded
        query string.

        Args:
            params (dict): A dictionary containing the parameters to be included in the
                query string. Keys are parameter names, and values are parameter values.
                Parameters with None values are excluded from the resulting query
                string.

        Returns:
            str: A URL-encoded query string constructed from the provided parameters. If
                all parameters are None, returns an empty string.

        Example:
            Given params = {"name": "John", "age": 30, "city": None}, the function
            returns "name=John&age=30".
        """
        query_params = {k: v for k, v in params.items() if v is not None}
        query_string = urlencode(query_params)
        return query_string

    def get_request_body_version(self, body: dict, endpoint: dict, version: str = None):
        if version is not None and not isinstance(version, str):
            raise exceptions.OptionsError("version must be a string or None")
        selected_version = version or self._authentication._api_version
        requests_body = body.get(endpoint, {}).get(selected_version)
        return requests_body

    def generate_request_body(self, dict_structure: dict, **kwargs) -> dict:
        """
        Transforms keyword arguments into a structured dictionary based on a given
        schema.

        This function maps keys from kwargs to a predefined dictionary structure,
        converting keys to CamelCase and filtering out any keys with None values. It
        handles nested lists of dictionaries by ensuring only specified sub-keys are
        included.

        Args:
            dict_structure (dict): A dictionary defining the desired structure and
                types of the output dictionary. The keys should be in CamelCase and the
                values should indicate the expected type, which could be a simple type
                (like str or int) or a list of dictionaries specifying sub-structure.
            **kwargs: Arbitrary keyword arguments that represent the data to be
                transformed according to `dict_structure`. Keys should be in snake_case
                or similar formats and will be converted to CamelCase.

        Returns:
            dict: A dictionary containing the structured data extracted and transformed
                from kwargs based on `dict_structure`. Only keys that exist in the
                `dict_structure` and have non-None values in `kwargs` are included.

        Example:
            >>> dict_structure = {
            >>>     'Title': str,
            >>>     'Description': str,
            >>>     'Username': str,
            >>>     'Password': str,
            >>>     'OwnerType': str,
            >>>     'Owners': [{'OwnerId': int, 'Owner': str, 'Email': str}]
            >>> }
            >>> kwargs = {
            >>>     'title': 'Example',
            >>>     'description': 'An example',
            >>>     'username': 'user1',
            >>>     'password': 'pass',
            >>>     'owner_type': 'User',
            >>>     'owners': [{'owner_id': 1, 'owner': 'Owner1'}]
            >>> }
            >>> output = generate_request_body(dict_structure, **kwargs)
            >>> print(output)
            >>> # Output: {
            >>> #     'Title': 'Example',
            >>> #     'Description': 'An example',
            >>> #     'Username': 'user1',
            >>> #     'Password': 'pass',
            >>> #     'OwnerType': 'User',
            >>> #     'Owners': [{'OwnerId': 1, 'Owner': 'Owner1'}]
            >>> # }
        """

        def simplify_key(key):
            """Converts a key to lowercase and removes underscores."""
            return key.replace("_", "").lower()

        def build_key_map(structure):
            """Builds a mapping of simplified keys to original keys."""
            return {simplify_key(key): key for key in structure.keys()}

        def transform_nested_list(nested_structure, nested_list):
            """Transforms a list of nested dictionaries."""
            simplified_nested_structure = {
                simplify_key(k): k for k in nested_structure[0].keys()
            }
            return [
                {
                    simplified_nested_structure[simplify_key(k)]: v
                    for k, v in item.items()
                    if simplify_key(k) in simplified_nested_structure
                }
                for item in nested_list
            ]

        def transform_value(value, value_type):
            """Transforms a value based on its type in the structure."""
            if isinstance(value_type, list) and isinstance(value, list):
                # Handle nested lists of dictionaries
                return transform_nested_list(value_type, value)
            return value

        # Build the key map for the top-level structure
        key_map = build_key_map(dict_structure)

        # Transform the kwargs into the output structure
        output = {}
        for kwarg_key, kwarg_value in kwargs.items():
            if kwarg_value is None:
                continue

            simplified_key = simplify_key(kwarg_key)

            if simplified_key in key_map:
                original_key = key_map[simplified_key]
                value_type = dict_structure[original_key]
                output[original_key] = transform_value(kwarg_value, value_type)

        return output
