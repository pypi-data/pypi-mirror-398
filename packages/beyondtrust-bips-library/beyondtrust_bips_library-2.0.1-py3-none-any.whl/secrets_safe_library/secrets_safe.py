"""SecretsSafe Module, all the logic to retrieve secrets from PS API"""

import logging
from urllib.parse import urlencode

import requests

from secrets_safe_library import exceptions, utils
from secrets_safe_library.authentication import Authentication
from secrets_safe_library.constants.endpoints import (
    POST_SECRETS_SAFE_FOLDERS_FOLDERID,
    POST_SECRETS_SAFE_FOLDERS_FOLDERID_FILE,
    POST_SECRETS_SAFE_FOLDERS_FOLDERID_TEXT,
    PUT_SECRETS_SAFE_SECRETS_SECRETID,
    PUT_SECRETS_SAFE_SECRETS_SECRETID_FILE,
    PUT_SECRETS_SAFE_SECRETS_SECRETID_TEXT,
)
from secrets_safe_library.core import APIObject
from secrets_safe_library.mapping.secrets import fields as secrets_fields
from secrets_safe_library.validators.secrets import SecretsValidator


class SecretsSafe(APIObject, SecretsValidator):
    _separator: str = None
    _decrypt: bool = None

    def __init__(
        self,
        authentication: Authentication,
        logger: logging.Logger = None,
        separator: str = "/",
        decrypt: bool = None,
    ):
        """
        Initialize a SecretsSafe client used to interact with the Secrets Safe API.
        Args:
            authentication (Authentication): Authentication handler used to make
                authorized requests to the API.
            logger (logging.Logger, optional): Logger instance to use for emitting
                diagnostic messages. If None, the default logger behavior from
                the base class is used.
            separator (str, optional): Path separator used when building and
                parsing secret paths (for example, between folder and secret
                name). Must resolve to a single non-whitespace character after
                stripping. Defaults to "/".
            decrypt (bool, optional): Whether to request decrypted secret values
                when retrieving them. If True, decrypted values are requested;
                if False, encrypted values may be returned depending on server
                support. If None, the server-side default behavior is used.
        """
        super().__init__(authentication, logger, endpoint="/secrets-safe/secrets")

        if len(separator.strip()) != 1:
            raise exceptions.LookupError(f"Invalid separator: {separator}")

        self._separator = separator
        self._decrypt = decrypt

        # Initialize the SecretsValidator parent class
        SecretsValidator.__init__(self)

    def set_decrypt(self, decrypt: bool) -> None:
        """
        Set the decrypt attribute
        Arguments:
        - True: request decrypted secret values.
        - False: request encrypted secret values, if supported by the server.
        - None: use the server-side default behavior.
        """

        self._decrypt = decrypt

    def get_secret(self, path: str) -> str:
        """
        Get secret by path
        Arguments:
            path (str): secret path
        Returns:
            Retrieved secret string

        """

        utils.print_log(
            self._logger,
            "Running get_secret method in SecretsSafe class",
            logging.DEBUG,
        )
        secrets_dict = self.secrets_by_path_flow(paths=[path])
        return secrets_dict[path]

    def get_secret_with_metadata(self, path: str) -> dict:
        """
        Get secret by path with metadata
        Arguments:
            path (str): secret path
        Returns:
           Retrieved secret in dict format
        """

        utils.print_log(
            self._logger,
            "Running get_secret method in SecretsSafe class",
            logging.DEBUG,
        )
        secrets_dict = self.secrets_by_path_flow(paths=[path], get_metadata=True)
        return secrets_dict

    def get_secrets(self, paths: list) -> dict:
        """
        Get secrets by paths
        Arguments:
            paths (list): list of secret paths
        Returns:
            Retrieved secret in dict format
        """

        utils.print_log(
            self._logger,
            "Running get_secrets method in SecretsSafe class",
            logging.INFO,
        )
        secrets_dict = self.secrets_by_path_flow(paths=paths)
        return secrets_dict

    def get_secrets_with_metadata(self, paths: list):
        """
        Get secrets by paths with metadata
        Arguments:
            paths (list): list of secret paths
        Returns:
            Retrieved secret in dict format
        """

        utils.print_log(
            self._logger,
            "Running get_secrets method in SecretsSafe class",
            logging.INFO,
        )
        secrets_dict = self.secrets_by_path_flow(paths=paths, get_metadata=True)
        return secrets_dict

    def get_all_secrets_by_folder_path(self, folder_path: str) -> dict:
        """
        Get all secrets by folder path
        Arguments:
            folder_path (str): folder path
        Returns:
            Response (Dict)
        """

        response = {}
        secret_response = self.get_secret_by_path(
            folder_path, None, self._separator, send_title=False
        )
        for secret in secret_response.json():
            secret_path = f"{secret['FolderPath']}/{secret['Title']}"
            response[f"{secret_path}-metadata"] = secret
            if secret["SecretType"] == "File":
                response[secret_path] = self.get_file_secret_data(secret["Id"])
            else:
                response[secret_path] = secret["Password"]
        return response

    def get_file_secret_data(self, secret_id) -> str:
        """
        Gets secret file as an attachment based on secretId.

        API: GET Secrets-Safe/Secrets/{secretId:guid}/file/download

        Args:
            secret_id (str): The secret id (GUID).

        Returns:
            file secret content (str).
        """

        utils.print_log(self._logger, "Getting secret by file", logging.DEBUG)
        try:
            file_response = self._get_file_by_id_req(secret_id)
        except exceptions.LookupError as e:
            raise exceptions.LookupError(f"Error getting file by id: {e}")

        return file_response.text

    def secrets_by_path_flow(self, paths: list, get_metadata: bool = False) -> dict:
        """
        Secrets by path flow
        Arguments:
            paths (list): list of secret paths
            get_metadata (bool): whether to get secret metadata or not.
        Returns:
            Response (Dict)
        """

        response = {}
        for path in paths:

            if not path:
                continue

            data = path.split(self._separator)

            if len(data) < 2:
                raise exceptions.LookupError(
                    f"Invalid secret path: {path}, check your path and title separator,"
                    f" separator must be: {self._separator}"
                )

            folder_path = data[:-1]
            title = data[-1]

            try:
                secret_response = self.get_secret_by_path(
                    path=self._separator.join(folder_path),
                    title=title,
                    separator=self._separator,
                )
            except exceptions.LookupError as e:
                raise exceptions.LookupError(f"Error getting secret by path: {e}")

            secret = secret_response.json()
            if secret:
                if get_metadata:
                    response[f"{path}-metadata"] = secret[0]

                if secret[0]["SecretType"] == "File":
                    response[path] = self.get_file_secret_data(secret[0]["Id"])
                else:
                    response[path] = secret[0]["Password"]

                utils.print_log(
                    self._logger, "A secret was successfully retrieved", logging.INFO
                )
            else:
                raise exceptions.LookupError(f"{path}, Secret was not found")

        return response

    def get_secret_by_path(
        self, path: str, title: str, separator: str, send_title: bool = True
    ) -> requests.Response:
        """
        Get secrets by path and title.
        Arguments:
            path (str): The path where the secret is stored.
            title (str): The title used to identify the secret.
            separator (str): The separator used in the secret storage format.
            send_title (bool, optional): Flag to determine if the title should be
                included in the request. Defaults to True.
        Returns:
            requests.Response: A response object containing the secret.

        Raises:
            exceptions.OptionsError: If any of the schema rules are not valid.
        """

        path_depth = path.count(separator) + 1
        attributes = {"path": path, "title": title, "path_depth": path_depth}

        # Use the new SecretsValidator instead of the old Cerberus validator
        self.validate(attributes, operation="get_secret_by_path")

        query_params = {"path": path, "separator": separator}

        if self._decrypt is not None:
            query_params["decrypt"] = str(self._decrypt).lower()

        if self._authentication._api_version:
            query_params["version"] = self._authentication._api_version

        if send_title:
            query_params["title"] = title

        params = urlencode(query_params)

        endpoint = f"{self.endpoint}?{params}"

        utils.print_log(
            self._logger,
            "Calling get_secret_by_path endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint)
        return response

    def _get_file_by_id_req(self, secret_id):
        """
        Get a File secret by File id
        Arguments:
            secret id
        Returns:
            File secret text
        """

        endpoint = f"{self.endpoint}/{secret_id}/file/download"

        utils.print_log(
            self._logger,
            "Calling _get_file_by_id_req endpoint",
            logging.DEBUG,
        )
        response = self._run_get_request(endpoint)
        return response

    def get_secret_by_id(self, secret_id: str) -> dict:
        """
        Find a secret by ID.

        API: GET Secrets-Safe/Secrets/{secretId:guid}

        Args:
            secret_id (str): The secret ID (GUID).

        Returns:
            dict: Secret object according requested API version.

        Raises:
            exceptions.LookupError: Raised when no secret is found using secret_id.
        """

        endpoint = f"{self.endpoint}/{secret_id}"

        utils.print_log(
            self._logger,
            "Calling get_secret_by_id endpoint",
            logging.DEBUG,
        )

        try:
            response = self._run_get_request(endpoint)
        except exceptions.LookupError as e:
            raise exceptions.LookupError(f"Error getting secret by id: {e}")

        return response.json()

    def list_secrets(
        self,
        path: str = None,
        separator: str = None,
        title: str = None,
        afterdate: str = None,
        limit: int = None,
        offset: int = None,
    ) -> list:
        """
        Returns a list of secrets with the option to filter the list using query
        parameters.

        API: GET Secrets-Safe/Secrets

        Args:
            path (str): the full path to the secret.
            separator (str): the separator used in the path above. Default is /.
            title (str): the full title of the secret.
            afterdate (str): filter by modified or created on, after, or equal to the
            given date. Must be in the following UTC format: yyyy-MM-ddTHH:mm:ssZ.
            limit (int): limit the results.
            offset (int): skip the first (offset) number of secrets.
        Returns:
            list: List of secrets matching specified arguments.
        """

        params = {
            "path": path,
            "separator": separator,
            "title": title,
            "afterdate": afterdate,
            "limit": limit,
            "offset": offset,
        }

        query_params = {k: v for k, v in params.items() if v is not None}

        if self._decrypt is not None:
            query_params["decrypt"] = str(self._decrypt).lower()

        query_string = urlencode(query_params)
        endpoint = f"{self.endpoint}?{query_string}"

        utils.print_log(self._logger, "Calling list_secrets endpoint", logging.DEBUG)

        try:
            response = self._run_get_request(endpoint)
        except exceptions.LookupError as e:
            raise exceptions.LookupError(f"Error getting secrets: {e}")

        return response.json()

    def list_secrets_by_folder_id(self, folder_id: str = None) -> list:
        """
        Returns a list of secrets with the option to filter the list using query
        parameters.

        API: GET Secrets-Safe/Folders/{folderId:guid}/secrets

        Args:
            folder_id (str): The folder GUID.

        Returns:
            list: List of secrets for the given folder_id.
        """

        params = {"folderId": folder_id}
        query_string = urlencode(params)
        endpoint = f"{self.endpoint}?{query_string}"

        utils.print_log(
            self._logger,
            "Calling list_secrets_by_folder_id endpoint",
            logging.DEBUG,
        )

        try:
            response = self._run_get_request(endpoint)
        except exceptions.LookupError as e:
            raise exceptions.LookupError(f"Error getting secrets by folder: {e}")

        return response.json()

    def create_secret(
        self,
        title: str,
        folder_id: str,
        description: str = None,
        username: str = None,  # Used for normal Secrets
        password: str = None,  # Used for normal Secrets
        text: str = None,  # Used for Text Secrets
        file_path: str = None,  # Used for File Secrets
        owner_id: int = None,
        owner_type: str = None,
        owners: list = None,
        password_rule_id: int = None,
        notes: str = None,
        urls: list = None,
    ) -> dict:
        """
        Creates a Secret (Normal Secret, Text o File) using provided parameters
        according configured version.

        API:
            - POST Secrets-Safe/Folders/{folderId:guid}/secrets
            - POST Secrets-Safe/Folders/{folderId:guid}/secrets/text
            - POST Secrets-Safe/Folders/{folderId:guid}/secrets/file

        Args:
            title (str): The full title of the secret.
            folder_id (str): The GUID of the folder where secrets will be created.
            description (str, optional): The description of the secret.
            username (str, optional): The username for normal Secrets.
            password (str, optional): The password for normal Secrets.
            text (str, optional): The text content for Text Secrets.
            file_path (str, optional): The path to the file for File Secrets.
            owner_id (int, optional): The ID of the owner.
            owner_type (str, optional): The type of the owner.
            owners (list, optional): A list of owners.
            password_rule_id (int, optional): The ID of the password rule.
            notes (str, optional): Notes about the secret.
            urls (list, optional): A list of URLs with this format
                {'Id': GUID, 'CredentialId': GUID, 'Url': string}.

        Returns:
            dict: Created secret object according requested API version.
        """

        attributes = {
            "title": title,
            "description": description,
            "notes": notes,
            "owner_id": owner_id,
            "owner_type": owner_type,
            "owners": owners,
            "urls": urls,
        }

        # Identify which request body is being used
        if username:
            attributes.update(
                {
                    "username": username,
                    "password": password,
                }
            )

            self.validate(
                attributes,
                operation="create_credential_secret",
                version=self._authentication._api_version,
            )

            partial_endpoint = "secrets"
            utils.print_log(
                self._logger,
                f"Creating a normal secret: {partial_endpoint}",
                logging.DEBUG,
            )
            req_structure = self.get_request_body_version(
                secrets_fields, POST_SECRETS_SAFE_FOLDERS_FOLDERID
            )
        elif text:
            attributes.update({"text": text})

            self.validate(
                attributes,
                operation="create_text_secret",
                version=self._authentication._api_version,
            )

            partial_endpoint = "secrets/text"
            utils.print_log(
                self._logger,
                f"Creating a text secret: {partial_endpoint}",
                logging.DEBUG,
            )
            req_structure = self.get_request_body_version(
                secrets_fields, POST_SECRETS_SAFE_FOLDERS_FOLDERID_TEXT
            )
        elif file_path:
            attributes.update({"file_path": file_path})

            self.validate(
                attributes,
                operation="create_file_secret",
                version=self._authentication._api_version,
            )

            partial_endpoint = "secrets/file"
            utils.print_log(
                self._logger,
                f"Creating a file secret: {partial_endpoint}",
                logging.DEBUG,
            )
            req_structure = self.get_request_body_version(
                secrets_fields, POST_SECRETS_SAFE_FOLDERS_FOLDERID_FILE
            )
        else:
            raise exceptions.IncompleteArgumentsError(
                "Either username, text or file_path is required"
            )

        req_body = self.generate_request_body(
            req_structure,
            title=title,
            description=description,
            username=username,
            password=password,
            text=text,
            file_path=file_path,
            owner_id=owner_id,
            owner_type=owner_type,
            owners=owners,
            password_rule_id=password_rule_id,
            notes=notes,
            urls=urls,
            folder_id=folder_id,
        )

        endpoint = f"/secrets-safe/folders/{folder_id}/{partial_endpoint}"

        if partial_endpoint == "secrets/file":
            utils.print_log(
                self._logger,
                "Calling _run_post_file_request",
                logging.DEBUG,
            )
            response = self._run_post_file_request(
                endpoint,
                req_body,
                file_path=file_path,
            )
        else:
            utils.print_log(
                self._logger,
                "Calling _run_post_request",
                logging.DEBUG,
            )
            response = self._run_post_request(endpoint, req_body)

        return response.json()

    def delete_secret_by_id(self, secret_id: str) -> None:
        """
        Delete a secret by ID.

        API: DELETE Secrets-Safe/Secrets/{secretId:guid}/

        Args:
            secret_id (str): The secret ID (GUID).

        Returns:
            None: If deletion is successful no exceptions.DeletionError is raised.
        """

        endpoint = f"{self.endpoint}/{secret_id}"

        utils.print_log(
            self._logger,
            "Calling delete_secret_by_id endpoint",
            logging.DEBUG,
        )
        self._run_delete_request(endpoint)

    def update_secret(
        self,
        secret_id: str,
        folder_id: str = None,
        title: str = None,
        description: str = None,
        username: str = None,  # Used for normal Secrets
        password: str = None,  # Used for normal Secrets
        text: str = None,  # Used for Text Secrets
        file_path: str = None,  # Used for File Secrets
        owner_id: int = None,
        owner_type: str = None,
        owners: list = None,
        password_rule_id: int = None,
        notes: str = None,
        urls: list = None,
    ) -> dict | None:
        """
        Updates a Secret (Normal Secret, Text o File) using provided parameters
        according configured version.

        API:
            - PUT Secrets-Safe/Secrets/{secretId:guid}/
            - PUT Secrets-Safe/Secrets/{secretId:guid}/text
            - PUT Secrets-Safe/Secrets/{secretId:guid}/file

        Args:
            secret_id (str): The ID of the secret to update.
            folder_id (str): The GUID of the folder where secrets will be created.
            title (str, optional): The full title of the secret.
            description (str, optional): The description of the secret.
            username (str, optional): The username for normal Secrets.
            password (str, optional): The password for normal Secrets.
            text (str, optional): The text content for Text Secrets.
            file_path (str, optional): The path to the file for File Secrets.
            owner_id (int, optional): The ID of the owner.
            owner_type (str, optional): The type of the owner.
            owners (list, optional): A list of owners.
            password_rule_id (int, optional): The ID of the password rule.
            notes (str, optional): Notes about the secret.
            urls (list, optional): A list of URLs with this format
                {'Id': GUID, 'CredentialId': GUID, 'Url': string}.

        Returns:
            dict: Created secret object according requested API version.
        """

        attributes = {
            "title": title,
            "description": description,
            "notes": notes,
            "folder_id": folder_id,
            "owner_id": owner_id,
            "owner_type": owner_type,
            "owners": owners,
            "urls": urls,
        }

        # Identify which request body is being used and validate accordingly
        partial_endpoint = ""
        if username:
            attributes.update(
                {
                    "username": username,
                    "password": password,
                    "password_rule_id": password_rule_id,
                }
            )

            self.validate(
                attributes,
                operation="update_credential_secret",
                version=self._authentication._api_version,
            )

            utils.print_log(
                self._logger,
                f"Updating a normal secret: {partial_endpoint}",
                logging.DEBUG,
            )
            req_structure = self.get_request_body_version(
                secrets_fields, PUT_SECRETS_SAFE_SECRETS_SECRETID
            )
        elif text:
            attributes.update({"text": text})
            self.validate(
                attributes,
                operation="update_text_secret",
                version=self._authentication._api_version,
            )

            partial_endpoint = "text"
            utils.print_log(
                self._logger,
                f"Updating a text secret: {partial_endpoint}",
                logging.DEBUG,
            )
            req_structure = self.get_request_body_version(
                secrets_fields, PUT_SECRETS_SAFE_SECRETS_SECRETID_TEXT
            )
        elif file_path:
            self.validate(
                attributes,
                operation="update_file_secret",
                version=self._authentication._api_version,
            )

            partial_endpoint = "file"
            utils.print_log(
                self._logger,
                f"Updating a file secret: {partial_endpoint}",
                logging.DEBUG,
            )
            req_structure = self.get_request_body_version(
                secrets_fields, PUT_SECRETS_SAFE_SECRETS_SECRETID_FILE
            )
        else:
            raise exceptions.IncompleteArgumentsError(
                "Either username, text or file_path is required"
            )

        req_body = self.generate_request_body(
            req_structure,
            title=title,
            description=description,
            username=username,
            password=password,
            text=text,
            file_path=file_path,
            owner_id=owner_id,
            owner_type=owner_type,
            owners=owners,
            password_rule_id=password_rule_id,
            notes=notes,
            urls=urls,
            folder_id=folder_id,
        )

        endpoint = f"{self.endpoint}/{secret_id}/{partial_endpoint}"

        if file_path:
            utils.print_log(
                self._logger,
                "Calling _run_put_file_request",
                logging.DEBUG,
            )
            _ = self._run_put_file_request(
                endpoint,
                req_body,
                file_path=file_path,
            )
            # File PUT request returns a 204 No content, so no need to return anything
            return
        else:
            utils.print_log(
                self._logger,
                "Calling _run_put_request",
                logging.DEBUG,
            )
            response = self._run_put_request(endpoint, req_body)

        return response.json()
