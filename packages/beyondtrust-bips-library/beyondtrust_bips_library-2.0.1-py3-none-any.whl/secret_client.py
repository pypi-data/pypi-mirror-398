import logging
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from secrets_safe_library import authentication, cert_util, secrets_safe, utils

env = os.environ

CLIENT_ID = env["CLIENT_ID"] if "CLIENT_ID" in env else None
CLIENT_SECRET = env["CLIENT_SECRET"] if "CLIENT_SECRET" in env else None
API_URL = env["API_URL"] if "API_URL" in env else None
VERIFY_CA = (
    False if "VERIFY_CA" in env and env["VERIFY_CA"].lower() == "false" else True
)
SECRET = env["SECRET"].strip() if "SECRET" in env else None
SECRET_LIST = (
    env["SECRET_LIST"].strip().split(",")
    if "SECRET_LIST" in env and env["SECRET_LIST"].strip() != ""
    else None
)

API_KEY = None

LOGGER_NAME = "custom_logger"

# the recommended version is 3.1. If no version is specified,
# the default API version 3.0 will be used
RECOMMENDED_API_VERSION = "3.1"

logging.basicConfig(
    format="%(asctime)-5s %(name)-15s %(levelname)-8s %(message)s", level=logging.DEBUG
)

logger = logging.getLogger(LOGGER_NAME)

CERTIFICATE_PATH = None
if "CERTIFICATE_PATH" in env and len(env["CERTIFICATE_PATH"]) > 0:
    CERTIFICATE_PATH = env["CERTIFICATE_PATH"]

CERTIFICATE_PASSWORD = (
    env["CERTIFICATE_PASSWORD"]
    if "CERTIFICATE_PASSWORD" in env and CERTIFICATE_PATH
    else ""
)

TIMEOUT_CONNECTION_SECONDS = 30
TIMEOUT_REQUEST_SECONDS = 30


def main():
    try:

        decrypt_obj = cert_util.CertUtil(CERTIFICATE_PATH, CERTIFICATE_PASSWORD, logger)

        certificate = decrypt_obj.get_certificate()
        certificate_key = decrypt_obj.get_certificate_key()

        with requests.Session() as session:
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.2,
                status_forcelist=[400, 408, 500, 502, 503, 504],
                allowed_methods=["GET", "POST"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)

            certificate, certificate_key = utils.prepare_certificate_info(
                certificate, certificate_key
            )

            authentication_obj = authentication.Authentication(
                req=session,
                timeout_connection=TIMEOUT_CONNECTION_SECONDS,
                timeout_request=TIMEOUT_REQUEST_SECONDS,
                api_url=API_URL,
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                certificate=certificate,
                certificate_key=certificate_key,
                verify_ca=VERIFY_CA,
                logger=logger,
                api_version=RECOMMENDED_API_VERSION,
            )

            get_api_access_response = authentication_obj.get_api_access()

            if get_api_access_response.status_code != 200:
                utils.print_log(
                    logger,
                    f"Please check credentials, error {get_api_access_response.text}",
                    logging.ERROR,
                )
                return

            if not SECRET and not SECRET_LIST:
                utils.print_log(
                    logger,
                    "Nothing to do, SECRET and SECRET_LIST parameters are empty!",
                    logging.ERROR,
                )
                return

            secrets_safe_obj = secrets_safe.SecretsSafe(
                authentication=authentication_obj, logger=logger, separator="/"
            )

            if SECRET:
                # Response could be logged if needed in development env
                _ = secrets_safe_obj.get_secret(SECRET)
            if SECRET_LIST:
                # Response could be logged if needed in development env
                _ = secrets_safe_obj.get_secrets(SECRET_LIST)

            # get all secrets inside of a specific folder, using folder path.
            folder_path = "oauthgrp/folder1/test"
            # Response could be logged if needed in development env, omitting
            # here for security reasons
            _ = secrets_safe_obj.get_all_secrets_by_folder_path(folder_path)

            authentication_obj.sign_app_out()

        del session

    except Exception as e:
        utils.print_log(logger, e, logging.ERROR)


# calling main method
main()
