"""
This file contains the fields mapping for each endpoint and version related to Access
Policies.

More info for the fields included in each endpoint and version:
- https://docs.beyondtrust.com/bips/docs/passwordsafe-apis
"""

from secrets_safe_library.constants.endpoints import (
    GET_ACCESS_POLICIES,
    POST_ACCESS_POLICIES_TEST,
)
from secrets_safe_library.constants.versions import Version

fields = {
    GET_ACCESS_POLICIES: {
        Version.DEFAULT.value: [
            "AccessPolicyID",
            "Name:string",
            "Description",
            "Schedules",
        ],
    },
    POST_ACCESS_POLICIES_TEST: {
        Version.DEFAULT.value: [
            "AccessPolicyID",
            "Name:string",
            "Description",
            "Schedules",
        ],
    },
}
