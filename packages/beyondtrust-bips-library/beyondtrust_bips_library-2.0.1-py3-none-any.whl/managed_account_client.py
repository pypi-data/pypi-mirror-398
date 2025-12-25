import logging
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from secrets_safe_library import authentication, cert_util, managed_account, utils

env = os.environ

CLIENT_ID = env["CLIENT_ID"] if "CLIENT_ID" in env else None
CLIENT_SECRET = env["CLIENT_SECRET"] if "CLIENT_SECRET" in env else None
API_URL = env["API_URL"] if "API_URL" in env else None
VERIFY_CA = (
    False if "VERIFY_CA" in env and env["VERIFY_CA"].lower() == "false" else True
)
MANAGED_ACCOUNT = env["MANAGED_ACCOUNT"].strip() if "MANAGED_ACCOUNT" in env else None
MANAGED_ACCOUNT_LIST = (
    env["MANAGED_ACCOUNT_LIST"].strip().split(",")
    if "MANAGED_ACCOUNT_LIST" in env and env["MANAGED_ACCOUNT_LIST"].strip() != ""
    else None
)

API_KEY = env.get("API_KEY")

LOGGER_NAME = "custom_logger"

TIMEOUT_CONNECTION_SECONDS = 30
TIMEOUT_REQUEST_SECONDS = 30

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
                certificate=certificate,
                certificate_key=certificate_key,
                verify_ca=VERIFY_CA,
                logger=logger,
                api_key=API_KEY,
            )

            get_api_access_response = authentication_obj.get_api_access()

            if get_api_access_response.status_code != 200:
                utils.print_log(
                    logger,
                    f"Please check credentials, error {get_api_access_response.text}",
                    logging.ERROR,
                )
                return

            if not MANAGED_ACCOUNT and not MANAGED_ACCOUNT_LIST:
                utils.print_log(
                    logger,
                    "Nothing to do, MANAGED_ACCOUNT and MANAGED_ACCOUNT_LIST parameters"
                    " are empty!",
                    logging.ERROR,
                )
                return

            managed_account_obj = managed_account.ManagedAccount(
                authentication=authentication_obj, logger=logger, separator="*"
            )

            if MANAGED_ACCOUNT:
                # Response could be logged if needed in development env
                _ = managed_account_obj.get_secret(MANAGED_ACCOUNT)
            if MANAGED_ACCOUNT_LIST:
                # Response could be logged if needed in development env
                _ = managed_account_obj.get_secrets(MANAGED_ACCOUNT_LIST)

            authentication_obj.sign_app_out()

        del session

    except Exception as e:
        utils.print_log(logger, e, logging.ERROR)


# calling main method
main()
