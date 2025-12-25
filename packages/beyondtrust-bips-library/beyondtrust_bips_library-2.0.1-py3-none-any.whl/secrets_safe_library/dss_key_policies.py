"""
DSS Key Policies module, all the logic to manage DSS Key Policies from Password Safe API
"""

import logging

from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import GetByIdMixin, ListMixin


class DSSKeyPolicies(APIObject, ListMixin, GetByIdMixin):
    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/dsskeyrules")
