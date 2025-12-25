"""
This file contains the fields mapping for each endpoint and version related to
WORKGROUPS.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-api
- https://docs.beyondtrust.com/bips/docs/secrets-safe-api
"""

from secrets_safe_library.constants.endpoints import (
    GET_WORKGROUPS,
    GET_WORKGROUPS_ID,
    GET_WORKGROUPS_NAME,
    POST_WORKGROUPS,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_WORKGROUPS: {
        Version.DEFAULT.value: [
            "OrganizationID",
            "Name",
        ],
    },
    GET_WORKGROUPS_ID: {
        Version.DEFAULT.value: [
            "OrganizationID",
            "ID",
            "Name",
        ],
    },
    GET_WORKGROUPS_NAME: {
        Version.DEFAULT.value: [
            "OrganizationID",
            "ID",
            "Name",
        ],
    },
    POST_WORKGROUPS: {
        Version.DEFAULT.value: {
            "OrganizationID": str,
            "Name": str,
        },
    },
}
