"""Utils module"""

import ast
import logging

from cerberus import Validator

from secrets_safe_library import exceptions
from secrets_safe_library.security import sanitize_sensitive_data


def print_log(logger, log_message, level):
    """
    Print a log message with automatic sanitization of sensitive information.

    This function automatically detects and redacts sensitive information such as:
    - API keys and tokens
    - Passwords and secrets
    - Certificate data
    - Authorization headers
    - Database credentials
    - URLs with embedded credentials

    All log levels (including DEBUG) are sanitized by default for security.

    Arguments:
        logger: Logger instance
        log_message: Message to log (will be sanitized)
        level: Log level (DEBUG, INFO, ERROR, WARN)
    Returns:
        None
    """
    if logger:
        # Sanitize the message
        log_message = sanitize_sensitive_data(log_message)

        if level == logging.DEBUG:
            logger.debug(log_message)
        elif level == logging.INFO:
            logger.info(log_message)
        elif level == logging.ERROR:
            logger.error(log_message)
        elif level == logging.WARN:
            logger.warning(log_message)


def validate_inputs(inputs):
    """
    Validate inputs
    Arguments:
        inputs (dict)
    Returns:
        inputs (dict)
    """

    schema = {
        "api_url": {
            "type": "string",
            "regex": r"^(https?|http)://[^\s/$.?#].[^\s]*$",
            "required": True,
        }
    }

    if "api_version" in inputs:
        schema.update(
            {
                "api_version": {
                    "type": "string",
                    "minlength": 3,
                    "maxlength": 3,
                    "required": False,
                }
            }
        )

    if "api_key" in inputs:
        schema.update(
            {
                "api_key": {
                    "type": "string",
                    "minlength": 128,
                    "maxlength": 263,
                    "required": True,
                }
            }
        )
    else:
        schema.update(
            {
                "client_id": {
                    "type": "string",
                    "minlength": 36,
                    "maxlength": 40,
                    "required": True,
                },
                "client_secret": {
                    "type": "string",
                    "minlength": 36,
                    "maxlength": 64,
                    "required": True,
                },
            }
        )

    v = Validator(schema)

    if v.validate(inputs):
        if "/BeyondTrust/api/public/v" not in inputs["api_url"]:
            raise exceptions.OptionsError(
                "invalid API URL, it must contains /BeyondTrust/api/public/v as part of"
                " the path"
            )

        inputs["api_url"] = inputs["api_url"].strip()

    else:
        raise exceptions.OptionsError(f"Errors: {v.errors}")

    return inputs


def prepare_certificate_info(certificate, certificate_key):
    """
    Validate certificate and certificate key
    Arguments:
        certificate
        certificate_key
    Returns:
        certificate
        certificate_key

    """

    if certificate and certificate_key:

        certificate_length_in_bits = len(certificate.encode("utf-8")) * 8

        if certificate_length_in_bits > 32768:
            message = "Invalid length for certificate, the maximum size is 32768 bits"
            raise exceptions.OptionsError(message)

        certificate_key_length_in_bits = len(certificate_key.encode("utf-8")) * 8

        if certificate_key_length_in_bits > 32768:
            message = (
                "Invalid length for certificate key, the maximum size is 32768 bits"
            )
            raise exceptions.OptionsError(message)

        if "BEGIN CERTIFICATE" not in certificate:
            raise exceptions.OptionsError("Bad certificate content")

        if "BEGIN PRIVATE KEY" not in certificate_key:
            raise exceptions.OptionsError("Bad certificate key content")

        certificate = certificate.replace(r"\n", "\n")
        certificate_key = certificate_key.replace(r"\n", "\n")

        certificate = f"{certificate}\n"
        certificate_key = f"{certificate_key}\n"

        return certificate, certificate_key

    return "", ""


def convert_as_literal(elements: list) -> list | None:
    """
    Converts a list of elements from string representation to actual strings, bytes,
    numbers, tuples, lists, dicts, sets, booleans, and None.

    Args:
        elements (list): A list of elements to be converted as its literal
        representation.

    Returns:
        list | None: A list of elements converted to their literal representation,
        or None if the input is empty or None.
    """
    if elements and isinstance(elements, list):
        try:
            elements = [
                ast.literal_eval(e) if isinstance(e, str) else e for e in elements
            ]
        except Exception as e:
            raise exceptions.OptionsError(
                f"Invalid element format in elements: {elements}"
            ) from e

    return elements
