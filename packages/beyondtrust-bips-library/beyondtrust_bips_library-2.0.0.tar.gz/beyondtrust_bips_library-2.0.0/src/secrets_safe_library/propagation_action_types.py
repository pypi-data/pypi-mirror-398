"""
Propagation Action Types module, all the logic to manage Propagation Action Types
from Password Safe API
"""

import logging

from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import ListMixin


class PropagationActionTypes(APIObject, ListMixin):
    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/propagationactiontypes")
