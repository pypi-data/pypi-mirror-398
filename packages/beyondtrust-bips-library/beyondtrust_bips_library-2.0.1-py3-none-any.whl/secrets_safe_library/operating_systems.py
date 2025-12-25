"""Operating Systems module, all the logic to manage operating systems from BI API"""

import logging

from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import ListMixin


class OperatingSystem(APIObject, ListMixin):
    """
    OperatingSystem class for managing operating systems via the PS API.

    This class provides functionality to list operating systems.
    Inherits from APIObject and ListMixin to provide basic API functionality
    and list operations.
    """

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/operatingsystems")
