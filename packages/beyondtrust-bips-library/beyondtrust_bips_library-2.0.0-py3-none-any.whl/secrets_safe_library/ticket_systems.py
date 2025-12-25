"""TicketSystems module, all the logic to manage ticket systems from PS API"""

import logging

from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import ListMixin


class TicketSystems(APIObject, ListMixin):
    """
    Class to manage Ticket Systems from Password Safe API.

    This class provides methods to list registered ticket systems.
    """

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/ticketsystems")
