"""
This file contains the fields mapping for each endpoint and version related to Roles.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/password-safe-apis
"""

from secrets_safe_library.constants.endpoints import GET_ROLES
from secrets_safe_library.constants.versions import Version

fields = {
    GET_ROLES: {
        Version.DEFAULT.value: [
            "RoleID",
            "Name",
        ],
    },
}
