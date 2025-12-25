"""Password rules module, all the logic to manage Password rules from PS API"""

import logging

from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import GetByIdMixin, ListByKeyMixin, ListMixin


class PasswordRule(APIObject, GetByIdMixin, ListMixin, ListByKeyMixin):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/passwordrules")
