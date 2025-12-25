"""Authentication Module, all the logic to authenticate in PS API"""

import json
import logging
import tempfile
from urllib.parse import urlparse

import requests

from secrets_safe_library import exceptions, utils

TIMEOUT_CONNECTION_SECONDS = 30
TIMEOUT_REQUEST_SECONDS = 30


class Authentication:

    _api_url = None
    _client_id = None
    _client_secret = None
    _verify_ca = True
    _token = None
    _certificate = None
    _certificate_key = None
    _sig_app_in_url = None
    _api_token = None
    _req = None
    _logger = None
    _timeout_connection_seconds = None
    _timeout_request_seconds = None
    _api_key = None
    _api_version = None

    def __init__(
        self,
        req: requests.sessions.Session = None,
        timeout_connection: int = 0,
        timeout_request: int = 0,
        api_url: str = "",
        client_id: str | None = None,
        client_secret: str | None = None,
        certificate: str | None = None,
        certificate_key: str | None = None,
        verify_ca: bool = True,
        logger: logging.Logger | None = None,
        api_key: str | None = None,
        api_version: str | None = None,
    ):

        self.validate_input("api_url", api_url)

        attributes = {}

        if api_version:
            attributes.update({"api_version": api_version})

        if api_key:
            attributes.update({"api_url": api_url, "api_key": api_key})
            inputs = utils.validate_inputs(attributes)
        else:
            self.validate_input("client_id", client_id)
            self.validate_input("client_secret", client_secret)
            attributes.update(
                {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "api_url": api_url,
                }
            )
            inputs = utils.validate_inputs(attributes)
            self._client_id = inputs["client_id"]
            self._client_secret = inputs["client_secret"]

        self._api_version = api_version

        self._api_url = inputs["api_url"]
        self._verify_ca = verify_ca
        self._sig_app_in_url = f"{self._api_url}/Auth/SignAppIn"
        self._certificate = certificate
        self._certificate_key = certificate_key
        self._logger = logger
        self._timeout_connection_seconds = (
            timeout_connection or TIMEOUT_CONNECTION_SECONDS
        )
        self._timeout_request_seconds = timeout_request or TIMEOUT_REQUEST_SECONDS
        self._api_key = api_key

        utils.print_log(
            self._logger,
            "How long to wait for the server to connect and send data before "
            f"giving up: connection timeout: {self._timeout_connection_seconds} seconds"
            f", request timeout {self._timeout_request_seconds} seconds",
            logging.DEBUG,
        )

        self._req = req

        if not self._verify_ca:
            utils.print_log(
                self._logger,
                "verify_ca=false is insecure, it instructs the caller to not verify "
                "the certificate authority when making API calls.",
                logging.WARNING,
            )
            self._req.verify = False

    def oauth(self):
        """
        Get API Token
        Arguments:
            Client Id
            Secret
        Returns:
            Token
        """

        endpoint_url = self._api_url + "/Auth/connect/token"
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        auth_info = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "client_credentials",
        }

        response = self._req.post(
            endpoint_url,
            auth_info,
            header,
            verify=self._verify_ca,
            timeout=(self._timeout_connection_seconds, self._timeout_request_seconds),
        )

        return response

    def sign_app_in(self):
        """
        Sign in to Secret safe API
        Arguments:
        Returns:
            logged user
        """

        utils.print_log(
            self._logger, f"Calling sign_app_in endpoint: {self._api_url}", logging.INFO
        )
        return self.send_post_sign_app_in()

    def get_api_access(self):
        """
        Get API Access
        Arguments:
        Returns:
            Result of sign_app_in call
        """

        if self._api_key:
            return self.sign_app_in()

        oauth_response = self.oauth()

        if oauth_response.status_code != 200:
            raise exceptions.AuthenticationFailure(
                f"Error getting token, message: {oauth_response.text}, statuscode: "
                f"{oauth_response.status_code}"
            )

        token_object = json.loads(oauth_response.text)
        self._api_token = token_object["access_token"]
        return self.sign_app_in()

    def sign_app_out(self):
        """
        Sign out to Secret safe API
        Arguments:
        Returns:
            Status of the action
        """
        url = f"{self._api_url}/Auth/Signout"
        utils.print_log(
            self._logger, f"Calling sign_app_out endpoint: {url}", logging.DEBUG
        )

        # Connection : close - tells secrets safe to close the session.
        response = self._req.post(
            url,
            timeout=(self._timeout_connection_seconds, self._timeout_request_seconds),
        )
        if response.status_code == 200:
            return True

    def send_post_sign_app_in(self):
        """
        Send Post request to Sign app in service
        Arguments:
        Returns:
            Service URL
            Certificate
        """

        headers = {"Authorization": f"Bearer {self._api_token}"}

        if self._api_key:
            utils.print_log(self._logger, "Using API key Authentication", logging.DEBUG)
            headers = {"Authorization": f"PS-Auth key={self._api_key}"}

        if self._certificate and self._certificate_key:
            with tempfile.NamedTemporaryFile(
                delete=True, mode="w", suffix=".pem"
            ) as cert_file:
                cert_file.write(self._certificate)
                cert_file.flush()

                with tempfile.NamedTemporaryFile(
                    delete=True, mode="w", suffix=".pem"
                ) as key_file:
                    key_file.write(self._certificate_key)
                    key_file.flush()

                    response = self._req.post(
                        self._sig_app_in_url,
                        headers=headers,
                        cert=(cert_file.name, key_file.name),
                    )
        else:
            response = self._req.post(self._sig_app_in_url, headers=headers)

        del headers

        return response

    def validate_input(self, parameter_name, parameter_value):
        """
        Validate input
        Arguments:
            Parameter name
            Parameter Value
        Returns:
        """
        if not parameter_value:
            raise exceptions.OptionsError(f"{parameter_name} parameter is missing")

        if parameter_name.lower() == "api_url":
            try:
                parsed_url = urlparse(parameter_value)
                all([parsed_url.scheme, parsed_url.netloc])
            except Exception:
                raise exceptions.OptionsError(
                    f"Url {parameter_value} is not valid, please check format"
                )
