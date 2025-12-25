"""CertUtil Module"""

import logging
from pathlib import Path

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from cryptography.hazmat.primitives.serialization.pkcs12 import (
    load_key_and_certificates,
)

from secrets_safe_library import exceptions, utils


class CertUtil:

    _logger = None

    # Check the scope
    certificate = None
    certificate_key = None

    def __init__(self, certificate_path, certificate_password, logger=None):

        self._logger = logger
        self.set_certificate_data_from_pfx_file(certificate_path, certificate_password)

    def get_certificate(self):
        """
        Get certificate
        Arguments:
        Returns:
            certificate
        """
        if self.certificate:
            return str(self.certificate, encoding="utf-8")
        return None

    def get_certificate_key(self):
        """
        Get certificate key
        Arguments:
        Returns:
            certificate key
        """
        if self.certificate_key:
            return str(self.certificate_key, encoding="utf-8")
        return None

    def set_certificate_data_from_pfx_file(
        self, certificate_path, certificate_password
    ):
        """
        Decrypt .pfx file, get certificate key and cert content and set them to class
        attributes
        Arguments:
            certificate_path
            certificate_password
        Returns:
        """

        if not certificate_path:
            utils.print_log(
                self._logger, "Certificate was not configured", logging.INFO
            )
            self.certificate = None
            self.certificate_key = None
            return None

        try:
            self.certificate, self.certificate_key = (
                self.get_certificate_and_certificate_key(
                    certificate_path, certificate_password
                )
            )

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Certificate not found: {e}")
        except Exception as e:
            raise exceptions.AuthenticationFailure(
                f"Missing certificate password or incorrect certificate password: {e}"
            )

    def get_certificate_and_certificate_key(
        self, certificate_path, certificate_password
    ):
        """
        Get certificate and certificate key from pfx file
        Arguments:
            certificate_path
            certificate_password
        Returns:
        """
        pfx = Path(certificate_path).read_bytes()
        private_key, main_cert, _ = load_key_and_certificates(
            pfx, certificate_password.encode("utf-8"), None
        )
        return main_cert.public_bytes(Encoding.PEM), private_key.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
        )
