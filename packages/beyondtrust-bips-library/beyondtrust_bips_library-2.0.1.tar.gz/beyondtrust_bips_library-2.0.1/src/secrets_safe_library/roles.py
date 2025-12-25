"""Roles module, all the logic to manage roles from PS API"""

import logging

from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import ListMixin


class Roles(APIObject, ListMixin):
    """
    Class to manage Roles from Password Safe API.

    This class provides methods to list registered roles.
    """

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/roles")
