"""
This file contains the fields mapping for each endpoint and version related to
Entity Types.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/password-safe-api
"""

from secrets_safe_library.constants.endpoints import GET_ENTITY_TYPES
from secrets_safe_library.constants.versions import Version

fields = {
    GET_ENTITY_TYPES: {
        Version.DEFAULT.value: [
            "EntityTypeID",
            "Name",
            "Description",
        ],
    },
}
