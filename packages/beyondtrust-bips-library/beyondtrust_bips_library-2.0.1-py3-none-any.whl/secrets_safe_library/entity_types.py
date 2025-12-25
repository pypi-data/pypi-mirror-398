"""Entity Types module, all the logic to manage entity types from PS API"""

import logging

from secrets_safe_library.authentication import Authentication
from secrets_safe_library.core import APIObject
from secrets_safe_library.mixins import ListMixin


class EntityType(APIObject, ListMixin):

    def __init__(self, authentication: Authentication, logger: logging.Logger = None):
        super().__init__(authentication, logger, endpoint="/entitytypes")
