"""
This file contains the fields mapping for each endpoint and version related to
Permissions.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/beyondinsight-apis
"""

from secrets_safe_library.constants.endpoints import (
    GET_PERMISSIONS,
    GET_USERGROUP_PERMISSIONS,
    POST_USERGROUP_PERMISSIONS,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_PERMISSIONS: {
        Version.DEFAULT.value: [
            "PermissionID",
            "Name",
        ],
    },
    GET_USERGROUP_PERMISSIONS: {
        Version.DEFAULT.value: [
            "PermissionID",
            "AccessLevelID",
        ],
    },
    POST_USERGROUP_PERMISSIONS: {
        Version.DEFAULT.value: {
            "PermissionID": int,
            "AccessLevelID": int,
        },
    },
}
