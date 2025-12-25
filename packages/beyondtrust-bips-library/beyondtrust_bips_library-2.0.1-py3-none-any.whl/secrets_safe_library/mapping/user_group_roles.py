"""
This file contains the fields mapping for each endpoint and version related to
User group roles.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/password-safe-apis
"""

from secrets_safe_library.constants.endpoints import (
    GET_USERGROUPS_ID_SMARTRULES_ROLES,
    POST_USERGROUPS_ID_SMARTRULES_ROLES,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_USERGROUPS_ID_SMARTRULES_ROLES: {
        Version.DEFAULT.value: ["RoleID", "Name"],
    },
    POST_USERGROUPS_ID_SMARTRULES_ROLES: {
        Version.DEFAULT.value: {"Roles": [{"RoleID": int}], "AccessPolicyID": int},
    },
}
